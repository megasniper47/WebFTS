import fs from 'fs-extra';
import readline from 'readline';
import path from 'path';
import { FeatureCollection, Feature, Polygon, LineString, Point, Position } from 'geojson';

interface ParseStats {
  airports: number;
  runways: number;
  taxiways: number;
  aprons: number;
  stands: number;
  taxiRoutes: number;
  holdShortLines: number;
  signs: number;
  lights: number;
  comms: number;
}

export class XplaneAptDatParser {
  private warnings: string[] = [];
  
  constructor() {}

  public async parseAptDat(
    sourcePath: string, 
    outputDir: string, 
    icaoPrefix: string = 'VV'
  ): Promise<{ parsedIcaos: string[], stats: ParseStats, warnings: string[] }> {
    
    await fs.ensureDir(outputDir);
    
    const stats: ParseStats = {
      airports: 0, runways: 0, taxiways: 0, aprons: 0, stands: 0, 
      taxiRoutes: 0, holdShortLines: 0, signs: 0, lights: 0, comms: 0
    };
    const parsedIcaos: string[] = [];

    const fileStream = fs.createReadStream(sourcePath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });

    let currentAirport: any = null;
    let currentPolygon: Position[] = [];
    let currentLine: Position[] = [];
    let isParsingPolygon = false;
    let isParsingLine = false;
    let lineType = ''; // e.g. solid, broken, hold_short
    
    // Feature collections for the current airport
    let runwaysFc: Feature[] = [];
    let apronsFc: Feature[] = [];
    let taxiwaysFc: Feature[] = [];
    let standsFc: Feature[] = [];
    let linesFc: Feature[] = [];
    let comms: any[] = [];

    const saveCurrentAirport = async () => {
      if (!currentAirport) return;
      if (!currentAirport.icao.startsWith(icaoPrefix)) return;
      
      const airportDir = path.join(outputDir, 'normalized', 'airports', currentAirport.icao);
      await fs.ensureDir(airportDir);

      // Save each feature collection
      const createFc = (features: Feature[]): FeatureCollection => ({
        type: "FeatureCollection",
        features
      });

      await fs.writeJson(path.join(airportDir, 'runways.geojson'), createFc(runwaysFc));
      await fs.writeJson(path.join(airportDir, 'aprons.geojson'), createFc(apronsFc));
      await fs.writeJson(path.join(airportDir, 'taxiways.geojson'), createFc(taxiwaysFc));
      await fs.writeJson(path.join(airportDir, 'stands.geojson'), createFc(standsFc));
      await fs.writeJson(path.join(airportDir, 'lines.geojson'), createFc(linesFc)); // includes hold short
      await fs.writeJson(path.join(airportDir, 'comms.json'), comms);
      
      const metadata = {
        icao: currentAirport.icao,
        name: currentAirport.name,
        elevation: currentAirport.elevation,
        features: {
          runways: runwaysFc.length,
          aprons: apronsFc.length,
          taxiways: taxiwaysFc.length,
          stands: standsFc.length,
          lines: linesFc.length,
          comms: comms.length
        }
      };
      await fs.writeJson(path.join(airportDir, 'metadata.json'), metadata);

      // Update global stats
      stats.airports++;
      stats.runways += runwaysFc.length;
      stats.aprons += apronsFc.length;
      stats.taxiways += taxiwaysFc.length;
      stats.stands += standsFc.length;
      stats.holdShortLines += linesFc.length; // rough estimate
      stats.comms += comms.length;
      
      parsedIcaos.push(currentAirport.icao);
    };

