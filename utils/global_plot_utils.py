import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

def get_time_strings(ds):
    """
    Return list of ISO-date strings for ds.time coordinate.
    """
    return [str(pd.to_datetime(t).date()) for t in ds["time"].values]

def extract_dataarray_at_time(ds, var_name, time_str):
    """
    Select a single time slice by its ISO string.
    Returns an xarray.DataArray.
    """
    times = ds["time"].values
    time_list = get_time_strings(ds)
    idx = time_list.index(time_str)
    return ds[var_name].isel(time=idx)

def extract_dataarray_average(ds, var_name):
    """
    Compute the time-mean of var_name.
    Returns an xarray.DataArray.
    """
    return ds[var_name].mean(dim="time")

def get_projection(proj_name):
    """
    Map a string name to a Cartopy CRS object.
    """
    mapping = {
        "PlateCarree":   ccrs.PlateCarree(),
        "Robinson":      ccrs.Robinson(),
        "Mollweide":     ccrs.Mollweide(),
        "Mercator":      ccrs.Mercator(),
        "Orthographic":  ccrs.Orthographic(central_longitude=0.0),
    }
    return mapping.get(proj_name, ccrs.PlateCarree())

def plot_global_map(da, projection, cmap, vmin=None, vmax=None):
    """
    Plot a DataArray on a global map with coastlines.
    Returns the matplotlib Figure.
    """
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 1, 1, projection=projection)

    # Use xarray’s built-in plotting with Cartopy transform
    da.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        cbar_kwargs={"shrink": 0.6, "label": da.name},
    )

    ax.coastlines()
    ax.set_global()
    ax.set_title(f"{da.name}", fontsize=14, weight="bold")
    return fig
