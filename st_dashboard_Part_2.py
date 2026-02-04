import streamlit as st
import pandas as pd
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Season color palette
season_colors = {
    "Winter": "#457b9d",   # cool blue
    "Spring": "#2a9d8f",   # green
    "Summer": "#e9c46a",   # yellow
    "Autumn": "#e76f51"    # orange
}

st.set_page_config(page_title="Bike Dashboard", layout="wide")

page = st.sidebar.selectbox(
    "Select an aspect of the analysis",
    [
        "Intro page",
        "Weather component and bike usage",
        "Most popular stations",
        "Interactive map with aggregated bike trips",
        "Recommendations",
        "Peak hours and demand",
    ],
)

@st.cache_data
def load_bike_data():
    df = pd.read_csv("reduced_data_to_plot_7.csv")
    df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
    df = df.dropna(subset=["started_at", "start_station_name"])
    return df

df_bike = load_bike_data()

@st.cache_data
def load_daily_weather_data():
    df = pd.read_csv("reduced_data_to_plot_merged.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "bike_rides_daily", "avgTemp"])
    return df

df_weather = load_daily_weather_data()

# ================= PAGES =================
if page == "Intro page":
    st.title("New York Bikes Dashboard")
    st.markdown("This interactive dashboard explores Citi Bike usage patterns in New York City (2022).")

elif page == "Weather component and bike usage":
    st.title("Weather component and bike usage")

    st.markdown(
        """
        This chart illustrates the relationship between daily Citi Bike usage
        and average daily temperature in 2022.
        """
    )

    # Prepare data
    df_plot = df_weather.copy()
    df_plot["date"] = pd.to_datetime(df_plot["date"])

    # ---- Dual-axis plotly chart ----
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Left axis: bike rides
    fig.add_trace(
        go.Scatter(
            x=df_plot["date"],
            y=df_plot["bike_rides_daily"],
            name="Daily bike rides",
            mode="lines",
        ),
        secondary_y=False,
    )

    # Right axis: temperature
    fig.add_trace(
        go.Scatter(
            x=df_plot["date"],
            y=df_plot["avgTemp"],
            name="Average temperature",
            mode="lines",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="Daily bike rides vs average temperature (2022)",
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
    )

    fig.update_yaxes(title_text="Bike rides (count)", secondary_y=False)
    fig.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


elif page == "Most popular stations":
    st.title("Most popular stations")

    # Make a working copy
    df1 = df_bike.copy()

    # Ensure started_at is datetime (needed for month/season)
    df1["started_at"] = pd.to_datetime(df1["started_at"], errors="coerce")

    # Create season column (if missing)
    if "season" not in df1.columns:
        df1["month"] = df1["started_at"].dt.month

        def get_season(m):
            if m in [12, 1, 2]:
                return "Winter"
            elif m in [3, 4, 5]:
                return "Spring"
            elif m in [6, 7, 8]:
                return "Summer"
            else:
                return "Autumn"

        df1["season"] = df1["month"].apply(get_season)

    # Season filter
    season_filter = st.multiselect(
        "Select season(s)",
        options=sorted(df1["season"].dropna().unique()),
        default=sorted(df1["season"].dropna().unique()),
    )

    df1 = df1[df1["season"].isin(season_filter)]

    # Top 20 stations
    top20 = (
        df1.dropna(subset=["start_station_name"])
        .groupby("start_station_name")
        .size()
        .reset_index(name="trips")
        .sort_values("trips", ascending=False)
        .head(20)
    )

    # Season-based bar color (if multiple selected, use Winter as default)
    selected_season = season_filter[0] if len(season_filter) == 1 else "Winter"
    bar_color = season_colors.get(selected_season, "#457b9d")

    # Plot
    fig = go.Figure(
        go.Bar(
            x=top20["start_station_name"],
            y=top20["trips"],
            marker_color=bar_color,
        )
    )

    fig.update_layout(
        title="Top 20 most popular start stations (filtered by season)",
        xaxis_title="Start station",
        yaxis_title="Number of trips",
        height=550,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretation
    st.markdown(
        """
        **Interpretation:**  
        The bar chart shows that Citi Bike usage is highly concentrated at a small number of start stations, with the top stations accounting for a                      disproportionately large share of trips. This pattern suggests that bike demand is strongly linked to key urban locations such as transit hubs, business         districts, and densely populated areas. Even when filtered by season, the same stations tend to remain among the most popular, indicating stable spatial         demand rather than purely seasonal shifts. Overall, the results highlight the importance of these high-demand stations for system planning, capacity             management, and maintenance prioritization.
        """
    )
elif page == "Interactive map with aggregated bike trips":
    st.title("Interactive map with aggregated bike trips")

    st.markdown(
        "Interactive map showing aggregated bike trips and flows between start and end stations."
    )

    path_to_html = "NYC_BikeTrips_Kepler.html"

    try:
        with open(path_to_html, "r", encoding="utf-8") as f:
            html_data = f.read()

        st.components.v1.html(
            html_data,
            height=900,
            scrolling=True
        )

        st.markdown(
            """
            **Interpretation:**

            The map shows that bike activity is concentrated in a few high-demand areas,
            with many trips starting and ending around key transport hubs and central city zones.

            The strongest flows occur between nearby stations, indicating short “last-mile”
            trips and local commuting patterns.

            High-volume corridors highlight where bike redistribution and infrastructure
            improvements could be most effective.
            """
        )

    except FileNotFoundError:
        st.error(
            "Kepler map HTML file not found. Please ensure it is in the same folder as this app."
        )
elif page == "Peak hours and demand":
    st.title("Peak hours and demand")

    # Filter: member vs casual (optional, very helpful)
    user_filter = st.multiselect(
        "Select user type(s)",
        options=sorted(df_bike["member_casual"].dropna().unique()),
        default=sorted(df_bike["member_casual"].dropna().unique()),
    )
    df2 = df_bike[df_bike["member_casual"].isin(user_filter)].copy()

    # Create hour column
    df2["hour"] = df2["started_at"].dt.hour

    # Hourly trips
    hourly = (
        df2.groupby("hour")
        .size()
        .reset_index(name="trips")
        .sort_values("hour")
    )

    # KPI: peak hour
    peak_row = hourly.loc[hourly["trips"].idxmax()]
    st.metric("Peak hour (highest demand)", f"{int(peak_row['hour']):02d}:00")
    st.metric("Trips at peak hour", f"{int(peak_row['trips']):,}")

    # Plot
    fig = go.Figure(
        go.Scatter(
            x=hourly["hour"],
            y=hourly["trips"],
            mode="lines+markers",
            name="Trips per hour",
        )
    )
    fig.update_layout(
        title="Trips by hour of day (shows demand peaks)",
        xaxis_title="Hour of day",
        yaxis_title="Number of trips",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        **Interpretation:**  
        This chart highlights the hours when demand is highest. Peaks typically indicate commute periods, when bike shortages are most likely.
        These insights can guide rebalancing schedules (e.g., move bikes before peak hours) and staffing decisions.
        """
    )
elif page == "Recommendations":
    st.title("Conclusion and Recommendations")
    total_trips = len(df_bike)

    top_station = (
        df_bike.dropna(subset=["start_station_name"])
        .groupby("start_station_name")
        .size()
        .sort_values(ascending=False)
        .index[0]
    )

    st.metric("Total trips in sample", f"{total_trips:,}")
    st.metric("Top demand station", top_station)

    st.markdown(
        """
        ### Key insights
        - **Strong seasonality:** Bike demand rises in warmer months and drops in winter (weather vs rides).
        - **Demand is concentrated:** A small number of stations account for a large share of trips (top stations).
        - **Spatial hotspots:** The map shows clear high-volume corridors and clusters, indicating where demand is consistently highest.
        - **Peak demand periods:** Shortage risk is highest during peak usage windows (e.g., commute hours), when bikes can run out quickly at key stations.

        ### Recommendations (to reduce supply shortages)
        1. **Prioritize rebalancing around the highest-demand stations and corridors**  
           Focus truck rebalancing and staff attention on the top start stations and the strongest map corridors.

        2. **Shift supply proactively before peak demand windows**  
           Use hourly demand patterns to move bikes *before* the peak hours (rather than reacting after stations are empty).

        3. **Season-based operations planning**  
           Increase bike availability and rebalancing frequency during warmer months; reduce redistribution intensity in winter to lower logistics costs.

        4. **Target “problem stations” with monitoring**  
           Flag stations that repeatedly appear in the top-demand list and in high-flow routes. These stations should be monitored for empty/full conditions                more frequently.

        ### Limitations
        - This analysis uses trip and weather patterns, but it does **not** include real-time station capacity, the number of docks per station, or operational            rebalancing logs.
        - Future improvements would combine this dashboard with station inventory data to predict shortages more accurately.
        """
    )
    
if page == "Intro page":
    st.title("Bike Usage Dashboard (2022)")

    st.markdown(
        """
        ### Purpose
        This dashboard provides an overview of bike usage patterns in 2022 to support planning and decision-making.
        The main goal is to understand when and where bike demand is higher, and what factors might influence demand.

        ### What analysis was done?
        Using bike trip data (and daily weather), we analysed:
        - How bike usage changes over time and relates to temperature
        - Which start stations are the most popular
        - Which areas/routes show the most frequent trips using an interactive map

        ### How to use this dashboard
        Use the dropdown menu in the left sidebar to navigate between pages.
        Each page contains a visualization and a short interpretation of the findings.
        """
    )
# -------------------- 1) PAGE SETUP --------------------
#st.set_page_config(page_title="NYC Citi Bike Strategy Dashboard", layout="wide")

#st.title("NYC Citi Bike Strategy Dashboard")#st.mark(
 #   """
    #This interactive dashboard explores Citi Bike usage patterns in New Yorty (2022).
    #It supports strategic decisioy showing:
    #- the most popular s stations,
    #- dailde trends,
    #- and how temperature relates ridership.
   # """
#)
#st.markdown("---")


# -------------------- 2) LOAD DATA (READY-TO-USE) --------------------
# Daily aggregated + weather (for line chart)
#df_daily = pd.read_csv("reduced_data_to_plot_merged.csv")
#df_daily["date"] = pd.to_datetime(df_daily["date"])

# Trip-level sample (for top stations bar chart)
#df_trips = pd.read_csv("reduced_data_to_plot.csv")
#df_trips = df_trips.dropna(subset=["start_station_name"])


# -------------------- 3) BAR CHART: TOP 20 START STATIONS --------------------
#st.subheader("Top 20 Most Popular Start Stations (NYC)#top20 = (
    #df_trips.groupby("start_ion_name"  #.size()
    #.reset_indexe="value")
    #.sort_values("value", asing=False)
    #.head(20)
#)

#fig_ba = go.Figure #   go.Bar(
  #      x=top20["start_sion_name"],
   #     y=t["value"],
    #    marker={"color": top20["value"], "colorsca"Blues"},
     #   hovertemplate="Station: %{x}<br>Trips: %{y}<e></extra>"
    #)
#)

#fig_bar.date_layout(
  #  title="Top 20 Most Popular Start Stations in N York City",
  #  xaxis_title="St stations",
   # yaxis_title="Num of trips",
   #height=520,
  #  margin=dict(l=40, r=40, t=70, b=160)
#)

#fig_bar.update_xaxes(tickangle=45)

#st.plotly_chart(fig_bar, use_container_width=True)

#st.markdown("---")


# -------------------- 4) LINE CHART: DUAL AXIS (RIDES VS TEMP) --------------------
#st.subheader("Daily Bike Trips vs Temperature (NYC, 2022)")

# Expecting columns in df_daily: date, bike_rides_daily, avgTemp
#fig_line = make_subplots(specs=[[{"secondary_y": True}]])

#fig_l.add_trace(
  #catter(
       # x=df_date"],
       # y=df_daily["bike_aily"],
       # name="Dailtrips",
       #ines",
        #hovertemplate="Date: %{x|%Y-%m-%d}<br>Trips: %{y}<e></e>"
    #),
    #secondary_y=False
#)

#fig_l.add_trace(
  #o.Scatter(
    #    x=df_["date"],
     #   y=df_daigTemp"],
      #  name="Avg temp (°C)",
       #ines",
        #hovertemplate="Date: %{x|%Y-%m-%d}<br>Temp: %{y:.1f} °C<ea></e>"
   # ),
    #secondary_y=True
#)

#fig_line.ate_layout(
   # title="Daily Rides andmperature",
  #height=560,
   # margin=dict(l=40, r=4070, b=40),
    #legend=dict(orientation="h", y=1.02, x=0)
#)

#fig_line.update_yaxes(title_text="Number of trips", secondary_y=False)
#fig_line.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

#st.plotly_chart(fig_line, use_container_width=True)

#st.markdown("---")
# -------------------- KEPLER MAP --------------------
#st.subheader("Aggregated Bike Trips Map (NYC)")

#path_to_html = "NYC_BikeTrips_Kepletml"

#try:
   # with open(path_to_html, "r", encoding=) as f:
       # html_da= f.read()

   # st.components.v1.html(html_data, height=900, scrolling=True)

#except FileoundError:
    #st.error("Kepler map file not found. Make sure NYC_BikeTrips_Kepler.html is in the projlder.")

      