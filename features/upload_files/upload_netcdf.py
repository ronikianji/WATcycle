import streamlit as st
import xarray as xr
from utils.file_handler import save_uploaded_file

def upload_netcdf():
    st.title("📊 NetCDF File Viewer")

    # Check if a file has already been uploaded and display it
    if "uploaded_nc_file" in st.session_state:
        st.info(f"Currently uploaded file: {st.session_state.uploaded_nc_file_name}")
        if st.button("Clear uploaded file"):
            del st.session_state.uploaded_nc_file
            del st.session_state.uploaded_nc_file_name
            st.rerun()  # Updated to new method

    # File uploader
    uploaded_file = st.file_uploader("Choose a NetCDF file", type=["nc"])

    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file, "nc")
        if file_path:
            st.session_state.uploaded_nc_file = file_path
            st.session_state.uploaded_nc_file_name = uploaded_file.name
            st.success(f"Uploaded file: {uploaded_file.name}")
            # Remove rerun to maintain state

    # Process the file if it exists in session state
    if "uploaded_nc_file" in st.session_state:
        file_path = st.session_state.uploaded_nc_file
        st.success("✅ Current file: " + st.session_state.uploaded_nc_file_name)

        try:
            ds = xr.open_dataset(file_path)

            st.subheader("Dataset Information")
            with st.expander("View Details"):
                st.write(ds.info())

            st.subheader("Dimensions & Coordinates")
            with st.expander("View Dimensions"):
                st.write(ds.dims)

            st.subheader("Variables")
            with st.expander("View Variables and Dimensions"):
                variable_list = list(ds.data_vars.keys())
                for variable in variable_list:
                    st.write(f"**{variable}**")
                    st.write(f"Dimensions: {ds[variable].dims}")

            st.subheader("Metadata (Attributes)")
            st.write(ds.attrs if ds.attrs else "No attributes found.")

            # DataFrame preview
            st.subheader("🧾 Convert to DataFrame")
            variable_selection = st.multiselect(
                "Select variables to include in DataFrame:", variable_list, default=[]
            )
            if variable_selection:
                df = ds[variable_selection].to_dataframe().reset_index()
                st.write("### Dataframe:")
                st.dataframe(df)

                csv = df.to_csv(index=False)
                st.download_button("Download DataFrame as CSV", data=csv, file_name="dataframe.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Error reading NetCDF file: {e}")
    else:
        st.warning("Please upload a NetCDF file.")

