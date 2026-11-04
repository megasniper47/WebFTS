# BÁO CÁO KIỂM CHỨNG KỊCH BẢN CẤT/HẠ CÁNH XEN KẼ — CẢNG HKQT ĐÀ NẴNG (VVDN)

**Cấu hình khai thác:** hướng 35, hai đường CHC song song (cách nhau 214 m) khai thác **phụ thuộc** — 35L hạ cánh (ILS), 35R cất cánh, cất/hạ cánh **xen kẽ**
**Thời lượng:** pha khởi động 0:00–0:28:38 (tàu đến bay STAR từ IAF, tàu đi lăn ra) + **cửa sổ đo 60 phút** 0:28:38–1:28:38 · **Seed:** 20261102 (tái lập 100 %, đã kiểm tra sinh lại giống từng byte) · **Mô hình hiệu năng:** BADA 3.16
**Phân cách áp dụng:** dự thảo *Phương thức khai thác 2 đường CHC song song Đà Nẵng* (24.7.2026), dự thảo *MANOP APP/TWR Đà Nẵng* (011026_Du-thao-Manop-DN-PB03), ICAO Doc 4444 và prompt *"kịch bản cất cánh xen kẽ (Linh)"*
**Ngày lập:** 04/11/2026 — thay toàn bộ các bản trước cùng ngày

---

## I. KẾT LUẬN CHÍNH

| Nội dung | Kết quả |
|---|---|
| **Năng lực khai thác tối đa mà mọi phân cách vẫn đạt và điểm chờ ≤ 3** | **18 đến + 18 đi = 36 lần chuyến/giờ**, xen kẽ tuyệt đối (Đ-I-Đ-I…) |
| Nhịp hạ cánh | TB **199 s**, nhỏ nhất **180 s** |
| Kiểm chứng | **30 mục, 0 mục KHÔNG ĐẠT** (14 mục trên lịch + 16 mục đo trong mô phỏng) |
| Vi phạm phân cách trên không / mặt đất · cảnh báo xung đột | **0 / 0 · 0** |
| Số tàu tại điểm chờ lớn nhất | **2** (đo trong mô phỏng; ổn định 2 tàu suốt cửa sổ đo, giới hạn 3) |
| **Mật độ bắt đầu vi phạm** | Dày hơn lịch hiện tại **bất kỳ mức nào**: nén lịch 2 % (≈ 37,8 lần chuyến/giờ) đã phát sinh **16 vi phạm** (mục VI) |
| **Nút cổ chai** | (1) **giãn cách hạ cánh liên tiếp 8 NM** của MANOP — mọi cặp đến–đến; (2) **cất cánh so với tàu đến** khi chuyến đi là **HEAVY** (6–7 NM). Ngay sau đó: tàu trước phải **cắt qua hết 35R trước khi tàu sau tới 2 NM** |

**Một chu kỳ đến–đi** (≈ 180–190 s): chạm càng → **30 s** → chuyến đi chạy đà → chuyến đến kế tiếp phải còn ≥ 5–7 NM (bảng mục 4.2.1) **và** cách chuyến đến trước ≥ 8 NM (MANOP). Với tốc độ 5 NM trung bình 155–157 kt, 8 NM ≈ **183–186 s** — chính là nhịp hạ cánh đo được.

> **Lưu ý khi diễn giải:** kết luận "không vi phạm" là hệ quả của thiết kế thuật toán (đặt mỗi mốc sớm nhất mà vẫn đủ mọi phân cách), không phải khẳng định khai thác thực tế sẽ không có vi phạm. Con số 36 lần chuyến/giờ là **trần năng lực** khi mọi phân cách được giữ đúng mức tối thiểu.

---

## II. GIẢ ĐỊNH VÀ ĐƠN GIẢN HOÁ

