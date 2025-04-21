# utils/geospatial_utils.py

import os
import xarray as xr
from affine import Affine
from rasterio.features import geometry_mask
import geopandas as gpd
import streamlit as st

def calculate_transform(ds):
    lon = ds['lon'].values
    lat = ds['lat'].values
    lon_res = (lon[1] - lon[0])
    lat_res = (lat[1] - lat[0])
    transform = Affine.translation(lon[0] - lon_res / 2, lat[0] - lat_res / 2) * Affine.scale(lon_res, lat_res)
    return transform

def clip_dataset_with_shapefile(ds, shapefile):
    transform = calculate_transform(ds)
    geoms = shapefile.geometry.values
    mask = geometry_mask([geom for geom in geoms],
                         transform=transform,
                         invert=True,
                         out_shape=(ds.sizes['lat'], ds.sizes['lon']))
    mask_da = xr.DataArray(mask, dims=("lat", "lon"), coords={"lat": ds["lat"], "lon": ds["lon"]})
    clipped_ds = ds.where(mask_da, drop=True)
    return clipped_ds

def load_netcdf_with_engines(file_path):
    engines = ['netcdf4', 'scipy', 'h5netcdf']
    for engine in engines:
        try:
            ds = xr.open_dataset(file_path, engine=engine)
            st.success(f"✅ File loaded successfully with engine: {engine}")
            return ds
        except Exception as e:
            st.warning(f"❌ Failed to load with engine {engine}: {e}")
    raise ValueError("Unable to read the file with any supported engine.")
