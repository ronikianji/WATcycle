# netcdf_standardizer_utils.py
import xarray as xr

def get_dataset_info(ds: xr.Dataset) -> dict:
    return {
        "Dimensions": dict(ds.dims),
        "Coordinates": {k: tuple(v.shape) for k, v in ds.coords.items()},
        "Variables": {
            k: {"dims": ds[k].dims, "shape": ds[k].shape, "attrs": ds[k].attrs}
            for k in ds.data_vars
        },
        "Global Attributes": ds.attrs
    }

def standardize_dataset(ds: xr.Dataset, mapping: dict, global_meta: dict) -> xr.Dataset:
    for dim in ("time", "lat", "lon"):
        src = mapping.get(dim)
        if src:
            if src in ds.data_vars:
                ds = ds.set_coords(src)
            ds = ds.rename({src: dim})
    for k, v in global_meta.items():
        ds.attrs[k] = v
    return ds

def aggregate_extra_dims(ds: xr.Dataset, method: str) -> xr.Dataset:
    allowed = {"time", "lat", "lon"}
    extra = [d for d in ds.dims if d not in allowed]
    if not extra:
        return ds
    if not hasattr(ds, method):
        raise ValueError(f"Invalid aggregation method: {method}")
    return getattr(ds, method)(dim=extra)

def slice_extra_dims(ds: xr.Dataset) -> dict:
    allowed = {"time", "lat", "lon"}
    slices = {}

    # Get all dimensions that are not time/lat/lon and not bounds dimensions
    extra_dims = [d for d in ds.dims if d not in allowed and not d.endswith('_bnds')]

    if not extra_dims:
        return slices

    # Create one file per combination of extra dimensions
    from itertools import product
    indices = [range(ds.dims[dim]) for dim in extra_dims]

    for idx_combination in product(*indices):
        selection = {dim: idx for dim, idx in zip(extra_dims, idx_combination)}
        slice_ds = ds.isel(selection)

        # Create filename with dimension values
        filename_parts = []
        for dim, idx in zip(extra_dims, idx_combination):
            try:
                value = slice_ds[dim].values.item()
                if hasattr(value, 'strftime'):  # Handle datetime
                    value_str = value.strftime('%Y%m%d')
                else:
                    value_str = str(value).replace(' ', '_')
            except:
                value_str = str(idx)
            filename_parts.append(f"{dim}_{value_str}")

        filename = "_".join(filename_parts) + "_standardized.nc"
        slices[filename] = slice_ds

    return slices

# # netcdf_standardizer_utils.py
# import xarray as xr

# def get_dataset_info(ds: xr.Dataset) -> dict:
#     info = {
#         'Dimensions': dict(ds.dims),
#         'Coordinates': {k: tuple(v.shape) for k, v in ds.coords.items()},
#         'Variables': {k: {'dims': ds[k].dims, 'shape': ds[k].shape, 'attrs': ds[k].attrs} for k in ds.data_vars},
#         'Global Attributes': ds.attrs
#     }
#     return info


# def standardize_dataset(ds: xr.Dataset, mapping: dict, var_renames: dict, global_meta: dict, var_meta: dict) -> xr.Dataset:
#     bound = [v for v in ds.variables if v.endswith('_bnds')]
#     safe_renames = {k: v for k, v in var_renames.items() if k not in bound}
#     if safe_renames:
#         ds = ds.rename(safe_renames)
#     for dim in ('time', 'lat', 'lon'):
#         src = mapping.get(dim)
#         if src and src != 'None':
#             if src in ds.data_vars:
#                 ds = ds.set_coords(src)
#             ds = ds.rename({src: dim})
#     other = {o: n for o, n in mapping.items() if o not in ('time','lat','lon')}
#     for old, new in other.items():
#         if old in ds.dims and new and not old.endswith('_bnds'):
#             ds = ds.rename({old: new})
#     for k, v in global_meta.items():
#         ds.attrs[k] = v
#     for var, attrs in var_meta.items():
#         if var in ds.data_vars and var not in bound:
#             for name, val in attrs.items():
#                 ds[var].attrs[name] = val
#     return ds


# def aggregate_extra_dims(ds: xr.Dataset, extra_dims: list, method: str) -> xr.Dataset:
#     """
#     Aggregate (e.g., mean, min, max, median) across extra dimensions.
#     """
#     if not extra_dims:
#         return ds
#     if not hasattr(ds, method):
#         raise ValueError(f"Invalid aggregation method: {method}")
#     return getattr(ds, method)(dim=extra_dims)


# def slice_extra_dims(ds: xr.Dataset, extra_dims: list) -> dict:
#     """
#     Return a dict of filenames to Dataset slices for each index in extra dimensions.

#     Args:
#         ds (xr.Dataset): Dataset to slice
#         extra_dims (list): List of dimension names to slice along

#     Returns:
#         dict: Dictionary mapping filenames to dataset slices
#     """
#     slices = {}

#     # Handle single dimension case
#     if len(extra_dims) == 1:
#         dim = extra_dims[0]
#         length = ds.dims.get(dim, 0)
#         for idx in range(length):
#             # Get dimension value for better filename
#             try:
#                 dim_val = ds[dim].values[idx]
#                 # Format the value for filename (handle different types)
#                 if hasattr(dim_val, 'strftime'):  # datetime
#                     val_str = dim_val.strftime('%Y%m%d')
#                 elif isinstance(dim_val, (int, float)):
#                     val_str = f"{dim_val}"
#                 else:
#                     val_str = str(dim_val).replace(' ', '_').replace('/', '-')
#                 fname = f"{dim}_{val_str}_standardized.nc"
#             except:
#                 # Fallback to index if we can't get the value
#                 fname = f"{dim}_{idx}_standardized.nc"

#             sl = ds.isel({dim: idx}).drop_dims(dim)
#             slices[fname] = sl

#     # Handle multiple dimensions case with a more organized approach
#     else:
#         # Create a recursive function to handle multiple dimensions
#         def slice_recursive(dataset, dims, current_dims=None, current_indices=None):
#             if current_dims is None:
#                 current_dims = []
#             if current_indices is None:
#                 current_indices = []

#             if not dims:
#                 # Base case: all dimensions processed, create filename and add slice
#                 parts = []
#                 for d, i in zip(current_dims, current_indices):
#                     try:
#                         val = dataset[d].values[i]
#                         if hasattr(val, 'strftime'):
#                             val_str = val.strftime('%Y%m%d')
#                         else:
#                             val_str = str(val).replace(' ', '_').replace('/', '-')
#                         parts.append(f"{d}_{val_str}")
#                     except:
#                         parts.append(f"{d}_{i}")

#                 fname = "_".join(parts) + "_standardized.nc"

#                 # Create selection dict for all dimensions at once
#                 sel_dict = {d: i for d, i in zip(current_dims, current_indices)}
#                 slice_ds = dataset.isel(sel_dict).drop_dims(current_dims)
#                 slices[fname] = slice_ds
#                 return

#             # Recursive case: process next dimension
#             dim = dims[0]
#             remaining_dims = dims[1:]
#             length = dataset.dims.get(dim, 0)

#             for idx in range(length):
#                 slice_recursive(
#                     dataset,
#                     remaining_dims,
#                     current_dims + [dim],
#                     current_indices + [idx]
#                 )

#         # Start recursion with all extra dimensions
#         slice_recursive(ds, extra_dims)

#     return slices


# def save_standardized_netcdf(ds: xr.Dataset, filename: str = 'standardized_netcdf.nc') -> str:
#     ds.to_netcdf(filename)
#     return filename
