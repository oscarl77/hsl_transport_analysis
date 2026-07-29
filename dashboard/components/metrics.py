import streamlit as st
import pandas as pd

def render_kpis(slot, df: pd.DataFrame) -> None:
    """Renders real-time KPI metrics into a persistent slot."""
    if df.empty:
        slot.warning("No active telemetry pings recorded.")
        return

    total_fleet = len(df)
    avg_delay = df["delay_seconds"].mean() if "delay_seconds" in df.columns else 0
    on_time_count = (df["delay_seconds"] <= 60).sum() if "delay_seconds" in df.columns else 0
    on_time_pct = (on_time_count / total_fleet) * 100 if total_fleet > 0 else 0

    with slot.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Fleet Count", total_fleet)
        col2.metric("Average Network Delay", f"{int(avg_delay)}s", delta=f"{int(avg_delay)}s", delta_color="inverse")
        col3.metric("On-Time Performance", f"{on_time_pct:.1f}%")