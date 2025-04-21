# utils/merge_netcdf_utils.py

import xarray as xr
import numpy as np

def load_dataset(file_path: str) -> xr.Dataset:
    """
    Loads a NetCDF file as an xarray Dataset.

    Args:
        file_path (str): Path to the NetCDF file

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

def merge_netcdf_concat(file_paths: list, dim: str = 'time') -> xr.Dataset:
    """
    Concatenates multiple NetCDF files along the specified dimension.

    This function stacks datasets end-to-end along a single dimension,
    similar to joining multiple time series into one longer series.

    Args:
        file_paths (list): List of NetCDF file paths
        dim (str): Dimension along which to concatenate (default 'time')

    Returns:
        xr.Dataset: The concatenated dataset

    Raises:
        RuntimeError: If concatenation fails
    """
    try:
        datasets = [load_dataset(fp) for fp in file_paths]
        merged_ds = xr.concat(datasets, dim=dim)
        return merged_ds
    except Exception as e:
        raise RuntimeError(f"Error concatenating datasets along '{dim}': {e}")

def merge_netcdf_merge(file_paths: list) -> xr.Dataset:
    """
    Merges multiple NetCDF files by combining their variables.

    This function combines different variables from files that share
    the same coordinate systems, like adding temperature data to
    a dataset that already contains precipitation.

    Args:
        file_paths (list): List of NetCDF file paths

    Returns:
        xr.Dataset: The merged dataset with combined variables

    Raises:
        RuntimeError: If merging fails
    """
    try:
        datasets = [load_dataset(fp) for fp in file_paths]
        merged_ds = xr.merge(datasets)
        return merged_ds
    except Exception as e:
        raise RuntimeError(f"Error merging datasets: {e}")

def smart_merge_netcdf(file_paths: list, dim: str = 'time', duplicate_policy: str = 'drop') -> xr.Dataset:
    """
    Intelligently merges NetCDF files with handling for overlapping values.

    This advanced merge function handles cases where datasets have
    overlapping coordinates (e.g., overlapping time periods).

    Args:
        file_paths (list): List of NetCDF file paths
        dim (str): The dimension along which to merge (default 'time')
        duplicate_policy (str): How to handle duplicates:
            - 'drop': Keep only the first occurrence
            - 'average': Calculate mean of all duplicate values

    Returns:
        xr.Dataset: The merged dataset with handled duplicates

    Raises:
        RuntimeError: If smart merging fails
        ValueError: If an invalid duplicate policy is provided
    """
    try:
        datasets = [load_dataset(fp) for fp in file_paths]
        merged_ds = xr.concat(datasets, dim=dim)

        # Get the coordinate values along the merge dimension
        coord_values = merged_ds[dim].values
        unique_vals, indices, counts = np.unique(coord_values, return_index=True, return_counts=True)

        # Handle duplicates according to policy
        if duplicate_policy == 'drop':
            # Select only the first occurrence for duplicate times
            if np.any(counts > 1):
                merged_ds = merged_ds.sel({dim: unique_vals})
            return merged_ds
        elif duplicate_policy == 'average':
            # Group by the coordinate and take the mean (averaging duplicates)
            merged_ds = merged_ds.groupby(dim).mean()
            return merged_ds
        else:
            raise ValueError("duplicate_policy must be either 'drop' or 'average'")
    except Exception as e:
        raise RuntimeError(f"Error in smart merging along '{dim}': {e}")
