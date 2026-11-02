"""Quet nang luc: tang dan nhip MUC TIEU va do nhip THUC TE dat duoc.

Thuat toan lap lich luon uu tien phan cach toi thieu, nen khi nhip muc tieu
vuot nang luc thi lich TU GIAN RA chu khong sinh ra vi pham. Gia tri ma thong
luong thuc te BAO HOA chinh la nang luc dieu hanh bay toi da cua cau hinh
khai thac 35L ha canh / 35R cat canh xen ke.

Chay:  python _sweep_vvdn_xenke.py    -> in bang + ghi VVDN-XENKE-60MIN.sweep.json
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import importlib.util
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
MUC_TIEU = [24, 30, 36, 40, 45, 50, 55, 60, 70, 90, 120]


def nap_generator():
    spec = importlib.util.spec_from_file_location("g", HERE / "_gen_vvdn_xenke_60min.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def main():
    g = nap_generator()
    ket_qua = []
    print(f"{'Muc tieu':>9} {'Thuc te':>9} {'Nhip den TB':>12} {'Nhip den min':>13} {'So chuyen':>11}")
    print("-" * 60)
    for muc in MUC_TIEU:
        for ph in g.PHASES:
            ph["muc_tieu_chuyen_dong_gio"] = muc
        arrs, deps, _ = g.schedule(random.Random(g.SEED), g.FIRST_ARR_TD, 60, 60)
        if len(arrs) < 3:
            continue
        gaps = [arrs[i]["td"] - arrs[i - 1]["td"] for i in range(1, len(arrs))]
        span = arrs[-1]["td"] - arrs[0]["td"]
        rate = (len(arrs) + len(deps) - 2) * 3600 / span if span else 0.0
        ket_qua.append({"muc_tieu_chuyen_dong_gio": muc,
                        "thuc_te_chuyen_dong_gio": round(rate, 1),
                        "nhip_den_trung_binh_s": round(sum(gaps) / len(gaps)),
                        "nhip_den_nho_nhat_s": round(min(gaps)),
                        "so_chuyen_den": len(arrs), "so_chuyen_di": len(deps)})
        print(f"{muc:>7}/h {rate:>7.1f}/h {sum(gaps)/len(gaps):>11.0f}s "
              f"{min(gaps):>12.0f}s {len(arrs):>5}+{len(deps):<5}")

    bao_hoa = max(k["thuc_te_chuyen_dong_gio"] for k in ket_qua)
    nguong = min(k["muc_tieu_chuyen_dong_gio"] for k in ket_qua
                 if k["thuc_te_chuyen_dong_gio"] >= bao_hoa - 0.5)
    print(f"\nNang luc BAO HOA: {bao_hoa}/h chuyen dong "
          f"(~{bao_hoa/2:.1f} chuyen den + {bao_hoa/2:.1f} chuyen di moi gio)")
    print(f"Nhip den nho nhat dat duoc: "
          f"{min(k['nhip_den_nho_nhat_s'] for k in ket_qua)}s")
    print(f"Tang nhip muc tieu tren {nguong}/h KHONG lam tang thong luong nua.")
    (HERE / "VVDN-XENKE-60MIN.sweep.json").write_text(
        json.dumps({"ket_qua": ket_qua, "nang_luc_bao_hoa_chuyen_dong_gio": bao_hoa,
                    "nguong_bao_hoa_muc_tieu": nguong}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print("Da ghi VVDN-XENKE-60MIN.sweep.json")


if __name__ == "__main__":
    main()
