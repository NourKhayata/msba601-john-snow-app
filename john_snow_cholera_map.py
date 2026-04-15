from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "CholeraPumps_Deaths.xls"
IMAGE_FILE = BASE_DIR / "Snow-cholera-map-1.jpg"

st.set_page_config(
    page_title="John Snow Cholera Map",
    page_icon="🗺️",
    layout="wide",
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = pd.read_excel(DATA_FILE)
    df = pd.DataFrame(data, columns=["count", "geometry"])

    df["geometry"] = (
        df["geometry"]
        .str.replace("<Point><coordinates>", "", regex=False)
        .str.replace("</coordinates></Point>", "", regex=False)
    )

    split = df["geometry"].str.split(",", n=1, expand=True)
    df["lon"] = split[0].astype(float)
    df["lat"] = split[1].astype(float)
    df = df.drop(columns=["geometry"])

    deaths_df = df[df["count"] >= 0].copy()
    pumps_df = df[df["count"] == -999].copy()

    # radius is scaled for map readability
    deaths_df["radius"] = deaths_df["count"].clip(lower=1) * 8

    distribution_df = (
        deaths_df.groupby("count", as_index=False)
        .size()
        .rename(columns={"size": "locations"})
        .sort_values("count")
    )

    return deaths_df, pumps_df, distribution_df


deaths_df, pumps_df, distribution_df = load_data()

st.title("John Snow's 1854 Cholera Deaths Map")
st.markdown(
    "An interactive view of the Soho cholera outbreak showing death clusters and nearby water pumps."
)

with st.sidebar:
    st.header("Map controls")
    min_deaths, max_deaths = int(deaths_df["count"].min()), int(deaths_df["count"].max())
    death_range = st.slider(
        "Death count range",
        min_value=min_deaths,
        max_value=max_deaths,
        value=(1, max_deaths),
        help="Show only locations whose recorded deaths fall inside this range.",
    )
    show_pumps = st.checkbox("Show pumps", value=True)
    map_style_label = st.selectbox(
        "Basemap style",
        ["Light", "Dark", "Road", "Satellite"],
        index=0,
    )
    show_table = st.checkbox("Show filtered data table", value=False)
    show_original = st.checkbox("Show original historical map image", value=True)

filtered_deaths = deaths_df[
    deaths_df["count"].between(death_range[0], death_range[1])
].copy()

locations_shown = int(len(filtered_deaths))
total_deaths_shown = int(filtered_deaths["count"].sum())
pump_count = int(len(pumps_df))

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Locations shown", f"{locations_shown}")
metric_2.metric("Deaths represented", f"{total_deaths_shown}")
metric_3.metric("Water pumps", f"{pump_count}")

MAP_STYLES = {
    "Light": pdk.map_styles.LIGHT,
    "Dark": pdk.map_styles.DARK,
    "Road": pdk.map_styles.ROAD,
    "Satellite": pdk.map_styles.SATELLITE,
}

layers = [
    pdk.Layer(
        "ScatterplotLayer",
        data=filtered_deaths,
        get_position="[lon, lat]",
        get_fill_color="[200, 30, 0, 170]",
        get_radius="radius",
        pickable=True,
    )
]

if show_pumps:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=pumps_df,
            get_position="[lon, lat]",
            get_fill_color="[0, 70, 220, 220]",
            get_radius=20,
            pickable=True,
        )
    )

st.pydeck_chart(
    pdk.Deck(
        map_style=MAP_STYLES[map_style_label],
        initial_view_state=pdk.ViewState(
            latitude=51.5134,
            longitude=-0.1365,
            zoom=15.5,
            pitch=0,
        ),
        tooltip={
            "html": "<b>Deaths:</b> {count}<br/><b>Longitude:</b> {lon}<br/><b>Latitude:</b> {lat}",
            "style": {"backgroundColor": "white", "color": "black"},
        },
        layers=layers,
    ),
    use_container_width=True,
)

st.caption("Red circles represent cholera deaths. Blue circles represent water pumps.")

chart_col, notes_col = st.columns([1.15, 0.85])

with chart_col:
    st.subheader("Distribution of deaths by location")
    st.bar_chart(distribution_df.set_index("count")["locations"], use_container_width=True)

with notes_col:
    st.subheader("What changed in this version")
    st.markdown(
        """
        1. Added a **death count range filter** instead of a single-threshold slider.
        2. Added **summary metrics** for locations, deaths, and pumps.
        3. Added **hover tooltips** and a **basemap selector**.
        4. Added a **bar chart** and optional **data table** for better analysis.
        """
    )

if show_table:
    st.subheader("Filtered dataset")
    st.dataframe(
        filtered_deaths[["count", "lon", "lat"]].sort_values("count", ascending=False),
        use_container_width=True,
    )

if show_original and IMAGE_FILE.exists():
    image = Image.open(IMAGE_FILE)
    st.subheader("Original map of John Snow")
    st.image(
        image,
        caption=(
            "Original map by John Snow showing the cluster of cholera cases in London during the 1854 outbreak."
        ),
        use_container_width=True,
    )

with st.expander("Historical context"):
    st.write(
        "John Snow's map is a classic example of spatial analysis. By comparing cholera deaths with nearby water pumps, "
        "he was able to identify the Broad Street pump as the likely source of the outbreak."
    )
