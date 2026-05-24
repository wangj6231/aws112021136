#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AWS CloudShell 專用大數據過濾腳本 (TDCS M06A 永康交流道分析) - 斷點續傳版
功能：
1. 自動篩選 S3 中 2026/04/26 至 2026/05/23 之間的原始 CSV 與 Tar.gz 檔案
2. 線上串流讀取 (Direct S3 Streaming)，免去下載至本地磁碟，速度極快且免費
3. 【強大優化】自動秒速檢查 S3，跳過已處理檔案，若 CloudShell 暫停，重新執行即可從斷點續傳
4. 儲存於 S3 cleaned-yongkang/date=YYYYMMDD/ 目錄下
"""

import os
import io
import csv
import tarfile
import boto3
from botocore.config import Config

# --- 參數設定 ---
BUCKET_NAME = "freeway-data-112021136"
STUDENT_ID = "112021136"

# 日期限制範圍 (4/26 到 5/23)
START_DATE = "20260426"
END_DATE = "20260523"

# 永康交流道前後的主線收費門架
NORTH_GATE_S = "01F3185S"
NORTH_GATE_N = "01F3185N"
SOUTH_GATE_S = "01F3227S"
SOUTH_GATE_N = "01F3227N"

def get_gantry_list(trip_info):
    """
    解析 TripInformation 欄位，回傳車輛依序經過的門架編號列表
    """
    gantry_list = []
    if not trip_info:
        return gantry_list
    for item in trip_info.split(';'):
        item = item.strip() # 去除兩側空格
        if not item:
            continue
        parts = item.rsplit('+', 1)
        if len(parts) == 2:
            gantry_list.append(parts[1].strip())
    return gantry_list

def classify_yongkang_trip(gantry_list):
    """
    判定車流方向與在永康交流道 (319K) 的行為類型。
    回傳值：(direction, travel_type)
    """
    if not gantry_list:
        return None, None

    first_gantry = gantry_list[0]
    direction = 'S' if first_gantry.endswith('S') else 'N'

    has_north_gate = any(g in gantry_list for g in [NORTH_GATE_S, NORTH_GATE_N])
    has_south_gate = any(g in gantry_list for g in [SOUTH_GATE_S, SOUTH_GATE_N])

    if not (has_north_gate or has_south_gate):
        return None, None

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

def process_tar_gz(s3_client, bucket, key):
    """
    串流讀取單個 S3 中的 tar.gz 壓縮檔，並過濾出永康交流道的數據
    """
    filtered_rows = []
    response = s3_client.get_object(Bucket=bucket, Key=key)
    with tarfile.open(fileobj=response['Body'], mode='r|gz') as tar:
        for member in tar:
            if member.isfile() and member.name.endswith('.csv'):
                f = tar.extractfile(member)
                if f is not None:
                    content = io.TextIOWrapper(f, encoding='utf-8')
                    reader = csv.reader(content)
                    for row in reader:
                        if len(row) < 8:
                            continue
                        trip_info = row[7]
                        gantry_list = get_gantry_list(trip_info)
                        direction, travel_type = classify_yongkang_trip(gantry_list)
                        if travel_type is not None:
                            enriched_row = row + [direction, travel_type]
                            filtered_rows.append(enriched_row)
    return filtered_rows

def process_csv(s3_client, bucket, key):
    """
    直接串流讀取 S3 中的 CSV 檔案，並過濾出永康交流道的數據
    """
    filtered_rows = []
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = io.TextIOWrapper(response['Body'], encoding='utf-8')
    reader = csv.reader(content)
    for row in reader:
        if len(row) < 8:
            continue
        trip_info = row[7]
        gantry_list = get_gantry_list(trip_info)
        direction, travel_type = classify_yongkang_trip(gantry_list)
        if travel_type is not None:
            enriched_row = row + [direction, travel_type]
            filtered_rows.append(enriched_row)
    return filtered_rows

def main():
    config = Config(
        retries={'max_attempts': 10, 'mode': 'standard'},
        connect_timeout=60,
        read_timeout=60
    )
    s3_client = boto3.client('s3', config=config)
    
    print(f"開始搜尋 S3 Bucket: {BUCKET_NAME} 中的原始資料 (日期範圍鎖定: {START_DATE} ~ {END_DATE})...")
    paginator = s3_client.get_paginator('list_objects_v2')
    
    raw_files = []
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                # 排除已經過濾完的資料夾
                if "cleaned-yongkang" in key:
                    continue
                
                if key.endswith('.tar.gz') or key.endswith('.csv'):
                    # 提早解析並判斷日期，決定是否加入處理隊列
                    filename = os.path.basename(key)
                    date_str = None
                    parts = filename.replace('.', '_').split('_')
                    for part in parts:
                        if part.isdigit() and len(part) == 8:
                            date_str = part
                            break
                    if not date_str:
                        path_parts = key.split('/')
                        for part in path_parts:
                            if part.isdigit() and len(part) == 8:
                                date_str = part
                                break
                    
                    # 篩選 4/26 - 5/23 檔案
                    if date_str and (START_DATE <= date_str <= END_DATE):
                        raw_files.append(key)
                    
    print(f"共篩選出 {len(raw_files)} 個位於指定日期範圍內的原始檔案。")
    if not raw_files:
        print(f"在 {START_DATE} 至 {END_DATE} 之間未找到任何原始資料！請檢查檔案是否在 S3 中。")
        return

    # 表頭定義
    headers = [
        "VehicleType", "DerectionTime_O", "GantryID_O", 
        "DerectionTime_D", "GantryID_D", "TripLength", 
        "TripEnd", "TripInformation", "direction", "travel_type"
    ]

    # 逐一處理原始檔案
    success_count = 0
    skipped_count = 0
    
    for idx, key in enumerate(sorted(raw_files), 1):
        filename = os.path.basename(key)
        
        # 提取日期與時間後綴
        date_str = None
        time_str = ""
        parts = filename.replace('.', '_').split('_')
        for part in parts:
            if part.isdigit():
                if len(part) == 8:
                    date_str = part
                elif len(part) == 6:
                    time_str = "_" + part
        
        if not date_str:
            path_parts = key.split('/')
            for part in path_parts:
                if part.isdigit() and len(part) == 8:
                    date_str = part
                    break
        
        if not date_str:
            date_str = f"unknown_{idx}"
            
        output_key = f"cleaned-yongkang/date={date_str}/M06A_Yongkang_{date_str}{time_str}.csv"
        
        # 【核心斷點續傳優化】：檢查 S3 中是否已經存在該處理後的檔案
        try:
            s3_client.head_object(Bucket=BUCKET_NAME, Key=output_key)
            # 檔案存在代表之前已經處理成功，直接跳過！
            skipped_count += 1
            continue
        except Exception:
            # 檔案不存在，正常處理
            pass
            
        print(f"\n[{idx}/{len(raw_files)}] 開始串流處理: {filename} (日期: {date_str})")
        
        try:
            if key.endswith('.tar.gz'):
                filtered_data = process_tar_gz(s3_client, BUCKET_NAME, key)
            else:
                filtered_data = process_csv(s3_client, BUCKET_NAME, key)
                
            print(f"過濾完成！篩選出永康相關旅次: {len(filtered_data)} 筆")
            
            # 寫入 CSV 記憶體
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(headers)
            writer.writerows(filtered_data)
            
            # 上傳回 S3
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=output_key,
                Body=csv_buffer.getvalue().encode('utf-8')
            )
            print(f"成功上傳至: s3://{BUCKET_NAME}/{output_key}")
            success_count += 1
            
        except Exception as e:
            print(f"⚠️ 處理 {key} 時發生錯誤: {str(e)}")
            
    print(f"\n==========================================")
    print(f"斷點續傳大數據過濾任務執行結束！")
    print(f"已跳過已存在檔案: {skipped_count} 個")
    print(f"本次新處理成功檔案: {success_count} 個")
    print(f"現在你可以前往 Amazon Athena 進行極速 SQL 交叉分析了！")
    print(f"==========================================")

if __name__ == "__main__":
    main()
