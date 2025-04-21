# features/data_transformation/resample_netcdf.py
import os
import tempfile
import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
from io import BytesIO

from utils.file_handler import load_dataset
from utils.resample_utils import (
    interp_resample,
    coarsen_resample,
    # xesmf_regrid,
    groupby_resample,
    create_zip_from_datasets
)

def resample_netcdf_ui():
    st.title("🏁 Resample NetCDF Resolution")

    st.markdown("""
    This tool helps you change the spatial resolution of your NetCDF data.
    You can make your grid finer (interpolation) or coarser (aggregation).
    """)

    if "uploaded_nc_file" not in st.session_state:
        st.warning("⚠️ Please upload a NetCDF file in the Upload Files section first!")
        return

    try:
        ds = load_dataset()

        # Dataset Preview in an expander
        with st.expander("📊 View Original Dataset", expanded=False):
            st.write(ds)

        # Let the user select the resampling method
        st.subheader("⚙️ Resampling Settings")
        resample_method = st.radio(
            "Select resampling approach:",
            options=["Interpolation", "Coarsening"],
            horizontal=True,
            help="Choose how to change your data resolution"
        )

        ds_resampled = None

        if resample_method == "Interpolation":
            st.info("💡 Interpolation creates a finer grid by estimating values between existing points")

            # Generate new coordinate arrays for lat and lon
            try:
                lat_min = float(ds["lat"].values.min())
                lat_max = float(ds["lat"].values.max())
                lon_min = float(ds["lon"].values.min())
                lon_max = float(ds["lon"].values.max())

                st.markdown("#### 📏 Current Grid Resolution")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Latitude range: {lat_min:.2f}° to {lat_max:.2f}°")
                with col2:
                    st.write(f"Longitude range: {lon_min:.2f}° to {lon_max:.2f}°")

                new_res = st.number_input(
                    "Target resolution:",
                    min_value=0.01,
                    value=0.25,
                    step=0.01,
                    help="Lower values create a finer grid (e.g., 0.25 for 0.25°)"
                )

                new_lat = np.arange(lat_min, lat_max + new_res, new_res)
                new_lon = np.arange(lon_min, lon_max + new_res, new_res)
                new_coords = {"lat": new_lat, "lon": new_lon}

                st.markdown(f"New grid will have {len(new_lat)}×{len(new_lon)} points")

                method = st.selectbox(
                    "Interpolation method:",
                    options=["linear", "nearest"],
                    index=0,
                    help="Linear: smooth transitions, Nearest: preserves original values"
                )

                if st.button("🔄 Start Interpolation", help="Begin resampling process"):
                    with st.spinner("Creating finer resolution grid..."):
                        try:
                            ds_resampled = interp_resample(ds, new_coords, method=method)
                            st.success("✅ Interpolation successful!")
                        except Exception as e:
                            st.error(f"❌ Error during interpolation: {e}")

            except Exception as e:
                st.error(f"❌ Error extracting spatial coordinates: {e}")
                return

        elif resample_method == "Coarsening":
            st.info("💡 Coarsening creates a lower-resolution grid by aggregating neighboring cells")

            # User specifies coarsening factors
            col1, col2 = st.columns(2)
            with col1:
                lat_factor = st.number_input(
                    "Latitude coarsening factor:",
                    min_value=1,
                    value=2,
                    step=1,
                    help="Higher values create a coarser grid"
                )
            with col2:
                lon_factor = st.number_input(
                    "Longitude coarsening factor:",
                    min_value=1,
                    value=2,
                    step=1,
                    help="Higher values create a coarser grid"
                )

            factors = {"lat": lat_factor, "lon": lon_factor}

            agg_func = st.selectbox(
                "Aggregation method:",
                options=["mean", "sum"],
                index=0,
                help="Mean: average values, Sum: total values"
            )

            if st.button("🔄 Start Coarsening",):
                with st.spinner("Creating coarser resolution grid..."):
                    try:
                        ds_resampled = coarsen_resample(ds, factors, boundary="trim", func=agg_func)
                        st.success("✅ Coarsening successful!")
                    except Exception as e:
                        st.error(f"❌ Error during coarsening: {e}")

        # Results and download section
        if ds_resampled is not None:
            st.subheader("📊 Results")

            with st.expander("View Resampled Dataset", expanded=True):
                st.write(ds_resampled)

                # Show comparison of dimensions
                st.markdown("#### 📏 Resolution Comparison")
                comparison = pd.DataFrame({
                    "Dimension": list(ds.dims.keys()),
                    "Original Size": [ds.dims[dim] for dim in ds.dims],
                    "New Size": [ds_resampled.dims[dim] for dim in ds_resampled.dims if dim in ds.dims]
                })
                st.table(comparison)

            # Download section - updated to use the approach from merge_netcdf.py
            st.subheader("💾 Save Results")
            with st.spinner("Preparing file for download..."):
                try:
                    # Convert directly to bytes instead of using BytesIO
                    resampled_nc = ds_resampled.to_netcdf()
                    st.download_button(
                        label="📥 Download Resampled NetCDF",
                        data=resampled_nc,
                        file_name="resampled_dataset.nc",
                        mime="application/x-netcdf",
                        help="Save the resampled file to your computer"
                    )
                except Exception as e:
                    st.error(f"❌ Error preparing download: {e}")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