    for await (const line of rl) {
      const trimmed = line.trim();
      if (!trimmed || trimmed === '' || trimmed === '99') {
        continue;
      }
      
      // Handle file header
      if (trimmed.startsWith('I') || trimmed.startsWith('A') || trimmed.startsWith('1000 Version')) {
        continue;
      }

      const parts = trimmed.split(/\s+/);
      const rowCode = parseInt(parts[0], 10);

      // Airport Header (1, 16, 17)
      if (rowCode === 1 || rowCode === 16 || rowCode === 17) {
        if (currentAirport) {
          await saveCurrentAirport();
        }
        
        // 1 elevation_ft control_tower_has_freq 0 ICAO Name
        const elevation = parseInt(parts[1], 10);
        const icao = parts[4];
        const name = parts.slice(5).join(' ');
        
        currentAirport = { icao, name, elevation };
        
        runwaysFc = [];
        apronsFc = [];
        taxiwaysFc = [];
        standsFc = [];
        linesFc = [];
        comms = [];
        
        isParsingPolygon = false;
        isParsingLine = false;
        continue;
      }

      // If we are not in a valid prefix airport, we can skip parsing its details to save time
      if (currentAirport && !currentAirport.icao.startsWith(icaoPrefix)) {
        continue;
      }

      // Runways
      if (rowCode === 100) {
        // 100 width_m surface_type shoulder_type roughness centerline_lights edge_lights auto_dist_remaining ... lat1 lon1 ... lat2 lon2 ...
        const width = parseFloat(parts[1]);
        const surface = parseInt(parts[2], 10);
        const lat1 = parseFloat(parts[9]);
        const lon1 = parseFloat(parts[10]);
        const name1 = parts[8];
        const lat2 = parseFloat(parts[18]);
        const lon2 = parseFloat(parts[19]);
        const name2 = parts[17];
        
        const runwayGeom: LineString = {
          type: "LineString",
          coordinates: [[lon1, lat1], [lon2, lat2]]
        };
        
        runwaysFc.push({
          type: "Feature",
          geometry: runwayGeom,
          properties: {
            width,
            surface,
            designator: `${name1}/${name2}`
          }
        });
      }

      // Pavement/Apron/Taxiway (110)
      if (rowCode === 110) {
        isParsingPolygon = true;
        isParsingLine = false;
        currentPolygon = [];
      }
      
      // Linear features (120)
      if (rowCode === 120) {
        isParsingLine = true;
        isParsingPolygon = false;
        currentLine = [];
        lineType = parts[1] || 'unknown'; // often defines the type of marking
      }

      // Polygon / Line Nodes
      if (rowCode >= 111 && rowCode <= 116) {
        const lat = parseFloat(parts[1]);
        const lon = parseFloat(parts[2]);
        
        if (isParsingPolygon) {
          currentPolygon.push([lon, lat]);
          if (rowCode === 113 || rowCode === 114) { // Close polygon
            if (currentPolygon.length >= 3) {
              currentPolygon.push(currentPolygon[0]); // Close the loop
              const polyGeom: Polygon = {
                type: "Polygon",
                coordinates: [currentPolygon]
              };
              apronsFc.push({
                type: "Feature",
                geometry: polyGeom,
                properties: {}
              });
            }
            isParsingPolygon = false;
            currentPolygon = [];
          }
        } else if (isParsingLine) {
          currentLine.push([lon, lat]);
          if (rowCode === 113 || rowCode === 114 || rowCode === 115 || rowCode === 116) { // End of line (115/116 are just nodes but can terminate the segment in some contexts, but usually a new 120 or other row code terminates it).
            // Actually in X-Plane, 115, 116 are just nodes. We'll close the line if we see a non-node row code.
          }
        }
      } else {
        // If we hit a non-node row code, finish the current line if active
        if (isParsingLine && rowCode !== 120) {
          if (currentLine.length >= 2) {
            const lineGeom: LineString = {
              type: "LineString",
              coordinates: currentLine
            };
            linesFc.push({
              type: "Feature",
              geometry: lineGeom,
              properties: { type: lineType }
            });
          }
          isParsingLine = false;
          currentLine = [];
        }
      }

      // Stands / Gates (15)
      if (rowCode === 15) {
        // 15 lat lon heading type name
        const lat = parseFloat(parts[1]);
        const lon = parseFloat(parts[2]);
        const heading = parseFloat(parts[3]);
        const name = parts.slice(4).join(' ');
        
        const ptGeom: Point = {
          type: "Point",
          coordinates: [lon, lat]
        };
        standsFc.push({
          type: "Feature",
          geometry: ptGeom,
          properties: { heading, name }
        });
      }

      // Comms (50-59)
      if (rowCode >= 50 && rowCode <= 59) {
        const freq = parseFloat(parts[1]) / 100;
        const name = parts.slice(2).join(' ');
        comms.push({ type: rowCode, freq, name });
      }
    }

    // Save the last airport if it matches
    if (currentAirport) {
      if (isParsingLine && currentLine.length >= 2) {
        const lineGeom: LineString = {
          type: "LineString",
          coordinates: currentLine
        };
        linesFc.push({
          type: "Feature",
          geometry: lineGeom,
          properties: { type: lineType }
        });
      }
      await saveCurrentAirport();
    }

    return { parsedIcaos, stats, warnings: this.warnings };
  }
}
