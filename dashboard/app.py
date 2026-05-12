import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
import numpy as np
from datetime import datetime

def ensure_data():
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "logistics.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if not os.path.exists(db_path):
        print("📦 Генерация данных для облака...")
        np.random.seed(42)
        n = 5000
        df = pd.DataFrame({
            'order_id': range(1, n+1),
            'order_date': pd.date_range('2024-01-01', periods=n, freq='H'),
            'warehouse_id': np.random.choice(['WH_Moscow','WH_SPb','WH_Kazan'], n),
            'destination_city': np.random.choice(['Moscow','SPb','Kazan','Ekaterinburg'], n),
            'distance_km': np.random.exponential(300, n).round(1),
            'carrier': np.random.choice(['CDEK','Boxberry','PickPoint','Russian Post'], n),
            'estimated_delivery_days': np.random.randint(1, 6, n),
            'weight_kg': np.random.exponential(2.5, n).round(2),
            'delivered': np.random.choice([True, False], n, p=[0.92, 0.08])
        })
        df['freight_cost'] = df['distance_km']*12*(1+df['weight_kg']*0.1)
        df['actual_delivery_days'] = df['estimated_delivery_days'] + np.random.choice([0,1,2,3], n, p=[0.8,0.1,0.07,0.03])
        df['delay_days'] = np.maximum(0, df['actual_delivery_days'] - df['estimated_delivery_days'])
        conn = sqlite3.connect(db_path)
        df.to_sql('deliveries', conn, index=False, if_exists='replace')
        conn.close()

ensure_data()
st.set_page_config(page_title="🚚 Logistics Analytics", layout="wide")
st.title("🚚 Logistics Delay Analytics & Route Optimization")

@st.cache_data
def load_data():
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "logistics.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM deliveries", conn)
    conn.close()
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df

df = load_data()

st.sidebar.header("🔍 Фильтры")
carriers = st.sidebar.multiselect("Перевозчик", df['carrier'].unique(), df['carrier'].unique())
warehouses = st.sidebar.multiselect("Склад", df['warehouse_id'].unique(), df['warehouse_id'].unique())
date_range = st.sidebar.date_input("Период", [df['order_date'].min(), df['order_date'].max()])

filtered = df[
    (df['carrier'].isin(carriers)) & 
    (df['warehouse_id'].isin(warehouses)) &
    (df['order_date'] >= pd.to_datetime(date_range[0])) &
    (df['order_date'] <= pd.to_datetime(date_range[1]))
]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Заказов", f"{len(filtered):,}")
c2.metric("On-time", f"{(filtered['delay_days']<=0).mean()*100:.1f}%")
c3.metric("Ср. задержка", f"{filtered['delay_days'].mean():.1f} д.")
c4.metric("Ср. стоимость", f"{filtered['freight_cost'].mean():.0f} ₽")

st.subheader("📊 On-time delivery по перевозчикам")
carrier_perf = filtered.groupby('carrier').agg(
    orders=('order_id','count'),
    on_time_pct=('delay_days', lambda x: (x<=0).mean()*100),
    avg_delay=('delay_days','mean')
).reset_index()
st.plotly_chart(px.bar(carrier_perf, x='carrier', y='on_time_pct', color='avg_delay',
                       title="On-time % (цвет = ср. задержка)", labels={'on_time_pct':'On-time %'}), use_container_width=True)

st.subheader("🗺️ Задержки по маршрутам")
route_map = filtered.groupby(['warehouse_id','destination_city']).agg(avg_delay=('delay_days','mean')).reset_index().dropna()
st.plotly_chart(px.density_heatmap(route_map, x='destination_city', y='warehouse_id', z='avg_delay',
                                   title="Средняя задержка (дней)", color_continuous_scale='RdYlGn_r'), use_container_width=True)