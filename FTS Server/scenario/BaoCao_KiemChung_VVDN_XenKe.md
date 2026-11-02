# BÁO CÁO KIỂM CHỨNG KỊCH BẢN CẤT CÁNH XEN KẼ — CẢNG HKQT ĐÀ NẴNG (VVDN)

**Cấu hình khai thác:** hướng 35, hai đường CHC song song **phụ thuộc** — 35L hạ cánh (ILS), 35R cất cánh
**Thời lượng:** 60 phút · **Seed:** 20261102 (tái lập 100%)
**Ngày lập:** 02/11/2026

---

## I. KẾT LUẬN CHÍNH

| Nội dung | Kết quả |
|---|---|
| **Năng lực điều hành bay tối đa** | **46,8 lần chuyến/giờ** (≈ 23,4 đến + 23,4 đi) |
| **Nhịp hạ cánh nhỏ nhất đạt được** | **142 giây** giữa hai chuyến đến liên tiếp |
| Số mục kiểm chứng | **20/20 ĐẠT** (10 mục tĩnh + 7 mục đo trong mô phỏng + 3 mục số liệu) |
| Vi phạm phân cách | **0** |
| Cảnh báo xung đột trên không | **0** |

**Phát hiện nghiệp vụ cốt lõi:** yếu tố khống chế năng lực **không phải** phân cách giữa hai chuyến hạ cánh liên tiếp (3–5 NM), mà là **ma trận cất cánh 35R khi có tàu đang tiếp cận 35L (5–7 NM)**. Ma trận này chặt hơn, nên muốn chen được một chuyến cất cánh giữa hai chuyến hạ cánh thì **phải giãn chuyến đến ra xa hơn mức phân cách nhiễu động xoáy yêu cầu**. Cụ thể, với cặp MEDIUM–MEDIUM:

- Phân cách hạ cánh liên tiếp yêu cầu 3 NM ≈ **72 s** → nếu chỉ hạ cánh, năng lực đạt ~50 chuyến đến/giờ.
- Nhưng để chen một chuyến đi: chạm càng → 30 s → cất cánh, rồi chuyến đến kế tiếp phải còn ≥ 5 NM ≈ 120 s → **tổng tối thiểu 150 s** giữa hai chuyến đến.

Chênh lệch **72 s → 150 s** chính là "giá" của việc xen kẽ. Đây là kết quả định lượng chính của kịch bản.

### Bảng quét năng lực

Thuật toán lập lịch **luôn ưu tiên phân cách tối thiểu**, nên khi nhịp mục tiêu vượt năng lực thì lịch tự giãn ra chứ không sinh ra vi phạm. Giá trị thông lượng bão hoà chính là năng lực thật:

| Nhịp mục tiêu | Thông lượng thực tế | Nhịp đến TB | Nhịp đến nhỏ nhất |
|---:|---:|---:|---:|
| 24/h | 24,0/h | 300 s | 300 s |
| 30/h | 30,0/h | 240 s | 240 s |
| 36/h | 36,0/h | 200 s | 200 s |
| 40/h | 39,6/h | 182 s | 180 s |
| 45/h | 43,4/h | 166 s | 160 s |
| **50/h** | **46,6/h** | 154 s | 144 s |
| 60/h | 46,8/h | 154 s | 142 s |
| 70/h | 46,8/h | 154 s | 142 s |
| 90/h | 46,8/h | 154 s | 142 s |
| 120/h | 46,8/h | 154 s | 142 s |

**Bão hoà từ mức mục tiêu 50/h.** Tăng nhịp mục tiêu lên trên mức này không làm tăng thông lượng — chỉ làm tăng thời gian chờ.

> **Lưu ý khi diễn giải:** kết luận "không phát sinh vi phạm ở mọi mật độ" là hệ quả của **thiết kế thuật toán** (ưu tiên phân cách tuyệt đối), không phải kết luận rằng khai thác thực tế sẽ không có vi phạm. Trong khai thác thật, áp lực mật độ chuyển thành **chậm chuyến và tải công việc KSVKL**, và vi phạm phát sinh khi con người phải rút ngắn phân cách để giữ nhịp. Kịch bản này lượng hoá **ngưỡng mà áp lực đó bắt đầu xuất hiện: 50 lần chuyến/giờ**.

---