### 2.1 Giả định cố định (theo prompt)
| Hạng mục | Giá trị |
|---|---|
| Thời tiết / giờ | Tốt, CHC khô, 07h00–17h00; không gió ⇒ tốc độ mặt đất = tốc độ thật |
| Bay lại / huỷ cất cánh | **Không** mô phỏng |
| Tàu đến | Bay STAR RNAV từ **IAF** tới DOTEN, tiếp cận ILS 35L, thoát ly G4 hoặc G6 (50/50 theo seed), **cắt qua 35R**, lăn về bến 28 (từ G4) hoặc bến 8 (từ G6), tới bến thì biến mất |
| Tàu đi | Xuất phát bến 26/27, lăn đường lăn E ra điểm chờ đầu 35R, bay SID; biến mất 420 s sau khi chạy đà |
| Cơ cấu đội tàu | 70 % MEDIUM / 30 % HEAVY, **hạn ngạch chính xác** rồi xáo trộn bằng seed (18 chuyến ⇒ 13 M + 5 H mỗi chiều); bảo đảm đủ cặp kế tiếp H-H, H-M, M-H, M-M ở cả chiều đến và chiều đi |

### 2.2 Đơn giản hoá có chủ đích
1. **Pha khởi động 28 phút 38 giây**: để **mọi** chuyến đến được tạo tại IAF của STAR (mục 5 prompt), mốc chạm bánh đầu tiên được lùi tới 0:28:38. Thông lượng chỉ tính trong cửa sổ 60 phút sau đó.
2. **Pha lăn điều khiển bằng `MOVE`** theo nhịp đều 2 s, không dùng LNAV/VNAV, để kiểm soát chính xác thời điểm tới/rời điểm chờ.
3. **Điểm chờ E có hai vị trí** (PREHOLD + vị trí thứ hai phía sau, cách tâm tàu trước nửa chiều dài hai tàu + 20 m) cộng tàu đã lên đường CHC = tối đa 3 tàu. Trong lịch này không chuyến nào phải dùng vị trí thứ hai: nhịp cất cánh ~199 s đủ để mỗi tàu tới đúng lúc tàu trước chạy đà.
4. **Tránh nhau khi lăn giải bằng lập lịch** (quy tắc ưu tiên của plugin `surfacetaxi.py`: tàu còn quãng đường tới đích ngắn hơn đi trước). Không mô phỏng phanh/dừng nhường đường bất ngờ.
5. **Khi không có giờ lăn ra hợp lệ, lùi giờ cất cánh 15 s một lần** rồi lập lại lịch (DEP008 +45 s, DEP013 +45 s). DEP016 lùi thêm 188 s để **bỏ trống một khe cất cánh** cho DEP017 (B748, code F) lăn trên đường lăn E (mục 3.3).

---

## III. QUY TẮC PHÂN CÁCH VÀ KHAI THÁC ÁP DỤNG

### 3.1 Trên đường CHC và trên không
| Quy tắc | Giá trị | Nguồn |
|---|---|---|
| Cấp huấn lệnh cất cánh 35R | Chỉ sau khi tàu hạ cánh **chạm càng chính** trên 35L; kịch bản chạy đà **30 s** sau chạm càng, huấn lệnh trước đó ≤ 10 s (code C) / 15 s (code D+) | Dự thảo = MANOP Phụ lục mục 4.2.1.a; prompt 3c, 3e |
| Tàu đến kế tiếp khi cấp huấn lệnh cất cánh (có giám sát ATS) | Hàng = cất cánh, cột = hạ cánh: **M/M 5 · M/H 5 · H/H 6 · H/M 7 NM** (SUPER/LIGHT theo bảng đầy đủ) | Dự thảo = MANOP Phụ lục mục 4.2.1; prompt 3d |
| Hạ cánh liên tiếp — nhiễu động | H sau H **4** · M sau H **5** · M sau M **3** · H sau M **3 NM**; tối thiểu **3 NM** | MANOP, Phân cách giám sát ATS (= ICAO Doc 4444 8.7.3.4); prompt mục 4 |
| Giãn cách hạ cánh liên tiếp | **8 NM** khi tàu trước chạm bánh, *gia tăng thích hợp khi có tàu cất cánh xen giữa* | MANOP, quy trình KSVKL APP — **CẦN XÁC NHẬN** |
| Giải phóng 35L trước huấn lệnh hạ cánh | Tàu trước **cắt qua hết 35R** trước khi tàu sau tới **2 NM** | MANOP (huấn lệnh hạ cánh trước 2 NM; tàu chờ giữa hai CHC ⇒ không dùng 35L); prompt 3b, mục 4 |
| Cất cánh liên tiếp 35R | M sau H **120 s** (MANOP, ICAO 5.8); ô khác 60–120 s và theo SID là giá trị đệm của prompt | Không ràng buộc trong lịch xen kẽ |
| Cảnh báo xung đột | Tàu đi > 400 ft và tàu đến < 3000 ft trên final, ngang < 3 NM | Prompt 3i |

