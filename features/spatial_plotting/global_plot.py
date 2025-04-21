# features/global_plot.py

import streamlit as st
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.interpolate import griddata

from utils.file_handler import load_dataset, get_image_download_button
from utils.global_plot_utils import (
    get_time_strings,
    extract_dataarray_at_time,
    extract_dataarray_average,
    get_projection,
    plot_global_map,
)

def global_plot_ui():
    st.header("🌐 Global Plot")

    # 1️⃣ Load dataset from session
    ds = load_dataset()
    if ds is None:
        st.warning("Please upload a NetCDF file first.")
        return

    # 2️⃣ Variable selection
    var = st.selectbox("Select Variable", list(ds.data_vars))

    # 3️⃣ Time vs Average mode
    mode = st.radio("Plot Mode", ["Time Index", "Average"], index=0)

    if mode == "Time Index":
        # build list of actual dates
        times = pd.to_datetime(ds["time"].values).date
        # calendar widget
        sel_date = st.date_input(
            "Select Date",
            value=times[0],
            min_value=times[0],
            max_value=times[-1]
        )
        if sel_date not in list(times):
            st.error("Selected date not found in dataset.")
            return
        # get DataArray
        da = extract_dataarray_at_time(ds, var, str(sel_date))
    else:
        da = extract_dataarray_average(ds, var)

    # 4️⃣ Projection & colormap
    proj_name = st.selectbox(
        "Select Projection",
        ["PlateCarree", "Robinson", "Mollweide", "Mercator", "Orthographic"],
        index=0
    )
    projection = get_projection(proj_name)

    cmap = st.selectbox("Select Colormap", plt.colormaps(), index=0)

    # 5️⃣ Smoothing option
    smoothing = st.checkbox("Enable smoothing (this may take time)")
    if smoothing:
        method = st.selectbox("Interpolation Method", ["linear", "nearest", "cubic"])
        grid_res = st.slider("Grid Resolution", min_value=50, max_value=1000, value=250, step=50)

    # 6️⃣ Generate Map
    if st.button("Generate Map"):
        if smoothing:
            st.info("Smoothing enabled—this may take a while…")
            # convert to DataFrame
            df = da.to_dataframe().reset_index()[["lat", "lon", da.name]].dropna()
            # build grid
            lon_min, lat_min = df["lon"].min(), df["lat"].min()
            lon_max, lat_max = df["lon"].max(), df["lat"].max()
            grid_lons = np.linspace(lon_min, lon_max, grid_res)
            grid_lats = np.linspace(lat_min, lat_max, grid_res)
            grid_lons, grid_lats = np.meshgrid(grid_lons, grid_lats)
            # interpolate
            values = griddata(
                (df["lon"], df["lat"]),
                df[da.name],
                (grid_lons, grid_lats),
                method=method
            )
            # plot via pcolormesh
            fig = plt.figure(figsize=(12, 6))
            ax = fig.add_subplot(1, 1, 1, projection=projection)
            pcm = ax.pcolormesh(
                grid_lons, grid_lats, values,
                cmap=cmap, transform=ccrs.PlateCarree()
            )
            ax.coastlines()
            ax.set_global()
            title = f"{da.name} ({sel_date})" if mode == "Time Index" else f"{da.name} (Average)"
            ax.set_title(title, fontsize=14, weight="bold")
            fig.colorbar(pcm, ax=ax, orientation="horizontal", pad=0.05, shrink=0.8, label=da.name)

        else:
            # use xarray built‑in
            fig = plt.figure(figsize=(12, 6))
            ax = fig.add_subplot(1, 1, 1, projection=projection)
            da.plot(
                ax=ax,
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                cbar_kwargs={"orientation":"horizontal","pad":0.05,"shrink":0.8,"label":da.name}
            )
            ax.coastlines()
            ax.set_global()
            title = f"{da.name} ({sel_date})" if mode == "Time Index" else f"{da.name} (Average)"
            ax.set_title(title, fontsize=14, weight="bold")

        # render & download
        st.pyplot(fig)
        get_image_download_button(
            fig,
            filename=f"global_{var}_{mode.replace(' ','_')}.png",
            label="📥 Download Map"
        )