## II. GIẢ ĐỊNH VÀ ĐƠN GIẢN HOÁ (ghi rõ, không che giấu)

### 2.1 Giả định cố định theo đề bài
| Hạng mục | Giá trị |
|---|---|
| Thời tiết | Tốt, đường CHC khô |
| Gió | Không có gió, không nhiễu động ⇒ tốc độ mặt đất = tốc độ thật |
| Giờ khai thác | 07:00–17:00 (ban ngày) |
| Cơ cấu đội tàu | 70 % MEDIUM / 30 % HEAVY, hạn ngạch **chính xác** rồi xáo trộn bằng seed cố định |

### 2.2 Đơn giản hoá có chủ đích
1. **Không mô phỏng bay lại / huỷ cất cánh** (theo đề bài).
2. **Pha lăn điều khiển bằng lệnh `MOVE` theo nhịp thời gian đều 2 giây**, không dùng LNAV/VNAV. Lý do: kiểm soát chính xác thời điểm tới/rời điểm chờ để số liệu kiểm chứng có ý nghĩa; đồng thời tránh hai lỗi đã ghi nhận của BlueSky (xem mục V).
3. **Tàu đi bị xoá 420 giây sau khi bắt đầu chạy đà** — khi đó đã ra khỏi khu vực TMA gần, không còn ảnh hưởng tới phân cách tại sân bay.
4. **Chưa mô phỏng cắt qua đường CHC 35R:** cả hai tuyến lăn vào bến (bến 28 và bến 8) đều nằm cùng phía tây với đường lăn thoát ly, không phải cắt qua 35R. Điều kiện cắt qua (≥ 6 NM) đã được cấu hình trong `vvdn_xenke_rules.json` nhưng chưa có tình huống nào kích hoạt.
5. **Chuyến đến đầu tiên chạm càng ở phút thứ 8:50.** Không thể sớm hơn: tàu đến sớm nhất cũng phải sinh tại CADAS (25 NM) ở thời điểm T=0, và bay từ CADAS vào ngưỡng 35L mất 455–506 giây tuỳ loại tàu. Vì vậy **pha 1 chỉ có 3 cặp chuyến** — đây là ràng buộc vật lý, không phải lỗi lập lịch.

### 2.3 Hai mục **CẦN XÁC NHẬN** trước khi dùng kết quả vào công tác chuyên môn

| Mục | Nội dung | Vì sao cần xác nhận |
|---|---|---|
| **Ma trận phân cách hạ cánh liên tiếp 35L** | H sau H = 4 NM · M sau H = 5 NM · M sau M = 3 NM · H sau M = 3 NM | Đề bài chỉ ghi "tham khảo: radar tối thiểu 3 NM; sau Heavy: 4 NM cho Heavy, 5 NM cho Medium". Hai ô còn lại là **suy ra** từ nguyên tắc radar tối thiểu, không được nêu trực tiếp. Dự án còn **một ma trận khác** (baseline 5 NM, theo dự thảo VVDN 2026 chưa ký) chưa thống nhất. |
| **Ma trận phân cách cất cánh liên tiếp 35R** | M sau H = 120 s · H sau H = 120 s · M sau M = 60 s · H sau M = 60 s; cùng đường bay 120 s / phân kỳ 60 s; ngưỡng phân kỳ 45° | Đề bài chỉ nêu trực tiếp **một** giá trị (2 phút khi Medium sau Heavy). Các ô còn lại và ngưỡng 45° là **suy diễn theo thông lệ ICAO Doc 4444**, chưa có văn bản cụ thể của Cục HKVN trong dự án để đối chiếu. |

Nếu hai ma trận này thay đổi, **năng lực 46,8 lần chuyến/giờ sẽ thay đổi theo**. Chạy lại: sửa `vvdn_xenke_rules.json` → chạy `_gen_vvdn_xenke_60min.py` → `_calib_vvdn_xenke.py` → `_verify_vvdn_xenke.py`.

---

## III. NGUỒN DỮ LIỆU

Toàn bộ toạ độ, tốc độ và sơ đồ sân bay đều lấy từ dữ liệu thật trong dự án — **không có số liệu tự đặt ra**.