### 3.2 Trên mặt đất
| Quy tắc | Áp dụng | Nguồn |
|---|---|---|
| Cắt qua 35R | Dừng chờ trước vạch 35R (giữa hai CHC); chỉ cắt khi tàu cất cánh đã qua điểm cắt; xong trong **≤ 45 s** (lăn 15 kt) | MANOP Phụ lục; prompt 3f, 3g |
| Thoát ly 35L | ≤ **100 s** từ ngưỡng tới vị trí dừng chờ | MANOP Phụ lục; prompt 3f |
| Đường lăn E (cách tim 35R 148 m) | Tàu code D/E/F cất cánh ⇒ chỉ tàu code C trên E; tàu code C cất cánh ⇒ tàu code ≤ E trên E | MANOP Phụ lục mục 3 |
| Điểm chờ trước 35R | ≤ **3 tàu** (kể cả tàu đã lên đường CHC); xếp hàng cách nửa chiều dài hai tàu + 20 m | Prompt mục 6 |
| Lên đường CHC | Khi tàu đi trước bắt đầu chạy đà | Prompt 3e |

Vạch dừng chờ đo từ `taxiway_centerlines.geojson`: 35R ở **−91 m / +94 m** so với tim 35R, 35L ở **−122 m**.

### 3.3 Các mục **CẦN XÁC NHẬN**
1. **8 NM là tối thiểu bắt buộc hay chỉ là hướng dẫn** — MANOP viết *"có thể là 8NM"*. Đây là một trong hai nút cổ chai; tuy vậy nếu bỏ đi, giới hạn kế tiếp (giải phóng 35L trước 2 NM) chỉ cho nén thêm 2–5 % (mục VI).
2. **Phạm vi "đường lăn E"** — kịch bản không tính tàu đứng tại khu điểm chờ (trong vòng 100 m quanh PREHOLD, gồm cả vị trí xếp hàng thứ hai) là "đang dùng đường lăn E" (theo lựa chọn của người dùng).
3. **Tàu code F (B748)** — MANOP chỉ nói code C/D/E; kịch bản áp cách hiểu chặt (không lên E khi có bất kỳ tàu nào cất cánh), làm mất một khe cất cánh trước DEP017.
4. **Cả hai văn bản nguồn đều là dự thảo**.
5. **Không dùng `compliance_rulesets/VVDN.json`**: file này đọc bảng *cất cánh – hạ cánh* của mục 4.2.1 thành ma trận *hạ cánh liên tiếp*, và đưa vào mức 8 NM tại điểm chờ E không có trong dự thảo/MANOP. Kiến nghị người quản lý file rà lại.

---

## IV. MA TRẬN GIÃN CÁCH TỐI THIỂU

Giây tại ngưỡng quy đổi bằng tốc độ 5 NM trung bình của loại tàu sau (BADA: MEDIUM **155 kt**, HEAVY **157 kt**). Ký hiệu cặp: *trước–sau*.

### 4.1 Yêu cầu
| Loại cặp | H-H | H-M | M-H | M-M | Ghi chú |
|---|---|---|---|---|---|
| **Đến–Đến** (nhiễu động) | 4 NM | 5 NM | 3 NM | 3 NM | MANOP = ICAO |
| **Đến–Đến** (áp dụng = max với 8 NM) | **8 NM · 183 s** | **8 NM · 186 s** | **8 NM · 183 s** | **8 NM · 186 s** | 8 NM khống chế mọi cặp |
| **Đi–Đến** (chạy đà → tàu đến kế tiếp) | **6 NM · 138 s** | **7 NM · 163 s** | **5 NM · 115 s** | **5 NM · 116 s** | cặp = loại tàu đi – loại tàu đến |
| **Đến–Đi** (chạm càng → chạy đà) | 30 s | 30 s | 30 s | 30 s | tối thiểu theo văn bản: huấn lệnh sau chạm càng |
| **Đi–Đi** (chạy đà → chạy đà) | 120 s | 120 s | 60 s | 60 s | chỉ H-M 120 s có nguồn MANOP |

