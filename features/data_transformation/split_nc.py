# features/data_transformation/split_nc.py
import os
import tempfile
import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
from io import BytesIO

from utils.file_handler import load_dataset
from utils.split_nc_utils import split_netcdf_by_index, split_netcdf_by_label, split_netcdf_by_group, create_zip_from_datasets

def split_netcdf_ui():
    st.title("✂️ Split NetCDF File")

    st.markdown("""
    This tool allows you to divide your NetCDF file into smaller parts using different methods:

    - ** Index-based**: Split into chunks of equal size
    - ** Label-based**: Extract a specific range of values
    """)

    # Check for uploaded NetCDF file in session state
    if "uploaded_nc_file" not in st.session_state:
        st.warning("⚠️ Please upload a NetCDF file in the Upload Files section first!")
        return

    try:
        # Load the dataset
        ds = load_dataset()

        # Dataset Preview in an expander
        with st.expander("📊 View Original Dataset", expanded=False):
            st.write(ds)

        # Select splitting method with better styling
        st.subheader("⚙️ Split Settings")
        method = st.radio(
            "Select splitting method:",
            options=["Index-based", "Label-based"],  # Removed "Group-by"
            horizontal=True,
            help="Choose how to divide your dataset"
        )

        split_files = None

        if method == "Index-based":
            st.info("💡 This method divides your dataset into chunks of equal size")

            dim = st.selectbox(
                "Select dimension to split on:",
                options=list(ds.dims.keys()),
                index=0,
                help="The dimension along which to divide the data"
            )

            chunk_size = st.number_input(
                "Number of indices per split:",
                min_value=1,
                value=10,
                step=1,
                help="How many points to include in each chunk"
            )

            if st.button("🔄 Start Splitting", help="Begin the splitting process"):
                with st.spinner("Dividing dataset into chunks..."):
                    try:
                        chunks = split_netcdf_by_index(ds, dim=dim, chunk_size=chunk_size)
                        split_files = create_zip_from_datasets(chunks, base_filename=f"chunk_{dim}_")
                        st.success(f"✅ Dataset successfully split into {len(chunks)} chunks!")
                    except Exception as e:
                        st.error(f"❌ Error during index-based splitting: {e}")

        elif method == "Label-based":
            st.info("💡 This method extracts a specific range of values along a coordinate")

            # For label-based splitting, we assume the dimension is a coordinate
            dim = st.selectbox(
                "Select coordinate to slice on:",
                options=list(ds.coords.keys()),
                index=0,
                help="The coordinate along which to extract data"
            )

            # Get min/max values for the selected coordinate
            try:
                min_val = ds[dim].values.min()
                max_val = ds[dim].values.max()

                # Format values nicely for display
                if np.issubdtype(ds[dim].dtype, np.datetime64):
                    min_val = pd.to_datetime(min_val).strftime('%Y-%m-%d')
                    max_val = pd.to_datetime(max_val).strftime('%Y-%m-%d')
                else:
                    min_val = str(min_val)
                    max_val = str(max_val)

                col1, col2 = st.columns(2)
                with col1:
                    start_val = st.text_input(f"Start value for {dim}:", value=min_val)
                with col2:
                    end_val = st.text_input(f"End value for {dim}:", value=max_val)

                if st.button("🔄 Start Slicing", help="Extract the specified range"):
                    with st.spinner("Extracting data slice..."):
                        try:
                            ds_slice = split_netcdf_by_label(ds, dim=dim, start_value=start_val, end_value=end_val)
                            # For label-based, we return one subset (not a list)
                            split_files = create_zip_from_datasets([ds_slice], base_filename=f"slice_{dim}_")
                            st.success("✅ Data slice extracted successfully!")
                        except Exception as e:
                            st.error(f"❌ Error during label-based splitting: {e}")
            except Exception as e:
                st.error(f"❌ Error processing coordinate values: {e}")

        # Commented out Group-by section
        # elif method == "Group-by":
        #     st.info("💡 This method organizes your data by time periods")
        #
        #     # Grouping is typically applied along a time coordinate
        #     time_coords = [coord for coord in ds.coords if 'time' in coord.lower()]
        #     if not time_coords:
        #         time_coords = list(ds.coords.keys())
        #
        #     group_dim = st.selectbox(
        #         "Select time coordinate to group by:",
        #         options=time_coords,
        #         index=0,
        #         help="The time coordinate to use for grouping"
        #     )
        #
        #     freq_options = {
        #         "D": "Daily",
        #         "M": "Monthly",
        #         "Y": "Yearly"
        #     }
        #
        #     group_freq = st.selectbox(
        #         "Select grouping frequency:",
        #         options=list(freq_options.keys()),
        #         format_func=lambda x: freq_options[x],
        #         index=1,
        #         help="How to group your time data"
        #     )
        #
        #     if st.button("🔄 Start Grouping", help="Begin the grouping process"):
        #         with st.spinner("Organizing data by time periods..."):
        #             try:
        #                 groups = split_netcdf_by_group(ds, dim=group_dim, group_freq=group_freq)
        #                 # groups is a dictionary; get list of datasets from its values
        #                 group_list = list(groups.values())
        #                 split_files = create_zip_from_datasets(group_list, base_filename=f"group_{group_dim}_")
        #                 st.success(f"✅ Dataset successfully split into {len(groups)} time periods!")
        #             except Exception as e:
        #                 st.error(f"❌ Error during group-by splitting: {e}")

        # Download option if splitting was successful - styled like merge_netcdf.py
        if split_files:
            st.subheader("💾 Save Results")
            with st.spinner("Preparing files for download..."):
                st.download_button(
                    label="📥 Download Split Files (ZIP)",
                    data=split_files,
                    file_name="split_files.zip",
                    mime="application/zip",
                    help="Save the split files to your computer"
                )

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
