# netcdf_standardizer.py
import streamlit as st
import xarray as xr
from io import BytesIO
from utils.netcdf_standardizer_utils import (
    get_dataset_info,
    standardize_dataset,
    aggregate_extra_dims,
    slice_extra_dims
)

def netcdf_standardizer_feature():
    st.title("📊 NetCDF Standardizer")
    st.markdown("Standardize your NetCDF file structure to ensure compatibility with WATcycle toolbox.")

    uploaded = st.file_uploader("Upload NetCDF file", type=["nc"])
    if not uploaded:
        st.info("👆 Upload a NetCDF file to begin")
        return
    try:
        ds = xr.open_dataset(BytesIO(uploaded.read()))
        st.success("✅ File loaded successfully")
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return

    st.subheader("Dataset Structure")
    with st.expander("View Current Structure"):
        st.json(get_dataset_info(ds))

    st.subheader("Map Required Dimensions")
    options = ["None"] + list(ds.coords.keys()) + list(ds.data_vars.keys())
    time_dim = st.selectbox("Time dimension", options)
    lat_dim = st.selectbox("Latitude dimension", options)
    lon_dim = st.selectbox("Longitude dimension", options)
    mapping = {
        "time": None if time_dim == "None" else time_dim,
        "lat": None if lat_dim == "None" else lat_dim,
        "lon": None if lon_dim == "None" else lon_dim
    }

    st.subheader("Global Metadata")
    gm = ds.attrs or {}
    global_meta = {
        "title": st.text_input("Title", gm.get("title", "")),
        "institution": st.text_input("Institution", gm.get("institution", "")),
        "source": st.text_input("Source", gm.get("source", "")),
        "description": st.text_area("Description", gm.get("description", ""))
    }

    mapped = [v for v in mapping.values() if v]
    extra_dims = [d for d in ds.dims if d not in mapped]
    do_agg = False
    agg_method = None
    export_slices = False
    if extra_dims:
        st.subheader("⚙️ Handle Extra Dimensions")
        do_agg = st.checkbox("Aggregate extra dimensions to 3D", help="Compute summary across extra dims")
        if do_agg:
            agg_method = st.selectbox("Aggregation method", ["mean", "min", "max", "median"], index=0)
        export_slices = st.checkbox("Export each slice separately", help="One file per extra-dim slice")

    if st.button("Standardize and Save"):
        try:
            ds_std = standardize_dataset(ds, mapping, global_meta)
            post_dims = set(ds_std.dims) - {"time", "lat", "lon"}

            if export_slices and post_dims:
                slices = slice_extra_dims(ds_std)
                for fname, slice_ds in slices.items():
                    data = slice_ds.to_netcdf()
                    st.download_button(f"Download {fname}", data,
                                       file_name=fname, mime="application/x-netcdf")
            else:
                if post_dims and do_agg and agg_method:
                    ds_std = aggregate_extra_dims(ds_std, agg_method)
                raw = ds_std.to_netcdf()
                st.download_button("💾 Download Standardized File", raw,
                                   file_name="standardized.nc", mime="application/x-netcdf")
            st.success("✅ Operation completed successfully!")
        except Exception as e:
            st.error(f"❌ Error during processing: {e}")
# st.info("Each exported file will contain the full time/lat/lon dimensions "
#                 "for one combination of the extra dimension values")

