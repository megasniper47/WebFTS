""" DepArrFinalAlert — Cảnh báo cự ly giữa tàu bay khởi hành đã rời đất và
tàu bay hạ cánh đang trên final.

Chỉ xét cặp (DEP đã cất cánh, ARR đang trên final) — KHÔNG bao giờ cảnh báo
giữa 2 tàu bay đang ở trên mặt đất (loại trừ tự nhiên vì cả 2 điều kiện lọc
dưới đây đều yêu cầu tàu bay đang bay, alt > 0):
    - DEP: callsign bắt đầu "DEP" và cao độ đã vượt ngưỡng rời đất.
    - ARR: callsign bắt đầu "ARR" và cao độ dưới ngưỡng "trên final".
Nếu cự ly ngang giữa 1 cặp (DEP, ARR) như trên < dep_arr_alert_nm (mặc định
3NM) thì đánh dấu CẢ HAI đang "in conflict".

Ghi kết quả trực tiếp vào bs.traf.cd.inconf/tcpamax -- đây là đúng 2 mảng mà
hệ thống ASAS gốc của BlueSky dùng, và pipeline ACDATA -> Socket.IO ->
frontend (ConflictsPanel, AircraftRenderer tô màu tàu bay trên bản đồ) ĐÃ
CÓ SẴN, đọc thẳng 2 mảng này -- nên không cần sửa gì ở frontend. An toàn vì
kịch bản luôn chạy "ASAS OFF" (chọn CD method cơ sở, không làm gì với 2 mảng
này), nên plugin này là bên viết duy nhất vào đó.
"""
import numpy as np

import bluesky as bs
from bluesky import core, settings
from bluesky.tools import geo
from bluesky.tools.aero import ft

settings.set_variable_defaults(
    dep_arr_alert_dt=1.0,             # chu kỳ kiểm tra [s]
    dep_arr_alert_nm=3.0,             # ngưỡng cảnh báo cự ly ngang [NM]
    dep_arr_alert_liftoff_ft=400.0,   # cao độ coi là "đã rời đất" [ft], theo mốc pha TO/IC của BADA
    dep_arr_alert_final_ft=3000.0,    # cao độ coi là "đang trên final" [ft], ~mốc 10NM cuối trên approach
)


def init_plugin():
    ''' Khởi tạo plugin — bắt buộc phải có hàm này để BlueSky nhận diện file
        là một plugin. '''
    global depalert
    depalert = DepArrFinalAlert()

    config = {
        'plugin_name': 'DEPARRALERT',
        'plugin_type': 'sim',
    }
    return config


class DepArrFinalAlert(core.Entity):
    ''' Cảnh báo phân cách giữa tàu bay vừa cất cánh và tàu bay đang hạ cánh trên final. '''

    @core.timed_function(name='deparralert', dt=settings.dep_arr_alert_dt)
    def update(self):
        n = bs.traf.ntraf
        # Luôn xoá cờ cũ trước -- đây là mảng "tính lại từ đầu mỗi chu kỳ",
        # không phải mảng "sticky" như confpairs của ASAS gốc, nên cặp không
        # còn vi phạm phải được giải phóng ngay (đèn báo tắt khi hết cảnh báo).
        bs.traf.cd.inconf[:] = False
        if n < 2:
            return

        ids = bs.traf.id
        alt_ft = bs.traf.alt / ft
        is_dep = np.array([cs.startswith('DEP') for cs in ids])
        is_arr = np.array([cs.startswith('ARR') for cs in ids])

        dep_idx = np.where(is_dep & (alt_ft > settings.dep_arr_alert_liftoff_ft))[0]
        arr_idx = np.where(is_arr & (alt_ft > 0.0) & (alt_ft < settings.dep_arr_alert_final_ft))[0]
        if len(dep_idx) == 0 or len(arr_idx) == 0:
            return

        for i in dep_idx:
            lat_i, lon_i = bs.traf.lat[i], bs.traf.lon[i]
            alt_i = alt_ft[i]
            for j in arr_idx:
                d_nm = geo.kwikdist(lat_i, lon_i, bs.traf.lat[j], bs.traf.lon[j])
                d_alt_ft = abs(alt_i - alt_ft[j])
                # Cảnh báo nếu cách nhau < 3NM chiều ngang VÀ < 1000ft chiều dọc (phân cách tiêu chuẩn ICAO)
                if d_nm < settings.dep_arr_alert_nm and d_alt_ft < 1000.0:
                    bs.traf.cd.inconf[i] = True
                    bs.traf.cd.inconf[j] = True
                    bs.traf.cd.tcpamax[i] = 0.0
                    bs.traf.cd.tcpamax[j] = 0.0
