import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from shapely.geometry import Point

def get_time_strings(ds):
    """
    Return a list of ISO‐date strings for the dataset's time coordinate.
    """
    return [str(pd.to_datetime(t).date()) for t in ds["time"].values]

def extract_df_at_time(ds, var_name, time_str):
    """
    Select a single time slice by its ISO string, then return a DataFrame
    with columns ['lat','lon', var_name], dropping any NaNs.
    """
    # find index of the chosen time
    times = ds["time"].values
    time_list = [str(pd.to_datetime(t).date()) for t in times]
    idx = time_list.index(time_str)
    da = ds[var_name].isel(time=idx)
    df = da.to_dataframe().reset_index()[["lat","lon", var_name]].dropna()
    return df

def extract_df_average(ds, var_name):
    """
    Compute the time‐mean of var_name and return a DataFrame
    with ['lat','lon', var_name], dropping NaNs.
    """
    da = ds[var_name].mean(dim="time")
    df = da.to_dataframe().reset_index()[["lat","lon", var_name]].dropna()
    return df

def interpolate_grid_data(df, shapefile, grid_resolution, method):
    """
    Given a DataFrame with ['lat','lon',value], interpolate onto a regular grid
    within the shapefile bounds, mask outside the polygon, and return
    (grid_lons, grid_lats, grid_values).
    """
    # bounding box
    minx, miny, maxx, maxy = shapefile.total_bounds
    # create regular grid
    grid_lons = np.linspace(minx, maxx, grid_resolution)
    grid_lats = np.linspace(miny, maxy, grid_resolution)
    grid_lons, grid_lats = np.meshgrid(grid_lons, grid_lats)

    # interpolate scattered data
    values = griddata(
        (df["lon"], df["lat"]),
        df[df.columns[-1]],  # the variable column
        (grid_lons, grid_lats),
        method=method,
    )

    # mask outside shapefile
    union = shapefile.unary_union
    pts = np.vstack([grid_lons.ravel(), grid_lats.ravel()]).T
    mask = np.array([union.contains(Point(x, y)) for x, y in pts]).reshape(grid_lons.shape)
    values[~mask] = np.nan

    return grid_lons, grid_lats, values

def plot_grid_map(ax, grid_lons, grid_lats, values, shapefile, cmap, var_name):
    """
    Plot interpolated grid on a Cartopy axis, overlay shapefile boundary.
    Returns the QuadMesh or pcolormesh object for colorbar.
    """
    import cartopy.crs as ccrs

    pcm = ax.pcolormesh(
        grid_lons, grid_lats, values,
        cmap=cmap, transform=ccrs.PlateCarree()
    )
    # shapefile boundary
    ax.add_geometries(
        shapefile.geometry,
        crs=ccrs.PlateCarree(),
        facecolor="none",
        edgecolor="black",
        linewidth=1.5
    )
    return pcm

def plot_scatter_map(ax, df, shapefile, cmap, var_name):
    """
    Scatter‐plot raw points on a Cartopy axis, overlay shapefile boundary.
    Returns the PathCollection for colorbar.
    """
    import cartopy.crs as ccrs

    sc = ax.scatter(
        df["lon"], df["lat"],
        c=df[var_name], cmap=cmap, s=15,
        transform=ccrs.PlateCarree()
    )
    ax.add_geometries(
        shapefile.geometry,
        crs=ccrs.PlateCarree(),
        facecolor="none",
        edgecolor="black",
        linewidth=1.5
    )
    return sc