Chu kỳ tối thiểu Đến–Đi–Đến = max(8 NM; 30 s + Đi–Đến): ví dụ chuyến đi HEAVY, chuyến đến kế tiếp MEDIUM: 30 + 163 = **193 s** > 186 s ⇒ cặp này đẩy nhịp lên trên 8 NM.

### 4.2 Thực đo trong mô phỏng — cự ly tàu sau tới tàu trước (NM), Đến–Đến
| Cặp | Lúc tàu trước qua DOTEN | 10 NM | 5 NM | 2 NM | Ngưỡng (nhỏ nhất / TB) |
|---|---|---|---|---|---|
| H-H (2 cặp) | — | 9,98 | 9,21 | 8,63 | **8,41** / 12,56 |
| H-M (3 cặp) | 24,28 | 10,02 | 9,23 | 8,64 | **8,61** / 8,68 |
| M-H (3 cặp) | 16,46 | 10,52 | 9,41 | 8,71 | **8,40** / 8,89 |
| M-M (9 cặp) | 15,95 | 9,47 | 8,90 | 8,51 | **8,34** / 8,57 |

Cột DOTEN chỉ có số liệu khi tàu sau đã xuất hiện trong mô phỏng lúc tàu trước qua DOTEN. Cự ly giảm dần về ngưỡng vì tàu trước giảm tốc trước; nhỏ nhất **8,34 NM ≥ 8 NM** tại ngưỡng.

---

## V. KẾT QUẢ KIỂM CHỨNG

Script `_verify_vvdn_xenke.py` **không dùng lại** hàm của generator: tự đọc file quy tắc, file lịch, các file `.geojson` sơ đồ sân bay và chú thích trong `.scn`, rồi tự tính lại.

### Phần A — trên lịch
| # | Nội dung | Kết quả | Số liệu |
|---|---|---|---|
| A1 | Cơ cấu đội tàu (đến / đi) | ✅ | 13 M + 5 H mỗi chiều, đúng hạn ngạch |
| A1b | Đủ cặp kế tiếp (đến / đi) | ✅ | Đến: H-H 2, H-M 3, M-H 3, M-M 9 · Đi: H-H 1, H-M 3, M-H 4, M-M 9 |
| A2 | Hạ cánh liên tiếp 35L | ✅ | 17 cặp, 0 không đạt |
| A3 | Cất cánh liên tiếp 35R | ✅ | 17 cặp, 0 không đạt |
| A4 | Cất cánh vs tàu đến kế tiếp (4.2.1) | ✅ | 18 chuyến, 0 không đạt |
| A5 | Huấn lệnh cất cánh sau chạm càng | ✅ | 18 chuyến |
| A6 | Số tàu tại điểm chờ | ✅ | lớn nhất 2 (giới hạn 3) |
| A7 | Lên đường CHC sau khi tàu trước chạy đà | ✅ | 17 cặp |
| A8 | Xen kẽ | ✅ | chuỗi cùng loại dài nhất **1** |
| A9 | Thông lượng cửa sổ 60 phút | 📊 | **18 đến + 18 đi = 36 lần chuyến/giờ**; nhịp đến TB 199 s, nhỏ nhất 180 s |
| A10 | Mọi chuyến đi bắt đầu lăn trong kịch bản | ✅ | sớm nhất 0:22:35,8 |
| A11 | Mọi chuyến đến tạo tại IAF | ✅ | **18/18** |

