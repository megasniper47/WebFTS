# BÁO CÁO KIỂM CHỨNG KỊCH BẢN CẤT/HẠ CÁNH XEN KẼ — CẢNG HKQT ĐÀ NẴNG (VVDN)

**Cấu hình khai thác:** hướng 35, hai đường CHC song song (cách nhau 214 m) khai thác **phụ thuộc** — 35L hạ cánh (ILS), 35R cất cánh, cất/hạ cánh **xen kẽ**
**Thời lượng:** 60 phút, một pha · **Seed:** 20261102 (tái lập 100 %) · **Mô hình hiệu năng:** BADA 3.16
**Phân cách áp dụng:** dự thảo *Phương thức khai thác 2 đường CHC song song Đà Nẵng* (24.7.2026), dự thảo *MANOP APP/TWR Đà Nẵng* (011026_Du-thao-Manop-DN-PB03) và ICAO Doc 4444
**Ngày lập:** 04/11/2026 — **thay hoàn toàn** bản cùng ngày dùng `compliance_rulesets/VVDN.json` (bản đó áp sai hai quy tắc phân cách, xem mục II)

---

## I. KẾT LUẬN CHÍNH

| Nội dung | Kết quả |
|---|---|
| **Số chuyến xử lý trong 60 phút** | **13 đến + 13 đi = 26 lần chuyến**, xen kẽ tuyệt đối (Đ-I-Đ-I…) |
| **Chu kỳ đến–đi khi không bị mặt đất cản** | **150–168 s** giữa hai chuyến đến (≈ 21–24 đến + 21–24 đi mỗi giờ) |
| **Nhịp hạ cánh thực tế** | TB **242 s**, nhỏ nhất **180 s**, lớn nhất 491 s |
| Số mục kiểm chứng | **26 mục, 0 mục KHÔNG ĐẠT** (11 mục trên lịch + 15 mục đo trong mô phỏng) |
| Vi phạm phân cách trên không / mặt đất | **0** |

**Phát hiện nghiệp vụ cốt lõi:** khi áp đúng văn bản, **phân cách trên đường CHC không phải yếu tố khống chế**. Một chu kỳ đến–đi gồm: chạm càng → 30 s → chạy đà, rồi tàu đến kế tiếp phải còn ≥ 5–7 NM (bảng mục 4.2.1) và đồng thời cách tàu đến trước ≥ 8 NM (MANOP). Chu kỳ đó chỉ mất **150–168 s**.

Năng lực bị kéo xuống 26 lần chuyến/giờ bởi **ràng buộc mặt đất**, cụ thể năm chuyến đi phải **lùi giờ cất cánh tổng cộng 830 s** (≈ 14 phút, ≈ 5 chu kỳ):

1. **Hạn chế đường lăn E (MANOP):** khi tàu code D/E cất cánh 35R thì chỉ tàu code C được ở trên đường lăn E. Tàu đi lăn trên E khoảng 300 s, dài hơn khoảng cách giữa hai lần cất cánh. Vì vậy tàu HEAVY phải tới điểm chờ trước khi một tàu HEAVY khác chạy đà, hoặc phải đợi ở bến.
2. **Tuyến lăn chung:** tàu đến thoát ly G4 về bến 28 lăn **ngược chiều** với tàu đi từ bến 26/27 trên cùng đoạn đường lăn E.
3. **Điểm chờ E chỉ có một vị trí dừng** (giả định của kịch bản, mục 2.2).

> **Lưu ý khi diễn giải:** con số 26 lần chuyến/giờ là **cận dưới** của cấu hình này, vì kịch bản đơn giản hoá phần mặt đất (một vị trí chờ, lăn đều tốc không có điểm dừng trung gian). Nếu bỏ được ràng buộc mặt đất, phân cách trên CHC cho phép khoảng **42–48 lần chuyến/giờ**. Kết luận "không vi phạm" là hệ quả của **thiết kế thuật toán** (ưu tiên phân cách tuyệt đối), không phải khẳng định khai thác thực tế không có vi phạm.

---

## II. VÌ SAO LẬP LẠI BÁO CÁO: BẢN TRƯỚC ÁP SAI QUY TẮC

Bản trước lấy phân cách từ `FTS Server/data/compliance_rulesets/VVDN.json`. Khi đối chiếu nguyên văn dự thảo và MANOP, phát hiện hai lỗi:

| Quy tắc | Bản trước (sai) | Văn bản thực tế |
|---|---|---|
| Cất cánh 35R so với tàu đến 35L | **8 NM** mọi cặp (VVDN-LINEUP-001, trích "CHC song song VVDN.pdf" mục 4.1.4/4.2.4/4.3.4 — file không có trong dự án, chưa đọc được nguyên văn) | Dự thảo mục **4.2.1** = MANOP Phụ lục mục **4.2.1**: bảng cự ly tàu đến khi cấp huấn lệnh cất cánh, **5/5/6/7 NM** theo loại tàu |
| Hạ cánh liên tiếp 35L | 6/7/5/5 NM (VVDN-SEP-*) | Đây chính là bảng cất cánh–hạ cánh ở trên bị đọc nhầm (tiêu đề hàng = *Tàu bay cất cánh*, cột = *Tàu bay hạ cánh*). Dự thảo **không có** ma trận hạ cánh liên tiếp. Nguồn đúng là MANOP mục Phân cách giám sát ATS: **4/5/3/3 NM**, tối thiểu 3 NM, và giãn cách hạ cánh liên tiếp **8 NM** |

Giá trị sai được lưu trong `vvdn_xenke_rules.json` (khoá `_gia_tri_sai_da_bo_2026_11_04`) để đối chiếu. **Kiến nghị người quản lý `compliance_rulesets/VVDN.json` rà lại hai nhóm quy tắc này.**

---

## III. PHÂN CÁCH VÀ QUY ĐỊNH ÁP DỤNG

### 3.1 Trên đường CHC và trên không

| Quy định | Giá trị | Nguồn | Trạng thái |
|---|---|---|---|
| **Cấp huấn lệnh cất cánh 35R** | Chỉ sau khi tàu hạ cánh đã **chạm càng chính** trên 35L (07h–17h, thời tiết tốt). Kịch bản: chạy đà 30 s sau chạm càng, huấn lệnh trước đó 10 s (code C) / 15 s (code D+) | Dự thảo / MANOP mục 4.2.1.a | Theo văn bản |
| **Tàu đến kế tiếp khi cấp huấn lệnh cất cánh** (có giám sát ATS) | Hàng = tàu cất cánh, cột = tàu hạ cánh: **M/M 5 · M/H 5 · H/H 6 · H/M 7 NM** (SUPER/LIGHT theo bảng đầy đủ) | Dự thảo mục 4.2.1 = MANOP Phụ lục mục 4.2.1 | Theo văn bản (cả hai đều là **dự thảo**) |
| **Hạ cánh liên tiếp 35L — nhiễu động** | H sau H **4** · M sau H **5** · M sau M **3** · H sau M **3 NM**; tối thiểu **3 NM** | MANOP, Phân cách giám sát ATS (= ICAO Doc 4444 8.7.3.4); 35L/35R cách 214 m < 760 m ⇒ áp như một CHC | Theo văn bản |
| **Giãn cách hạ cánh liên tiếp** | **8 NM** (tàu trước chạm bánh khi tàu sau còn 8 NM), *gia tăng thích hợp khi có tàu cất cánh xen giữa* | MANOP, quy trình KSVKL APP | **CẦN XÁC NHẬN** — văn bản viết *"có thể là 8NM"*; kịch bản hiểu là mức tối thiểu bắt buộc |
| **Giải phóng 35L trước huấn lệnh hạ cánh** | Tàu hạ cánh trước phải **cắt qua hết 35R** trước khi tàu sau tới 2 NM | MANOP: huấn lệnh hạ cánh trước 2 NM, chỉ khi tàu trước đã rời CHC; Phụ lục: tàu dừng chờ giữa hai CHC ⇒ **không sử dụng 35L** | Theo văn bản |
| **Cất cánh liên tiếp 35R** | M sau H **120 s** (MANOP, ICAO 5.8); các ô còn lại 60–120 s và theo SID là giá trị đệm của đề bài | MANOP + đề bài | Không ràng buộc trong lịch xen kẽ (hai lần cất cánh luôn cách nhau một chuyến đến) |

### 3.2 Trên mặt đất (MANOP Phụ lục 2 CHC song song)

