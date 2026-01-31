import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# -------------------- 1) PAGE SETUP --------------------
st.set_page_config(page_title="NYC Citi Bike Strategy Dashboard", layout="wide")

st.title("NYC Citi Bike Strategy Dashboard")
st.markdown(
    """
    This interactive dashboard explores Citi Bike usage patterns in New York City (2022).
    It supports strategic decisions by showing:
    - the most popular start stations,
    - daily ride trends,
    - and how temperature relates to ridership.
    """
)
st.markdown("---")


# -------------------- 2) LOAD DATA (READY-TO-USE) --------------------
# Daily aggregated + weather (for line chart)
df_daily = pd.read_csv("reduced_data_to_plot_merged.csv")
df_daily["date"] = pd.to_datetime(df_daily["date"])

# Trip-level sample (for top stations bar chart)
df_trips = pd.read_csv("reduced_data_to_plot.csv")
df_trips = df_trips.dropna(subset=["start_station_name"])


# -------------------- 3) BAR CHART: TOP 20 START STATIONS --------------------
st.subheader("Top 20 Most Popular Start Stations (NYC)")

top20 = (
    df_trips.groupby("start_station_name")
    .size()
    .reset_index(name="value")
    .sort_values("value", ascending=False)
    .head(20)
)

fig_bar = go.Figure(
    go.Bar(
        x=top20["start_station_name"],
        y=top20["value"],
        marker={"color": top20["value"], "colorscale": "Blues"},
        hovertemplate="Station: %{x}<br>Trips: %{y}<extra></extra>"
    )
)

fig_bar.update_layout(
    title="Top 20 Most Popular Start Stations in New York City",
    xaxis_title="Start stations",
    yaxis_title="Number of trips",
    height=520,
    margin=dict(l=40, r=40, t=70, b=160)
)

fig_bar.update_xaxes(tickangle=45)

st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")


# -------------------- 4) LINE CHART: DUAL AXIS (RIDES VS TEMP) --------------------
st.subheader("Daily Bike Trips vs Temperature (NYC, 2022)")

# Expecting columns in df_daily: date, bike_rides_daily, avgTemp
fig_line = make_subplots(specs=[[{"secondary_y": True}]])

fig_line.add_trace(
    go.Scatter(
        x=df_daily["date"],
        y=df_daily["bike_rides_daily"],
        name="Daily bike trips",
        mode="lines",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Trips: %{y}<extra></extra>"
    ),
    secondary_y=False
)

fig_line.add_trace(
    go.Scatter(
        x=df_daily["date"],
        y=df_daily["avgTemp"],
        name="Avg temperature (°C)",
        mode="lines",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Temp: %{y:.1f} °C<extra></extra>"
    ),
    secondary_y=True
)

fig_line.update_layout(
    title="Daily Rides and Temperature",
    height=560,
    margin=dict(l=40, r=40, t=70, b=40),
    legend=dict(orientation="h", y=1.02, x=0)
)

fig_line.update_yaxes(title_text="Number of trips", secondary_y=False)
fig_line.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")
# -------------------- KEPLER MAP --------------------
st.subheader("Aggregated Bike Trips Map (NYC)")

path_to_html = "NYC_BikeTrips_Kepler.html"

try:
    with open(path_to_html, "r", encoding="utf-8") as f:
        html_data = f.read()

    st.components.v1.html(html_data, height=900, scrolling=True)

except FileNotFoundError:
    st.error("Kepler map file not found. Make sure NYC_BikeTrips_Kepler.html is in the project folder.")