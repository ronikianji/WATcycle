# utils/resample_utils.py

import xarray as xr
import numpy as np
# import xesmf as xe  # make sure xESMF is installed: pip install xesmf
import pandas as pd

def interp_resample(ds: xr.Dataset, new_coords: dict, method: str = "linear") -> xr.Dataset:
    """
    Interpolates the dataset to new coordinate arrays using xarray's interp().

    Parameters:
      ds: xarray.Dataset to be resampled.
      new_coords: Dictionary with keys as coordinate names and values as arrays of new coordinates.
                  Example: {"lat": np.arange(-90, 90.25, 0.25), "lon": np.arange(0, 360.25, 0.25)}
      method: Interpolation method (default "linear"). Other options include "nearest", etc.

    Returns:
      ds_interp: The interpolated dataset.
    """
    try:
        ds_interp = ds.interp(new_coords, method=method)
        return ds_interp
    except Exception as e:
        raise RuntimeError(f"Error in interp_resample: {e}")

def coarsen_resample(ds: xr.Dataset, factors: dict, boundary: str = "trim", func: str = "mean") -> xr.Dataset:
    """
    Resamples the dataset by aggregating over blocks using xarray's coarsen().

    Parameters:
      ds: xarray.Dataset to be coarsened.
      factors: Dictionary specifying the factor for each dimension.
               Example: {"lat": 4, "lon": 4} to average every 4 grid cells in lat and lon.
      boundary: How to handle boundaries; options include "trim" (default) or "pad".
      func: Aggregation function to apply; default is "mean". Other options: "sum", etc.

    Returns:
      ds_coarse: The coarsened dataset.
    """
    try:
        coarsened = ds.coarsen(**factors, boundary=boundary)
        if func == "mean":
            ds_coarse = coarsened.mean()
        elif func == "sum":
            ds_coarse = coarsened.sum()
        else:
            # You can add more aggregation methods as needed
            ds_coarse = coarsened.mean()
        return ds_coarse
    except Exception as e:
        raise RuntimeError(f"Error in coarsen_resample: {e}")

# def xesmf_regrid(ds: xr.Dataset, target_grid: dict, method: str = "bilinear") -> xr.Dataset:
#     """
#     Regrids the dataset to a new target grid using xESMF.

#     Parameters:
#       ds: xarray.Dataset to regrid.
#       target_grid: Dictionary defining the target grid.
#                    Example: {"lat": np.arange(-90, 90.25, 0.25), "lon": np.arange(0, 360.25, 0.25)}
#       method: Regridding method; options include "bilinear", "nearest_s2d", "conservative", "patch".

#     Returns:
#       ds_regrid: The regridded dataset.
#     """
#     try:
#         # Build the target grid as a dictionary of xarray DataArrays
#         target = {
#             "lat": xr.DataArray(target_grid["lat"], dims=["lat"]),
#             "lon": xr.DataArray(target_grid["lon"], dims=["lon"])
#         }
#         regridder = xe.Regridder(ds, target, method=method, reuse_weights=True)
#         ds_regrid = regridder(ds)
#         return ds_regrid
#     except Exception as e:
#         raise RuntimeError(f"Error in xesmf_regrid: {e}")

def groupby_resample(ds: xr.Dataset, dim: str = "time", group_freq: str = "YS") -> dict:
    """
    Splits the dataset by grouping a coordinate based on a frequency.

    Parameters:
      ds: xarray.Dataset to be split.
      dim: Coordinate along which to group (usually "time").
      group_freq: Frequency string (e.g., "D" for daily, "MS" for monthly, "YS" for yearly).

    Returns:
      A dictionary mapping group labels (as strings) to xarray.Dataset objects.
    """
    if dim not in ds.coords:
        raise ValueError(f"Coordinate '{dim}' not found in the dataset.")
    try:
        times = pd.to_datetime(ds[dim].values)
        df_time = pd.DataFrame({dim: times})
        df_time.index = df_time[dim]
        groups = {}
        for group, indices in df_time.resample(group_freq).groups.items():
            label = pd.to_datetime(group).strftime("%Y-%m-%d")
            groups[label] = ds.sel({dim: indices})
        return groups
    except Exception as e:
        raise RuntimeError(f"Error in groupby_resample: {e}")

def create_zip_from_datasets(datasets: list, base_filename: str = "split_", suffix: str = ".nc") -> bytes:
    """
    Saves each dataset in the list to a temporary NetCDF file, compresses them into a ZIP archive, and returns the ZIP archive as bytes.

    Parameters:
      datasets: list of xarray.Dataset objects.
      base_filename: base filename to use for temporary files.
      suffix: file suffix (default ".nc").

    Returns:
      A bytes object representing the ZIP archive.
    """
    import os, tempfile, zipfile
    from io import BytesIO

    try:
        temp_files = []
        for idx, ds in enumerate(datasets):
            temp_path = os.path.join(tempfile.gettempdir(), f"{base_filename}{idx}{suffix}")
            ds.to_netcdf(temp_path)
            temp_files.append(temp_path)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file_path in temp_files:
                zf.write(file_path, os.path.basename(file_path))
        for file_path in temp_files:
            try:
                os.remove(file_path)
            except Exception:
                pass
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    except Exception as e:
        raise RuntimeError(f"Error creating zip archive: {e}")
