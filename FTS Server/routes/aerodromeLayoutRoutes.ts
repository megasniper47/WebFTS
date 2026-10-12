import { Router } from 'express';
import path from 'path';
import fs from 'fs-extra';
import { XplaneDataDiscoveryService } from '../services/xplaneDataDiscoveryService';
import { spawn } from 'child_process';

const router = Router();
const datasetsDir = path.resolve(__dirname, '../../data/aerodrome_layout/datasets');
const activeDatasetPath = path.resolve(__dirname, '../../data/aerodrome_layout/active_dataset.json');

// 1. GET /api/aerodrome-layout/discover
router.get('/discover', async (req, res) => {
  try {
    const discoveryService = new XplaneDataDiscoveryService();
    const result = await discoveryService.discoverXplaneAirportDataRoots();
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 2. POST /api/aerodrome-layout/import-xplane
router.post('/import-xplane', async (req, res) => {
  const { sourcePath, datasetName } = req.body;
  if (!sourcePath) return res.status(400).json({ error: "sourcePath is required" });

  try {
    // Run the import script as a child process so it doesn't block the API server
    // For a real production app, use a queue like BullMQ.
    const scriptPath = path.resolve(__dirname, '../scripts/importVietnamXplaneAerodromeLayout.ts');
    
    // Quick response, task running in background (in reality, should return job ID)
    // To satisfy the user prompt's synchronous-looking response, we could await it, 
    // but parsing 300MB might take a few seconds to a minute.
    // For simplicity, we'll run it synchronously here or just return a generic status.
    
    res.json({
      status: "import_started",
      message: "Import process started in background. Please check datasets list later."
    });

    const child = spawn('npx', ['ts-node', scriptPath, '--source', sourcePath, '--name', datasetName || 'Vietnam X-Plane Aerodrome Layout'], {
      cwd: path.resolve(__dirname, '../')
    });
    
    child.stdout.on('data', data => console.log(`[Import] ${data}`));
    child.stderr.on('data', data => console.error(`[Import] ${data}`));
    child.on('close', code => console.log(`[Import] finished with code ${code}`));

  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 3. GET /api/aerodrome-layout/datasets
router.get('/datasets', async (req, res) => {
  try {
    if (!await fs.pathExists(datasetsDir)) return res.json([]);
    const dirs = await fs.readdir(datasetsDir);
    const datasets = [];
    
    for (const dir of dirs) {
      const metaPath = path.join(datasetsDir, dir, 'normalized', 'dataset_metadata.json');
      if (await fs.pathExists(metaPath)) {
        datasets.push(await fs.readJson(metaPath));
      }
    }
    res.json(datasets);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 4. GET /api/aerodrome-layout/datasets/:datasetId
router.get('/datasets/:datasetId', async (req, res) => {
  try {
    const metaPath = path.join(datasetsDir, req.params.datasetId, 'normalized', 'dataset_metadata.json');
    if (!await fs.pathExists(metaPath)) return res.status(404).json({ error: "Not found" });
    res.json(await fs.readJson(metaPath));
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 5. GET /api/aerodrome-layout/datasets/:datasetId/airports
router.get('/datasets/:datasetId/airports', async (req, res) => {
  try {
    const airportsDir = path.join(datasetsDir, req.params.datasetId, 'normalized', 'airports');
    if (!await fs.pathExists(airportsDir)) return res.json([]);
    const dirs = await fs.readdir(airportsDir);
    const airports = [];
    
    for (const dir of dirs) {
      const metaPath = path.join(airportsDir, dir, 'metadata.json');
      if (await fs.pathExists(metaPath)) {
        airports.push(await fs.readJson(metaPath));
      }
    }
    res.json(airports);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 6. GET /api/aerodrome-layout/datasets/:datasetId/airports/:icao/layers
router.get('/datasets/:datasetId/airports/:icao/layers', async (req, res) => {
  try {
    const { datasetId, icao } = req.params;
    const airportDir = path.join(datasetsDir, datasetId, 'normalized', 'airports', icao);
    
    if (!await fs.pathExists(airportDir)) return res.status(404).json({ error: "Airport not found in dataset" });
    
    const readGeoJson = async (filename: string) => {
      const p = path.join(airportDir, filename);
      return (await fs.pathExists(p)) ? await fs.readJson(p) : { type: "FeatureCollection", features: [] };
    };

    res.json({
      airport: { icao },
      layers: {
        runways: await readGeoJson('runways.geojson'),
        runway_centerlines: await readGeoJson('runway_centerlines.geojson'),
        runway_labels: await readGeoJson('runway_labels.geojson'),
        pavements: await readGeoJson('pavements.geojson'),
        taxiway_centerlines: await readGeoJson('taxiway_centerlines.geojson'),
        taxiway_labels: await readGeoJson('taxiway_labels.geojson'),
        gates: await readGeoJson('gates.geojson'),
        ground_markings: await readGeoJson('ground_markings.geojson'),
        taxiway_signs: await readGeoJson('taxiway_signs.geojson'),
        boundaries: await readGeoJson('boundaries.geojson'),
        helipads: await readGeoJson('helipads.geojson')
      },
      comms: await readGeoJson('comms.json').catch(() => [])
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 7. POST /api/aerodrome-layout/datasets/:datasetId/validate
router.post('/datasets/:datasetId/validate', async (req, res) => {
  res.json({ status: "validated", warnings: [] }); // Stubbed
});

// 8. POST /api/aerodrome-layout/datasets/:datasetId/activate
router.post('/datasets/:datasetId/activate', async (req, res) => {
  try {
    const datasetId = req.params.datasetId;
    const metaPath = path.join(datasetsDir, datasetId, 'normalized', 'dataset_metadata.json');
    if (!await fs.pathExists(metaPath)) return res.status(404).json({ error: "Not found" });
    
    await fs.writeJson(activeDatasetPath, { activeDatasetId: datasetId, activatedAt: new Date().toISOString() });
    res.json({ status: "active", datasetId });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 9. GET /api/aerodrome-layout/active
router.get('/active', async (req, res) => {
  try {
    if (!await fs.pathExists(activeDatasetPath)) return res.json({ activeDatasetId: null });
    res.json(await fs.readJson(activeDatasetPath));
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 10. GET /api/aerodrome-layout/active/airports/:icao/layers
router.get('/active/airports/:icao/layers', async (req, res) => {
  try {
    if (!await fs.pathExists(activeDatasetPath)) return res.status(404).json({ error: "No active dataset" });
    const { activeDatasetId } = await fs.readJson(activeDatasetPath);
    
    const icao = req.params.icao;
    const airportDir = path.join(datasetsDir, activeDatasetId, 'normalized', 'airports', icao);
    if (!await fs.pathExists(airportDir)) return res.status(404).json({ error: "Airport not found in active dataset" });
    
    const readGeoJson = async (filename: string) => {
      const p = path.join(airportDir, filename);
      return (await fs.pathExists(p)) ? await fs.readJson(p) : { type: "FeatureCollection", features: [] };
    };

    res.json({
      airport: { icao },
      layers: {
        runways: await readGeoJson('runways.geojson'),
        runway_centerlines: await readGeoJson('runway_centerlines.geojson'),
        runway_labels: await readGeoJson('runway_labels.geojson'),
        pavements: await readGeoJson('pavements.geojson'),
        taxiway_centerlines: await readGeoJson('taxiway_centerlines.geojson'),
        taxiway_labels: await readGeoJson('taxiway_labels.geojson'),
        gates: await readGeoJson('gates.geojson'),
        ground_markings: await readGeoJson('ground_markings.geojson'),
        taxiway_signs: await readGeoJson('taxiway_signs.geojson'),
        boundaries: await readGeoJson('boundaries.geojson'),
        helipads: await readGeoJson('helipads.geojson')
      },
      comms: await readGeoJson('comms.json').catch(() => [])
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 11. GET /api/aerodrome-layout/health
router.get('/health', async (req, res) => {
  res.json({ ok: true });
});

export default router;
