import time
from pathlib import Path
import sys

import pandas as pd
import pydeck as pdk
from sqlalchemy import create_engine
import streamlit as st

from pipeline.config import DATABASE_URL

# Page Configuration
st.set_page_config(page_title="Live Transit Tracker", layout="wide")
st.title("Real-Time Fleet Tracking Dashboard")

# Cached Connection Engine
@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL)

engine = get_db_engine()

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

# Setup an auto-refresh container loop
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 3)

# Placeholders for layout metrics and map canvas
metrics_placeholder = st.empty()
map_placeholder = st.empty()

while True:
    # Query PostgreSQL using window function
    query = """
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
    """

    df = pd.read_sql(query, con=engine)
        
    # Update the Dashboard Visual Elements
    if not df.empty:
        # Update metrics box
        with metrics_placeholder.container():
            st.metric(label="Active Fleet Count", value=len(df))
            
        # Build Geospatial Mapping Layer (PyDeck)
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
            get_color="[255, 100, 0, 160]",
            get_radius=150,
            pickable=True
        )
        
        # Render using stateful view container variable
        with map_placeholder.container():
            st.pydeck_chart(pdk.Deck(
                layers=[layer], 
                # Passing the session_state object blocks the engine from resetting coordinates
                initial_view_state=st.session_state.map_view,
                tooltip={"text": "Route: {route_id} | Car ID: {vehicle_id}"}
            ))

    # Sleep until the next refresh pulse
    time.sleep(refresh_rate)