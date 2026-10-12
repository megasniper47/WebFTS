""" SurfaceTaxiController — Điều phối viên đa phương tiện cho di chuyển mặt đất.

Cơ chế "Stop & Go" phỏng theo thuật toán Opt_StopGo của dự án OpenTaxi:
    - Ưu tiên (priority) = tàu bay nào còn quãng đường (distance-to-go) ngắn
      hơn tới điểm đích thì được đi trước.
    - Phát hiện xung đột được vector hoá bằng numpy trên toàn bộ tập tàu bay
      đang taxi (không lặp O(n^2) bằng Python thuần).
    - Xử lý xung đột CHỈ bằng phanh (giảm traf.selspd về 0), không bao giờ
      đổi traf.trk/hdg — khác với CD&R trên không (MVP) vốn né bằng vector hoá
      hướng bay.
"""
import numpy as np

import bluesky as bs
from bluesky import core, stack, settings
from bluesky.tools import geo
from bluesky.tools.aero import nm, kts

# ---------------------------------------------------------------------------
# Tham số có thể chỉnh trong settings.cfg (hoặc để mặc định)
# ---------------------------------------------------------------------------
settings.set_variable_defaults(
    taxi_dt=1.0,                # chu kỳ vòng lặp điều khiển [s]
    taxi_min_separation=50.0,   # ngưỡng dừng khẩn cấp khi KHÔNG biết chiều dài tàu bay (fallback) [m]
    taxi_tail_buffer=20.0,      # đệm tối thiểu sau ĐUÔI tàu phía trước khi ĐÃ biết chiều dài 2 tàu [m]
    taxi_predict_horizon=60.0,  # tầm nhìn dự đoán tương lai [s]
    taxi_predict_steps=6,       # số lát cắt thời gian trong tầm nhìn (vector hoá)
    taxi_default_spd=15.0,      # tốc độ taxi danh định phục hồi khi hết xung đột [kts CAS]
)


def init_plugin():
    ''' Khởi tạo plugin — bắt buộc phải có hàm này để BlueSky nhận diện file
        là một plugin. '''
    global taxictrl
    taxictrl = SurfaceTaxiController()

    config = {
        'plugin_name': 'SURFACETAXI',
        'plugin_type': 'sim',
    }
    return config


