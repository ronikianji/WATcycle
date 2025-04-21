import xarray as xr
import os
import tempfile
import zipfile
from io import BytesIO
import numpy as np
import pandas as pd

def load_dataset(file_path: str) -> xr.Dataset:
    """
    Loads a NetCDF file as an xarray Dataset.

    Args:
        file_path: Path to the NetCDF file

    Returns:
        xr.Dataset: Loaded dataset

    Raises:
        RuntimeError: If file cannot be loaded
    """
    try:
        ds = xr.open_dataset(file_path)
        return ds
    except Exception as e:
        raise RuntimeError(f"Error loading {file_path}: {e}")

def split_netcdf_by_index(ds: xr.Dataset, dim: str = 'time', chunk_size: int = 10) -> list:
    """
    Splits the dataset along the specified dimension by fixed chunk size.

    This function divides your dataset into equal-sized chunks along a dimension,
    like splitting a time series into monthly segments.

    Args:
        ds: The dataset to split
        dim: The dimension to split on (e.g., 'time')
        chunk_size: The number of indices per chunk

    Returns:
        List of xarray.Dataset objects (each a chunk)

    Raises:
        ValueError: If dimension is not found
        RuntimeError: If splitting fails
    """
    if dim not in ds.dims:
        raise ValueError(f"Dimension '{dim}' not found in the dataset.")

    total = ds.dims[dim]
    chunks = []

    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        try:
            ds_chunk = ds.isel({dim: slice(start, end)})
            chunks.append(ds_chunk)
        except Exception as e:
            raise RuntimeError(f"Error splitting dataset from index {start} to {end}: {e}")

    return chunks

def split_netcdf_by_label(ds: xr.Dataset, dim: str = 'time', start_value=None, end_value=None) -> xr.Dataset:
    """
    Extracts a subset of the dataset by selecting a slice along a coordinate.

    This function creates a subset of your data within a specific range of values,
    like extracting data for a particular time period or geographic region.

    Args:
        ds: The dataset to slice
        dim: The coordinate along which to slice
        start_value: The starting label value
        end_value: The ending label value

    Returns:
        A subset xarray.Dataset for the specified coordinate range

    Raises:
        ValueError: If coordinate is not found or values are missing
        RuntimeError: If slicing fails
    """
    if dim not in ds.coords:
        raise ValueError(f"Coordinate '{dim}' not found in the dataset.")

    if start_value is None or end_value is None:
        raise ValueError("Both start_value and end_value must be provided for label-based splitting.")

    try:
        # Handle datetime conversion if needed
        if np.issubdtype(ds[dim].dtype, np.datetime64):
            try:
                start_value = pd.to_datetime(start_value)
                end_value = pd.to_datetime(end_value)
            except Exception:
                pass

        ds_slice = ds.sel({dim: slice(start_value, end_value)})
        return ds_slice
    except Exception as e:
        raise RuntimeError(f"Error in label-based splitting along '{dim}': {e}")

def split_netcdf_by_group(ds: xr.Dataset, dim: str = 'time', group_freq: str = 'Y') -> dict:
    """
    Splits the dataset by grouping the time coordinate based on a frequency.

    This function organizes your data into time periods like days, months, or years,
    creating separate datasets for each period.

    Args:
        ds: The dataset to group
        dim: The time coordinate to group by
        group_freq: Frequency string ('Y' for yearly, 'M' for monthly, 'D' for daily)

    Returns:
        Dictionary mapping group labels to the corresponding xarray.Dataset

    Raises:
        ValueError: If coordinate is not found
        RuntimeError: If grouping fails
    """
    if dim not in ds.coords:
        raise ValueError(f"Coordinate '{dim}' not found in the dataset.")

    try:
        # Convert to pandas datetime
        times = pd.to_datetime(ds[dim].values)

        # Create a pandas Series to group by
        df_time = pd.DataFrame({dim: times})
        df_time.index = df_time[dim]

        # Resample to get groups
        groups = {}
        for group, indices in df_time.resample(group_freq).groups.items():
            # Format the group label nicely
            if group_freq == 'Y':
                label = pd.to_datetime(group).strftime("%Y")
            elif group_freq == 'M':
                label = pd.to_datetime(group).strftime("%Y-%m")
            else:
                label = pd.to_datetime(group).strftime("%Y-%m-%d")

            groups[label] = ds.sel({dim: indices})

        return groups
    except Exception as e:
        raise RuntimeError(f"Error in group-based splitting along '{dim}': {e}")

def create_zip_from_datasets(datasets: list, base_filename: str = "split_", suffix: str = ".nc") -> bytes:
    """
    Packages multiple datasets into a ZIP archive for download.

    This function saves each dataset to a temporary NetCDF file, combines them
    into a ZIP archive, and returns the archive as bytes for download.

    Args:
        datasets: List of xarray.Dataset objects
        base_filename: Base name for temporary files
        suffix: File suffix (default '.nc')

    Returns:
        Bytes representing the zipped archive of all split files

    Raises:
        RuntimeError: If ZIP creation fails
    """
    try:
        temp_files = []

        # Save each dataset to a temporary file
        for idx, ds in enumerate(datasets):
            temp_path = os.path.join(tempfile.gettempdir(), f"{base_filename}{idx}{suffix}")
            ds.to_netcdf(temp_path)
            temp_files.append(temp_path)

        # Create a zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file_path in temp_files:
                zf.write(file_path, os.path.basename(file_path))

        # Clean up temporary files
        for file_path in temp_files:
            try:
                os.remove(file_path)
            except Exception:
                pass

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    except Exception as e:
        raise RuntimeError(f"Error creating zip archive: {e}")