| Dữ liệu | Nguồn |
|---|---|
| SID/STAR RNAV RWY 35L/R | `_gen_kb5_1hour.py` (generator kịch bản 40 chuyến đã kiểm chứng), trích từ AIP AD 2-VVDN, AMDT 01/23, cập nhật AIRAC 01/26 |
| Tốc độ tiếp cận theo từng loại tàu | Bảng `APPROACH_SPEEDS` theo BADA, cùng nguồn trên |
| Toạ độ bến 26/27 | "Toạ độ sân đỗ VVDN.pdf" (INS coordinates, © 2022 Cục HKVN) |
| Toạ độ bến 28, bến 8 | `gates.geojson` (bộ dữ liệu KML sân bay chuẩn hoá) |
| Tim đường lăn, điểm chờ | `taxiway_centerlines.geojson`, `taxiway_labels.geojson` |
| Tuyến lăn vào bến 28 / bến 8 | `_ARR_RESUME_G4_GATE28.scn` / `_ARR_RESUME_G6_GATE8.scn` |
| Quy tắc phân cách, tham số lăn | `vvdn_xenke_rules.json` (18 nhóm tham số, mỗi nhóm ghi điều khoản nguồn) |

---

## IV. KẾT QUẢ KIỂM CHỨNG CHI TIẾT

Script `_verify_vvdn_xenke.py` **không dùng lại** hàm lập lịch của generator. Nó tự đọc file quy tắc và file lịch, rồi tự tính lại từng điều kiện.

### Phần A — kiểm tra trên lịch

| # | Nội dung | Kết quả | Số liệu |
|---|---|---|---|
| A1 | Cơ cấu đội tàu (đến) | ✅ ĐẠT | 12 M + 5 H / 17 chuyến (71 %/29 %) |
| A1 | Cơ cấu đội tàu (đi) | ✅ ĐẠT | 12 M + 5 H / 17 chuyến (71 %/29 %) |
| A2 | Phân cách hai tàu hạ cánh liên tiếp 35L | ✅ ĐẠT | 16 cặp, 0 cặp không đạt |
| A3 | Phân cách hai tàu cất cánh liên tiếp 35R | ✅ ĐẠT | 16 cặp, 0 cặp không đạt |
| A4 | Cất cánh 35R khi có tàu đang tiếp cận 35L | ✅ ĐẠT | 17 chuyến đi, 0 chuyến không đạt |
| A5 | Chỉ cấp huấn lệnh chạy đà sau khi tàu đến chạm càng | ✅ ĐẠT | 17 chuyến, đúng 30 s |
| A6 | Số tàu chờ tại điểm chờ trước 35R | ✅ ĐẠT | lớn nhất **2** tàu (giới hạn 3) |
| A7 | Chỉ lên đường CHC sau khi tàu trước bắt đầu chạy đà | ✅ ĐẠT | 16 cặp, 0 trường hợp không đạt |
| A8 | Tính xen kẽ | ✅ ĐẠT | chuỗi cùng loại dài nhất **1** — xen kẽ tuyệt đối (Đ-I-Đ-I…) |
| A10 | Mọi chuyến đi bắt đầu lăn trong phạm vi kịch bản | ✅ ĐẠT | sớm nhất 02:47,5 |

### Phần B — đo trong mô phỏng headless thật

| # | Nội dung | Kết quả | Số liệu |
|---|---|---|---|
| B1 | Mọi chuyến đến đều chạm càng | ✅ ĐẠT | **17/17** |
| B2 | Sai lệch chạm càng so với lịch | 📊 | TB **0,2 s**, lớn nhất **0,5 s** |
| B3 | Cự ly **thật** giữa hai tàu hạ cánh liên tiếp | ✅ ĐẠT | 16 cặp, nhỏ nhất **6,64 NM** |
| B4 | Cảnh báo xung đột trên không | ✅ ĐẠT | **0 cặp** |
| B5 | Pha lăn bám tim đường lăn thật | ✅ ĐẠT | 34 tàu, lệch TB **1,8 m**, lớn nhất 2,3 m |
| B6 | Không có tàu bị "trôi" trong pha lăn | ✅ ĐẠT | tốc độ lăn lớn nhất **23,2 kt** |
| B7 | Mọi chuyến đến đều lăn về tới bến đỗ | ✅ ĐẠT | **17/17** |

---

## V. BỐN LỖI ĐÃ PHÁT HIỆN VÀ KHẮC PHỤC TRONG QUÁ TRÌNH KIỂM CHỨNG

