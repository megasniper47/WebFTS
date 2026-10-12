"""
VVDN_KB5_1HR_G6_RWYQ.scn
- Tất cả ARR thoát ly G6 -> Gate 11
- 70% medium / 30% heavy, seed 20260812
- RWYHOLD queue: DEP[i+1] đứng cách đuôi DEP[i] 20m tính ngược từ RWYHOLD
  theo đường lăn thật. Khi DEP[i] lăn qua điểm 100m trên CHC 35R,
  DEP[i+1] được tiếp tục lăn theo lộ trình cũ vào RWYHOLD.
"""
import math, random, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

random.seed(20260812)
OUT = "."
N  = 20
ARR_SEP = 180
DEP_SEP = 150

MED = ["A320","A321","A20N","A21N","B738","B38M","B739","E190"]
HVY = ["A332","A333","A359","B744","B763","B772","B773","B77W","B788","B789","B748","B78X"]
LEN = {"A320":37.57,"A321":44.51,"A20N":37.57,"A21N":44.51,
       "B738":39.47,"B38M":39.52,"B739":42.11,"E190":36.24,
       "A332":59.00,"A333":63.60,"A359":66.80,"B744":70.67,
       "B763":54.94,"B772":63.73,"B773":73.86,"B77W":73.86,
       "B788":56.72,"B789":62.81,"B748":76.25,"B78X":67.97}

nm  = round(N*0.70); nh = N*2-nm
pool = [random.choice(MED) for _ in range(nm)] + [random.choice(HVY) for _ in range(nh)]
random.shuffle(pool)
it = iter(pool)
pick = lambda: next(it)

def hav(a,b,c,d):
    R=6371000.
    p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def brg(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c); dl=math.radians(d-b)
    y=math.sin(dl)*math.cos(p2)
    x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360

def pt_before_end(poly, dist):
    if dist<=0:
        a,b=poly[-2]; c,d=poly[-1]
        return c,d,brg(a,b,c,d)
    rem=dist
    for i in range(len(poly)-1,0,-1):
        a,b=poly[i-1]; c,d=poly[i]
        s=hav(a,b,c,d); h=brg(a,b,c,d)
        if s>=rem:
            f=rem/s
            return c+(a-c)*f, d+(b-d)*f, h
        rem-=s
    a,b=poly[0]; c,d=poly[1]
    return a,b,brg(a,b,c,d)