| Quy định | Cách áp dụng trong kịch bản |
|---|---|
| **Cắt qua 35R** | Tàu đến thoát ly 35L ra G4/G6 (nằm **giữa** hai CHC) rồi cắt qua 35R về bến 28/8. Dừng chờ trước vạch 35R; chỉ cắt khi tàu cất cánh đã qua điểm cắt; cắt xong trong **45 s** (lăn 15 kt) |
| **Tàu dừng chờ giữa hai CHC** | Không có tàu nào chạm bánh 35L trong lúc đó (bảo đảm bằng quy tắc giải phóng 35L ở mục 3.1) |
| **Đường lăn E** (song song 35R, cách tim 148 m) | Tàu code D/E/F cất cánh ⇒ chỉ tàu code C ở trên E; tàu code C cất cánh ⇒ tàu code E trở xuống được ở trên E. Áp từ lúc chạy đà tới khi rời đường CHC (60 s, đo trong mô phỏng) |
| **Thoát ly 35L** | ≤ **100 s** từ lúc qua ngưỡng tới khi qua vạch dừng chờ của đường lăn thoát ly (hoặc tới vị trí dừng chờ giữa hai CHC) |
| **Chạy đà sau huấn lệnh** | ≤ 10 s (code C) / 15 s (code D trở lên) |

Vạch dừng chờ đo trực tiếp từ `taxiway_centerlines.geojson`: 35R ở **−91 m / +94 m** so với tim 35R, 35L ở **−122 m**. Tàu dài trên 32 m dừng giữa hai CHC luôn lấn vạch của một trong hai đường — chính là lý do MANOP đóng 35L khi có tàu chờ ở đó.

### 3.3 Các mục **CẦN XÁC NHẬN**

1. **8 NM là tối thiểu bắt buộc hay chỉ là hướng dẫn** (*"có thể là 8NM"*). Nếu chỉ là hướng dẫn, chu kỳ trên CHC rút ngắn thêm, nhưng năng lực của kịch bản này hầu như không đổi vì mặt đất đang khống chế.
2. **Phạm vi "đường lăn E"**: kịch bản tính trong vòng 30 m quanh tim E, **không tính** vị trí dừng chờ cất cánh (trong vòng 100 m quanh PREHOLD).
3. **Tàu code F (B748)**: MANOP chỉ nói tới code C/D/E. Kịch bản áp cách hiểu chặt: code F không được ở trên E khi có **bất kỳ** tàu nào cất cánh 35R. Nếu có chuyến đi B748, kịch bản bỏ trống một khe cất cánh. Lịch hiện tại có B748 là chuyến **đến** (ARR013), không có chuyến đi B748.
4. **Cả hai văn bản nguồn đều là dự thảo** — cần đối chiếu lại khi có bản ký.

---

## IV. KẾT QUẢ KIỂM CHỨNG

Script `_verify_vvdn_xenke.py` **không dùng lại** hàm lập lịch của generator. Nó tự đọc file quy tắc, file lịch và các file `.geojson` sơ đồ sân bay, rồi tự tính lại từng điều kiện.

### Phần A — kiểm tra trên lịch

| # | Nội dung | Kết quả | Số liệu |
|---|---|---|---|
| A1 | Cơ cấu đội tàu (đến / đi) | ✅ ĐẠT | mỗi chiều 9 M + 4 H / 13 chuyến, đúng hạn ngạch 70/30 |
| A2 | Hạ cánh liên tiếp 35L (nhiễu động + 8 NM) | ✅ ĐẠT | 12 cặp, 0 không đạt |
| A3 | Cất cánh liên tiếp 35R | ✅ ĐẠT | 12 cặp, 0 không đạt |
| A4 | Cất cánh 35R vs tàu đến kế tiếp (bảng 4.2.1) | ✅ ĐẠT | 13 chuyến đi, 0 không đạt |
| A5 | Huấn lệnh cất cánh sau chạm càng | ✅ ĐẠT | 13 chuyến đi |
| A6 | Số tàu tại điểm chờ trước 35R | ✅ ĐẠT | lớn nhất **2** tàu (giới hạn 3) |
| A7 | Lên đường CHC sau khi tàu trước chạy đà | ✅ ĐẠT | 12 cặp |
| A8 | Tính xen kẽ | ✅ ĐẠT | chuỗi cùng loại dài nhất **1** |
| A9 | Thông lượng 60 phút | 📊 | 13 đến + 13 đi = 26; nhịp đến TB 242 s, nhỏ nhất 180 s |
| A10 | Mọi chuyến đi bắt đầu lăn trong phạm vi kịch bản | ✅ ĐẠT | sớm nhất 02:47,5 |

### Phần B — đo trong mô phỏng headless thật (BADA 3.16)

