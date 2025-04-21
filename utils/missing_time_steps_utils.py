import pandas as pd
import numpy as np
import xarray as xr

def find_missing_time_steps(df, time_col, frequency, base_date=None):
    """
    Identifies missing time steps in a DataFrame based on a specified time column and frequency.

    Parameters:
    - df: pandas DataFrame containing the time column.
    - time_col: name of the column with datetime information.
    - frequency: one of 'daily', 'monthly', or 'yearly'.
    - base_date: Optional base date string (e.g., '2002-01-01T00:00:00') to compute day offsets.

    Returns:
    - missing_df: DataFrame with a column "Missing_Date" listing the missing time steps.
      If base_date is provided, an additional column "Days_Since_{base_date}" is included.
    """
    if time_col not in df.columns:
        raise ValueError(f"Column '{time_col}' not found in the DataFrame")

    # Ensure time column is datetime
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])

    # Map frequency to pandas frequency string
    freq_map = {
        "daily": "D",
        "monthly": "MS",  # Month Start
        "yearly": "YS"    # Year Start
    }
    if frequency not in freq_map:
        raise ValueError("Frequency must be one of 'daily', 'monthly', or 'yearly'")

    freq = freq_map[frequency]

    # Generate the full time range
    time_sorted = df[time_col].sort_values()
    full_range = pd.date_range(start=time_sorted.min(), end=time_sorted.max(), freq=freq)

    # Identify missing times
    existing = pd.to_datetime(df[time_col].dropna().unique())
    missing_times = full_range.difference(existing)

    missing_df = pd.DataFrame({"Missing_Date": missing_times})
    if base_date:
        base = pd.to_datetime(base_date)
        missing_df[f"Days_Since_{base_date}"] = (missing_df["Missing_Date"] - base).dt.days

    return missing_df

def generate_missing_timesteps_netcdf(ds: xr.Dataset, missing_times: list) -> xr.Dataset:
    """
    Generates a new xarray.Dataset by adding missing time steps to the dataset.
    For each missing time, creates a new time slice with the same lat/lon coordinates
    and fills all data variables (that have 'time' as a dimension) with NaN.

    Parameters:
    - ds: Original xarray.Dataset that has been aligned (with standard time, lat, lon coordinates).
    - missing_times: List of missing time steps (as datetime-like objects).

    Returns:
    - new_ds: xarray.Dataset containing the original data plus new time slices for missing times.
    """
    # Ensure missing_times is a sorted list of timestamps
    missing_times = pd.to_datetime(missing_times).sort_values()

    # Get the coordinate values from the original dataset
    if "lat" not in ds.coords or "lon" not in ds.coords:
        raise ValueError("Dataset must have 'lat' and 'lon' coordinates.")

    lat_vals = ds["lat"].values
    lon_vals = ds["lon"].values

    # Create a new dataset for the missing time steps:
    # For variables that depend on time, create arrays of shape (len(missing_times), len(lat_vals), len(lon_vals))
    new_data_vars = {}
    for var in ds.data_vars:
        # Only update variables that have 'time' as a dimension
        if "time" in ds[var].dims:
            new_shape = (len(missing_times), len(lat_vals), len(lon_vals))
            # Fill with NaN (using float32 as a common type; adjust if needed)
            new_data_vars[var] = (("time", "lat", "lon"), np.full(new_shape, np.nan, dtype=np.float32))

    # Create a new Dataset with the missing time slices
    new_ds = xr.Dataset(
        data_vars=new_data_vars,
        coords={
            "time": ("time", missing_times),
            "lat": ("lat", lat_vals),
            "lon": ("lon", lon_vals)
        },
        attrs={"note": "This dataset contains padded missing timesteps filled with NaN."}
    )

    # Combine the original dataset with the new dataset
    combined_ds = xr.concat([ds, new_ds], dim="time")
    # Sort by time to ensure chronological order
    combined_ds = combined_ds.sortby("time")

    return combined_ds
