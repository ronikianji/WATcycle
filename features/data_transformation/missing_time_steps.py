import streamlit as st
import pandas as pd
from datetime import datetime
from utils.file_handler import load_dataset_to_dataframe, load_dataset
from utils.missing_time_steps_utils import find_missing_time_steps, generate_missing_timesteps_netcdf

def missing_time_steps_ui():
    st.subheader("📅 Identify & Fill Missing Time Steps in Dataset")

    if "uploaded_nc_file" not in st.session_state:
        st.warning("⚠️ Please upload a NetCDF file first.")
        return

    # Load the aligned NetCDF dataset and also convert it to a DataFrame
    ds = load_dataset()  # This should load the aligned dataset (with standard variable names)
    df = load_dataset_to_dataframe()  # Returns a flattened DataFrame

    if "time" not in df.columns:
        st.error("❌ 'time' column not found. Ensure the file is aligned correctly.")
        return

    # Ensure 'time' is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        try:
            df["time"] = pd.to_datetime(df["time"])
        except Exception as e:
            st.error(f"❌ Could not convert 'time' to datetime: {e}")
            return

    # Frequency selection
    freq_option = st.radio("Select the frequency of your dataset:", options=["daily", "monthly", "yearly"], horizontal=True)

    # Optional base date for computing day offsets
    base_date_input = st.date_input("Optional: Set Base Date to Calculate Day Offsets", datetime(2002, 1, 1))
    base_date = pd.to_datetime(base_date_input)

    if st.button("🔍 Find & Fill Missing Time Steps"):
        try:
            with st.spinner("Analyzing time steps..."):
                # Detect missing time steps (returns a DataFrame)
                result_df = find_missing_time_steps(df, "time", freq_option, base_date)

            if result_df.empty:
                st.success(" No missing time steps found!")
            else:
                st.success(f"✅ Found {len(result_df)} missing time steps.")
                st.dataframe(result_df)

                # Download CSV of missing time steps
                csv = result_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Missing Time Steps CSV", csv, file_name="missing_time_steps.csv")

            # Generate new NetCDF with missing time steps filled with NaN
            with st.spinner("Generating NetCDF with padded missing time steps..."):
                missing_times = result_df["Missing_Date"].tolist()  # Ensure these are in a datetime-like format
                filled_ds = generate_missing_timesteps_netcdf(ds, missing_times)
                filled_filename = "netcdf_with_missing_timesteps.nc"
                filled_ds.to_netcdf(filled_filename)

            with open(filled_filename, "rb") as f:
                st.download_button("📦 Download NetCDF File", data=f, file_name=filled_filename, mime="application/x-netcdf")

        except Exception as e:
            st.error(f"❌ Error occurred: {e}")