| # | Nội dung | Kết quả | Số liệu |
|---|---|---|---|
| B1 | Mọi chuyến đến đều chạm càng | ✅ ĐẠT | **13/13** |
| B2 | Sai lệch chạm càng so với lịch | 📊 | TB **2,5 s**, lớn nhất **4,0 s** (ARR005) |
| B3 | Cự ly **thật** giữa hai tàu hạ cánh liên tiếp (lúc tàu trước chạm bánh) | ✅ ĐẠT | 12 cặp, nhỏ nhất **8,43 NM** (yêu cầu 8 NM) |
| B4 | Cảnh báo xung đột trên không | ✅ ĐẠT | **0 cặp** |
| B5 | Pha lăn bám tim đường lăn thật | ✅ ĐẠT | 26 tàu, lệch TB **1,4 m** |
| B6 | Không có tàu bị "trôi" khi lăn | ✅ ĐẠT | tốc độ lăn lớn nhất 22,4 kt, 0 tàu vượt 60 kt |
| B7 | Mọi chuyến đến lăn về tới bến | ✅ ĐẠT | **13/13** |
| B8 | Cự ly giữa hai tàu đang lăn | ✅ ĐẠT | **0 cặp vi phạm**; sát nhất ARR008 ↔ DEP011 **81 m** (yêu cầu 58 m) |
| B9 | Lên đường CHC và chạy đà đúng tim 35R | ✅ ĐẠT | lệch **0,0 m** lúc chạy đà, **0,1 m** suốt pha chạy đà |
| B10 | Cất cánh 35R vs tàu đến 35L — **đo thật** lúc chạy đà; huấn lệnh sau chạm càng | ✅ ĐẠT | 13 chuyến đi, dư nhỏ nhất **+0,11 NM** so với bảng 4.2.1 |
| B11a | Cắt qua 35R trong 45 s | ✅ ĐẠT | 13 lần, lâu nhất **34 s** (vạch dừng chờ đo được −91 m / +94 m) |
| B11b | Không cắt qua 35R khi tàu cất cánh chưa qua điểm cắt | ✅ ĐẠT | 13 × 13 cặp, **0 xung đột**; dừng chờ giữa hai CHC lâu nhất 76 s (ARR004) |
| B11c | Tàu trước cắt qua hết 35R trước khi tàu sau tới 2 NM | ✅ ĐẠT | 12 cặp, 0 không đạt |
| B12 | Đường lăn E khi tàu code D/E/F cất cánh | ✅ ĐẠT | 13 lần cất cánh, **0 vi phạm** |
| B13 | Thoát ly 35L trong 100 s | ✅ ĐẠT | lâu nhất **97 s** (ARR004) |

**Tổng: 26 mục, 0 mục KHÔNG ĐẠT** (24 ĐẠT + 2 mục số liệu A9, B2).

B10 chỉ dư **0,11 NM** và B13 sát mốc (97/100 s): lịch được xếp **sát** phân cách tối thiểu, đúng mục đích đo trần năng lực. Nếu đổi tham số lăn hoặc thoát ly, nên xem lại hai mục này trước tiên.

---

## V. THAY ĐỔI KỸ THUẬT TRONG LẦN LẬP LẠI NÀY

1. **Áp đúng hai quy tắc phân cách** (mục II).
2. **Mô hình hoá cắt qua 35R.** Bản trước ghi trong file `.scn` rằng tuyến về bến 28/8 *"không phải cắt qua 35R"* — **sai**: đo bằng tim đường CHC thật thì cả hai tuyến đều cắt qua 35R. Tuyến lăn vào bến được tách ba đoạn: (1) tới vị trí dừng chờ trước vạch 35R giữa hai CHC, (2) cắt qua ở 15 kt, (3) về bến. Chuỗi thoát ly LNAV của G6 được rút ngắn: điểm cuối cũ chỉ cách tim 35R 112 m, tàu dài đã lấn mũi qua vạch 35R.
3. **Hạn chế đường lăn E theo mã chữ sân bay** — sải cánh từng loại ghi trong `vvdn_xenke_rules.json` (ICAO Annex 14, Bảng 1-1).
4. **Một vị trí dừng chờ tại điểm chờ E.** Bản trước ghim mọi tàu chờ vào **cùng một toạ độ** (tàu chồng lên nhau). Lỗi này không lộ ra vì trước đây không có tàu nào phải chờ sớm; khi áp hạn chế đường lăn E, đo được 4 cặp tàu cách nhau 0–7 m.
5. **Thời gian thoát ly 35L.** Đệm 10 s trước khi chuỗi lệnh lăn tiếp quản làm 3 chuyến thoát ly G6 mất 102–104 s (vượt 100 s). Giảm còn 4 s, vẫn lớn hơn sai lệch chạm bánh sau hiệu chuẩn (≤ 3,9 s).
6. **Hạn chế đường lăn E xét cả chuyến đến vừa hạ cánh.** Khi giờ cất cánh bị lùi, chuyến đến trước đó có thể đã cắt qua 35R và đang lăn trên E đúng lúc chạy đà (lần chạy đầu: DEP005 B772 cất cánh khi ARR005 B773 còn trên E). Generator tính lại lịch lăn vào của chuyến đến theo giờ chạy đà đang xét.
7. **Lùi giờ cất cánh khi không có giờ lăn ra hợp lệ** — generator lùi 15 s mỗi lần rồi lập lại cả lịch, giống cách điều hành thật.
8. **Hiệu chuẩn lại từ đầu** (lịch mới hoàn toàn khác): hội tụ sau 6 vòng (sai lệch lớn nhất 4,0 s), lần sửa cuối xác nhận ngay vòng 1 vòng.

