"""Kiem tra may nay co du dieu kien TAO KICH BAN mo phong hay chua.

Chay TRUOC KHI bat dau tao kich ban. Script bao ro tung muc DAT / THIEU kem
cach khac phuc cu the, khong bat nguoi dung tu mo doan.

    python kiem_tra_moi_truong.py

Dung chinh trinh Python ma ban se dung de chay generator -- vi du:
    .venv\\Scripts\\python.exe FTS Server/scenario/kiem_tra_moi_truong.py
"""
from __future__ import annotations

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FTS = HERE.parent              # "FTS Server"
ROOT = FTS.parent              # goc repo

ket_qua: list[tuple[str, bool, str, str]] = []   # (muc, dat, chi_tiet, khac_phuc)


def kiem(muc: str, dat: bool, chi_tiet: str, khac_phuc: str = "") -> bool:
    ket_qua.append((muc, dat, chi_tiet, khac_phuc))
    return dat


# ---------------------------------------------------------------------------
def c1_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 13)
    kiem("1. Phien ban Python", ok,
         f"dang dung {sys.executable}  ({v.major}.{v.minor}.{v.micro})",
         "Du an yeu cau Python 3.13+ (pyproject.toml). Cai tu python.org roi tao lai "
         "moi truong ao:  python -m venv .venv")


def c2_moi_truong_ao():
    trong_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    exe = Path(sys.executable)
    kiem("2. Dang chay trong moi truong ao", trong_venv,
         f"{'co' if trong_venv else 'KHONG'} -- {exe}",
         "Chay lai bang trinh Python cua moi truong ao, vi du:\n"
         "     .venv\\Scripts\\python.exe (Windows)  hoac  .venv/bin/python (Linux/macOS)\n"
         "   Neu chua co .venv:  python -m venv .venv")


def c3_thu_vien():
    can = {
        "numpy": "numpy", "msgpack": "msgpack", "zmq": "pyzmq",
        "flask": "Flask", "scipy": "scipy",
    }
    thieu = [pip for mod, pip in can.items() if importlib.util.find_spec(mod) is None]
    kiem("3. Thu vien bat buoc", not thieu,
         "day du" if not thieu else f"THIEU: {', '.join(thieu)}",
         f"pip install -r requirements.txt    (hoac: pip install {' '.join(thieu)})")


def c4_thu_vien_bao_cao():
    thieu = [p for m, p in {"docx": "python-docx"}.items()
             if importlib.util.find_spec(m) is None]
    kiem("4. Thu vien xuat bao cao (tuy chon)", not thieu,
         "day du" if not thieu else f"thieu: {', '.join(thieu)} -- van tao duoc kich ban, "
         "chi khong xuat duoc bao cao .docx",
         "pip install python-docx")


def c5_bluesky():
    ok = (FTS / "bluesky").is_dir() and (FTS / "settings.cfg").is_file()
    chi_tiet = []
    if not (FTS / "bluesky").is_dir():
        chi_tiet.append("khong thay thu muc bluesky/")
    if not (FTS / "settings.cfg").is_file():
        chi_tiet.append("khong thay settings.cfg")
    kiem("5. Engine mo phong (bluesky)", ok,
         "co day du" if ok else "; ".join(chi_tiet),
         "Chay tu ban clone day du cua repo. Neu vua clone, kiem tra lai duong dan.")


def c6_scenario_path():
    """Bay da tung gay treo mo phong: settings.cfg tu them tien to 'scenario'."""
    cfg = FTS / "settings.cfg"
    if not cfg.is_file():
        return kiem("6. settings.cfg > scenario_path", False, "khong doc duoc settings.cfg", "")
    dong = [l.strip() for l in cfg.read_text(encoding="utf-8", errors="ignore").splitlines()
            if l.strip().startswith("scenario_path")]
    ok = bool(dong)
    kiem("6. settings.cfg > scenario_path", ok,
         (dong[0] if dong else "KHONG co dong scenario_path")
         + "  -> lenh IC TU THEM tien to nay, nen viet 'IC TEN-KICH-BAN', "
           "KHONG viet 'IC scenario/TEN-KICH-BAN'",
         "Neu thieu, them vao settings.cfg:  scenario_path = 'scenario'")


