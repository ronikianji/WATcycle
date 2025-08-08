# # features/spatial_plotting/shp_spatial.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
import geopandas as gpd
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


def _compute_edges_from_centers(centers):
    """Compute cell edges from 1D sorted center coordinates."""
    centers = np.asarray(np.unique(centers))
    if centers.size == 1:
        d = 1.0
        return np.array([centers[0] - d / 2.0, centers[0] + d / 2.0])
    diffs = np.diff(centers)
    edges = np.empty(centers.size + 1, dtype=centers.dtype)
    edges[1:-1] = (centers[:-1] + centers[1:]) / 2.0
    first = diffs[0] if diffs.size > 0 else 0.0
    last = diffs[-1] if diffs.size > 0 else first
    edges[0] = centers[0] - first / 2.0
    edges[-1] = centers[-1] + last / 2.0
    return edges


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

    # ensure df has lon/lat columns named 'lon'/'lat' or find alternatives
    if "lon" not in df.columns or "lat" not in df.columns:
        # attempt to find columns that look like lon/lat
        cols = list(df.columns)
        lon_col = next((c for c in cols if "lon" in c.lower() or "long" in c.lower()), None)
        lat_col = next((c for c in cols if "lat" in c.lower()), None)
        if lon_col and lat_col:
            df = df.rename(columns={lon_col: "lon", lat_col: "lat"})
        else:
            st.error("Could not find 'lon'/'lat' columns in the extracted dataframe.")
            return

    # Mask out-of-polygon points — vectorized via GeoPandas for speed
    try:
        union = gdf.unary_union
        points = gpd.GeoSeries(gpd.points_from_xy(df["lon"], df["lat"]), crs=gdf.crs)
        mask = points.within(union)  # vectorized
        df_masked = df[mask.values].copy()
    except Exception:
        # fallback to per-row check (slower) if GeoPandas vector ops fail
        union = gdf.unary_union
        mask = df.apply(lambda row: union.contains(Point(row["lon"], row["lat"])), axis=1)
        df_masked = df[mask].copy()

    if df_masked.empty:
        st.warning("No data points fall within the uploaded shapefile.")
        return

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

        # Ensure shapefile is in lon/lat (EPSG:4326) for proper contains checks & plotting
        try:
            gdf_plot = gdf.to_crs(epsg=4326) if (hasattr(gdf, "crs") and gdf.crs is not None and gdf.crs.to_string().lower() != "epsg:4326") else gdf
        except Exception:
            gdf_plot = gdf

        # union geometry used for fast contains checks
        union = gdf_plot.unary_union

        if smoothing:
            st.info("Smoothing enabled—this may take a while…")
            # interpolate & mask on grid (assumes interpolate_grid_data returns center arrays)
            grid_lons, grid_lats, values = interpolate_grid_data(
                df_masked, gdf_plot, grid_res, method
            )

            # get 1D center arrays
            if np.ndim(grid_lons) == 2:
                lon_centers_1d = np.unique(grid_lons[0, :])
                lat_centers_1d = np.unique(grid_lats[:, 0])
            else:
                lon_centers_1d = np.asarray(grid_lons)
                lat_centers_1d = np.asarray(grid_lats)

            # compute edges for pcolormesh
            lon_edges = _compute_edges_from_centers(lon_centers_1d)
            lat_edges = _compute_edges_from_centers(lat_centers_1d)

            # mask cells whose centres are outside the polygon
            lon_mesh, lat_mesh = np.meshgrid(lon_centers_1d, lat_centers_1d)
            pts = gpd.GeoSeries(gpd.points_from_xy(lon_mesh.ravel(), lat_mesh.ravel()), crs="EPSG:4326")
            mask_flat = pts.within(union).values  # True = inside
            mask = mask_flat.reshape(lon_mesh.shape)
            # apply mask (set outside to NaN)
            values_masked = np.where(mask, values, np.nan)

            # plot masked grid and overlay shapefile boundary
            pcm = ax.pcolormesh(
                lon_edges, lat_edges, values_masked,
                cmap=cmap,
                transform=ccrs.PlateCarree(),
                shading="flat"
            )
            fig.colorbar(pcm, ax=ax, orientation="vertical", shrink=0.6, label=var)

        else:
            # NON-smoothed: create gridded array from point centres then pcolormesh to fill pixels
            lon_centers = np.sort(df_masked["lon"].unique())
            lat_centers = np.sort(df_masked["lat"].unique())

            pivot = df_masked.pivot_table(index="lat", columns="lon", values=var, aggfunc="first")
            pivot = pivot.reindex(index=lat_centers, columns=lon_centers)
            values = pivot.values.astype(float)

            # compute edges
            lon_edges = _compute_edges_from_centers(lon_centers)
            lat_edges = _compute_edges_from_centers(lat_centers)

            # mask using cell centers
            lon_mesh, lat_mesh = np.meshgrid(lon_centers, lat_centers)
            pts = gpd.GeoSeries(gpd.points_from_xy(lon_mesh.ravel(), lat_mesh.ravel()), crs="EPSG:4326")
            mask_flat = pts.within(union).values
            mask = mask_flat.reshape(lon_mesh.shape)
            values_masked = np.where(mask, values, np.nan)

            pcm = ax.pcolormesh(
                lon_edges, lat_edges, values_masked,
                cmap=cmap,
                transform=ccrs.PlateCarree(),
                shading="flat"
            )
            fig.colorbar(pcm, ax=ax, orientation="vertical", shrink=0.6, label=var)

        # Draw shapefile boundary on top so it's always visible
        try:
            ax.add_geometries(
                [geom for geom in gdf_plot.geometry],
                crs=ccrs.PlateCarree(),
                facecolor="none",
                edgecolor="black",
                linewidth=1.2,
                zorder=5
            )
        except Exception:
            # Fallback: geopandas plotting (less control over cartopy transforms)
            gdf_plot.boundary.plot(ax=ax, linewidth=1.2, edgecolor="black")

        # Set extent to shapefile bounds with a tiny padding
        minx, miny, maxx, maxy = gdf_plot.total_bounds
        pad_x = (maxx - minx) * 0.02 if (maxx - minx) != 0 else 0.01
        pad_y = (maxy - miny) * 0.02 if (maxy - miny) != 0 else 0.01
        ax.set_extent([minx - pad_x, maxx + pad_x, miny - pad_y, maxy + pad_y], crs=ccrs.PlateCarree())

        # Set title with date if in Time Index mode
        title = f"{var} ({sel_date})" if mode == "Time Index" else f"{var} ({mode})"
        ax.set_title(title, fontsize=14, weight="bold")
        st.pyplot(fig)
        get_image_download_button(
            fig,
            filename=f"shapefile_plot_{var}_{mode.replace(' ', '_')}.png",
            label="📥 Download Plot"
        )

