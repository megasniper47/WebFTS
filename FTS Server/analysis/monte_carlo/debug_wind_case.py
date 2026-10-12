import sys, os
sys.path.insert(0, r"D:\Coding\Dự án FTS\WebFTS v4\FTS Server")
os.chdir(r"D:\Coding\Dự án FTS\WebFTS v4\FTS Server")
import bluesky as bs
bs.init(mode="sim", detached=True)

THR_LAT, THR_LON, THR_HDG = 16.0290376, 108.202528, 352.10

bs.stack.stack(f"WIND {THR_LAT},{THR_LON},220,5")
bs.stack.stack(f"CRE TST01,B773,{THR_LAT},{THR_LON},{THR_HDG},0,0")
for _ in range(3):
    bs.sim.step()
bs.stack.stack("TST01 ALT 5000")
bs.stack.stack("TST01 SPD 250")
bs.stack.stack("TST01 LNAV OFF")
bs.stack.stack("TST01 VNAV OFF")

last_print = -100
while bs.sim.simt < 150:
    bs.sim.step()
    idx = bs.traf.id2idx("TST01")
    if idx < 0:
        print(f"t={bs.sim.simt:.1f} DELETED")
        break
    alt_ft = bs.traf.alt[idx] * 3.28084
    gs_kt = bs.traf.gs[idx] * 1.94384
    tas_kt = bs.traf.tas[idx] * 1.94384 if hasattr(bs.traf, 'tas') else None
    cas_kt = bs.traf.cas[idx] * 1.94384 if hasattr(bs.traf, 'cas') else None
    if bs.sim.simt - last_print >= 5:
        last_print = bs.sim.simt
        print(f"t={bs.sim.simt:.1f} alt={alt_ft:.1f}ft gs={gs_kt:.1f}kt tas={tas_kt} cas={cas_kt}")