def c7_du_lieu_san_bay():
    thu_muc = (FTS / "data/aerodrome_layout/datasets/vietnam_kml_layout/normalized/airports")
    if not thu_muc.is_dir():
        return kiem("7. So do san bay (duong lan, bai do)", False,
                    f"khong thay {thu_muc.relative_to(ROOT)}",
                    "Du lieu nay di kem repo. Kiem tra lai ban clone.")
    sb = sorted(p.name for p in thu_muc.iterdir() if p.is_dir())
    kiem("7. So do san bay (duong lan, bai do)", bool(sb),
         f"{len(sb)} san bay: {', '.join(sb[:12])}" + (" ..." if len(sb) > 12 else ""),
         "")


def c8_du_lieu_phuong_thuc():
    f = ROOT / "WebATM/static/data/vatm_kmz/procedures_index.json"
    if not f.is_file():
        return kiem("8. Du lieu phuong thuc bay (SID/STAR/IAP)", False,
                    f"khong thay {f.name}", "Du lieu nay di kem repo.")
    d = json.loads(f.read_text(encoding="utf-8"))
    tong = sum(len(v.get(k, {})) for v in d.values()
               for k in ("SID", "STAR", "IAP", "HOLDING") if isinstance(v.get(k), dict))
    kiem("8. Du lieu phuong thuc bay (SID/STAR/IAP)", tong > 0,
         f"{len(d)} san bay, {tong} phuong thuc", "")


def c12_bada():
    """Du lieu hieu nang BADA -- khong co trong repo vi co BAN QUYEN.

    Day la muc quan trong nhat de hai may cho ra CUNG KET QUA: thieu BADA thi
    engine dung mo hinh hieu nang khac, kha nang leo khac, va ket qua mo phong
    LECH. Da do duoc: cung mot file .scn giong nhau tung byte, may co BADA cho
    0 cap canh bao xung dot, may thieu BADA cho 4 cap.
    """
    thu_muc = FTS / "bluesky/resources/performance/BADA"
    n = len(list(thu_muc.glob("*.APF"))) if thu_muc.is_dir() else 0
    cfg = FTS / "settings.cfg"
    dung_bada = (cfg.is_file()
                 and "performance_model = 'bada'" in cfg.read_text(encoding="utf-8",
                                                                   errors="ignore"))
    ok = n > 100 or not dung_bada
    kiem("12. Du lieu hieu nang BADA", ok,
         f"{n} file .APF trong bluesky/resources/performance/BADA"
         + (f"; settings.cfg dang dat performance_model = 'bada'" if dung_bada
            else "; settings.cfg KHONG dung bada nen khong bat buoc"),
         "BADA co BAN QUYEN cua EUROCONTROL nen KHONG duoc dua len GitHub.\n"
         "   Xin bo du lieu tu quan tri du an (kenh noi bo), giai nen vao:\n"
         "        FTS Server/bluesky/resources/performance/BADA/\n"
         "   Neu khong co BADA, sua settings.cfg thanh performance_model = 'openap'\n"
         "   -- NHUNG ket qua se LECH so voi may co BADA, khong doi chieu duoc.")


