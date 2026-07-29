from pathlib import Path
import sys
import pandas as pd
import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine
import queries
from components.metrics import render_kpis
from components.maps import render_fleet_map
from components.charts import render_route_table

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from pipeline.config import DATABASE_URL

st.set_page_config(
    page_title="Helsinki Transit Operations Hub",
    page_icon="🚌",
    layout="wide",
)

# Cached Connection Engine
@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL)

engine = get_db_engine()

# Map Viewport State Preservation
if "map_view" not in st.session_state:
    st.session_state.map_view = pdk.ViewState(
        latitude=60.1699,  # Helsinki Center
        longitude=24.9384,
        zoom=12,
        pitch=0,
        bearing=0,
    )

# Sidebar controls
with st.sidebar:
    st.header("🎛️ Control Panel")
    refresh_rate = st.slider("Live Refresh Rate (seconds)", 1, 10, 3)
    
    st.divider()
    st.markdown("### Map Legend")
    st.markdown("🟢  **On-Time**")
    st.markdown("🟡  **Minor Delay**")
    st.markdown("🔴  **Major Delay**")

# Dashboard header
st.title("🚌 Helsinki Transit Operations Hub")
st.caption("Real-time telemetry, spatial fleet monitoring, and delay analysis pipeline.")
st.divider()

# Persistent slots
kpi_slot = st.empty()
map_slot = st.empty()

st.divider()

# Analytical tabs 
st.subheader("📊 Current Delay & Active Fleet Metrics by Route")
routes_slot = st.empty()


# Fast live fragment (Map & KPIs)
@st.fragment(run_every=refresh_rate)
def render_live_fleet_view():
    df = queries.fetch_latest_fleet_positions(engine)
    render_kpis(kpi_slot, df)
    render_fleet_map(map_slot, df, st.session_state.map_view)


# Slow analytics
@st.fragment(run_every=30)
def render_analytics_views():
    route_df = queries.fetch_route_delay_breakdown(engine)
    render_route_table(routes_slot, route_df)

# Execute fragments
render_live_fleet_view()
render_analytics_views() 