### Phần B — đo trong mô phỏng headless thật (BADA 3.16)
| # | Nội dung | Kết quả | Số liệu |
|---|---|---|---|
| B1 | Mọi chuyến đến chạm càng | ✅ | 18/18 |
| B2 | Sai lệch chạm càng so với lịch | 📊 | TB **0,2 s**, lớn nhất **0,9 s** |
| B3 | Cự ly thật hai tàu hạ cánh liên tiếp | ✅ | nhỏ nhất **8,53 NM** (yêu cầu 8 NM) |
| B4 | Cảnh báo xung đột trên không | ✅ | 0 cặp |
| B5 | Bám tim đường lăn | ✅ | 36 tàu, lệch TB 1,6 m |
| B6 | Không có tàu "trôi" khi lăn | ✅ | tốc độ lăn lớn nhất 21,9 kt |
| B7 | Tàu đến về tới bến | ✅ | 18/18 |
| B8 | Cự ly hai tàu đang lăn | ✅ | 0 vi phạm; sát nhất ARR016 ↔ DEP018 **92 m** (yêu cầu 80 m) |
| B9 | Lên CHC và chạy đà đúng tim 35R | ✅ | lệch 0,0–0,1 m |
| B10 | Cất cánh vs tàu đến kế tiếp — đo thật | ✅ | dư nhỏ nhất **+0,26 NM** |
| B11a | Cắt qua 35R ≤ 45 s | ✅ | lâu nhất **34 s** |
| B11b | Không cắt qua khi tàu cất cánh chưa qua điểm cắt | ✅ | 0 xung đột; dừng chờ giữa hai CHC lâu nhất 54 s |
| B11c | Tàu trước cắt qua hết 35R trước khi tàu sau tới 2 NM | ✅ | 17 cặp, 0 không đạt |
| B12 | Đường lăn E khi tàu code D/E/F cất cánh | ✅ | 18 lần cất cánh, 0 vi phạm |
| B13 | Thoát ly 35L ≤ 100 s | ✅ | lâu nhất **94 s** |
| B14 | Số tàu tại điểm chờ — đo thật | ✅ | lớn nhất **2**; mọi khoảng 5 phút trong cửa sổ đo đều là 2 |

**Tổng: 30 mục, 0 mục KHÔNG ĐẠT** (28 ĐẠT + 2 mục số liệu A9, B2).

---

## VI. MẬT ĐỘ BẮT ĐẦU VI PHẠM VÀ NÚT CỔ CHAI

Kịch bản chạy một pha sát phân cách tối thiểu. Để trả lời "mật độ nào bắt đầu vi phạm", script `_phan_tich_mat_do_vvdn_xenke.py` (độc lập với generator) **nén** mọi khoảng cách giữa các mốc chạm bánh/chạy đà theo hệ số *f* < 1 và đếm vi phạm theo quy tắc và loại cặp. Các khoảng thời gian mặt đất (chạm bánh → cắt qua xong 35R, phản ứng chạy đà 10/15 s) giữ nguyên. Chỉ xét quy tắc trên đường CHC/trên không, **không chạy lại mô phỏng** cho các lịch đã nén.

### 6.1 Hệ số nén tới hạn (vi phạm khi f < f*)
| f* | Quy tắc | Cặp |
|---|---|---|
| **1,000** | Giãn cách hạ cánh 8 NM (MANOP) | H-H, H-M, M-H, M-M |
| **1,000** | Cất cánh vs tàu đến (4.2.1) | I**H**-ĐH, I**H**-ĐM, IM-ĐH |
| 0,977 / 0,964 / 0,950 / 0,949 | Giải phóng 35L trước 2 NM | M-M / M-H / H-M / H-H |
| 0,823 | Cất cánh vs tàu đến (4.2.1) | IM-ĐM |
| 0,727 | Nhiễu động cất cánh 2 phút | H-M |
| 0,625 | Nhiễu động hạ cánh | H-M |

### 6.2 Kết quả theo mật độ
| f | ≈ Lần chuyến/giờ | Số vi phạm | Quy tắc vi phạm |
|---|---|---|---|
| **1,00** | **37,0** (tính theo nhịp) | **0** | — |
| 0,98 | 37,8 | 16 | 8 NM (11 cặp), cất cánh vs tàu đến khi chuyến đi HEAVY (5) |
| 0,96 | 38,5 | 23 | + giải phóng 35L trước 2 NM (4) |
| 0,90 | 41,1 | 30 | |
| 0,80 | 46,2 | 38 | + cất cánh vs tàu đến M/M |

*(37,0 lần chuyến/giờ ở dòng f = 1,00 tính theo nhịp từ mốc đầu tới mốc cuối; trong cửa sổ 60 phút thực tế đếm được 36.)*

