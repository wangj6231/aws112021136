#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
永康交流道 (319K) 門架判定邏輯——本地驗證測試腳本
功能：
1. 模擬 M06A 原始 CSV 資料集 (含 7 種代表性旅次：上交流道、下交流道、直行、無關路段等)
2. 在本地離線執行過濾與分類邏輯，並印出格式化結果
3. 用以證明此演算法的正確性與精準度
"""

import csv
import io

# 永康交流道前後的主線收費門架定義
NORTH_GATE_S = "01F3185S"
NORTH_GATE_N = "01F3185N"
SOUTH_GATE_S = "01F3227S"
SOUTH_GATE_N = "01F3227N"

def get_gantry_list(trip_info):
    """解析 TripInformation，回傳車輛依序經過的門架編號列表"""
    gantry_list = []
    if not trip_info:
        return gantry_list
    for item in trip_info.split(';'):
        item = item.strip() # 去除空間
        if not item:
            continue
        parts = item.rsplit('+', 1) # 使用 '+' 分割
        if len(parts) == 2:
            gantry_list.append(parts[1].strip())
    return gantry_list

def classify_yongkang_trip(gantry_list):
    """
    判定車流方向與在永康交流道 (319K) 的行為類型
    回傳值：(direction, travel_type)
    - direction: 'N' (北上) 或 'S' (南下)
    - travel_type: 'entering' (上交流道), 'exiting' (下交流道), 'passing' (直行過境)
    """
    if not gantry_list:
        return None, None

    # 第一個門架方向判定
    first_gantry = gantry_list[0]
    direction = 'S' if first_gantry.endswith('S') else 'N'

    # 確認是否有行經永康區間
    has_north_gate = any(g in gantry_list for g in [NORTH_GATE_S, NORTH_GATE_N])
    has_south_gate = any(g in gantry_list for g in [SOUTH_GATE_S, SOUTH_GATE_N])

    if not (has_north_gate or has_south_gate):
        return None, None

    # 校正方向
    if NORTH_GATE_S in gantry_list or SOUTH_GATE_S in gantry_list:
        direction = 'S'
    elif NORTH_GATE_N in gantry_list or SOUTH_GATE_N in gantry_list:
        direction = 'N'

    # 南下邏輯
    if direction == 'S':
        if NORTH_GATE_S in gantry_list and SOUTH_GATE_S in gantry_list:
            idx_north = gantry_list.index(NORTH_GATE_S)
            idx_south = gantry_list.index(SOUTH_GATE_S)
            if idx_north < idx_south:
                return 'S', 'passing'
        if gantry_list[-1] == NORTH_GATE_S:
            return 'S', 'exiting'
        if gantry_list[0] == SOUTH_GATE_S:
            return 'S', 'entering'

    # 北上邏輯
    else:
        if SOUTH_GATE_N in gantry_list and NORTH_GATE_N in gantry_list:
            idx_south = gantry_list.index(SOUTH_GATE_N)
            idx_north = gantry_list.index(NORTH_GATE_N)
            if idx_south < idx_north:
                return 'N', 'passing'
        if gantry_list[-1] == SOUTH_GATE_N:
            return 'N', 'exiting'
        if gantry_list[0] == NORTH_GATE_N:
            return 'N', 'entering'

    return None, None

# --- 模擬測試資料庫 (Mock M06A CSV) ---
MOCK_M06A_CSV = """VehicleType,DerectionTime_O,GantryID_O,DerectionTime_D,GantryID_D,TripLength,TripEnd,TripInformation
31,2026-03-10 12:00:00,01F3227S,2026-03-10 12:30:00,01F3560S,35.2,Y,2026-03-10 12:00:00+01F3227S; 2026-03-10 12:15:00+01F3298S; 2026-03-10 12:30:00+01F3560S
31,2026-03-10 12:00:00,01F2500S,2026-03-10 12:15:00,01F3185S,15.5,Y,2026-03-10 12:00:00+01F2500S; 2026-03-10 12:15:00+01F3185S
31,2026-03-10 12:00:00,01F2500S,2026-03-10 12:30:00,01F3560S,50.1,Y,2026-03-10 12:00:00+01F2500S; 2026-03-10 12:10:00+01F3185S; 2026-03-10 12:20:00+01F3227S; 2026-03-10 12:30:00+01F3560S
31,2026-03-10 12:00:00,01F3185N,2026-03-10 12:30:00,01F2500N,30.5,Y,2026-03-10 12:00:00+01F3185N; 2026-03-10 12:30:00+01F2500N
31,2026-03-10 12:00:00,01F3560N,2026-03-10 12:15:00,01F3227N,20.2,Y,2026-03-10 12:00:00+01F3560N; 2026-03-10 12:15:00+01F3227N
31,2026-03-10 12:00:00,01F3560N,2026-03-10 12:30:00,01F2500N,50.1,Y,2026-03-10 12:00:00+01F3560N; 2026-03-10 12:10:00+01F3227N; 2026-03-10 12:20:00+01F3185N; 2026-03-10 12:30:00+01F2500N
31,2026-03-10 12:00:00,01F0500S,2026-03-10 12:10:00,01F0600S,10.0,Y,2026-03-10 12:00:00+01F0500S; 2026-03-10 12:10:00+01F0600S
"""

# 測試案例預期結果對照表
EXPECTED_RESULTS = {
    0: ("S", "entering", "南下上交流道"),
    1: ("S", "exiting",  "南下下交流道"),
    2: ("S", "passing",  "南下直行過境"),
    3: ("N", "entering", "北上上交流道"),
    4: ("N", "exiting",  "北上下交流道"),
    5: ("N", "passing",  "北上直行過境"),
    6: (None, None,      "無關路段(應被過濾)")
}

def run_test():
    print("======================================================================")
    print(" [Start] 開始執行永康交流道 (319K) 門架判定邏輯本地測試")
    print("======================================================================")
    
    csv_file = io.StringIO(MOCK_M06A_CSV.strip())
    reader = csv.reader(csv_file)
    next(reader) # 跳過表頭
    
    passed_tests = 0
    total_tests = 7
    
    for idx, row in enumerate(reader):
        trip_info = row[7]
        gantry_list = get_gantry_list(trip_info)
        direction, travel_type = classify_yongkang_trip(gantry_list)
        
        expected_dir, expected_type, chinese_desc = EXPECTED_RESULTS[idx]
        
        # 驗證是否符合預期
        status = "[FAIL] 失敗"
        if direction == expected_dir and travel_type == expected_type:
            status = "[PASS] 成功"
            passed_tests += 1
            
        print(f"\n[Test Case {idx + 1}] 行經路徑: {trip_info}")
        print(f"   -> 預期結果: 方向={expected_dir}, 類型={expected_type} ({chinese_desc})")
        print(f"   -> 判定結果: 方向={direction}, 類型={travel_type}")
        print(f"   -> 測試狀態: {status}")
        
    print("\n======================================================================")
    print(f" [Summary] 測試結果彙整: 共執行 {total_tests} 個案例，成功 {passed_tests} 個，失敗 {total_tests - passed_tests} 個。")
    if passed_tests == total_tests:
        print(" [SUCCESS] 恭喜！判定演算法 100% 正確！已具備上傳 AWS CloudShell 執行的完美條件！")
    else:
        print(" [WARNING] 部分案例未通過，請檢查邏輯演算法。")
    print("======================================================================")

if __name__ == "__main__":
    run_test()