Ghi lại đầy đủ vì đây là kinh nghiệm dùng được cho các kịch bản sau.

**1. Lập lịch chuyến đi xét sai "tàu đến kế tiếp"** — generator giả định chuyến đi thứ *j* luôn đi ngay sau chuyến đến thứ *j*. Khi lịch bị giãn, thứ tự này lệch. Kết quả: **9/20 chuyến đi vi phạm** cự ly với tàu đang tiếp cận (thấp nhất 4,75 NM so với yêu cầu 5 NM). Khắc phục: tìm tàu đến kế tiếp **theo thời gian**, và lặp đến khi ba ràng buộc cùng thoả mãn.

**2. Hiệu chuẩn thời điểm tạo tàu** — thời điểm tạo tàu được tính ngược từ mốc chạm càng bằng hàm ước lượng, sai **trung bình 52 s, lớn nhất 85 s**. Hậu quả: chuỗi lệnh lăn vào bến khởi động khi tàu chưa tới điểm chờ, và lệnh `MOVE` đầu tiên **kéo tàu đi 11.669 m trong 1 giây**. Khắc phục: script `_calib_vvdn_xenke.py` chạy mô phỏng thật, đo mốc chạm càng thực tế, bù vào **mốc qua CADAS** (không bù vào thời điểm tạo tàu — chuyến đầu phải sinh tại T=0 nên giá trị âm bị kẹp về 0 và hiệu chuẩn không có tác dụng). Sau 3 vòng: sai lệch lớn nhất còn **0,5 s**.

**3. Khoảng trống giữa hai lệnh `MOVE`** — file tuyến lăn gốc của kịch bản 40 chuyến có chỗ giãn tới 3,5 s và lệnh áp chót vẫn đặt 5 kt; trong khoảng trống đó BlueSky cho tàu bay tự do, đo được **vọt 674 m (hiển thị 1019 kt)**. Khắc phục: lấy **hình tuyến** từ file gốc nhưng **phát lại theo nhịp đều 2 giây**, lệnh cuối đặt 0 kt rồi ghim thêm 30 giây tại bến.

**4. Tốc độ lăn lên đường CHC quá nhỏ** — quãng đường lên 35R (~130 m) bị trải ra suốt thời gian chờ (240 s) → tốc độ `MOVE` tụt xuống **1,7 kt**, BlueSky không giữ nổi tàu ở tốc độ đó, đo được **dao động qua lại 294 m mỗi giây (577 kt)**. Khắc phục: lăn lên đường CHC ở đúng tốc độ lăn khi rẽ (10 kt) rồi **ghim đứng tại chỗ** đến lúc chạy đà — giống điều hành thật.

Ngoài ra, **hai "vi phạm" ban đầu là lỗi tiêu chí kiểm tra, không phải lỗi kịch bản**, đã sửa tiêu chí và ghi diễn giải vào file quy tắc:
- Tính cả tàu **đã chạm càng** (cao độ 0 < 3000 ft) là "tàu đang tiếp cận" → báo sai **49 cặp** xung đột.
- Đo "trôi" bằng `gs` tức thời của BlueSky: tại đúng bước có lệnh `MOVE`, quãng đường `MOVE` dịch tàu bị quy ra tốc độ của **một bước 0,05 s** → cho trị số vô nghĩa (1021 kt trong khi dịch chuyển thật chỉ 6,2 m/s).

---

## VI. BẢNG LỊCH KỊCH BẢN

Thời gian tính từ đầu kịch bản. Đ = chuyến đến (chạm càng 35L), I = chuyến đi (bắt đầu chạy đà 35R).