Các lỗi đã ghi nhận ở những bản trước (hiệu chuẩn có điểm gãy, khoảng trống giữa hai lệnh `MOVE`, toạ độ lên đường CHC lệch tim 41,2 m, SID bắt đầu ngoài đường CHC, tránh nhau khi lăn bằng lập lịch…) vẫn được xử lý như cũ; chi tiết trong `HUONG_DAN_TAO_KICH_BAN.md` phần 4.

---

## VI. BẢNG LỊCH KỊCH BẢN

Đ = chuyến đến (chạm càng 35L), I = chuyến đi (bắt đầu chạy đà 35R). NĐX/Mã = nhóm nhiễu động / mã chữ sân bay.

| Thời điểm | Loại | Số hiệu | Tàu bay | NĐX/Mã | SID/STAR | Đường lăn / bến | Giãn cách |
|---|---|---|---|---|---|---|---|
| 08:50,0 | Đ | ARR001 | A320 | M/C | CAHEO | G6 → bến 8 | — |
| 09:20,0 | I | DEP001 | B38M | M/C | VIDEN | bến 27 | +30 s |
| 11:55,8 | Đ | ARR002 | A321 | M/C | SADIN | G4 → bến 28 | +156 s |
| 12:25,8 | I | DEP002 | A320 | M/C | XAQUA | bến 26 | +30 s |
| 15:01,6 | Đ | ARR003 | B738 | M/C | BUNTA | G6 → bến 8 | +156 s |
| 15:31,6 | I | DEP003 | B77W | H/E | KONCO | bến 26 | +30 s |
| 18:19,6 | Đ | ARR004 | A320 | M/C | SADIN | G6 → bến 8 | +168 s |
| 20:04,6 | I | DEP004 | B38M | M/C | BUNTA | bến 27 | +105 s |
| 22:24,0 | Đ | ARR005 | B773 | H/E | VILOT | G6 → bến 8 | +139 s |
| 25:58,8 | I | DEP005 | B772 | H/E | PAPRA | bến 27 | +215 s |
| 28:13,8 | Đ | ARR006 | B744 | H/E | CAHEO | G6 → bến 8 | +135 s |
| 28:43,8 | I | DEP006 | A320 | M/C | XAQUA | bến 26 | +30 s |
| 31:13,8 | Đ | ARR007 | B38M | M/C | PAPRA | G4 → bến 28 | +150 s |
| 33:43,8 | I | DEP007 | B738 | M/C | KUMUN | bến 27 | +150 s |
| 35:43,8 | Đ | ARR008 | A320 | M/C | HUE | G4 → bến 28 | +120 s |
| 36:13,8 | I | DEP008 | B38M | M/C | KUMUN | bến 27 | +30 s |
| 38:49,6 | Đ | ARR009 | A21N | M/C | PAPRA | G4 → bến 28 | +156 s |
| 39:19,6 | I | DEP009 | A332 | H/E | PHULU | bến 26 | +30 s |
| 41:55,4 | Đ | ARR010 | B788 | H/E | BUNTA | G4 → bến 28 | +156 s |
| 42:25,4 | I | DEP010 | B739 | M/C | KUMUN | bến 27 | +30 s |
| 44:55,4 | Đ | ARR011 | B38M | M/C | VILOT | G4 → bến 28 | +150 s |
| 51:10,4 | I | DEP011 | A320 | M/C | KUMUN | bến 27 | +375 s |
| 53:06,6 | Đ | ARR012 | A21N | M/C | VILOT | G4 → bến 28 | +116 s |
| 55:21,6 | I | DEP012 | B738 | M/C | KONCO | bến 27 | +135 s |
| 57:14,1 | Đ | ARR013 | B748 | H/F | LATOM | G4 → bến 28 | +112 s |
| 57:44,1 | I | DEP013 | A332 | H/E | VIDEN | bến 27 | +30 s |

