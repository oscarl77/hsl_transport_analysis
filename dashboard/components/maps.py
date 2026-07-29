import pydeck as pdk
import pandas as pd

def get_delay_color(delay_sec: float) -> list[int]:
    if pd.isna(delay_sec) or delay_sec <= 60:
        return [59, 202, 46, 220]    # Green
    elif delay_sec <= 180:
        return [241, 196, 15, 220]   # Yellow
    else:
        return [231, 76, 60, 220]    # Red

def render_fleet_map(slot, df: pd.DataFrame, view_state: pdk.ViewState) -> None:
    """Updates PyDeck map in-place without triggering block-level dimming."""
    if df.empty:
        return

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
        initial_view_state=view_state,
        tooltip={"text": "Route: {route_id} | Vehicle: {vehicle_id}\nDelay: {delay_seconds}s | Speed: {speed} km/h"},
    )

    # Direct placeholder update + on_select='ignore' completely eliminates map dimming
    slot.pydeck_chart(
        deck, 
        width="stretch", 
        on_select="ignore", 
        key="live_tram_map"
    )