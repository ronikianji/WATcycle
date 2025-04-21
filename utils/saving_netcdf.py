import streamlit as st
import xarray as xr
import pandas as pd

def interactive_save_netcdf(df: pd.DataFrame, default_filename="output.nc"):
    st.subheader("💾 Save as NetCDF")

    st.markdown("Customize how your data will be saved to a NetCDF file.")

    with st.form("save_nc_form"):
        st.markdown("### 1️⃣ Select Dimensions (Optional)")
        columns = list(df.columns)

        time_dim = st.selectbox("Time Dimension", ["None"] + columns, index=0, key="save_dim_time")
        lat_dim = st.selectbox("Latitude Dimension", ["None"] + columns, index=0, key="save_dim_lat")
        lon_dim = st.selectbox("Longitude Dimension", ["None"] + columns, index=0, key="save_dim_lon")

        selected_dims = {}
        for label, value in zip(["time", "lat", "lon"], [time_dim, lat_dim, lon_dim]):
            if value != "None":
                selected_dims[label] = value

        st.markdown("### 2️⃣ Select Variables to Include (Optional)")
        selectable_vars = [col for col in columns if col not in selected_dims.values()]
        variables = st.multiselect("Variables to include in file", options=["None"] + selectable_vars, default=selectable_vars)

        st.markdown("### 3️⃣ Add Global Metadata")
        title = st.text_input("Title", value="Generated NetCDF file")
        institution = st.text_input("Institution", value="Your Institution")
        source = st.text_input("Source", value="Custom Toolbox")
        description = st.text_area("Description", value="This NetCDF file was created using a custom Streamlit toolbox.")

        st.markdown("### ✏️ Variable Metadata (Optional)")
        variable_metadata = {}
        if variables and variables != ["None"]:
            for var in variables:
                with st.expander(f"Metadata for variable: `{var}`"):
                    long_name = st.text_input(f"Long name for `{var}`", key=f"{var}_long_name")
                    units = st.text_input(f"Units for `{var}`", key=f"{var}_units")
                    standard_name = st.text_input(f"Standard name for `{var}` (optional)", key=f"{var}_std_name")

                    variable_metadata[var] = {
                        "long_name": long_name,
                        "units": units,
                        "standard_name": standard_name
                    }

        submit_save = st.form_submit_button("Save NetCDF File")

    if submit_save:
        try:
            # Filter DataFrame
            if variables != ["None"]:
                df_to_use = df[selected_dims.values()].join(df[variables]) if selected_dims else df[variables]
            else:
                df_to_use = df.copy()

            # Set index for conversion
            index_cols = list(selected_dims.values())
            if index_cols:
                df_to_use = df_to_use.set_index(index_cols)

            # Convert to xarray
            ds = df_to_use.to_xarray()

            # Assign global metadata
            ds.attrs["title"] = title
            ds.attrs["institution"] = institution
            ds.attrs["source"] = source
            ds.attrs["description"] = description

            # Assign variable-level metadata
            for var, attrs in variable_metadata.items():
                for attr_name, attr_value in attrs.items():
                    if attr_value:
                        ds[var].attrs[attr_name] = attr_value

            # Save to disk
            save_path = f"./{default_filename}"
            ds.to_netcdf(save_path)

            with open(save_path, "rb") as f:
                st.success("✅ NetCDF file saved successfully!")
                st.download_button("📥 Download NetCDF", data=f, file_name=default_filename, mime="application/netcdf")

            st.markdown("### 📦 Preview Saved Dataset")
            st.write(ds)

        except Exception as e:
            st.error(f"❌ Failed to save NetCDF file: {e}")
