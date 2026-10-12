import path from 'path';
import fs from 'fs-extra';

export interface DiscoveredPath {
  path: string;
  type: "apt_dat" | "airtrafficsim_airport_data" | "unknown";
  exists: boolean;
  files: string[];
  confidence: number;
}

export interface DiscoveryResult {
  candidatePaths: DiscoveredPath[];
  selectedPath: string | null;
  warnings: string[];
}

export class XplaneDataDiscoveryService {
  private projectRoot: string;

  constructor() {
    // Assuming this service is running in FTS Server/services
    this.projectRoot = path.resolve(__dirname, '../../');
  }

  public async discoverXplaneAirportDataRoots(): Promise<DiscoveryResult> {
    const candidatePaths: DiscoveredPath[] = [];
    const warnings: string[] = [];
    let selectedPath: string | null = null;

    // 1. Check Environment Variables first
    const envAptDatPath = process.env.WEBFTS_XPLANE_APT_DAT_PATH;
    if (envAptDatPath) {
      const resolvedPath = path.resolve(envAptDatPath);
      const exists = await fs.pathExists(resolvedPath);
      if (exists) {
        candidatePaths.push({
          path: resolvedPath,
          type: "apt_dat",
          exists: true,
          files: ['apt.dat'],
          confidence: 1.0
        });
        selectedPath = resolvedPath;
      } else {
        warnings.push(`Environment variable WEBFTS_XPLANE_APT_DAT_PATH points to non-existent path: ${resolvedPath}`);
      }
    }

    const envDataRoot = process.env.WEBFTS_XPLANE_DATA_ROOT;
    if (envDataRoot) {
      const resolvedPath = path.resolve(envDataRoot);
      const exists = await fs.pathExists(resolvedPath);
      if (exists) {
        const potentialAptDat = path.join(resolvedPath, 'apt.dat');
        if (await fs.pathExists(potentialAptDat)) {
           candidatePaths.push({
            path: potentialAptDat,
            type: "apt_dat",
            exists: true,
            files: ['apt.dat'],
            confidence: 0.95
          });
          if (!selectedPath) selectedPath = potentialAptDat;
        } else {
           warnings.push(`Environment variable WEBFTS_XPLANE_DATA_ROOT found, but no apt.dat inside: ${resolvedPath}`);
        }
      } else {
        warnings.push(`Environment variable WEBFTS_XPLANE_DATA_ROOT points to non-existent path: ${resolvedPath}`);
      }
    }

    // 2. Scan standard project directories
    const potentialDirs = [
      'vietnam_ats_routes_pack/Airport/xplane',
      'vietnam_ats_routes_pack/Airport/xplane/apt.dat',
      'data/airports',
      'data/navigation',
      'data/xplane',
      'data/performance',
      'airtrafficsim/data',
      'AirTrafficSim/data',
      'resources/default scenery',
      'Global Airports',
      'Earth nav data'
    ];

    for (const dir of potentialDirs) {
      const fullPath = path.join(this.projectRoot, dir);
      
      try {
        const stats = await fs.stat(fullPath);
        if (stats.isFile() && fullPath.toLowerCase().endsWith('apt.dat')) {
           candidatePaths.push({
            path: fullPath,
            type: "apt_dat",
            exists: true,
            files: ['apt.dat'],
            confidence: 0.9
          });
          if (!selectedPath) selectedPath = fullPath;
        } else if (stats.isDirectory()) {
          const aptDatPath = path.join(fullPath, 'apt.dat');
          if (await fs.pathExists(aptDatPath)) {
            candidatePaths.push({
              path: aptDatPath,
              type: "apt_dat",
              exists: true,
              files: ['apt.dat'],
              confidence: 0.85
            });
            if (!selectedPath) selectedPath = aptDatPath;
          }
        }
      } catch (err) {
        // Path doesn't exist, ignore
      }
    }

    // Deduplicate candidate paths
    const uniqueCandidates: DiscoveredPath[] = [];
    const seenPaths = new Set<string>();
    
    for (const candidate of candidatePaths) {
      if (!seenPaths.has(candidate.path)) {
        seenPaths.add(candidate.path);
        uniqueCandidates.push(candidate);
      }
    }

    if (uniqueCandidates.length === 0) {
      warnings.push("Could not find any apt.dat files in standard locations. Please specify via environment variables.");
    }

    return {
      candidatePaths: uniqueCandidates.sort((a, b) => b.confidence - a.confidence),
      selectedPath: uniqueCandidates.length > 0 ? uniqueCandidates[0].path : null,
      warnings
    };
  }
}