| Thời điểm | Loại | Số hiệu | Tàu bay | NĐX | SID/STAR | Đường lăn / bến | Giãn cách |
|---|---|---|---|---|---|---|---|
| 08:50,0 | Đ | ARR001 | A320 | M | VILOT | G4 → bến 28 | — |
| 09:20,0 | I | DEP001 | B38M | M | PHULU | bến 27 | +30 s |
| 12:50,0 | Đ | ARR002 | B739 | M | CAHEO | G6 → bến 8 | +210 s |
| 13:20,0 | I | DEP002 | B78X | H | KUMUN | bến 27 | +30 s |
| 16:50,0 | Đ | ARR003 | A21N | M | PAPRA | G4 → bến 28 | +210 s |
| 17:20,0 | I | DEP003 | B738 | M | KUMUN | bến 27 | +30 s |
| 20:50,0 | Đ | ARR004 | B738 | M | HUE | G4 → bến 28 | +210 s |
| 21:20,0 | I | DEP004 | B773 | H | KONCO | bến 26 | +30 s |
| 23:50,0 | Đ | ARR005 | B744 | H | PAPRA | G6 → bến 8 | +150 s |
| 24:20,0 | I | DEP005 | A320 | M | VIDEN | bến 26 | +30 s |
| 26:50,0 | Đ | ARR006 | B773 | H | BUNTA | G6 → bến 8 | +150 s |
| 27:20,0 | I | DEP006 | A320 | M | KUMUN | bến 27 | +30 s |
| 29:50,0 | Đ | ARR007 | B38M | M | VILOT | G4 → bến 28 | +150 s |
| 30:20,0 | I | DEP007 | B748 | H | VIDEN | bến 27 | +30 s |
| 32:57,5 | Đ | ARR008 | B38M | M | VILOT | G6 → bến 8 | +158 s |
| 33:27,5 | I | DEP008 | B738 | M | KUMUN | bến 26 | +30 s |
| 35:57,5 | Đ | ARR009 | B789 | H | LATOM | G6 → bến 8 | +150 s |
| 36:27,5 | I | DEP009 | A333 | H | PAPRA | bến 26 | +30 s |
| 38:57,5 | Đ | ARR010 | B788 | H | BUNTA | G4 → bến 28 | +150 s |
| 39:27,5 | I | DEP010 | B739 | M | PAPRA | bến 26 | +30 s |
| 41:57,5 | Đ | ARR011 | A21N | M | LATOM | G6 → bến 8 | +150 s |
| 42:27,5 | I | DEP011 | B38M | M | PAPRA | bến 27 | +30 s |
| 44:23,6 | Đ | ARR012 | B739 | M | CAHEO | G6 → bến 8 | +116 s |
| 44:53,6 | I | DEP012 | A21N | M | KONCO | bến 26 | +30 s |
| 46:47,6 | Đ | ARR013 | B77W | H | KUMUN | G6 → bến 8 | +114 s |
| 47:17,6 | I | DEP013 | B788 | H | KONCO | bến 27 | +30 s |
| 50:05,6 | Đ | ARR014 | A320 | M | PAPRA | G6 → bến 8 | +168 s |
| 50:35,6 | I | DEP014 | A320 | M | KONCO | bến 27 | +30 s |
| 52:29,6 | Đ | ARR015 | B38M | M | LATOM | G6 → bến 8 | +114 s |
| 52:59,6 | I | DEP015 | A20N | M | VIDEN | bến 27 | +30 s |
| 54:55,8 | Đ | ARR016 | A321 | M | SADIN | G6 → bến 8 | +116 s |
| 55:25,8 | I | DEP016 | A320 | M | BUNTA | bến 26 | +30 s |
| 57:25,8 | Đ | ARR017 | A320 | M | SADIN | G6 → bến 8 | +120 s |
| 57:55,8 | I | DEP017 | B738 | M | VIDEN | bến 27 | +30 s |

### Thông lượng theo pha

| Pha | Khoảng | Mục tiêu | Đạt được |
|---|---|---|---|
| 1 | 0–20 phút | 30/h | 3 đến + 3 đi = **18/h** |
| 2 | 20–40 phút | 40/h | 7 đến + 7 đi = **42/h** |
| 3 | 40–60 phút | 50/h | 7 đến + 7 đi = **42/h** |

Pha 1 thấp vì ràng buộc vật lý nêu ở mục 2.2.5 (chuyến đến đầu tiên không thể chạm càng trước phút 8:30). Pha 3 không đạt mục tiêu 50/h vì **đã chạm trần năng lực**.

---

## VII. SỐ LIỆU LĂN VÀ ĐIỂM CHỜ

| Chỉ tiêu | Giá trị |
|---|---|
| Thời gian lăn ra (bến 26/27 → điểm chờ 35R) | TB **335 s**, dao động 333–337 s |
| Thời gian chờ tại điểm chờ trước 35R | TB **175 s**, lớn nhất **240 s** |
| Thời gian giải phóng đường CHC (chạm càng → thoát ly) | TB **96 s**, lớn nhất **109 s** |
| Thời gian lăn vào bến (đường lăn thoát ly → bến) | TB **235 s** |
| Số tàu tại điểm chờ lớn nhất | **2** (giới hạn đề bài: 3) |
| Độ lệch tim đường lăn | TB **1,8 m**, lớn nhất 2,3 m |

