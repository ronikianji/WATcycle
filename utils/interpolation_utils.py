import xarray as xr
import numpy as np
import pandas as pd

def interpolate_na_along_dim(ds: xr.Dataset, dim: str, method: str = "linear") -> xr.Dataset:
    """
    Fills missing values (NaNs) along a specified dimension.

    Args:
        ds: Input dataset with missing values
        dim: Dimension for interpolation (e.g., "time", "lat", "lon")
        method: Interpolation method ("linear", "nearest", or "spline")

    Returns:
        Dataset with filled values along specified dimension
    """
    if dim not in ds.dims:
        raise ValueError(f"Dimension '{dim}' not found in dataset")
    try:
        return ds.interpolate_na(dim=dim, method=method)
    except Exception as e:
        raise RuntimeError(f"Interpolation failed: {e}")

def interpolate_na_all(ds: xr.Dataset, method: str = "linear") -> xr.Dataset:
    """
    Fills missing values (NaNs) using all available dimensions.

    Args:
        ds: Input dataset with missing values
        method: Interpolation method ("linear", "nearest", or "spline")

    Returns:
        Dataset with filled values across all dimensions
    """
    try:
        return ds.interpolate_na(method=method)
    except Exception as e:
        raise RuntimeError(f"Multi-dimensional interpolation failed: {e}")