**Kết luận:** năng lực tối đa **≈ 36 lần chuyến/giờ**; vi phạm phát sinh **ngay khi** lịch dày hơn. Nút cổ chai là **giãn cách 8 NM** (mọi cặp, nhiều nhất cặp **M-M** vì phổ biến nhất) và **cất cánh vs tàu đến khi chuyến đi là HEAVY** (6–7 NM). Nếu 8 NM chỉ là hướng dẫn (mục 3.3), giới hạn kế tiếp là **giải phóng 35L trước 2 NM** — tàu đến phải thoát ly và cắt qua hết 35R — chỉ cho nén thêm khoảng 2–5 %.

---

## VII. BẢNG LỊCH KỊCH BẢN

Đ = chuyến đến (chạm càng 35L), I = chuyến đi (bắt đầu chạy đà 35R). NĐX/Mã = nhóm nhiễu động / mã chữ sân bay.

| Thời điểm | Loại | Số hiệu | Tàu bay | NĐX/Mã | SID/STAR | Đường lăn / bến | Giãn cách |
|---|---|---|---|---|---|---|---|
| 0:28:38,3 | Đ | ARR001 | A21N | M/C | VILOT | G4 → bến 28 | — |
| 0:29:08,3 | I | DEP001 | A321 | M/C | PAPRA | bến 27 | +30 s |
| 0:31:44,1 | Đ | ARR002 | A21N | M/C | LATOM | G6 → bến 8 | +156 s |
| 0:32:14,1 | I | DEP002 | B38M | M/C | PAPRA | bến 26 | +30 s |
| 0:34:44,1 | Đ | ARR003 | B38M | M/C | BUNTA | G6 → bến 8 | +150 s |
| 0:35:14,1 | I | DEP003 | B38M | M/C | PAPRA | bến 27 | +30 s |
| 0:37:44,1 | Đ | ARR004 | B38M | M/C | LATOM | G6 → bến 8 | +150 s |
| 0:38:14,1 | I | DEP004 | B38M | M/C | KONCO | bến 27 | +30 s |
| 0:40:56,1 | Đ | ARR005 | A320 | M/C | CAHEO | G6 → bến 8 | +162 s |
| 0:41:26,1 | I | DEP005 | A20N | M/C | KONCO | bến 27 | +30 s |
| 0:43:56,1 | Đ | ARR006 | B77W | H/E | KUMUN | G6 → bến 8 | +150 s |
| 0:44:26,1 | I | DEP006 | B739 | M/C | KONCO | bến 26 | +30 s |
| 0:47:01,9 | Đ | ARR007 | B789 | H/E | PAPRA | G6 → bến 8 | +156 s |
| 0:47:31,9 | I | DEP007 | B789 | H/E | VIDEN | bến 27 | +30 s |
| 0:50:19,9 | Đ | ARR008 | A320 | M/C | LATOM | G6 → bến 8 | +168 s |
| 0:51:34,9 | I | DEP008 | B738 | M/C | BUNTA | bến 27 | +75 s |
| 0:53:56,0 | Đ | ARR009 | B738 | M/C | SADIN | G6 → bến 8 | +141 s |
| 0:54:26,0 | I | DEP009 | B739 | M/C | VIDEN | bến 26 | +30 s |
| 0:57:01,8 | Đ | ARR010 | B739 | M/C | SADIN | G6 → bến 8 | +156 s |
| 0:57:31,8 | I | DEP010 | B788 | H/E | VIDEN | bến 26 | +30 s |
| 1:00:19,8 | Đ | ARR011 | A320 | M/C | HUE | G6 → bến 8 | +168 s |
| 1:00:49,8 | I | DEP011 | B738 | M/C | SADIN | bến 26 | +30 s |
| 1:03:19,8 | Đ | ARR012 | B38M | M/C | SADIN | G4 → bến 28 | +150 s |
| 1:03:49,8 | I | DEP012 | B738 | M/C | VIDEN | bến 26 | +30 s |
| 1:06:25,6 | Đ | ARR013 | A321 | M/C | SADIN | G4 → bến 28 | +156 s |
| 1:07:40,6 | I | DEP013 | B763 | H/D | VIDEN | bến 26 | +75 s |
| 1:09:55,6 | Đ | ARR014 | B744 | H/E | CAHEO | G6 → bến 8 | +135 s |
| 1:10:25,6 | I | DEP014 | A320 | M/C | PAPRA | bến 27 | +30 s |
| 1:13:01,4 | Đ | ARR015 | B739 | M/C | BUNTA | G6 → bến 8 | +156 s |
| 1:13:31,4 | I | DEP015 | A21N | M/C | XAQUA | bến 27 | +30 s |
| 1:16:07,2 | Đ | ARR016 | B788 | H/E | SADIN | G4 → bến 28 | +156 s |
| 1:19:45,2 | I | DEP016 | A320 | M/C | PHULU | bến 27 | +218 s |
| 1:21:41,3 | Đ | ARR017 | B773 | H/E | BUNTA | G4 → bến 28 | +116 s |
| 1:22:11,3 | I | DEP017 | B748 | H/F | SADIN | bến 27 | +30 s |
| 1:24:53,9 | Đ | ARR018 | A321 | M/C | SADIN | G4 → bến 28 | +163 s |
| 1:25:23,9 | I | DEP018 | A333 | H/E | SADIN | bến 27 | +30 s |