**Nhận xét:** thời gian giải phóng đường CHC trung bình 96 s, lớn nhất 109 s — **vượt mốc tham chiếu 100 s** nêu trong đề bài ở một số chuyến. Nguyên nhân: chuỗi thoát ly lấy từ kịch bản 40 chuyến giảm tốc tương đối chậm. Không ảnh hưởng tới kết luận năng lực (yếu tố khống chế là ma trận cất cánh vs tàu đến, không phải thời gian chiếm dụng đường CHC), nhưng nên rà lại nếu dùng cho bài toán chiếm dụng đường CHC.

Số tàu tại điểm chờ chỉ đạt lớn nhất 2/3 vì nhịp cất cánh bị khống chế bởi nhịp hạ cánh — không có đủ chuyến đi để xếp hàng 3 tàu. Muốn đạt 2–3 tàu thường xuyên như mục tiêu đề bài thì phải có **nhu cầu cất cánh vượt nhịp xen kẽ**, tức kịch bản ưu tiên cất cánh theo đợt thay vì xen kẽ tuyệt đối.

---

## VIII. SẢN PHẨM BÀN GIAO

| File | Nội dung |
|---|---|
| `VVDN-XENKE-60MIN.scn` | **Kịch bản mô phỏng** — 7.110 lệnh, phần đầu ghi seed, tham số, giả định, đơn giản hoá |
| `_gen_vvdn_xenke_60min.py` | **Generator** có seed cố định, tái lập 100 % |
| `vvdn_xenke_rules.json` | **Cấu hình quy tắc phân cách và tham số lăn**, mỗi nhóm ghi điều khoản nguồn, 2 nhóm đánh dấu `can_xac_nhan: true` |
| `_verify_vvdn_xenke.py` | **Script kiểm chứng độc lập** — 20 mục, tự tính lại từ file quy tắc, chạy mô phỏng headless thật |
| `_calib_vvdn_xenke.py` | Script hiệu chuẩn thời điểm tạo tàu đến |
| `_sweep_vvdn_xenke.py` | Script quét năng lực |
| `VVDN-XENKE-60MIN.plan.json` | Lịch chi tiết (đầu vào của script kiểm chứng) |
| `VVDN-XENKE-60MIN.calib.json` | Bảng hiệu chuẩn |
| `VVDN-XENKE-60MIN.sweep.json` | Kết quả quét năng lực |
| `_ARR_RESUME_G6_GATE8.scn` | Tuyến lăn G6 → bến 8 (dựng mới từ tim đường lăn thật) |
| `BaoCao_KiemChung_VVDN_XenKe.md` | Báo cáo này |

### Cách chạy lại

```bash
cd "FTS Server/scenario"
python _gen_vvdn_xenke_60min.py     # sinh kịch bản
python _calib_vvdn_xenke.py         # hiệu chuẩn (chỉ cần khi đổi tham số lập lịch)
python _verify_vvdn_xenke.py        # kiểm chứng đầy đủ (có chạy mô phỏng)
python _verify_vvdn_xenke.py --static   # chỉ kiểm tra trên lịch, chạy trong vài giây
python _sweep_vvdn_xenke.py         # quét năng lực
```

---

## IX. KIẾN NGHỊ

1. **Xác nhận hai ma trận phân cách** nêu ở mục 2.3 trước khi dùng con số 46,8 lần chuyến/giờ vào công tác chuyên môn.
2. **Rà lại thời gian giải phóng đường CHC** (hiện TB 96 s, lớn nhất 109 s) nếu cần dùng cho bài toán chiếm dụng đường CHC.
3. **Xây dựng thêm kịch bản ưu tiên cất cánh theo đợt** để đánh giá tình huống điểm chờ đạt 3 tàu — cấu hình xen kẽ tuyệt đối không tạo ra tình huống đó.
4. **Bổ sung kịch bản có cắt qua đường CHC 35R** (tàu về bến phía đông) để kiểm chứng điều kiện 6 NM đã cấu hình nhưng chưa có dịp kích hoạt.
