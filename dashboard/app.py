# dashboard/app.py
import streamlit as st
from pipeline.database import get_db_engine  # Or your engine getter
from dashboard.queries import fetch_latest_fleet_positions

engine = get_db_engine()

@st.fragment(run_every=3)
def render_map():
    # Calling the function that loads & executes the SQL file under the hood
    df = fetch_latest_fleet_positions(engine)
    
    if not df.empty:
        # Render map using returned DataFrame
        st.write(df)

render_map()