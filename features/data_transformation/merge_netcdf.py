# features/data_transformation/merge_netcdf.py
import os
import tempfile
import streamlit as st
import xarray as xr
from io import BytesIO

from utils.merge_netcdf_utils import merge_netcdf_concat, merge_netcdf_merge, smart_merge_netcdf

def merge_netcdf_ui():
    st.title("🔗 Merge NetCDF Files")

    st.markdown("""
    This tool allows you to combine multiple NetCDF files using different methods:

    - ** Concatenate**: Stack datasets along a dimension (e.g., combine time series)
    - ** Merge**: Combine different variables from files with matching coordinates
    - ** Smart Merge**: Advanced concatenation with handling for overlapping data
    """)

    # Method selection with better styling
    st.subheader("⚙️ Merge Settings")
    merge_method = st.radio(
        "Select merge method:",
        options=["Concatenate", "Merge", "Smart Merge"],
        horizontal=True,
        help="Choose how to combine your files"
    )

    # Dynamic options based on method
    concat_dim = None
    duplicate_policy = None

    if merge_method == "Concatenate":
        st.info("💡 Concatenation joins datasets along a single dimension ")
        concat_dim = st.selectbox(
            "Select dimension for concatenation:",
            options=["time", "lat", "lon"],
            index=0,
            help="The dimension along which files will be stacked"
        )

    elif merge_method == "Smart Merge":
        st.info("💡 Smart Merge handles overlapping values when combining datasets")
        concat_dim = st.selectbox(
            "Select dimension for merging:",
            options=["time", "lat", "lon"],
            index=0
        )
        duplicate_policy = st.selectbox(
            "How to handle duplicate values:",
            options=["drop", "average"],
            index=0,
            help="Drop: keep first occurrence, Average: calculate mean of duplicates"
        )

    # File uploader with better instructions
    st.subheader("📤 Upload Files")
    uploaded_files = st.file_uploader(
        "Select multiple NetCDF files to merge",
        type=["nc"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        file_paths = []
        with st.spinner(f"Processing {len(uploaded_files)} files..."):
            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp_file:
                    tmp_file.write(file.getbuffer())
                    file_paths.append(tmp_file.name)

        st.success(f"✅ Successfully loaded {len(file_paths)} file(s)")

        # Process button
        if st.button("🔄 Start Merging",):
            try:
                with st.spinner("Merging your NetCDF files..."):
                    if merge_method == "Concatenate":
                        merged_ds = merge_netcdf_concat(file_paths, dim=concat_dim)
                    elif merge_method == "Merge":
                        merged_ds = merge_netcdf_merge(file_paths)
                    elif merge_method == "Smart Merge":
                        merged_ds = smart_merge_netcdf(file_paths, dim=concat_dim, duplicate_policy=duplicate_policy)
                    else:
                        st.error("Invalid merge method selected.")
                        return

                # Results section
                st.subheader("📊 Results")
                st.success("✅ Merging completed successfully!")

                with st.expander("View Merged Dataset Details", expanded=True):
                    st.write(merged_ds)

                # Download section
                st.subheader("💾 Save Results")
                with st.spinner("Preparing file for download..."):
                    merged_nc = merged_ds.to_netcdf()
                    st.download_button(
                        label="📥 Download Merged NetCDF",
                        data=merged_nc,
                        file_name="merged_dataset.nc",
                        mime="application/x-netcdf",
                        help="Save the merged file to your computer"
                    )
            except Exception as e:
                st.error(f"❌ Error during merging: {str(e)}")
            finally:
                # Clean up temporary files
                for fp in file_paths:
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
    else:
        st.info("Please upload at least two NetCDF files to merge")
