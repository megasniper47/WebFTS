import path from 'path';
import fs from 'fs-extra';
import { v4 as uuidv4 } from 'uuid';
import { XplaneAptDatParser } from '../services/xplaneAptDatParser';

const args = process.argv.slice(2);
let sourcePath = '';
let datasetName = 'Vietnam X-Plane Aerodrome Layout';

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--source' && args[i + 1]) {
    sourcePath = args[i + 1];
    i++;
  } else if (args[i] === '--name' && args[i + 1]) {
    datasetName = args[i + 1];
    i++;
  }
}

if (!sourcePath) {
  console.error("Usage: npm run import:xplane-aerodrome -- --source <path-to-apt.dat> [--name <Dataset Name>]");
  process.exit(1);
}

const targetAirports = [
  "VVNB", "VVTS", "VVDN", "VVCR", "VVCT", "VVPQ", "VVCI", "VVVD", "VVVH",
  "VVPB", "VVDL", "VVPC", "VVTH", "VVBM", "VVDH", "VVCA", "VVCM", "VVRG",
  "VVCS", "VVDB", "VVPK", "VVTX", "VVQT", "VVLT"
];

async function run() {
  console.log(`Starting import from: ${sourcePath}`);
  const datasetId = uuidv4();
  const datasetDir = path.resolve(__dirname, `../../data/aerodrome_layout/datasets/${datasetId}`);
  
  await fs.ensureDir(datasetDir);
  const normalizedDir = path.join(datasetDir, 'normalized');

  const parser = new XplaneAptDatParser();
  console.log("Parsing apt.dat (this may take a while depending on file size)...");
  
  const { parsedIcaos, stats, warnings } = await parser.parseAptDat(sourcePath, datasetDir, 'VV');
  
  const missingAirports = targetAirports.filter(icao => !parsedIcaos.includes(icao));
  
  await fs.writeJson(path.join(normalizedDir, 'missing_airports.json'), missingAirports, { spaces: 2 });
  await fs.writeJson(path.join(normalizedDir, 'parse_warnings.json'), warnings, { spaces: 2 });

  const metadata = {
    id: datasetId,
    name: datasetName,
    sourceType: "xplane_apt_dat",
    sourcePath,
    status: "parsed",
    airportCount: parsedIcaos.length,
    vietnamAirportCount: parsedIcaos.length,
    parsedAirportIcaos: parsedIcaos,
    missingAirportIcaos: missingAirports,
    featureCounts: stats,
    warnings,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  await fs.writeJson(path.join(normalizedDir, 'dataset_metadata.json'), metadata, { spaces: 2 });

  console.log("===================================");
  console.log(`Import Complete!`);
  console.log(`Dataset ID: ${datasetId}`);
  console.log(`Airports Parsed: ${parsedIcaos.length}`);
  console.log(`Runways: ${stats.runways}, Aprons: ${stats.aprons}, Taxiways/Lines: ${stats.holdShortLines}`);
  console.log(`Missing Priority Airports: ${missingAirports.length}`);
  console.log(`Metadata saved to ${path.join(normalizedDir, 'dataset_metadata.json')}`);
  console.log("===================================");
}

run().catch(err => {
  console.error("Import failed:", err);
  process.exit(1);
});
