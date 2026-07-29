from pathlib import Path
import sys
import pandas as pd
import pydeck as pdk
from sqlalchemy import create_engine
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from pipeline.config import DATABASE_URL

# Page Configuration
st.set_page_config(page_title="Live Transit Tracker", layout="wide")
st.title("Real-Time Fleet Tracking Dashboard")

# Cached Connection Engine
@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL)

engine = get_db_engine()

# Initialize viewport once to preserve pan/zoom upon updates
if "map_view" not in st.session_state:
    st.session_state.map_view = pdk.ViewState(
        latitude=60.1699,  # Default center for HSL / Helsinki region
        longitude=24.9384,
        zoom=12,
        pitch=0,
        bearing=0,
    )

# Sidebar auto-refresh configuration
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 3)

# Static containers outside the fragment to prevent page layout redraws
metric_container = st.empty()
map_container = st.empty()


# Streamlit Fragment auto-refreshes data without triggering a full page redraw
@st.fragment(run_every=refresh_rate)
def render_live_dashboard():
    query = """
        SELECT DISTINCT ON (vehicle_id)
            route_id,
            vehicle_id,
            latitude,
            longitude,
            timestamp
        FROM tram_telemetry
        ORDER BY vehicle_id, timestamp DESC;
    """

    df = pd.read_sql(query, con=engine)

    if df.empty:
        st.warning("No active fleet telemetry recorded yet.")
        return

    # Update metric quietly in its designated static slot
    metric_container.metric(label="Active Fleet Count", value=len(df))

    # Build PyDeck mapping layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position="[longitude, latitude]",
        get_color="[59, 202, 46, 255]",
        get_radius=80,
        pickable=True,
    )

    with map_container:
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=st.session_state.map_view,
                tooltip={"text": "Route: {route_id} | Vehicle ID: {vehicle_id}"},
            ),
            key="live_tram_map",
            use_container_width=True,
        )

# Execute the fragment
render_live_dashboard()