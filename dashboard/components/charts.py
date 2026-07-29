import streamlit as st
import pandas as pd

def render_route_table(slot, route_df: pd.DataFrame) -> None:
    """Renders route delay metrics table into a persistent slot."""
    if route_df.empty:
        slot.info("No active route analytics available.")
        return

    with slot.container():
        st.dataframe(
            route_df,
            width="stretch",
            hide_index=True,
            column_config={
                "route_id": "Route",
                "active_vehicles": "Active Vehicles",
                "avg_delay_sec": st.column_config.NumberColumn("Avg Delay (s)", format="%d s"),
                "max_delay_sec": st.column_config.NumberColumn("Max Delay (s)", format="%d s"),
            },
        )