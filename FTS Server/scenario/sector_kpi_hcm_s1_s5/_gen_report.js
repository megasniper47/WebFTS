const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak,
} = require("docx");

const HERE = __dirname;
const result = JSON.parse(fs.readFileSync(path.join(HERE, "sector_kpi_result.json"), "utf-8"));
const atwiResult = JSON.parse(fs.readFileSync(path.join(HERE, "sector_atwi_result.json"), "utf-8"));

const TASK_NAMES_VI = {
  SURV_SCAN: "Quét giám sát radar/vị trí",
  TRAFFIC_COUNT_MONITOR: "Theo dõi mật độ lưu lượng",
  CONFLICT_CHECK: "Kiểm tra phân cách",
  STCA_RESPONSE: "Xử lý cảnh báo phân cách nghiêm trọng",
  VECTOR_OR_DIRECT: "Đổi hướng bay (vector/direct) — proxy",
  ALTITUDE_CHANGE: "Đổi mực bay — proxy",
  SPEED_CONTROL: "Điều chỉnh tốc độ — proxy",
  HANDOFF_COORD: "Phối hợp chuyển giao (vào sector)",
  CROSS_SECTOR_COORD: "Phối hợp chuyển tiếp liên sector",
};

const BAND_VI = { normal: "Bình thường", watch: "Cần theo dõi", high: "Cao", critical: "Quá tải" };

function taskBreakdownAgg(res) {
  const agg = {};
  for (const w of res.timeseries) {
    for (const tb of w.taskBreakdown) {
      agg[tb.taskCode] = (agg[tb.taskCode] || 0) + tb.totalSeconds;
    }
  }
  const grand = Object.values(agg).reduce((a, b) => a + b, 0);
  return Object.entries(agg)
    .map(([code, sec]) => ({ code, sec, pct: grand ? (sec / grand) * 100 : 0 }))
    .sort((a, b) => b.sec - a.sec);
}

function bandCounts(res) {
  const c = {};
  for (const w of res.timeseries) c[w.band] = (c[w.band] || 0) + 1;
  return c;
}

function atwiBreakdownTable(res) {
  const agg = taskBreakdownAgg(res);
  const header = new TableRow({
    children: [
      cell("Loại tác vụ", { header: true, width: 3200 }),
      cell("Tổng thời lượng (phút)", { header: true, width: 1800, center: true }),
      cell("Tỷ trọng", { header: true, width: 1400, center: true }),
    ],
  });
  const rows = agg.map(r => new TableRow({
    children: [
      cell(TASK_NAMES_VI[r.code] || r.code, { width: 3200 }),
      cell((r.sec / 60).toFixed(1), { width: 1800, center: true }),
      cell(r.pct.toFixed(1) + "%", { width: 1400, center: true }),
    ],
  }));
  return new Table({
    width: { size: 6400, type: WidthType.DXA },
    columnWidths: [3200, 1800, 1400],
    rows: [header, ...rows],
  });
}

function atwiTimeseriesTable(res) {
  const header = new TableRow({
    children: [
      cell("Cửa sổ (UTC)", { header: true, width: 2200 }),
      cell("Số tàu", { header: true, width: 1200, center: true }),
      cell("ATWI %", { header: true, width: 1400, center: true }),
      cell("Mức", { header: true, width: 1800, center: true }),
    ],
  });
  const rows = res.timeseries.map(w => new TableRow({
    children: [
      cell(`${clock(w.startTime).slice(0,5)}–${clock(w.endTime).slice(0,5)}`, { width: 2200 }),
      cell(String(w.activeAircraftCount), { width: 1200, center: true }),
      cell(w.atwiPercent.toFixed(1), { width: 1400, center: true }),
      cell(BAND_VI[w.band] || w.band, { width: 1800, center: true }),
    ],
  }));
  return new Table({
    width: { size: 6600, type: WidthType.DXA },
    columnWidths: [2200, 1200, 1400, 1800],
    rows: [header, ...rows],
  });
}

