import streamlit as st
import pandas as pd
import xarray as xr
import os
from utils.file_handler import save_uploaded_file
from utils.netcdf_standardizer_utils import standardize_dataset

def csv_to_netcdf():
    st.title("🔄 CSV to NetCDF Converter")

    uploaded_file = st.file_uploader(
        "Choose your CSV file",
        type=["csv"],
        key="csv_upload",
    )

    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file, "csv")
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        try:
            df = pd.read_csv(file_path)
            st.subheader("📊 Data Preview")
            st.dataframe(df.head())

            # Column Selection
            st.subheader("📋 Column Selection")
            columns = df.columns.tolist()
            selected_columns = st.multiselect(
                "Select columns:",
                columns,
                default=columns,
                help="Select the columns you want to include in your NetCDF file"
            )

            if not selected_columns:
                st.warning("⚠️ Please select at least one column to proceed.")
                return

            # Standardization Settings
            st.subheader("🎯 Column Mapping")
            st.markdown("Map your columns to standard NetCDF dimensions")

            mapping = {
                "time": st.selectbox("Time dimension", ["None"] + columns),
                "lat": st.selectbox("Latitude dimension", ["None"] + columns),
                "lon": st.selectbox("Longitude dimension", ["None"] + columns)
            }

            # Global Attributes
            st.subheader("📝 Global Attributes")
            with st.expander("Add global attributes"):
                title = st.text_input("Title", "CSV converted NetCDF")
                institution = st.text_input("Institution", "WATcycle")
                source = st.text_input("Source", "CSV file")

                global_meta = {
                    "title": title,
                    "institution": institution,
                    "source": source,
                    "creation_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # File naming and conversion
            st.subheader("💾 Output Settings")
            netcdf_filename = st.text_input(
                "Name your NetCDF file:",
                "output_file",
                help="Enter a name for your NetCDF file (without .nc extension)"
            )

            if st.button("🔄 Convert to NetCDF"):
                with st.spinner("Converting and standardizing your data..."):
                    # Create initial dataset
                    df_subset = df[selected_columns]
                    ds = xr.Dataset.from_dataframe(df_subset)

                    # Standardize the dataset
                    ds = standardize_dataset(
                        ds=ds,
                        mapping=mapping,
                        var_renames={},  # No renaming in this case
                        global_meta=global_meta,
                        var_meta={}  # No variable metadata in this case
                    )

                    output_path = os.path.join(os.getcwd(), f"{netcdf_filename}.nc")
                    ds.to_netcdf(output_path)

                    st.success("✨ Download complete!")

                    # # Download section
                    # st.subheader("📥 Download")
                    # with open(output_path, 'rb') as f:
                    #     st.download_button(
                    #         label="Download NetCDF File",
                    #         data=f.read(),
                    #         file_name=f"{netcdf_filename}.nc",
                    #         mime="application/x-netcdf",
                    #         help="Click to download your standardized NetCDF file"
                    #     )

        except pd.errors.EmptyDataError:
            st.error("❌ The uploaded file appears to be empty.")
        except pd.errors.ParserError:
            st.error("❌ Unable to parse the CSV file. Please check the file format.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
