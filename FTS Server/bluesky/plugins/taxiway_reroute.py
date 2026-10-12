""" TaxiwayReroute — tự động chọn đường lăn ra (E hoặc D) cho tàu bay cất
cánh, dựa trên TÍNH TOÁN xem tàu bay đó có khả năng "gặp nhau" (đối đầu) với
một tàu bay hạ cánh đang lăn về bến trên đoạn đường lăn E hay không.

Cơ chế:
    - Đoạn đường lăn E xung đột được định nghĩa bằng 1 đoạn thẳng (2 điểm
      toạ độ) trong settings.
    - Lệnh stack TAXIROUTE <acid> tính "cửa sổ thời gian" acid sẽ chiếm đoạn
      E NẾU đi theo lộ trình chuẩn (đường lăn E): ETA tới đầu gần của đoạn
      và ETA tới đầu xa, dựa trên tốc độ lăn danh định (acid còn đứng yên
      tại bến lúc gọi lệnh này, nên KHÔNG dùng gs=0 hiện tại của nó).
    - Tương tự tính cửa sổ thời gian của MỌI tàu bay hạ cánh đang lăn trên
      mặt đất (callsign bắt đầu "ARR", đã chạm đất, còn di chuyển thật).
    - Nếu 2 cửa sổ giao nhau (có biên an toàn) => dự đoán 2 tàu sẽ gặp nhau
      trên đoạn E => PCALL lộ trình thay thế (đường lăn D) cho acid ngay lập
      tức. Nếu không => PCALL lộ trình chuẩn (đường lăn E).

QUAN TRỌNG VỀ THỜI ĐIỂM GỌI: TAXIROUTE phải được gọi TRỰC TIẾP, ĐỒNG BỘ từ
kịch bản .scn ngay sau CRE+TAXION (cùng một dòng lệnh tại t=0), KHÔNG được
để plugin tự "quét" tìm tàu bay mới qua timed_function định kỳ -- bản đầu
tiên của plugin này làm vậy và có lỗi thật: TAXION đặt tốc độ 15kt ngay lập
tức trong khi tàu bay CHƯA có route/LNAV (vẫn giữ đúng hướng đỗ tại bến), nên
trong khoảng thời gian chờ tới lượt quét kế tiếp (tối đa 1 chu kỳ dt), tàu
bay trôi thẳng theo hướng đỗ -- đã được người dùng phát hiện qua quan sát
trực tiếp (tàu bay "đi thẳng luôn" khi vừa xuất hiện). Gọi TAXIROUTE đồng bộ
ngay sau TAXION loại bỏ hoàn toàn khoảng hở này (route được gán trong cùng
1 lượt xử lý lệnh, không có bước nào tàu bay có tốc độ mà chưa có route).

Việc PCALL từ trong 1 stack.command (không phải từ trong 1 file .scn được
gọi qua Condition) hoàn toàn không liên quan đến cơ chế Condition
(ATDIST/ATALT) của BlueSky nên không có rủi ro lỗi đăng ký Condition lồng
nhau đã phát hiện trong phiên làm việc trước.
"""
import bluesky as bs
from bluesky import core, stack, settings
from bluesky.tools import geo
from bluesky.tools.aero import ft

settings.set_variable_defaults(
    taxiway_e_seg_a_lat=16.049407, taxiway_e_seg_a_lon=108.200982,
    taxiway_e_seg_b_lat=16.052437, taxiway_e_seg_b_lon=108.200543,
    taxiway_conflict_margin_s=20.0,       # biên an toàn [s] khi so 2 cửa sổ thời gian
    taxiway_nominal_taxi_kt=15.0,         # tốc độ lăn danh định [kt] dùng để dự đoán ETA của
                                           # CHÍNH tàu bay cất cánh (nó còn đứng yên tại bến,
                                           # chưa có tốc độ thật -- không thể dùng gs hiện tại
                                           # =0 để ước lượng ETA của chính nó được)
    taxiway_normal_taxi_file='DEP_TAXI_TO_HOLD',       # lộ trình chuẩn (đường lăn E)
    taxiway_alt_taxi_file='DEP_TAXI_TO_HOLD_ALT_D',    # lộ trình thay thế (đường lăn D)
)