function atwiSectionFor(name) {
  const res = atwiResult[name];
  const bc = bandCounts(res);
  const bcStr = Object.entries(bc).map(([b, c]) => `${BAND_VI[b] || b}: ${c} cửa sổ`).join("; ");
  return [
    new Paragraph({ text: name, heading: HeadingLevel.HEADING_2 }),
    new Paragraph({ text: `• ATWI tổng thể (toàn bộ 40 phút): ${res.overallAtwiPercent.toFixed(1)}% — mức "${BAND_VI[res.overallBand] || res.overallBand}"` }),
    new Paragraph({ text: `• Phân bố mức theo 8 cửa sổ 5 phút: ${bcStr}` }),
    new Paragraph({ text: `• Cửa sổ đỉnh: ${clock(res.peakWindow.startTime).slice(0,5)}–${clock(res.peakWindow.endTime).slice(0,5)} UTC, ${res.peakWindow.activeAircraftCount} tàu, ATWI=${res.peakWindow.atwiPercent.toFixed(1)}%` }),
    new Paragraph({ text: "", spacing: { after: 100 } }),
    new Paragraph({ children: [new TextRun({ text: "Tỷ trọng đóng góp theo loại tác vụ (toàn bộ 40 phút)", italics: true })] }),
    atwiBreakdownTable(res),
    new Paragraph({ text: "", spacing: { after: 100 } }),
    new Paragraph({ children: [new TextRun({ text: "ATWI % theo từng cửa sổ 5 phút", italics: true })] }),
    atwiTimeseriesTable(res),
    new Paragraph({ text: "", spacing: { after: 150 } }),
  ];
}

const SIM_T0 = Date.UTC(2026, 5, 5, 7, 20, 0); // 2026-06-05T07:20:00Z
function clock(tSec) {
  const d = new Date(SIM_T0 + tSec * 1000);
  return d.toISOString().substring(11, 19) + "Z";
}
function fmtMin(sec) {
  return (sec / 60).toFixed(1);
}

const CORE_START = 600, CORE_END = 1800;

function sectorStats(name) {
  const data = result[name];
  const core = data.timeseries.filter(b => b.bin_start_s >= CORE_START && b.bin_start_s < CORE_END);
  const peakCore = core.reduce((a, b) => (b.aircraft_count > a.aircraft_count ? b : a), core[0]);
  const avgCore = core.reduce((s, b) => s + b.aircraft_count, 0) / core.length;
  return { data, core, peakCore, avgCore };
}

const S1 = sectorStats("HCM ACC Sector 1");
const S5 = sectorStats("HCM ACC Sector 5");

function cell(text, opts = {}) {
  return new TableCell({
    width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
    shading: opts.header ? { type: ShadingType.CLEAR, fill: "DCE6F1" } : undefined,
    children: [new Paragraph({
      alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: [new TextRun({ text, bold: !!opts.header })],
    })],
  });
}

function timeseriesTable(core) {
  const header = new TableRow({
    children: [cell("Giờ (UTC)", { header: true, width: 2500 }), cell("Số tàu trong sector", { header: true, width: 2500, center: true })],
  });
  const rows = core.map(b => new TableRow({
    children: [cell(clock(b.bin_start_s).slice(0, 5), { width: 2500 }), cell(String(b.aircraft_count), { width: 2500, center: true })],
  }));
  return new Table({
    width: { size: 5000, type: WidthType.DXA },
    columnWidths: [2500, 2500],
    rows: [header, ...rows],
  });
}

function dwellTable(detail, topN = 10) {
  const header = new TableRow({
    children: [
      cell("Callsign", { header: true, width: 2000 }),
      cell("Số lần vào/ra", { header: true, width: 1800, center: true }),
      cell("Tổng thời gian trong sector (phút)", { header: true, width: 2800, center: true }),
    ],
  });
  const rows = detail.slice(0, topN).map(r => new TableRow({
    children: [
      cell(r.callsign, { width: 2000 }),
      cell(String(r.entries), { width: 1800, center: true }),
      cell(fmtMin(r.total_dwell_s), { width: 2800, center: true }),
    ],
  }));
  return new Table({
    width: { size: 6600, type: WidthType.DXA },
    columnWidths: [2000, 1800, 2800],
    rows: [header, ...rows],
  });
}