class SurfaceTaxiController(core.Entity):
    ''' Bộ điều phối tránh va chạm khi taxi trên mặt đất (Stop & Go). '''

    def __init__(self):
        super().__init__()
        # Mọi mảng khai báo trong khối with() này sẽ tự động được BlueSky
        # resize theo traf (thêm/xoá phần tử khi CRE/DEL tàu bay) — đây là
        # cách "thêm biến vào traf" đúng chuẩn plugin, không sửa trực tiếp
        # class Traffic gốc.
        with self.settrafarrays():
            self.istaxiing = np.array([], dtype=bool)      # cờ: đang dưới quyền điều phối taxi
            self.yield_flag = np.array([], dtype=bool)      # đang nhường đường (dự đoán)
            self.immediate_stop = np.array([], dtype=bool)  # đang dừng khẩn (va chạm cận kề)
            self.priority = np.array([])                    # điểm ưu tiên hiện tại (để debug/hiển thị)
            self.taxi_spd = np.array([])                     # tốc độ taxi danh định [m/s CAS]
            self.length = np.array([])                       # chiều dài tàu bay [m], 0.0 = chưa biết
            self.conflict_with = []                          # callsign tàu bay đang cản đường (debug)

    def create(self, n=1):
        ''' Gọi tự động mỗi khi có tàu bay mới được tạo. '''
        super().create(n)
        self.taxi_spd[-n:] = settings.taxi_default_spd * kts
        self.length[-n:] = 0.0

    # ------------------------------------------------------------------
    # Stack commands
    # ------------------------------------------------------------------
    @stack.command(name='TAXION')
    def taxi_on(self, acidx: 'acid', spd: 'spd' = None, length_m: 'float' = 0.0):
        ''' TAXION acid [spd] [length_m]

            Đặt tàu bay dưới quyền điều phối của SurfaceTaxiController.
            spd (tuỳ chọn, kts) là tốc độ taxi danh định sẽ được phục hồi
            mỗi khi hết xung đột. length_m (tuỳ chọn, mét) là chiều dài thân
            tàu bay thật -- dùng để tính khoảng cách an toàn = nửa chiều dài
            2 tàu + taxi_tail_buffer (đúng nghĩa "còn lại sau đuôi tàu
            trước"), thay cho ngưỡng cố định taxi_min_separation khi biết
            chiều dài của CẢ HAI tàu trong 1 cặp đang xét. '''
        self.istaxiing[acidx] = True
        self.yield_flag[acidx] = False
        self.immediate_stop[acidx] = False
        self.conflict_with[acidx] = ''
        if spd is not None:
            self.taxi_spd[acidx] = spd
        self.length[acidx] = length_m
        bs.traf.selspd[acidx] = self.taxi_spd[acidx]
        # Tắt VNAV speed để autopilot không tự ý ghi đè lại selspd của ta
        bs.traf.swvnavspd[acidx] = False
        return True, f'{bs.traf.id[acidx]} is now under SURFACETAXI control.'

    @stack.command(name='TAXIOFF')
    def taxi_off(self, acidx: 'acid'):
        ''' TAXIOFF acid

            Giải phóng tàu bay khỏi quyền điều phối taxi (trả lại quyền
            điều khiển tốc độ cho autopilot/VNAV bình thường). '''
        self.istaxiing[acidx] = False
        self.yield_flag[acidx] = False
        self.immediate_stop[acidx] = False
        self.conflict_with[acidx] = ''
        return True, f'{bs.traf.id[acidx]} released from SURFACETAXI control.'

    # ------------------------------------------------------------------
    # Vòng lặp điều khiển chính
    # ------------------------------------------------------------------
    @core.timed_function(name='surfacetaxi', dt=settings.taxi_dt)
    def update(self):
        ''' Một chu kỳ điều phối cho toàn bộ tàu bay đang taxi. '''
        # --- 0. Lọc tập tàu bay đang taxi -------------------------------
        # Đây là điểm tích hợp: nếu nhánh BlueSky của bạn có sẵn traf.state
        # (mảng string), chỉ cần thay dòng dưới bằng:
        #     idx = np.where(bs.traf.state == 'TAXI')[0]
        idx = np.where(self.istaxiing)[0]
        n = len(idx)
        if n < 2:
            if n == 1:
                self._release(idx)
            return

        lat = bs.traf.lat[idx]
        lon = bs.traf.lon[idx]
        gs = bs.traf.gs[idx]
        trk = bs.traf.trk[idx]

        # --- 1. Ưu tiên: distance-to-go càng nhỏ, ưu tiên càng cao -------
        priority = self._calc_priority(idx)
        # higher[i, j] = True nếu tàu j có ưu tiên cao hơn tàu i
        higher = priority.reshape(1, n) > priority.reshape(n, 1)

        # --- 1b. Khoảng cách an toàn CẦN THIẾT cho từng cặp (i, j) -------
        # Nếu biết chiều dài thật của CẢ HAI tàu: yêu cầu = nửa dài(i) +
        # nửa dài(j) + taxi_tail_buffer -- đúng nghĩa "còn lại sau đuôi tàu
        # trước" (không phải khoảng cách tâm-tới-tâm phi thực tế). Nếu chưa
        # biết chiều dài 1 trong 2 (length=0.0, ví dụ tàu bay không dùng
        # TAXION với length_m) thì dùng ngưỡng cố định taxi_min_separation.
        length = self.length[idx]
        both_known = (length.reshape(1, n) > 0) & (length.reshape(n, 1) > 0)
        req_sep = np.where(
            both_known,
            (length.reshape(1, n) + length.reshape(n, 1)) / 2.0 + settings.taxi_tail_buffer,
            settings.taxi_min_separation,
        )

        # --- 2. Khoảng cách hiện tại, vector hoá toàn bộ cặp -------------
        latm, lonm = np.asmatrix(lat), np.asmatrix(lon)
        _, dist_nm = geo.kwikqdrdist_matrix(latm, lonm, latm, lonm)
        dist_now = np.asarray(dist_nm) * nm  # [m], ma trận (n, n)

        immediate = np.any((dist_now < req_sep) & higher, axis=1)

        # --- 3. Dự đoán tương lai: phóng chiếu vị trí theo gs & trk ------
        # Lấy mẫu nhiều mốc thời gian trong predict_horizon (vector hoá theo
        # từng lát thời gian, mỗi lát là một phép toán ma trận (n, n)).
        yield_now = np.zeros(n, dtype=bool)
        horizon = settings.taxi_predict_horizon
        steps = max(1, int(settings.taxi_predict_steps))
        for t in np.linspace(horizon / steps, horizon, steps):
            dist_t_nm = gs * t / nm
            flat, flon = geo.kwikpos(lat, lon, trk, dist_t_nm)
            flatm, flonm = np.asmatrix(flat), np.asmatrix(flon)
            _, dist_future_nm = geo.kwikqdrdist_matrix(flatm, flonm, flatm, flonm)
            dist_future = np.asarray(dist_future_nm) * nm
            yield_now |= np.any((dist_future < req_sep) & higher, axis=1)

        # immediate_stop được ưu tiên tuyệt đối so với yield dự đoán
        yield_now &= ~immediate

        # --- 4. Áp dụng lệnh Stop & Go (chỉ phanh, không đổi hướng) ------
        self._apply(idx, immediate, yield_now, higher, dist_now)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _calc_priority(self, idx):
        ''' priority càng lớn => càng ưu tiên (càng gần đích). '''
        dist2go = np.empty(len(idx))
        for k, i in enumerate(idx):
            route = bs.traf.ap.route[i]
            if route.nwp > 0:
                dist2go[k] = geo.kwikdist(bs.traf.lat[i], bs.traf.lon[i],
                                           route.wplat[-1], route.wplon[-1]) * nm
            else:
                # Không có route -> coi như còn rất xa đích (ưu tiên thấp
                # nhất) nhưng vẫn được kiểm tra an toàn immediate_stop.
                dist2go[k] = 1e9

        # Tie-break theo idx để tránh hai tàu bay có priority bằng nhau
        # (dẫn đến deadlock đối xứng: cả hai cùng nhường nhau / cùng không
        # nhường ai).
        priority = -dist2go - idx * 1e-6
        self.priority[idx] = priority
        return priority

    def _apply(self, idx, immediate, yield_now, higher, dist_now):
        stop_mask = immediate | yield_now
        for k, i in enumerate(idx):
            if not bs.traf.swlnav[i]:
                # Tàu bay đang bị dừng cứng bởi cơ chế KHÁC (STOP_HOLD/MOVE,
                # LNAV đã OFF) -- vẫn nằm trong idx để các tàu khác né nó,
                # nhưng TUYỆT ĐỐI không đụng vào selspd ở đây: nếu không, khi
                # hết xung đột plugin sẽ tự đặt lại selspd=taxi_spd, và vì
                # LNAV off (không có waypoint dẫn đường) tàu bay sẽ TRÔI
                # THẲNG theo hướng đang giữ -- trông như tự ý chạy đi sớm dù
                # chưa được lệnh (đã kiểm chứng lỗi này qua headless sim).
                self.immediate_stop[i] = False
                self.yield_flag[i] = False
                self.conflict_with[i] = ''
                continue
            if stop_mask[k]:
                blockers = np.where(higher[k])[0]
                if len(blockers):
                    j = blockers[np.argmin(dist_now[k, blockers])]
                    self.conflict_with[i] = bs.traf.id[idx[j]]
                # Chỉ đặt lệnh vận tốc mục tiêu = 0, để traf.perf tự giảm
                # traf.gs về 0 theo giới hạn giảm tốc thực của tàu bay
                # (không set traf.gs = 0 trực tiếp — sẽ phi vật lý).
                bs.traf.selspd[i] = 0.0
                bs.traf.swvnavspd[i] = False
            else:
                # Cạnh xuống (vừa hết xung đột): phục hồi tốc độ taxi danh
                # định đúng một lần, tránh ghi đè liên tục lên selspd.
                if self.yield_flag[i] or self.immediate_stop[i]:
                    bs.traf.selspd[i] = self.taxi_spd[i]
                    bs.traf.swvnavspd[i] = False
                self.conflict_with[i] = ''

        self.immediate_stop[idx] = immediate & bs.traf.swlnav[idx]
        self.yield_flag[idx] = yield_now & bs.traf.swlnav[idx]

    def _release(self, idx):
        ''' n == 1: không còn ai để xung đột, xoá mọi cờ yield. '''
        for i in idx:
            if (self.yield_flag[i] or self.immediate_stop[i]) and bs.traf.swlnav[i]:
                bs.traf.selspd[i] = self.taxi_spd[i]
            self.yield_flag[i] = False
            self.immediate_stop[i] = False
            self.conflict_with[i] = ''
