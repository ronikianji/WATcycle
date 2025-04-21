import xarray as xr
import pandas as pd
import numpy as np

def prepare_seasonal_df(ds: xr.Dataset, variable: str) -> pd.DataFrame:
    """
    Prepares time series data for seasonal analysis.

    Parameters:
        ds (xr.Dataset): Input dataset with time dimension
        variable (str): Variable name to analyze

    Returns:
        pd.DataFrame: Processed data with time, value, month, and year columns
    """
    try:
        # Process time dimension
        time = pd.to_datetime(ds["time"].values)

        # Average over spatial dimensions
        dims_to_average = [dim for dim in ds[variable].dims if dim != "time"]
        values = ds[variable].mean(dim=dims_to_average).values

        # Create and process DataFrame
        df = pd.DataFrame({
            "time": time,
            "value": values
        }).dropna()

        # Extract temporal components
        df["month"] = df["time"].dt.month
        df["year"] = df["time"].dt.year

        return df
    except Exception as e:
        raise RuntimeError(f"Error in seasonal data preparation: {str(e)}")

def compute_monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates comprehensive monthly statistics.

    Parameters:
        df (pd.DataFrame): Input DataFrame with 'month' and 'value' columns

    Returns:
        pd.DataFrame: Monthly statistics including mean, std, min, max
    """
    try:
        monthly = (df.groupby("month")["value"]
                  .agg(["mean", "std", "min", "max"])
                  .reset_index())

        monthly.columns = ["month", "Mean", "Std", "Min", "Max"]
        return monthly
    except Exception as e:
        raise RuntimeError(f"Error computing monthly statistics: {str(e)}")

def compute_monthly_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates deviations from monthly means.

    Parameters:
        df (pd.DataFrame): Input DataFrame with time series data

    Returns:
        pd.DataFrame: Original data with additional 'anomaly' column
    """
    try:
        # Calculate monthly means
        monthly_means = df.groupby("month")["value"].transform("mean")

        # Compute anomalies
        df = df.copy()
        df["anomaly"] = df["value"] - monthly_means

        return df
    except Exception as e:
        raise RuntimeError(f"Error computing anomalies: {str(e)}")
