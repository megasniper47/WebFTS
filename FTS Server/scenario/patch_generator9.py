import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update STAR_IAF
old_iaf = """STAR_IAF = {
    # tên: (lat, lon, alt_ft khi CRE, spd_kt khi CRE)
    "HUE": (16.402222, 107.701667, 14000, 280),
    "CAHEO": (16.536389, 107.965278, 13000, 280),   # +FL130 theo chart
    "BUNTA": (16.833333, 109.395000, 14000, 280),
    "KUMUN": (14.971389, 108.807500, 14000, 280),
    "SADIN": (15.080000, 108.177222, 14000, 280),
    "VILOT": (15.038611, 108.111667, 14000, 280),
    "LATOM": (14.879444, 107.843611, 14000, 280),
    "PAPRA": (15.766667, 107.183333, 14000, 280),
}"""
new_iaf = """STAR_IAF = {
    # tên: (lat, lon, alt_ft khi CRE, spd_kt khi CRE)
    "HUE": (16.402222, 107.701667, 24000, 280),
    "CAHEO": (16.536389, 107.965278, 24000, 280),
    "BUNTA": (16.833333, 109.395000, 24000, 280),
    "KUMUN": (14.971389, 108.807500, 24000, 280),
    "SADIN": (15.080000, 108.177222, 24000, 280),
    "VILOT": (15.038611, 108.111667, 24000, 280),
    "LATOM": (14.879444, 107.843611, 24000, 280),
    "PAPRA": (15.766667, 107.183333, 24000, 280),
}"""
content = content.replace(old_iaf, new_iaf)

# 2. Update _CHAIN_HINTA_ONWARD
old_hinta = """_CHAIN_HINTA_ONWARD = [
    (16.167500, 108.048611, 9022, 280),   # HINTA +2750m
    (16.020000, 108.081667, 8038, 225),   # DN369 -2450m, <=420km/h(≈227kt)
    (15.854722, 108.105278, 7500, 250),   # TAWAN (không khống chế trên chart)
    (15.767222, 108.118333, 6070, 250),   # CADAS +1850m
]"""
new_hinta = """_CHAIN_HINTA_ONWARD = [
    (16.167500, 108.048611, 15000, 280),  # HINTA
    (16.020000, 108.081667, 12000, 250),  # DN369
    (15.854722, 108.105278, 8000, 250),   # TAWAN
    (15.767222, 108.118333, 6070, 250),   # DOTEN
]"""
content = content.replace(old_hinta, new_hinta)

# 3. Update _CHAIN_NOCKA_ONWARD
old_nocka = """_CHAIN_NOCKA_ONWARD = [
    (15.419444, 108.046667, 10000, 280),  # NOCKA +FL100
    (15.585278, 108.022500, 9000, 280),   # DN368 (không khống chế trên chart)
    (15.750833, 107.998611, 7054, 225),   # VIDAN +2150m, <=420km/h(≈227kt)
    (15.767222, 108.118333, 6070, 250),   # CADAS +1850m
]"""
new_nocka = """_CHAIN_NOCKA_ONWARD = [
    (15.419444, 108.046667, 16000, 280),  # NOCKA
    (15.585278, 108.022500, 12000, 280),  # DN368
    (15.750833, 107.998611, 8500, 250),   # VIDAN
    (15.767222, 108.118333, 6070, 250),   # DOTEN
]"""
content = content.replace(old_nocka, new_nocka)

# 4. Update STAR_CHAINS
old_chains = """STAR_CHAINS = {
    "HUE": _CHAIN_HINTA_ONWARD,                                            # IAF -> HINTA thẳng (VẪN "2K", giữ nguyên qua CADAS theo yêu cầu)
    "CAHEO": _CHAIN_HINTA_ONWARD,                                          # IAF -> HINTA thẳng (CAHEO +FL130 chỉ là cao độ CRE, VẪN "2K")
    # BUNTA: ĐÃ ĐỔI SANG "BUNTA 2M" (bản sửa đổi AIP thật, đọc trực tiếp từ
    # PDF STAR RNAV RWY35LR HUE 2M/CAHEO 2M/BUNTA 2M, © 2023 CAAV) -- không
    # còn qua CADAS nữa, hội tụ tại LINDA rồi cùng KONGA->ROMIN->ZATON->ESSEN
    # tới CADAS (điểm hội tụ đo giãn cách MỚI, xem CADAS/_full_pre_cadas_chain
    # ở dưới). HUE/CAHEO KHÔNG đổi (giữ "2K" qua CADAS) theo yêu cầu người
    # dùng -- chỉ riêng BUNTA dùng lộ trình LINDA mới này.
    "BUNTA": [
        (16.354167, 108.664722, 13000, 280),   # KANGU +FL130 (94.26km từ BUNTA)
        (16.258056, 108.507222, 12000, 280),   # LINDA +FL120 (19.91km)
        (15.908611, 108.512500, 7054, 250),    # KONGA -2150m(max)=7054ft (38.67km)
        (15.820556, 108.512778, 6600, 240),    # ROMIN (không khống chế trên chart, giảm dần) (9.74km)
        (15.799722, 108.358056, 6300, 230),    # ZATON (16.74km)
        (15.633889, 108.381667, 6100, 225),    # ESSEN, ngay trước CADAS (18.52km)
    ],
    "KUMUN": _CHAIN_NOCKA_ONWARD,                                          # IAF -> NOCKA thẳng
    "SADIN": [(15.262778, 108.106944, 11000, 280)] + _CHAIN_NOCKA_ONWARD,  # qua HENTA +FL110 trước
    "VILOT": [(15.254444, 108.074722, 11000, 280)] + _CHAIN_NOCKA_ONWARD,  # qua KHUHO +FL110 trước
    "LATOM": [(15.262500, 107.987500, 11000, 280)] + _CHAIN_NOCKA_ONWARD,  # qua NOVAN +FL110 trước
    "PAPRA": [
        (15.748611, 107.733056, 9022, 280),   # MANGA +2750m
        (15.750833, 107.998611, 7054, 225),   # VIDAN +2150m, <=420km/h
        (15.767222, 108.118333, 6070, 250),   # CADAS +1850m
    ],
}"""
new_chains = """STAR_CHAINS = {
    "HUE": _CHAIN_HINTA_ONWARD,
    "CAHEO": _CHAIN_HINTA_ONWARD,
    "BUNTA": [
        (16.354167, 108.664722, 24000, 280),   # KANGU
        (16.258056, 108.507222, 22000, 280),   # LINDA
        (15.908611, 108.512500, 15000, 250),   # KONGA
        (15.820556, 108.512778, 12000, 240),   # ROMIN
        (15.799722, 108.358056, 9500, 230),    # ZATON
        (15.633889, 108.381667, 8000, 225),    # ESSEN
    ],
    "KUMUN": _CHAIN_NOCKA_ONWARD,
    "SADIN": [(15.262778, 108.106944, 20000, 280)] + _CHAIN_NOCKA_ONWARD,  # HENTA
    "VILOT": [(15.254444, 108.074722, 20000, 280)] + _CHAIN_NOCKA_ONWARD,  # KHUHO
    "LATOM": [(15.262500, 107.987500, 20000, 280)] + _CHAIN_NOCKA_ONWARD,  # NOVAN
    "PAPRA": [
        (15.748611, 107.733056, 14000, 280),  # MANGA
        (15.750833, 107.998611, 8500, 250),   # VIDAN
        (15.767222, 108.118333, 6070, 250),   # DOTEN
    ],
}"""
content = content.replace(old_chains, new_chains)

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)
