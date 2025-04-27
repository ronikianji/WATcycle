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