def init_plugin():
    ''' Khởi tạo plugin — bắt buộc phải có hàm này để BlueSky nhận diện file
        là một plugin. '''
    global reroute
    reroute = TaxiwayReroute()

    config = {
        'plugin_name': 'TAXIWAYREROUTE',
        'plugin_type': 'sim',
    }
    return config


class TaxiwayReroute(core.Entity):
    ''' Chọn đường lăn ra (E hoặc D) cho tàu bay cất cánh, dựa trên dự đoán
        xung đột đối đầu với tàu bay hạ cánh trên đoạn đường lăn E. '''

    @stack.command(name='TAXIROUTE')
    def taxi_route(self, acidx: 'acid', normal_file: 'txt' = '', alt_file: 'txt' = ''):
        ''' TAXIROUTE acid [normalfile] [altfile]

            Gọi NGAY SAU TAXION (cùng thời điểm, đồng bộ) để tính toán và
            PCALL đúng 1 trong 2 lộ trình lăn ra (chuẩn/đường E, hoặc thay
            thế/đường D) cho acid.

            normalfile/altfile (tuỳ chọn): tên file .scn cụ thể cho acid này
            (vd. có nhiều biến thể lộ trình chuẩn khác nhau theo bến đỗ/hàng
            đợi PRE_HOLD hay RWYHOLD trực tiếp) -- nếu bỏ trống thì dùng
            settings.taxiway_normal_taxi_file / taxiway_alt_taxi_file mặc
            định (giữ nguyên hành vi cũ, tương thích ngược). '''
        acid = bs.traf.id[acidx]
        normal = normal_file or settings.taxiway_normal_taxi_file
        alt = alt_file or settings.taxiway_alt_taxi_file
        if self._predict_head_on_conflict(acidx):
            stack.stack(f'PCALL {alt} {acid}')
            stack.stack(f'ECHO {acid}: dự đoán gặp tàu bay hạ cánh đối đầu trên '
                        f'đường lăn E -> đổi sang đường lăn D')
            return True, f'{acid}: taxi route = D (alternate, conflict predicted)'
        stack.stack(f'PCALL {normal} {acid}')
        return True, f'{acid}: taxi route = E (normal)'

    def _predict_head_on_conflict(self, dep_idx):
        # Tàu bay cất cánh còn đứng yên tại bến (gs=0) lúc ra quyết định --
        # KHÔNG dùng gs hiện tại của nó (luôn =0, vô nghĩa để dự đoán), mà
        # dùng tốc độ lăn danh định (nó SẮP lăn với tốc độ này ngay sau khi
        # được cấp lộ trình, do chính lệnh TAXIROUTE này cấp).
        nominal_gs = settings.taxiway_nominal_taxi_kt * 0.514444
        dep_window = self._eta_window(dep_idx, override_gs=nominal_gs)
        if dep_window is None:
            return False
        dep_enter, dep_exit = dep_window

        ids = bs.traf.id
        alt_ft = bs.traf.alt / ft
        for j in range(bs.traf.ntraf):
            if not ids[j].startswith('ARR') or alt_ft[j] > 10.0:
                continue
            arr_window = self._eta_window(j)
            if arr_window is None:
                continue
            arr_enter, arr_exit = arr_window

            margin = settings.taxiway_conflict_margin_s
            if dep_enter <= arr_exit + margin and arr_enter <= dep_exit + margin:
                return True
        return False

    def _eta_window(self, idx, override_gs=None):
        ''' Cửa sổ thời gian [ETA tới đầu gần, ETA tới đầu xa] của tàu bay
            idx đối với đoạn đường lăn E, ước lượng từ vị trí hiện tại và tốc
            độ mặt đất (đường thẳng) -- None nếu không xác định được hướng
            di chuyển sắp tới (đang đứng yên và không có override_gs). '''
        gs = bs.traf.gs[idx] if override_gs is None else override_gs
        if gs < 0.5:
            return None

        lat, lon = bs.traf.lat[idx], bs.traf.lon[idx]
        d_a = geo.kwikdist(lat, lon, settings.taxiway_e_seg_a_lat, settings.taxiway_e_seg_a_lon) * 1852.0
        d_b = geo.kwikdist(lat, lon, settings.taxiway_e_seg_b_lat, settings.taxiway_e_seg_b_lon) * 1852.0
        near_d, far_d = (d_a, d_b) if d_a <= d_b else (d_b, d_a)
        return near_d / gs, far_d / gs