---

## VIII. LỊCH LĂN RA VÀ ĐIỂM CHỜ

Thời gian lăn tính từ chiều dài tuyến lăn thật (bến 26/27 → điểm chờ E) và tốc độ lăn 15 kt đoạn thẳng / 10 kt khi rẽ. "Chờ" = từ lúc vào khu điểm chờ tới lúc chạy đà (gồm cả lúc đã lên đường CHC).

| Chuyến | Tàu | Bến | Bắt đầu lăn | Thời gian lăn | Tới điểm chờ | Vị trí 2 | Lên CHC | Chạy đà | Chờ |
|---|---|---|---|---|---|---|---|---|---|
| DEP001 | A321 | bến 27 | 0:22:35,8 | 333 s | 0:28:08,3 | — | 0:28:08,3 | 0:29:08,3 | 60 s |
| DEP002 | B38M | bến 26 | 0:23:30,8 | 337 s | 0:29:08,3 | — | 0:29:08,3 | 0:32:14,1 | 186 s |
| DEP003 | B38M | bến 27 | 0:26:41,6 | 333 s | 0:32:14,1 | — | 0:32:14,1 | 0:35:14,1 | 180 s |
| DEP004 | B38M | bến 27 | 0:29:21,6 | 333 s | 0:34:54,1 | — | 0:35:14,1 | 0:38:14,1 | 200 s |
| DEP005 | A20N | bến 27 | 0:32:46,6 | 333 s | 0:38:19,1 | — | 0:38:19,1 | 0:41:26,1 | 187 s |
| DEP006 | B739 | bến 26 | 0:35:48,6 | 337 s | 0:41:26,1 | — | 0:41:26,1 | 0:44:26,1 | 180 s |
| DEP007 | B789 | bến 27 | 0:38:53,6 | 333 s | 0:44:26,1 | — | 0:44:26,1 | 0:47:31,9 | 186 s |
| DEP008 | B738 | bến 27 | 0:41:59,4 | 333 s | 0:47:31,9 | — | 0:47:31,9 | 0:51:34,9 | 243 s |
| DEP009 | B739 | bến 26 | 0:45:57,4 | 337 s | 0:51:34,9 | — | 0:51:34,9 | 0:54:26,0 | 171 s |
| DEP010 | B788 | bến 26 | 0:48:48,6 | 337 s | 0:54:26,0 | — | 0:54:26,0 | 0:57:31,8 | 186 s |
| DEP011 | B738 | bến 26 | 0:51:54,4 | 337 s | 0:57:31,8 | — | 0:57:31,8 | 1:00:49,8 | 198 s |
| DEP012 | B738 | bến 26 | 0:55:12,4 | 337 s | 1:00:49,8 | — | 1:00:49,8 | 1:03:49,8 | 180 s |
| DEP013 | B763 | bến 26 | 0:58:22,4 | 337 s | 1:03:59,8 | — | 1:03:59,8 | 1:07:40,6 | 221 s |
| DEP014 | A320 | bến 27 | 1:02:08,1 | 333 s | 1:07:40,6 | — | 1:07:40,6 | 1:10:25,6 | 165 s |
| DEP015 | A21N | bến 27 | 1:04:03,1 | 333 s | 1:09:35,6 | — | 1:10:25,6 | 1:13:31,4 | 236 s |
| DEP016 | A320 | bến 27 | 1:07:53,9 | 333 s | 1:13:26,4 | — | 1:13:31,4 | 1:19:45,2 | 379 s |
| DEP017 | B748 | bến 27 | 1:14:17,6 | 333 s | 1:19:50,2 | — | 1:19:50,2 | 1:22:11,3 | 141 s |
| DEP018 | A333 | bến 27 | 1:16:38,8 | 333 s | 1:22:11,3 | — | 1:22:11,3 | 1:25:23,9 | 193 s |

