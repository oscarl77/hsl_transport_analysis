from pathlib import Path
import sys
import pandas as pd
import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine
import queries

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

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    refresh_rate = st.slider("Live Refresh Rate (seconds)", 1, 10, 3)
    
    st.divider()
    st.markdown("### Map Legend")
    st.markdown("🟢  **On-Time**")
    st.markdown("🟡  **Minor Delay**")
    st.markdown("🔴  **Major Delay**")

# --- 3. DASHBOARD HEADER ---
st.title("🚌 Helsinki Transit Operations Hub")
st.caption("Real-time telemetry, spatial fleet monitoring, and delay analysis pipeline.")
st.divider()

# --- 4. PERSISTENT CONTAINER SLOTS (Prevents Page Jitter) ---
kpi_slot = st.empty()
map_slot = st.empty()

st.divider()

# --- 5. ANALYTICAL TABS (Static Workspace Below Map) ---
tab_trends, tab_routes = st.tabs(["📉 3-Hour Delay Trends", "📊 Route Delay Breakdown"])

with tab_trends:
    st.subheader("Network-Wide Average Delay (5-Minute Buckets)")
    trends_slot = st.empty()

with tab_routes:
    st.subheader("Current Delay & Active Fleet Metrics by Route")
    routes_slot = st.empty()


# --- 6. COLOR HELPER FOR MAP ---
def get_delay_color(delay_sec):
    if pd.isna(delay_sec) or delay_sec <= 60:
        return [59, 202, 46, 220]    # Green
    elif delay_sec <= 180:
        return [241, 196, 15, 220]   # Yellow
    else:
        return [231, 76, 60, 220]    # Red


# --- 7. FAST LIVE FRAGMENT (Runs Every N Seconds) ---
@st.fragment(run_every=refresh_rate)
def render_live_fleet_view():
    df = queries.fetch_latest_fleet_positions(engine)

    if df.empty:
        kpi_slot.warning("No active telemetry pings recorded.")
        return

    # A. Render KPI Cards
    total_fleet = len(df)
    avg_delay = df["delay_seconds"].mean() if "delay_seconds" in df.columns else 0
    on_time_count = (df["delay_seconds"] <= 60).sum() if "delay_seconds" in df.columns else 0
    on_time_pct = (on_time_count / total_fleet) * 100 if total_fleet > 0 else 0

    with kpi_slot.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Fleet Count", total_fleet)
        col2.metric("Average Network Delay", f"{int(avg_delay)}s", delta=f"{int(avg_delay)}s", delta_color="inverse")
        col3.metric("On-Time Performance", f"{on_time_pct:.1f}%")

    # B. Prepare and Render Map
    df["color"] = df["delay_seconds"].apply(get_delay_color)

    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position="[longitude, latitude]",
        get_color="color",
        get_radius=30,
        pickable=True,
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=st.session_state.map_view,
        tooltip={"text": "Route: {route_id} | Vehicle: {vehicle_id}\nDelay: {delay_seconds}s | Speed: {speed} km/h"},
    )

    with map_slot:
        st.pydeck_chart(deck, key="live_tram_map", width='stretch')


# --- 8. SLOW ANALYTICS FRAGMENT (Runs Every 30 Seconds) ---
@st.fragment(run_every=30)
def render_analytics_views():
    # A. Render Historical Trends Chart
    trends_df = queries.fetch_network_delay_trends(engine)
    if not trends_df.empty:
        with trends_slot:
            st.line_chart(
                trends_df.set_index("time_bucket")["avg_delay_sec"],
                y_label="Average Delay (Seconds)",
            )

    # B. Render Route Performance Table
    route_df = queries.fetch_route_delay_breakdown(engine)
    if not route_df.empty:
        with routes_slot:
            st.dataframe(
                route_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "route_id": "Route",
                    "active_vehicles": "Active Vehicles",
                    "avg_delay_sec": st.column_config.NumberColumn("Avg Delay (s)", format="%d s"),
                    "max_delay_sec": st.column_config.NumberColumn("Max Delay (s)", format="%d s"),
                },
            )


# Execute fragments
render_live_fleet_view()
render_analytics_views()