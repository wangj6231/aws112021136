import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

def main():
    csv_path = r"C:\Users\milo9\Desktop\aws112021136\database.csv"
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'] >= 5
    df['hour_of_day'] = df['hour_of_day'].astype(int)
    
    output_dir = r"C:\Users\milo9\Desktop\aws112021136\src"

    # 5. 平假日每小時車流對比圖
    plt.figure(figsize=(10, 6))
    wk_data = df.groupby(['is_weekend', 'hour_of_day'])['trip_count'].mean().unstack(level=0)
    plt.plot(wk_data.index, wk_data[False], marker='o', label="平日 (Weekday)", color="blue")
    plt.plot(wk_data.index, wk_data[True], marker='o', label="假日 (Weekend)", color="orange")
    plt.title("平假日 - 24小時車流分佈對比", fontsize=16)
    plt.xlabel("小時 (0-23)", fontsize=12)
    plt.ylabel("平均車流量", fontsize=12)
    plt.xticks(range(0, 24))
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_weekend_vs_weekday.png"), dpi=300)
    plt.close()

    # 6. 大貨車/聯結車 專屬趨勢圖
    plt.figure(figsize=(12, 5))
    trucks = df[df['vehicle_type'].isin([42, 5])]
    truck_trend = trucks.groupby('date')['trip_count'].sum()
    plt.plot(truck_trend.index, truck_trend.values, linestyle='-', color='purple')
    plt.title("重型工業車輛 (大貨車+聯結車) - 每日車流趨勢", fontsize=16)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("重車總量", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_trucks_daily.png"), dpi=300)
    plt.close()

if __name__ == "__main__":
    main()
