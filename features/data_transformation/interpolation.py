# features/data_transformation/interpolate_netcdf.py
import os
import tempfile
import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
from io import BytesIO

from utils.file_handler import load_dataset
from utils.interpolation_utils import interpolate_na_along_dim, interpolate_na_all

def interpolate_netcdf_ui():
    st.title("🔍 Interpolate Missing Values")


    if "uploaded_nc_file" not in st.session_state:
        st.warning("⚠️ Please upload a NetCDF file in the Upload Files section first!")
        return

    try:
        ds = load_dataset()

        # Dataset Preview in an expander
        with st.expander("📊 View Dataset Summary", expanded=False):
            st.write(ds)

        st.subheader("⚙️ Interpolation Settings")

        # Interpolation mode selection
        interp_mode = st.radio(
            "Choose interpolation approach:",
            options=[
                "Fill NaNs along one dimension",
                "Fill NaNs across all dimensions"
            ],
            horizontal=True
        )

        # Method selection with help text
        method = st.selectbox(
            "Select interpolation method:",
            options=["linear", "nearest", "spline"],
            help="Linear: straight line between points\nNearest: uses closest value\nSpline: smooth curve fitting",
            index=0
        )

        ds_interp = None

        if interp_mode == "Fill NaNs along one dimension":
            st.info("💡 This method fills missing values along a single dimension (e.g., time or space)")
            dim = st.selectbox(
                "Select dimension for interpolation:",
                options=list(ds.dims.keys()),
                help="Choose the dimension along which to interpolate"
            )

            if st.button("🔄 Start Interpolation"):
                with st.spinner("📊 Interpolating missing values..."):
                    ds_interp = interpolate_na_along_dim(ds, dim, method=method)
                    st.success("✅ Interpolation complete!")

        else:  # Fill NaNs across all dimensions
            st.info("💡 This method fills missing values using all available dimensions")

            if st.button("🔄 Start Interpolation"):
                with st.spinner("📊 Interpolating missing values..."):
                    ds_interp = interpolate_na_all(ds, method=method)
                    st.success("✅ Interpolation complete!")

        # Results section
        if ds_interp is not None:
            st.subheader("📊 Results")

            # Show results in a single tab instead of trying to create two
            st.write("### Interpolated Dataset")
            st.write(ds_interp)

            # Download section
            st.subheader("💾 Save Results")
            with st.spinner("Preparing download..."):
                merged_nc = ds_interp.to_netcdf()
                st.download_button(
                    label="📥 Download Interpolated NetCDF",
                    data=merged_nc,
                    file_name="interpolated_data.nc",
                    mime="application/x-netcdf"
                )

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
