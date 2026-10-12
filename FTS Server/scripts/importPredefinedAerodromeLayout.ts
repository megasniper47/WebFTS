import path from 'path';
import fs from 'fs-extra';
import { v4 as uuidv4 } from 'uuid';

const sourceDir = path.resolve(__dirname, '../../vietnam_ats_routes_pack/vietnam_all_airports_webfts_input_package_FULL_FROM_APTDAT');
const datasetName = 'Vietnam All Airports Aerodrome Layout FULL FROM APTDAT';

async function run() {
  console.log(`Starting predefined import from: ${sourceDir}`);
  
  if (!await fs.pathExists(sourceDir)) {
    console.error(`Source directory not found: ${sourceDir}`);
    process.exit(1);
  }

  const datasetId = uuidv4();
  const datasetDir = path.resolve(__dirname, `../../data/aerodrome_layout/datasets/${datasetId}`);
  const normalizedDir = path.join(datasetDir, 'normalized');
  
  await fs.ensureDir(normalizedDir);

  const srcAirports = path.join(sourceDir, 'geojson_by_airport');
  const srcAllAirports = path.join(sourceDir, 'geojson_all_airports');
  
  const destAirports = path.join(normalizedDir, 'airports');
  const destAllAirports = path.join(normalizedDir, 'all_airports');

  console.log('Copying geojson_by_airport...');
  if (await fs.pathExists(srcAirports)) {
    await fs.copy(srcAirports, destAirports);
  }

  console.log('Copying geojson_all_airports...');
  if (await fs.pathExists(srcAllAirports)) {
    await fs.copy(srcAllAirports, destAllAirports);
  }

  // Generate metadata.json
  const dirs = await fs.readdir(destAirports).catch(() => []);
  const parsedIcaos = dirs.filter(d => d.startsWith('VV'));

  // Try to load the summary file to get counts if possible
  let stats = {
    runways: 0, pavements: 0, taxiway_centerlines: 0,
    gates: 0, taxiway_signs: 0, ground_markings: 0
  };

  const summaryFile = path.join(sourceDir, 'vietnam_all_airports_aerodrome_layout_FULL_FROM_APTDAT_summary.json');
  if (await fs.pathExists(summaryFile)) {
    try {
        const summary = await fs.readJson(summaryFile);
        stats.runways = summary.total_features?.runways || 0;
        stats.pavements = summary.total_features?.pavements || 0;
        stats.taxiway_centerlines = summary.total_features?.taxiway_centerlines || 0;
        stats.gates = summary.total_features?.gates || 0;
        stats.taxiway_signs = summary.total_features?.taxiway_signs || 0;
        stats.ground_markings = summary.total_features?.ground_markings || 0;
    } catch (e) {
        console.warn("Could not parse summary file, using 0s for stats");
    }
  }

  const metadata = {
    id: datasetId,
    name: datasetName,
    sourceType: "xplane_apt_dat",
    status: "parsed",
    country: "Vietnam",
    icaoPrefix: "VV",
    airportCount: parsedIcaos.length,
    vietnamAirportCount: parsedIcaos.length,
    parsedAirportIcaos: parsedIcaos,
    missingAirportIcaos: [],
    featureCounts: stats,
    warnings: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  await fs.writeJson(path.join(normalizedDir, 'dataset_metadata.json'), metadata, { spaces: 2 });

  console.log("===================================");
  console.log(`Import Complete!`);
  console.log(`Dataset ID: ${datasetId}`);
  console.log(`Airports Parsed: ${parsedIcaos.length}`);
  console.log(`Metadata saved to ${path.join(normalizedDir, 'dataset_metadata.json')}`);
  console.log("===================================");
}

run().catch(err => {
  console.error("Import failed:", err);
  process.exit(1);
});