| Chỉ tiêu | Giá trị |
|---|---|
| Thời gian chờ tại điểm chờ | TB **194 s**, 60–379 s |
| Số tàu tại điểm chờ theo thời gian (đo trong mô phỏng, lớn nhất mỗi 5 phút) | 0:25 → 1:25: **2** ở mọi khoảng (khoảng cuối 1) |
| Số tàu tại điểm chờ lớn nhất | **2** (giới hạn 3) |
| Cắt qua 35R | lâu nhất 34 s; chờ trước vạch 35R 0–56 s |
| Thoát ly 35L (qua ngưỡng → vị trí dừng chờ) | lâu nhất 94 s |
| Lăn vào bến (hết chuỗi thoát ly → bến) | 173–232 s |

Điểm chờ luôn có **2 tàu** (một tàu trên đường CHC chờ chạy đà + một tàu tại PREHOLD) — KSVKL luôn có tàu sẵn sàng cất cánh, đúng mục tiêu mục 6 prompt. Không cần tới tàu thứ ba vì nhịp cất cánh bị khống chế bởi nhịp hạ cánh.

---

## IX. SẢN PHẨM BÀN GIAO

| File | Nội dung |
|---|---|
| `VVDN-XENKE-60MIN.scn` | Kịch bản — **369.001 byte, 6.191 lệnh**; header ghi seed, phân cách và nguồn, giả định, đơn giản hoá |
| `_gen_vvdn_xenke_60min.py` | Generator, seed cố định, tái lập 100 % |
| `vvdn_xenke_rules.json` | Quy tắc phân cách và mặt đất, ghi điều khoản nguồn; giá trị sai cũ lưu kèm |
| `_calib_vvdn_xenke.py` / `VVDN-XENKE-60MIN.calib.json` | Hiệu chuẩn thời điểm tạo tàu đến (BADA 3.16) |
| `_verify_vvdn_xenke.py` | Kiểm chứng độc lập — **30 mục**, chạy mô phỏng headless thật |
| `_ma_tran_gian_cach_vvdn_xenke.py` / `.ma_tran.json` | Ma trận giãn cách (mục IV) |
| `_phan_tich_mat_do_vvdn_xenke.py` / `.mat_do.json` | Phân tích mật độ bắt đầu vi phạm (mục VI) |
| `VVDN-XENKE-60MIN.plan.json` | Lịch chi tiết |
| `BaoCao_KiemChung_VVDN_XenKe.md` / `.docx` | Báo cáo này |

### Cách chạy lại
```bash
cd "FTS Server/scenario"
python _gen_vvdn_xenke_60min.py            # sinh kịch bản (~10 s)
python _calib_vvdn_xenke.py                # hiệu chuẩn — khi lịch thay đổi
python _verify_vvdn_xenke.py               # kiểm chứng đầy đủ, có mô phỏng
python _ma_tran_gian_cach_vvdn_xenke.py    # ma trận giãn cách (sau kiểm chứng)
python _phan_tich_mat_do_vvdn_xenke.py     # mật độ bắt đầu vi phạm
```
Hiệu chuẩn và phần B **bắt buộc chạy với BADA** (`performance_model = 'bada'`).

---

## X. KIẾN NGHỊ

1. **Xác nhận các mục ở 3.3**, đặc biệt cách hiểu 8 NM — đây là nút cổ chai chính của năng lực.
2. **Rà lại `compliance_rulesets/VVDN.json`** (đọc sai hai bảng phân cách).
3. Nếu muốn tăng năng lực, đối tượng cần xem xét là **thời gian giải phóng 35L** (thoát ly + cắt qua 35R) và **giãn cách hạ cánh**, không phải phân cách cất cánh.
4. Muốn kiểm chứng hành vi khi vi phạm (thay vì chỉ đếm trên lịch như mục VI), cần sinh thêm kịch bản nén lịch và chạy mô phỏng.