def c9_chay_thu_mo_phong():
    """Kiem tra quan trong nhat: co THUC SU chay duoc mo phong khong."""
    # Duong dan repo co the chua dau tieng Viet ("Du an FTS"). KHONG nhung no
    # vao ma nguon truyen qua -c: tren Windows, doi so dong lenh duoc ma hoa
    # theo bang ma he thong (cp1252) nen chu co dau bi vo. Truyen qua BIEN MOI
    # TRUONG va bat che do UTF-8 cho tien trinh con.
    ma = (
        "import os, sys; sys.path.insert(0, os.environ['FTS_DIR'])\n"
        "import bluesky as bs\n"
        "bs.init(mode='sim', detached=True)\n"
        "bs.stack.stack('CRE TEST,A320,16.03,108.20,352,2000,250')\n"
        "bs.sim.op()\n"
        "[bs.sim.step() for _ in range(40)]\n"
        "assert bs.traf.ntraf == 1, 'khong tao duoc tau bay'\n"
        "print('OK', round(float(bs.sim.simt), 2))\n"
    )
    env = {**os.environ, "FTS_DIR": str(FTS), "PYTHONUTF8": "1",
           "PYTHONIOENCODING": "utf-8"}
    try:
        r = subprocess.run([sys.executable, "-c", ma], cwd=str(FTS), env=env,
                           capture_output=True, text=True, timeout=240,
                           encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return kiem("9. Chay thu mo phong headless", False,
                    "qua 240 giay khong xong",
                    "Lan chay dau phai dung bang du lieu dan duong (~1-2 phut). "
                    "Chay lai lan nua; neu van treo, xoa thu muc 'FTS Server/cache' roi thu lai.")
    ok = r.returncode == 0 and "OK" in r.stdout
    kiem("9. Chay thu mo phong headless", ok,
         r.stdout.strip().splitlines()[-1] if ok
         else (r.stderr.strip().splitlines() or ["(khong co thong bao loi)"])[-1][:200],
         "Day la muc BAT BUOC: khong chay duoc mo phong thi khong kiem chung duoc kich ban.\n"
         "   Thuong do thieu thu vien (xem muc 3) hoac sai phien ban Python (muc 1).")


def c10_git():
    exe = shutil.which("git")
    if not exe:
        return kiem("10. Git (de lam viec song song)", False, "khong tim thay git",
                    "Cai Git: https://git-scm.com/download")
    try:
        nhanh = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ROOT),
                               capture_output=True, text=True, timeout=20).stdout.strip()
        ten = subprocess.run(["git", "config", "user.name"], cwd=str(ROOT),
                             capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e:
        return kiem("10. Git (de lam viec song song)", False, str(e)[:120], "")
    kiem("10. Git (de lam viec song song)", bool(nhanh),
         f"nhanh hien tai: {nhanh or '(khong xac dinh)'}"
         + (f", nguoi dung: {ten}" if ten else ", CHUA dat user.name"),
         "" if ten else
         'git config user.name "Ho Ten" && git config user.email "email@vatm.vn"')


def c11_duong_dan_dai():
    """Windows cat duong dan qua 260 ky tu -- da tung lam hong ban clone."""
    if os.name != "nt":
        return
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SYSTEM\CurrentControlSet\Control\FileSystem")
        bat = winreg.QueryValueEx(k, "LongPathsEnabled")[0] == 1
    except Exception:
        bat = False
    sau = len(str(ROOT))
    kiem("11. Windows: ho tro duong dan dai", bat or sau < 80,
         f"{'da bat' if bat else 'CHUA bat'}; duong dan repo dai {sau} ky tu",
         "" if bat else
         "Repo co file nam sau nhieu cap thu muc. Neu clone bi loi 'Filename too long':\n"
         "     git config --global core.longpaths true\n"
         "   hoac dat repo o duong dan ngan hon (vi du D:\\FTS).")


# ---------------------------------------------------------------------------
def main():
    print("=" * 78)
    print("KIEM TRA MOI TRUONG TAO KICH BAN MO PHONG -- WebFTS")
    print("=" * 78)
    print(f"Repo: {ROOT}")
    print(f"Python: {sys.executable}\n")

    for ham in (c1_python, c2_moi_truong_ao, c3_thu_vien, c4_thu_vien_bao_cao,
                c5_bluesky, c6_scenario_path, c7_du_lieu_san_bay,
                c8_du_lieu_phuong_thuc, c12_bada, c11_duong_dan_dai, c10_git,
                c9_chay_thu_mo_phong):
        try:
            ham()
        except Exception as e:                      # khong de 1 muc loi lam hong ca bang
            kiem(ham.__name__, False, f"loi khi kiem tra: {e}", "")

    rong = max(len(m) for m, *_ in ket_qua)
    hong = []
    print()
    for muc, dat, chi_tiet, khac_phuc in ket_qua:
        print(f"[{'DAT   ' if dat else 'THIEU '}] {muc.ljust(rong)}  {chi_tiet}")
        if not dat and khac_phuc:
            for d in khac_phuc.splitlines():
                print(f"{'':>10} -> {d}")
        if not dat:
            hong.append(muc)

    print("\n" + "=" * 78)
    if hong:
        print(f"CHUA SAN SANG: {len(hong)}/{len(ket_qua)} muc chua dat")
        for m in hong:
            print(f"   - {m}")
        print("\nKhac phuc cac muc tren roi chay lai script nay.")
    else:
        print(f"SAN SANG -- ca {len(ket_qua)} muc deu dat. Co the bat dau tao kich ban.")
        print("Buoc tiep theo: doc FTS Server/scenario/HUONG_DAN_TAO_KICH_BAN.md")
    print("=" * 78)
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