function sectionFor(name, stats, intro) {
  return [
    new Paragraph({ text: name, heading: HeadingLevel.HEADING_2 }),
    new Paragraph({ children: [new TextRun({ text: intro })] }),
    new Paragraph({ text: "", spacing: { after: 100 } }),
    new Paragraph({ children: [new TextRun({ text: "Chỉ số tổng hợp", bold: true })] }),
    new Paragraph({ text: `• Số tàu bay khác nhau đi qua sector trong toàn bộ 40 phút mô phỏng (07:20–08:00 UTC): ${stats.data.distinct_aircraft}` }),
    new Paragraph({ text: `• Đỉnh đồng thời trong cửa sổ quan sát 07:30–07:50 UTC: ${stats.peakCore.aircraft_count} tàu, lúc ${clock(stats.peakCore.bin_start_s).slice(0,5)} UTC` }),
    new Paragraph({ text: `• Trung bình số tàu/phút trong cửa sổ quan sát: ${stats.avgCore.toFixed(1)}` }),
    new Paragraph({ text: `• Thời gian bay trong sector (dwell time) trung bình/tàu: ${fmtMin(stats.data.avg_dwell_s)} phút` }),
    new Paragraph({ text: "", spacing: { after: 100 } }),
    new Paragraph({ children: [new TextRun({ text: "Số tàu trong sector theo từng phút (07:30–07:50 UTC)", bold: true })] }),
    timeseriesTable(stats.core),
    new Paragraph({ text: "", spacing: { after: 150 } }),
    new Paragraph({ children: [new TextRun({ text: "10 tàu có thời gian bay trong sector dài nhất", bold: true })] }),
    dwellTable(stats.data.dwell_detail, 10),
    new Paragraph({ text: "", spacing: { after: 150 } }),
  ];
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 } } },
    children: [
      new Paragraph({ text: "BÁO CÁO KPI SECTOR ACC — SECTOR 1 & SECTOR 5 HỒ CHÍ MINH ACC", heading: HeadingLevel.TITLE }),
      new Paragraph({ children: [new TextRun({ text: "Dữ liệu track thật ngày 05/06/2026 (r72_tracks_20260605.csv) — cửa sổ quan sát 07:30–07:50 UTC (14:30–14:50 giờ Việt Nam)", italics: true })] }),
      new Paragraph({ text: "", spacing: { after: 200 } }),

      new Paragraph({ text: "1. Nguồn dữ liệu và phương pháp", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({ text: "• Ranh giới sector: WebATM/static/data/vietnam_acc_sector_boundaries.geojson — đã đối chiếu độc lập khớp 100% với biểu đồ AIRAC AIP SUP A37/23 \"SECTORIZATION OF HA NOI ACC AND HO CHI MINH ACC\" (hiệu lực 02/11/2023), gồm 41 điểm tọa độ." }),
      new Paragraph({ text: "• Sector 1 HCM ACC = polygon <=FL265 (bên dưới FL265) hợp với polygon FL265–FL460 (bên trên)." }),
      new Paragraph({ text: "• Sector 5 HCM ACC = polygon <=FL460 (toàn cột) hợp với 2 polygon lớp trên FL265–FL460 và FL305–FL460 (các khu vực được bàn giao thêm cho Sector 5 ở mực bay cao)." }),
      new Paragraph({ text: "• Lưu lượng: trích từ track radar/ADS-B thật ngày 05/06/2026 (file r72_tracks_20260605.csv, 744MB, ~4.13 triệu điểm). KHÔNG dùng cột fir_id trong file gốc vì gần như toàn bộ bị gán sai \"VVHN\"; việc xác định tàu có ở trong sector hay không được tính lại từ tọa độ + mực bay thật đối chiếu polygon ở trên." }),
      new Paragraph({ text: "• Khung giờ 07:30–07:50 UTC được chọn vì đây là 1 trong các đỉnh mật độ thật trong ngày của cả Sector 1 và Sector 5 (dựa trên khảo sát toàn bộ 24 giờ dữ liệu)." }),
      new Paragraph({ text: "• 59 chuyến bay thật xuất hiện trong khung này được chuyển thành kịch bản BlueSky (HCM_S1S5_KPI_20260605_0730-0750.scn, 32.351 lệnh MOVE) tái hiện đúng vị trí/tốc độ/hướng bay thật theo nhịp mẫu thật (~4 giây/lần), chạy headless 40 phút (07:20–08:00 UTC, có đệm 10 phút mỗi đầu)." }),
      new Paragraph({ text: "• Kết quả KPI được kiểm chứng độc lập: một script riêng (_verify_sector_kpi.py) đọc lại toàn bộ dữ liệu nguồn và tự tính lại bằng thuật toán ray-casting tự viết (không dùng thư viện shapely, không tái dùng hàm của analyzer) — khớp 100% với kết quả báo cáo dưới đây." }),
      new Paragraph({ text: "", spacing: { after: 150 } }),

      new Paragraph({ text: "2. Lưu ý quan trọng về giới hạn dữ liệu", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({ text: "• Loại tàu bay: dữ liệu track gốc không có cột loại tàu bay (aircraft type), nên toàn bộ 59 chuyến được gán mặc định A320 khi tạo kịch bản BlueSky. Vì kịch bản dùng lệnh MOVE (đặt lại vị trí trực tiếp mỗi ~4 giây, không đi qua mô hình hiệu năng), loại tàu KHÔNG ảnh hưởng đến độ chính xác của các KPI vị trí/thời gian dưới đây." }),
      new Paragraph({ text: "• Tốc độ hiển thị trong log mô phỏng (ground speed) bị lệch so với tốc độ thật do tham số \"spd\" của lệnh CRE/MOVE trong BlueSky được hiểu là tốc độ hiệu chỉnh (CAS), trong khi dữ liệu nguồn là tốc độ mặt đất (GS) — hai đại lượng khác nhau ở độ cao lớn. Đã kiểm tra: sai lệch này KHÔNG làm trôi vị trí tích lũy theo thời gian (độ lệch vị trí đo được ổn định quanh 0,3 km trong suốt 40 phút, và hoàn toàn giải thích được bằng chênh lệch thời điểm lấy mẫu log so với mẫu thật gần nhất — không phải sai số mô phỏng tích lũy). Vì vậy KPI về số tàu/sector và thời gian bay trong sector (dựa hoàn toàn vào vị trí + mốc thời gian) là đáng tin cậy; chỉ số tốc độ tức thời trong log mô phỏng thì không nên dùng." }),
      new Paragraph({ text: "• Chỉ số \"workload\": mục 4 của báo cáo này áp dụng mô hình ATWI (Air Traffic Workload Indicator) đã có trong dự án — vốn được xây cho vị trí sân bay/tiếp cận (TWR/APP/EC...), dựa trên đếm số lệnh controller theo từng loại tác vụ — sang sector ACC đường dài. Bản thân mô hình ATWI gốc hiện vẫn ở trạng thái \"draft\", chưa approvedForKpi (ghi rõ trong atwi_models.json), áp dụng chung baseEffortSec cho mọi vị trí. Phần mở rộng cho ACC giữ NGUYÊN công thức/hệ số đó, nhưng một số loại tác vụ (đổi hướng/đổi mực bay/đổi tốc độ) phải suy ra từ biến động THẬT của track vì kịch bản này là replay vị trí, không có log lệnh controller — xem chi tiết giới hạn ở đầu mục 4." }),
      new Paragraph({ text: "", spacing: { after: 150 } }),

      new Paragraph({ text: "3. KPI số tàu và thời gian bay theo sector", heading: HeadingLevel.HEADING_1 }),
      ...sectionFor("HCM ACC Sector 1", S1, "Sector 1 HCM ACC kiểm soát không phận GND–FL265 ở cell ① (khu vực trung tâm Biển Đông ngoài khơi Đà Nẵng/Quy Nhơn) và FL265–FL460 riêng ở phần phía bắc (cell ①, không gồm phần đã bàn giao cho Sector 5)."),
      ...sectionFor("HCM ACC Sector 5", S5, "Sector 5 HCM ACC kiểm soát toàn bộ cột khí (GND–FL460) ở cell ⑤ (phía đông, giáp ranh giới FIR Manila) cộng thêm các lớp trên FL265/FL305 được san sẻ từ các cell lân cận ở mực bay cao."),

      new Paragraph({ text: "4. Đánh giá workload theo mô hình ATWI (mở rộng cho sector ACC)", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({ children: [new TextRun({ text: "4.1. Phương pháp và giới hạn — ĐỌC TRƯỚC KHI DÙNG SỐ LIỆU DƯỚI ĐÂY", bold: true })] }),
      new Paragraph({ text: "• Công thức, hệ số (complexityCoeff=0,15; coordinationCoeff=0,12...) và ngưỡng băng workload (Bình thường <60%, Cần theo dõi 60–75%, Cao 75–90%, Quá tải ≥90%) lấy NGUYÊN VẸN từ mô hình ATWI đã có trong dự án (FTS Server/data/atwi_models.json, atwi_task_index.json) — không tự đặt hệ số mới." }),
      new Paragraph({ text: "• Tác vụ tính được TRỰC TIẾP từ dữ liệu thật (không phải suy đoán): SURV_SCAN/TRAFFIC_COUNT_MONITOR (số tàu hiện diện), HANDOFF_COORD (số lần tàu THẬT SỰ bay vào sector trong khung quan sát — đã loại trừ các tàu đã có mặt từ trước khung quan sát để không đếm trùng), CROSS_SECTOR_COORD (số lần tàu chuyển tiếp thật giữa Sector 1 và Sector 5), CONFLICT_CHECK/STCA_RESPONSE (vi phạm phân cách thật giữa các cặp tàu, theo chuẩn ICAO Doc 4444: 5NM ngang / 1000ft dọc RVSM — do dự án chưa có ruleset en-route riêng cho VVHM)." }),
      new Paragraph({ text: "• Tác vụ PHẢI SUY RA theo proxy hành vi bay thật (không có log lệnh controller vì đây là kịch bản replay track, không phải kịch bản có người/AI điều hành phát lệnh): VECTOR_OR_DIRECT = đổi hướng bay thật >15° giữa đầu/cuối cửa sổ 5 phút; ALTITUDE_CHANGE = đổi mực bay thật >500ft; SPEED_CONTROL = đổi tốc độ mặt đất thật >15kt. CẢNH BÁO QUAN TRỌNG: một phần biến động này là do bay bình thường (gió, step-climb, điều chỉnh nhỏ của phi công/FMS) chứ KHÔNG chắc chắn là do kiểm soát viên can thiệp — khác với mô hình ATWI gốc (đếm đúng lệnh controller đã phát ra). Vì vậy con số ATWI% dưới đây nên hiểu là CẬN TRÊN minh họa (nếu mọi biến động đều cần can thiệp), KHÔNG phải số đo đã hiệu chỉnh/kiểm chứng vận hành." }),
      new Paragraph({ text: "• Số ATCO/vị trí dùng mặc định 1 (giống cách mô hình ATWI gốc tính cho 1 vị trí \"COMBINED_TMA\"), tức giả định 1 kiểm soát viên phải tự làm hết mọi tác vụ của cả sector. Thực tế một sector ACC thường có kíp 2 người (EC điều hành + PLC/phối hợp kế hoạch) chia sẻ tải — dự án CHƯA có mô hình phân việc theo kíp 2 người, nên %ATWI dưới đây có thể cao hơn thực tế nếu áp dụng đúng biên chế kíp." }),
      new Paragraph({ text: "• Mô hình ATWI gốc (atwi_models.json) bản thân cũng đang ở trạng thái draft, approvedForKpi=false, baseEffortSec của mọi loại tác vụ đều ghi evidenceLevel=\"assumed\" (giá trị khởi tạo, chưa hiệu chỉnh từ số liệu vận hành thật) — áp dụng y nguyên các giá trị đó cho ACC không làm độ tin cậy thấp hơn so với khi dùng cho TWR, nhưng cũng không cao hơn." }),
      new Paragraph({ text: "• Kết quả đã được kiểm chứng độc lập (_verify_sector_atwi.py): đếm lại HANDOFF_COORD bằng code riêng (khớp), rà soát phân cách bằng vét cạn mọi cặp mẫu thật trong ±10s (không lấy mẫu thưa 30s như analyzer chính) để đảm bảo không bỏ sót xung đột — xác nhận cả 2 sector đều KHÔNG có vi phạm phân cách thật nào trong khung quan sát, và công thức ATWI% cho 1 cửa sổ mẫu tính lại khớp với kết quả chính." }),
      new Paragraph({ text: "", spacing: { after: 150 } }),
      ...atwiSectionFor("HCM ACC Sector 1"),
      ...atwiSectionFor("HCM ACC Sector 5"),
      new Paragraph({ text: "4.2. Nhận xét", heading: HeadingLevel.HEADING_2 }),
      new Paragraph({ text: `• Cả hai sector đều đạt mức "Quá tải" ở phần lớn các cửa sổ 5 phút ngay cả khi chỉ có 13–28 tàu đồng thời — phần lớn tải đến từ việc mô hình cộng dồn ĐỘC LẬP từng loại tác vụ (giám sát + đổi hướng + đổi mực bay + đổi tốc độ + phối hợp) cho mỗi tàu mà không có cơ chế giảm tải khi các tác vụ trùng thời điểm, và từ việc 1 ATCO phải gánh toàn bộ (xem 4.1). Đây có thể là đặc điểm vốn có của mô hình ATWI (muốn cảnh báo sớm), hoặc do ngưỡng proxy (15°/500ft/15kt) hơi nhạy — cần hiệu chỉnh với số lệnh controller thật mới kết luận được.` }),
      new Paragraph({ text: "• Sector 1 có ATWI% cao hơn Sector 5 (150% so với 111%), nhất quán với việc Sector 1 cũng có mật độ tàu và tỷ lệ biến động hướng/mực bay (proxy) cao hơn ở mục 3." }),
      new Paragraph({ text: "• Khuyến nghị: để dùng số liệu này cho mục đích chuyên môn, cần (1) thay proxy hành vi bằng log lệnh controller thật (khi có kịch bản có người/AI điều hành phát lệnh qua sector này), (2) hiệu chỉnh baseEffortSec/ngưỡng proxy với dữ liệu quan sát thật, (3) mô hình hoá biên chế kíp 2 người (EC+PLC) thay vì 1 ATCO." }),
      new Paragraph({ text: "", spacing: { after: 150 } }),

      new Paragraph({ text: "5. Kết luận", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({ text: `• Sector 1 có mật độ cao hơn Sector 5 trong khung quan sát (đỉnh ${S1.peakCore.aircraft_count} so với ${S5.peakCore.aircraft_count} tàu đồng thời), phù hợp vì Sector 1 nằm trên trục bay chính Bắc–Nam dọc bờ biển.` }),
      new Paragraph({ text: `• Thời gian bay trung bình trong sector (${fmtMin(S1.data.avg_dwell_s)} phút ở Sector 1, ${fmtMin(S5.data.avg_dwell_s)} phút ở Sector 5) phản ánh các chuyến bay chặng dài quốc tế (ví dụ CPA758, FDX5315 ở Sector 5 với ~40 phút) cùng tồn tại với các chuyến chỉ cắt qua rìa sector trong vài phút.` }),
      new Paragraph({ text: `• Về workload (mục 4): cả hai sector đều lên mức "Quá tải" trong phần lớn khung quan sát theo mô hình ATWI mở rộng, nhưng số liệu này mang tính minh họa/cận trên do dùng proxy hành vi bay thay cho log lệnh controller thật — KHÔNG nên dùng trực tiếp cho quyết định biên chế/mở sector mà cần hiệu chỉnh thêm (xem khuyến nghị 4.2).` }),
      new Paragraph({ text: "• Toàn bộ số liệu trong báo cáo này xuất phát từ dữ liệu track thật và polygon sector đã đối chiếu với AIP — không có số liệu suy đoán/bịa đặt, ngoại trừ loại tàu bay mặc định (mục 2) và các proxy hành vi dùng cho workload (mục 4.1), đều đã nêu rõ và không ảnh hưởng tới KPI số tàu/dwell time ở mục 3." }),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(HERE, "BaoCao_KPI_Sector1_Sector5_HCMACC.docx");
  fs.writeFileSync(out, buf);
  console.log("Da ghi", out);
});