Chu kỳ không bị cản: chạm càng → **+30 s** chạy đà → **+120…138 s** chuyến đến kế tiếp. Năm chuyến đi bị lùi giờ cất cánh để có giờ lăn ra hợp lệ hoặc để tránh vi phạm hạn chế đường lăn E: DEP004 +75 s, DEP005 +185 s, DEP007 +120 s, DEP011 +345 s, DEP012 +105 s.

---

## VII. SỐ LIỆU LĂN, CẮT QUA 35R VÀ ĐIỂM CHỜ

| Chỉ tiêu | Giá trị |
|---|---|
| Thời gian lăn ra (bến 26/27 → điểm chờ 35R) | 333–337 s |
| Thời gian chờ tại điểm chờ trước 35R | TB **200 s**, dao động 56–550 s (DEP011 lâu nhất) |
| Thời gian chờ trước vạch 35R giữa hai CHC | 0–66 s (ARR004 lâu nhất) |
| Thời gian lăn vào bến (hết chuỗi thoát ly → bến) | 173–243 s |
| Số tàu tại điểm chờ lớn nhất | **2** (giới hạn đề bài 3; kịch bản chỉ cho **một** tàu dừng tại vị trí chờ E) |
| Cắt qua 35R | lâu nhất **34 s** (giới hạn 45 s) |
| Thoát ly 35L (qua ngưỡng → vị trí dừng chờ) | lâu nhất **97 s** (giới hạn 100 s) |
| Độ lệch tim đường lăn / tim 35R | TB 1,4 m / 0,0–0,1 m |

---

## VIII. SẢN PHẨM BÀN GIAO

| File | Nội dung |
|---|---|
| `VVDN-XENKE-60MIN.scn` | **Kịch bản mô phỏng** — 266.665 byte, 4.459 lệnh; phần đầu ghi seed, phân cách áp dụng và nguồn, giả định |
| `_gen_vvdn_xenke_60min.py` | Generator, seed cố định, tái lập 100 % |
| `vvdn_xenke_rules.json` | Quy tắc phân cách và mặt đất, mỗi nhóm ghi điều khoản nguồn; giá trị sai cũ lưu kèm |
| `_verify_vvdn_xenke.py` | Kiểm chứng độc lập — 26 mục, chạy mô phỏng headless thật |
| `_calib_vvdn_xenke.py` | Hiệu chuẩn thời điểm tạo tàu đến |
| `VVDN-XENKE-60MIN.plan.json` / `.calib.json` | Lịch chi tiết / bảng hiệu chuẩn (BADA 3.16) |
| `BaoCao_KiemChung_VVDN_XenKe.md` / `.docx` | Báo cáo này |

### Cách chạy lại

```bash
cd "FTS Server/scenario"
python _gen_vvdn_xenke_60min.py         # sinh kịch bản (~2,5 phút)
python _calib_vvdn_xenke.py             # hiệu chuẩn — chỉ cần khi lịch thay đổi
python _verify_vvdn_xenke.py --static   # kiểm tra nhanh trên lịch
python _verify_vvdn_xenke.py            # kiểm chứng đầy đủ, có chạy mô phỏng
```

Hiệu chuẩn và phần B **bắt buộc chạy với BADA** (`performance_model = 'bada'`).

---

## IX. KIẾN NGHỊ

1. **Xác nhận bốn mục ở 3.3**, đặc biệt cách hiểu 8 NM và phạm vi "đường lăn E", trước khi dùng con số năng lực vào công tác chuyên môn.
2. **Rà lại `compliance_rulesets/VVDN.json`** — hai nhóm quy tắc đọc sai văn bản (mục II).
3. **Mô hình hoá xếp hàng tại điểm chờ E và điểm dừng trung gian khi lăn** để đo năng lực sát thực tế hơn. Mặt đất đang khống chế: năng lực CHC cho phép khoảng 42–48 lần chuyến/giờ, kịch bản chỉ đạt 26.
4. **Đánh giá phương án tuyến lăn** cho tàu về bến 28 (đang lăn ngược chiều tàu đi trên đường lăn E) — đây là một trong ba nguyên nhân làm lùi giờ cất cánh.
