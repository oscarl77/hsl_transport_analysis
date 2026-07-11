import time
import duckdb
import streamlit as st
import pydeck as pdk
import sys
from pathlib import Path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
from pipeline import config

# 1. Page Configuration
st.set_page_config(page_title="Live Transit Tracker", layout="wide")
st.title("Real-Time Fleet Tracking Dashboard")

# This ensures it is only created ONCE when the browser tab boots up,
# and is never overwritten when new tram coordinates stream in.
if "map_view" not in st.session_state:
    st.session_state.map_view = pdk.ViewState(
        latitude=61.4978,   # Default center latitude
        longitude=23.7610,  # Default center longitude
        zoom=12,
        pitch=0,
        bearing=0
    )

# 2. Setup an auto-refresh container loop
# Streamlit will re-run this script block at a set interval to grab new data
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 3)

# Placeholders for our layout metrics and map canvas
metrics_placeholder = st.empty()
map_placeholder = st.empty()

while True:
    # 3. Read the latest positions from DuckDB
    conn = duckdb.connect(str(config.DB_PATH), read_only=True)
    try:
        # Window function query: Grab only the absolute latest timestamp for each distinct route_id
        df = conn.sql("""
            WITH latest_positions AS (
                SELECT 
                    route_id,
                    vehicle_id,
                    latitude,
                    longitude,
                    timestamp,
                    ROW_NUMBER() OVER(PARTITION BY vehicle_id ORDER BY timestamp DESC) as rn
                FROM tram_telemetry
            )
            SELECT route_id, vehicle_id, latitude, longitude, timestamp
            FROM latest_positions
            WHERE rn = 1;
        """).df() # Convert directly to a standard Pandas DataFrame for PyDeck
    finally:
        conn.close()
        
    # 4. Update the Dashboard Visual Elements
    if not df.empty:
        # Update metrics box
        with metrics_placeholder.container():
            st.metric(label="Active Fleet Count", value=len(df))
            
        # 5. Build the Geospatial Mapping Layer (PyDeck)
        # We define a ScatterplotLayer to draw circles at the latitude/longitude points
        view_state = pdk.ViewState(
            latitude=df["latitude"].mean(),
            longitude=df["longitude"].mean(),
            zoom=12,
            pitch=0
        )
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            df,
            get_position="[longitude, latitude]",
            get_color="[255, 100, 0, 160]", # Bright transit orange
            get_radius=150,                 # Size of the marker in meters
            pickable=True
        )
        
        # Render using our stateful view container variable
        with map_placeholder.container():
            st.pydeck_chart(pdk.Deck(
                layers=[layer], 
                # Passing the session_state object blocks the engine from resetting coordinates
                initial_view_state=st.session_state.map_view,
                tooltip={"text": "Route: {route_id} | Car ID: {vehicle_id}"}
            ))

        
            
    # Sleep until the next refresh pulse
    time.sleep(refresh_rate)