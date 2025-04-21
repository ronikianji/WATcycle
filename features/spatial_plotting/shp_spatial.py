# features/spatial_plotting/shp_spatial.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
from shapely.geometry import Point
from scipy.interpolate import griddata

from utils.file_handler import load_dataset, get_image_download_button
from utils.shp_spatial_utils import (
    get_time_strings,
    extract_df_at_time,
    extract_df_average,
    interpolate_grid_data,
    plot_grid_map,
    plot_scatter_map,
)

def spatial_plotting_ui():
    st.header("🗺️ Spatial Plot with Shapefile")

    # 1️⃣ Load NetCDF
    ds = load_dataset()
    if ds is None:
        st.warning("Please upload a NetCDF file first.")
        return

    # 2️⃣ Load Shapefile
    gdf = st.session_state.get("uploaded_shapefile_gdf")
    if gdf is None:
        st.warning("Please upload a shapefile first.")
        return

    # 3️⃣ Variable & Time/Average selection
    var = st.selectbox("Select Variable", list(ds.data_vars))
    mode = st.radio("Plot Mode", ["Time Index", "Average"], index=0)

    if mode == "Time Index":
        times = pd.to_datetime(ds["time"].values).date
        sel_date = st.date_input("Select Date",
                                 value=times[0],
                                 min_value=times[0],
                                 max_value=times[-1])
        if sel_date not in list(times):
            st.error("Selected date not in dataset.")
            return
        df = extract_df_at_time(ds, var, str(sel_date))
    else:
        df = extract_df_average(ds, var)

    # Mask out-of-polygon points
    union = gdf.unary_union
    mask = df.apply(lambda row: union.contains(Point(row["lon"], row["lat"])), axis=1)
    df_masked = df[mask]

    st.subheader("Data Table (masked to shapefile)")
    st.dataframe(df_masked)

    # 4️⃣ Colormap (always shown)
    cmap = st.selectbox("Select Colormap", plt.colormaps(), index=0)

    # 5️⃣ Smoothing options
    smoothing = st.checkbox("Enable smoothing (this may take time)")
    if smoothing:
        method = st.selectbox("Interpolation Method", ["linear", "nearest", "cubic"])
        grid_res = st.slider("Grid Resolution", 50, 1000, 250, 50)

    # 6️⃣ Generate Plot
    if st.button("Generate Plot"):
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        if smoothing:
            st.info("Smoothing enabled—this may take a while…")
            # interpolate & mask on grid
            grid_lons, grid_lats, values = interpolate_grid_data(
                df_masked, gdf, grid_res, method
            )
            pcm = plot_grid_map(ax, grid_lons, grid_lats, values, gdf, cmap, var)
            fig.colorbar(pcm, ax=ax, orientation="vertical", shrink=0.6, label=var)
        else:
            # use masked points only
            sc = plot_scatter_map(ax, df_masked, gdf, cmap, var)
            fig.colorbar(sc, ax=ax, orientation="vertical", shrink=0.6, label=var)

        # Set extent to shapefile bounds
        minx, miny, maxx, maxy = gdf.total_bounds
        ax.set_extent([minx, maxx, miny, maxy], crs=ccrs.PlateCarree())

        # Set title with date if in Time Index mode
        title = f"{var} ({sel_date})" if mode == "Time Index" else f"{var} ({mode})"
        ax.set_title(title, fontsize=14, weight="bold")
        st.pyplot(fig)
        get_image_download_button(
            fig,
            filename=f"shapefile_plot_{var}_{mode.replace(' ', '_')}.png",
            label="📥 Download Plot"
        )
