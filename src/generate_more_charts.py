import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# 設定字體以支援中文 (Windows)
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

def main():
    csv_path = r"C:\Users\milo9\Desktop\aws112021136\database.csv"
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    
    # 確保資料型態正確
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df['day_of_week'] = df['date'].dt.day_name()
    df['hour_of_day'] = df['hour_of_day'].astype(int)
    
    output_dir = r"C:\Users\milo9\Desktop\aws112021136\src"
    os.makedirs(output_dir, exist_ok=True)

    # 1. 每小時車流熱力圖 (Heatmap)
    plt.figure(figsize=(12, 6))
    # 將星期排序
    cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=cats, ordered=True)
    heatmap_data = df.groupby(['day_of_week', 'hour_of_day'])['trip_count'].sum().unstack()
    sns.heatmap(heatmap_data, cmap="YlOrRd", annot=False, fmt=".0f", linewidths=.5)
    plt.title("永康交流道 - 週間各時段車流熱力圖", fontsize=16)
    plt.xlabel("小時 (0-23)", fontsize=12)
    plt.ylabel("星期", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_hourly_heatmap.png"), dpi=300)
    plt.close()

    # 2. 方向與進出狀態圓餅圖 (Pie Chart)
    plt.figure(figsize=(10, 6))
    # 結合 direction 與 travel_type
    df['dir_travel'] = df['direction'] + " - " + df['travel_type']
    pie_data = df.groupby('dir_travel')['trip_count'].sum().sort_values(ascending=False)
    
    # 替換為中文標籤
    label_map = {
        'S - passing': '南下 - 通過主線',
        'N - passing': '北上 - 通過主線',
        'S - exiting': '南下 - 出口',
        'N - exiting': '北上 - 出口',
        'S - entering': '南下 - 入口',
        'N - entering': '北上 - 入口'
    }
    labels = [label_map.get(k, k) for k in pie_data.index]
    
    plt.pie(pie_data, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("Set3"))
    plt.title("交流道方向與進出流量比例", fontsize=16)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_direction_pie.png"), dpi=300)
    plt.close()

    # 3. 車種總量長條圖 (Bar Chart)
    plt.figure(figsize=(10, 6))
    vt_data = df.groupby('vehicle_type')['trip_count'].sum().sort_values(ascending=False)
    
    vt_map = {
        31: "小客車(31)",
        32: "小貨車(32)",
        41: "大客車(41)",
        42: "大貨車(42)",
        5: "聯結車(5)"
    }
    vt_data.index = [vt_map.get(k, str(k)) for k in vt_data.index]
    
    sns.barplot(x=vt_data.values, y=vt_data.index, palette="viridis")
    plt.title("各車種總流量統計", fontsize=16)
    plt.xlabel("總車流筆數", fontsize=12)
    plt.ylabel("車種", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_vehicle_type_bar.png"), dpi=300)
    plt.close()

    # 4. 每日總車流折線圖 (Line Chart)
    plt.figure(figsize=(14, 5))
    daily_trend = df.groupby('date')['trip_count'].sum()
    plt.plot(daily_trend.index, daily_trend.values, marker='o', linestyle='-', color='#d62728', markersize=4)
    plt.title("每日總車流趨勢 (12 週)", fontsize=16)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("總車流量", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_daily_trend.png"), dpi=300)
    plt.close()

    print("Charts generated successfully.")

if __name__ == "__main__":
    main()