def fmt(s):
    s=round(s,2); h=int(s//3600); m=int((s%3600)//60); sc=s%60
    return f"{h:02d}:{m:02d}:{sc:05.2f}"

# ── Toạ độ gốc (từ VVDN_KB5_35L35R_2ARR2DEP_v2) ──────────────────────────
STAR=[(15.601667,108.142222,230),(15.618056,108.262500,220),(15.700556,108.250000,210),
      (15.788333,108.237500,200),(15.873556,108.223083,180),(15.947115,108.212410,160),
      (15.957222,108.210944,155),(16.030133,108.200372,140)]
DOTEN=(15.767222,108.118333)

# ARR G6 rollout + hold
ROLL_G6=[(16.034580,108.199721,128),(16.039028,108.199071,115),(16.043475,108.198420,100),
         (16.047922,108.197769,83),(16.052370,108.197119,61),(16.055927,108.196598,34),
         (16.057199,108.196412,15),(16.057250,108.196800,8),(16.0572,108.1974,0)]
G6H=(16.0572,108.1974)

# ARR cross G6 -> Gate 11
CROSS6=[(16.057402,108.198639,8.0),(16.057604,108.199978,12.0),(16.057809,108.201338,0.0)]
GATE11=(16.057809,108.201338)

# DEP taxi G26 (chung cho mọi cặp, xen kẽ G26/G27)
TX26=[(16.052004,108.200773,10),(16.051764,108.200781,15),(16.051560,108.200776,15),
      (16.051307,108.200786,15),(16.049490,108.200986,15),(16.049218,108.201025,12),
      (16.044100,108.201789,18),(16.038291,108.202625,18),(16.030836,108.203677,15),
      (16.029967,108.203803,10),(16.029680,108.203824,8),(16.029490,108.203744,6),
      (16.029355,108.203538,5),(16.029272,108.203047,5),(16.029181,108.202508,5)]
TX27=[(16.051764,108.200781,10),(16.051560,108.200776,15),(16.051307,108.200786,15),
      (16.049490,108.200986,15),(16.049218,108.201025,12),(16.044100,108.201789,18),
      (16.038291,108.202625,18),(16.030836,108.203677,15),(16.029967,108.203803,10),
      (16.029680,108.203824,8),(16.029490,108.203744,6),(16.029355,108.203538,5),
      (16.029272,108.203047,5)]
G26=(16.052622,108.201973,80.9)
G27=(16.052259,108.202091,80.9)
RWYH=(16.029200,108.202500,352.1)   # runway hold point
# Dummy wpt sau RWYH (để tránh bug auto-delete)
RWYD=(16.030000,108.202000)

# Polyline để tính vị trí queue ngược từ RWYH
RWYQ_POLY=[(lat,lon) for lat,lon,_ in TX26]+[(RWYH[0],RWYH[1])]

# Trigger "đã vào CHC": ~100m past RWYH theo hdg 352.1° 
RWY_ENTRY_LAT, RWY_ENTRY_LON = 16.030100, 108.202372
RWY_ENTRY_NM = 0.04   # bán kính NM

# ── Ước lượng thời gian ───────────────────────────────────────────────────
def leg_t(pts, start):
    K=0.514444; t=0.; prev=start; pspd=None
    for la,lo,sp in pts:
        if prev:
            d=hav(prev[0],prev[1],la,lo)
            v0=pspd if pspd else sp
            t+=d/max(((v0+sp)/2)*K,1.)
        prev=(la,lo); pspd=sp
    return t

STAR_T = leg_t(STAR, DOTEN)
DEP_CLR_T = 155.   # 30s roll + ~125s bay hết CHC (từ bản v1)
GATE_T = 10.

print(f"[debug] STAR_T={STAR_T:.0f}s")

# ── Tạo pairs ──────────────────────────────────────────────────────────────
pairs=[]
for i in range(1, N+1):
    at=(i-1)*ARR_SEP; dt=(i-1)*DEP_SEP
    at_=pick(); dt_=pick()
    gate=G26 if i%2==1 else G27
    gn="G26" if i%2==1 else "G27"
    pairs.append({"i":i,"arr_id":f"ARR{i:03d}","dep_id":f"DEP{i:03d}",
                  "arr_t":at,"dep_t":dt,"arr_type":at_,"dep_type":dt_,
                  "gate":gate,"gate_name":gn,
                  "touchdown_t":at+STAR_T,
                  "rwy_cleared_t":at+STAR_T+DEP_CLR_T})

# ── RWYHOLD queue (FIFO động): tính vị trí chờ thực tế tại RWYHOLD ──────────
# DEP[i] rời hàng đợi khi nó bắt đầu chạy đà = touchdown_t[i] + 30s.
# Khi DEP mới đến (tại dep_t[i]), chỉ những DEP chưa rời hàng đợi mới
# đóng góp vào offset (giống FIFO bản v2 nhưng tại RWYHOLD thay vì PRE_HOLD).
# DEP001 luôn đứng tại RWYHOLD (offset=0). DEP[i+1] đứng sau đuôi DEP[i]
# khi DEP[i] vừa đến vị trí của nó trong hàng đợi.

# Thời điểm DEP[i] rời hàng đợi (bắt đầu roll = ARR[i] chạm đất + 30s)
for p in pairs:
    p["roll_t"] = p["touchdown_t"] + 30.0  # lúc bắt đầu chạy đà

# FIFO queue: list (dep_id, roll_t, offset_m)
q_members = []
for p in pairs:
    i = p["i"]
    arrive_t = p["dep_t"]
    # Loại bỏ DEP đã roll trước khi DEP này đến
    q_members = [(d, rt, off) for d, rt, off in q_members if rt > arrive_t]
    if i == 1:
        p["rwy_offset"] = 0.0
    elif not q_members:
        p["rwy_offset"] = 0.0  # không còn ai trong queue, tiến thẳng RWYHOLD
    else:
        # Đứng sau DEP cuối cùng trong queue
        _, _, back_off = q_members[-1]
        back_dep_id = q_members[-1][0]
        back_type = next(x["dep_type"] for x in pairs if x["dep_id"]==back_dep_id)
        p["rwy_offset"] = back_off + LEN[back_type] + 20.0
    q_members.append((p["dep_id"], p["roll_t"], p["rwy_offset"]))

    if p["rwy_offset"] == 0.0:
        p["rwy_lat"]=RWYH[0]; p["rwy_lon"]=RWYH[1]; p["rwy_hdg"]=RWYH[2]
    else:
        la,lo,hd=pt_before_end(RWYQ_POLY, p["rwy_offset"])
        p["rwy_lat"]=la; p["rwy_lon"]=lo; p["rwy_hdg"]=round(hd,1)
        print(f"[debug] {p['dep_id']}: RWYQ offset={p['rwy_offset']:.0f}m "
              f"-> ({la:.6f},{lo:.6f}) hdg={p['rwy_hdg']} (roll_t={p['roll_t']:.0f}s)")

# ── Sinh file ──────────────────────────────────────────────────────────────
files={}
def af(n,c): files[n]=c

# Shared templates
af("_KB5G6Q_STOP.scn",
"# Dừng cứng bằng MOVE. Gọi: PCALL _KB5G6Q_STOP <acid> <lat> <lon> <hdg>\n"
"00:00:00.00>%0 LNAV OFF\n00:00:00.00>%0 VNAV OFF\n00:00:00.00>MOVE %0,%1,%2,0,%3,0.0\n")

af("_KB5G6Q_DEL10.scn",
"# Xoá tàu bay sau 10s\n00:00:10.00>DEL %0\n")

af("_KB5G6Q_ARR_APPROACH.scn",
"# DOTEN -> STAR -> IAP ILS V 35L\n"
"00:00:00.00>%0 ADDWPT 15.601667,108.142222 7695 230\n"
"00:00:00.00>%0 ADDWPT 15.618056,108.262500 6071 220\n"
"00:00:00.00>%0 ADDWPT 15.700556,108.250000 4921 210\n"
"00:00:00.00>%0 ADDWPT 15.788333,108.237500 4429 200\n"
"00:00:00.00>%0 ADDWPT 15.873556,108.223083 2592 180\n"
"00:00:00.00>%0 ADDWPT 15.947115,108.212410 1611 160\n"
"00:00:00.00>%0 ADDWPT 15.957222,108.210944 1476 155\n"
"00:00:00.00>%0 ADDWPT 16.030133,108.200372 0 140\n")

af("_KB5G6Q_ARR_EXIT_G6.scn",
"# Thoát ly G6, dừng chờ\n"
"00:00:00.00>%0 ADDWPT 16.034580,108.199721 0 128\n"
"00:00:00.00>%0 ADDWPT 16.039028,108.199071 0 115\n"
"00:00:00.00>%0 ADDWPT 16.043475,108.198420 0 100\n"
"00:00:00.00>%0 ADDWPT 16.047922,108.197769 0 83\n"
"00:00:00.00>%0 ADDWPT 16.052370,108.197119 0 61\n"
"00:00:00.00>%0 ADDWPT 16.055927,108.196598 0 34\n"
"00:00:00.00>%0 ADDWPT 16.057199,108.196412 0 15\n"
"00:00:00.00>%0 ADDWPT 16.057250,108.196800 0 8\n"
"00:00:00.00>%0 ADDWPT 16.0572,108.1974 0 0\n"
"00:00:00.00>%0 ADDWPT 16.0572,108.1988 0 8\n"
"00:00:00.00>%0 LNAV ON\n00:00:00.00>%0 VNAV ON\n"
"00:00:00.00>%0 ATDIST 16.0572,108.1974,0.015 PCALL _KB5G6Q_STOP %0 16.0572 108.1974 82.0\n")

af("_KB5G6Q_CROSS_G6.scn",
"# Cắt 35R từ G6 về Gate 11\n"
"00:00:00.00>%0 DELRTE\n"
"00:00:00.00>%0 ADDWPT 16.057402,108.198639 0 8.0\n"
"00:00:00.00>%0 ADDWPT 16.057604,108.199978 0 12.0\n"
"00:00:00.00>%0 ADDWPT 16.057809,108.201338 0 0.0\n"
"00:00:00.00>%0 ADDWPT 16.057850,108.201800 0 5.0\n"
"00:00:00.00>%0 LNAV ON\n00:00:00.00>%0 VNAV ON\n"
"00:00:00.00>%0 ATDIST 16.057809,108.201338,0.02 PCALL _KB5G6Q_STOP_GATE11 %0\n")

af("_KB5G6Q_STOP_GATE11.scn",
"00:00:00.00>%0 LNAV OFF\n00:00:00.00>%0 VNAV OFF\n"
"00:00:00.00>MOVE %0,16.057809,108.201338,0,82.0,0.0\n"
"00:00:00.00>PCALL _KB5G6Q_DEL10 %0\n")

af("_KB5G6Q_DEP_ROLL.scn",
"# Chạy đà 35R + SID BUNTA 2G (30s sau ARR chạm đất)\n"
"00:00:30.00>%0 LNAV OFF\n00:00:30.00>%0 VNAV OFF\n"
"00:00:30.00>MOVE %0,16.029200,108.202500,0,352.1,0.0\n"
"00:00:38.00>MOVE %0,16.029573,108.202446,0,352.1,20.4\n"
"00:00:46.00>MOVE %0,16.030690,108.202285,0,352.1,40.7\n"
"00:00:54.00>MOVE %0,16.032553,108.202016,0,352.1,61.0\n"
"00:01:02.00>MOVE %0,16.035159,108.201640,0,352.1,81.4\n"
"00:01:10.00>MOVE %0,16.038514,108.201155,0,352.1,101.7\n"
"00:01:18.00>MOVE %0,16.042616,108.200563,0,352.1,122.0\n"
"00:01:26.00>MOVE %0,16.047469,108.199862,0,352.1,142.4\n"
"00:01:29.00>MOVE %0,16.049442,108.199582,0,352.1,150.0\n"
"00:01:38.00>MOVE %0,16.055778,108.198667,375,352.1,157.5\n"
"00:01:47.00>MOVE %0,16.062422,108.197708,750,352.1,165.0\n"
"00:01:56.00>MOVE %0,16.069382,108.196704,1125,352.1,172.5\n"
"00:02:05.00>MOVE %0,16.076637,108.195656,1500,352.1,180.0\n"
"00:02:05.00>%0 DELRTE\n"
"00:02:05.00>%0 ADDWPT 16.334167,108.192500 7500 250\n"
"00:02:05.00>%0 ADDWPT 16.451111,108.578611 10500 280\n"
"00:02:05.00>%0 ADDWPT 16.833333,109.395000 34000 320\n"
"00:02:05.00>%0 LNAV ON\n00:02:05.00>%0 VNAV ON\n")

# Per-DEP taxi files
def taxi_wpts(pts):
    return "\n".join(f"00:00:00.00>%0 ADDWPT {la:.6f},{lo:.6f} 0 {sp}" for la,lo,sp in pts)

def wpts_offset(pts, t="00:00:00.10"):
    return "\n".join(f"{t}>%0 ADDWPT {la:.6f},{lo:.6f} 0 {sp}" for la,lo,sp in pts)

for p in pairs:
    dep=p["dep_id"]; i=p["i"]
    tx = TX26 if p["gate_name"]=="G26" else TX27
    rlat,rlon,rhdg = p["rwy_lat"],p["rwy_lon"],p["rwy_hdg"]

    # Phase B: gate -> vị trí chờ RWYHOLD queue
    if i==1:
        # DEP001 đi thẳng đến RWYHOLD
        bname = f"_KB5G6Q_TAXI_{dep}"
        af(f"{bname}.scn",
           f"# {dep}: gate -> RWYHOLD\n"
           f"{taxi_wpts(tx)}\n"
           f"00:00:00.00>%0 ADDWPT {RWYH[0]:.6f},{RWYH[1]:.6f} 0 0.0\n"
           f"00:00:00.00>%0 ADDWPT {RWYD[0]:.6f},{RWYD[1]:.6f} 0 5.0\n"
           f"00:00:00.00>%0 LNAV ON\n00:00:00.00>%0 VNAV ON\n"
           f"00:00:00.00>%0 ATDIST {RWYH[0]:.6f},{RWYH[1]:.6f},0.01 "
           f"PCALL _KB5G6Q_STOP %0 {RWYH[0]:.6f} {RWYH[1]:.6f} {RWYH[2]}\n")
    else:
        # DEP[i]: taxi đến vị trí queue của mình
        bname = f"_KB5G6Q_TAXI_{dep}"
        # Tìm idx cắt taxi route để biết đến điểm nào thì dừng
        # Dùng toàn bộ tx rồi dừng ở queue position
        cname = f"_KB5G6Q_RESUME_{dep}"
        af(f"{bname}.scn",
           f"# {dep}: gate -> queue position (offset={p['rwy_offset']:.0f}m from RWYHOLD)\n"
           f"{taxi_wpts(tx)}\n"
           f"00:00:00.00>%0 ADDWPT {rlat:.6f},{rlon:.6f} 0 0.0\n"
           f"00:00:00.00>%0 ADDWPT {RWYH[0]:.6f},{RWYH[1]:.6f} 0 5.0\n"
           f"00:00:00.00>%0 LNAV ON\n00:00:00.00>%0 VNAV ON\n"
           f"00:00:00.00>%0 ATDIST {rlat:.6f},{rlon:.6f},0.01 "
           f"PCALL _KB5G6Q_STOP %0 {rlat:.6f} {rlon:.6f} {rhdg}\n")

        # Phase C: từ queue position tiếp tục vào RWYHOLD
        af(f"{cname}.scn",
           f"# {dep}: tiếp tục từ queue -> RWYHOLD\n"
           f"00:00:00.00>%0 LNAV OFF\n00:00:00.00>%0 VNAV OFF\n"
           f"00:00:00.00>MOVE %0,{rlat:.6f},{rlon:.6f},0,{rhdg},0.0\n"
           f"00:00:00.10>%0 DELRTE\n"
           f"00:00:00.10>%0 ADDWPT {RWYH[0]:.6f},{RWYH[1]:.6f} 0 0.0\n"
           f"00:00:00.10>%0 ADDWPT {RWYD[0]:.6f},{RWYD[1]:.6f} 0 5.0\n"
           f"00:00:00.10>%0 LNAV ON\n00:00:00.10>%0 VNAV ON\n"
           f"00:00:00.10>%0 ATDIST {RWYH[0]:.6f},{RWYH[1]:.6f},0.01 "
           f"PCALL _KB5G6Q_STOP %0 {RWYH[0]:.6f} {RWYH[1]:.6f} {RWYH[2]}\n")

# ── File kịch bản chính ────────────────────────────────────────────────────
lines=[]
lines.append(f"""# VVDN_KB5_1HR_G6_RWYQ.scn — sinh tự động
# {N} cặp ARR/DEP, 1 giờ, G6 all, 70% medium/30% heavy
# RWYHOLD queue: mỗi DEP chờ cách đuôi DEP trước 20m (tính ngược từ RWYHOLD)
# Trigger "vào CHC": khi DEP[i] qua điểm {RWY_ENTRY_LAT},{RWY_ENTRY_LON}
# (~100m trên CHC 35R) -> DEP[i+1] tiến lên RWYHOLD
#
00:00:00.00>TRAILS ON
00:00:00.00>ASAS OFF
00:00:00.00>PAN 16.0400,108.2000
""")

for p in pairs:
    i=p["i"]
    dep=p["dep_id"]; arr=p["arr_id"]
    at=fmt(p["arr_t"]); dt=fmt(p["dep_t"])
    glat,glon,ghdg=p["gate"]
    bname=f"_KB5G6Q_TAXI_{dep}"

    # Trigger khi DEP[i] vào CHC (100m mark) -> DEP[i+1] tiến vào RWYHOLD
    if i < N:
        next_dep = pairs[i]["dep_id"]
        next_cname = f"_KB5G6Q_RESUME_{next_dep}"
        entry_trigger = (f"{dt}>{dep} ATDIST {RWY_ENTRY_LAT},{RWY_ENTRY_LON},{RWY_ENTRY_NM} "
                        f"PCALL {next_cname} {next_dep}")
    else:
        entry_trigger = f"# {dep} la DEP cuoi, khong co DEP tiep theo"

    # Trigger khi DEP[i] bay het CHC -> ARR[i] cat G6
    end_trigger = (f"{dt}>{dep} ATDIST 16.0604,108.1980,0.15 "
                   f"PCALL _KB5G6Q_CROSS_G6 {arr}")

    lines.append(f"""
# ── CẶP {i}/{N}: {arr}({p['arr_type']},G6) + {dep}({p['dep_type']},{p['gate_name']}) ──
{dt}>CRE {dep},{p['dep_type']},{glat},{glon},{ghdg},0,15
{dt}>PCALL {bname} {dep}
{entry_trigger}
{end_trigger}

{at}>CRE {arr},{p['arr_type']},15.767222,108.118333,173,10000,250
{at}>PCALL _KB5G6Q_ARR_APPROACH {arr}
{at}>PCALL _KB5G6Q_ARR_EXIT_G6 {arr}
{at}>{arr} ATALT 0 PCALL _KB5G6Q_DEP_ROLL {dep}""")

af("VVDN_KB5_1HR_G6_RWYQ.scn", "\n".join(lines))

# Ghi tất cả file
for fn, content in files.items():
    with open(f"{OUT}/{fn}", "w", encoding="utf-8", errors="replace") as f:
        f.write(content)

print(f"\nDa sinh {len(files)} file")
for p in pairs:
    print(f"  {p['i']:2d}. {p['arr_id']}({p['arr_type']},G6) t={fmt(p['arr_t'])}  "
          f"{p['dep_id']}({p['dep_type']},{p['gate_name']}) t={fmt(p['dep_t'])}  "
          f"RWYQ_offset={p['rwy_offset']:.0f}m")
