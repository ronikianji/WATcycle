# import numpy as np
# import pandas as pd
# import pymannkendall as mk
# import ruptures as rpt

# def calculate_sens_slopes(df: pd.DataFrame, value_col: str = 'value', time_col: str = 'ordinal_time') -> np.ndarray:
#     """
#     Calculate pairwise slopes for the time series using vectorized operations.

#     Args:
#         df: DataFrame containing time series data.
#         value_col: Column name for the observed values.
#         time_col: Column name for the numeric time (e.g., ordinal days).

#     Returns:
#         np.ndarray: Array of computed slopes.
#     """
#     values = df[value_col].values
#     times = df[time_col].values
#     # Get upper triangular indices to avoid duplicate pairs
#     i, j = np.triu_indices(len(values), k=1)
#     dt = times[j] - times[i]
#     valid = dt != 0
#     slopes = (values[j][valid] - values[i][valid]) / dt[valid]
#     return slopes

# def compute_sen_summary(slopes: np.ndarray) -> dict:
#     """
#     Compute summary statistics for Sen's slope, including uncertainty and conversion
#     to yearly and monthly units (assuming time in days).

#     Args:
#         slopes: Array of pairwise slopes.

#     Returns:
#         dict: Dictionary with keys 'Sen Slope', 'Slope (yearly)', 'Slope (monthly)',
#               'Uncertainty', 'Uncertainty (yearly)', 'Uncertainty (monthly)'.
#     """
#     if len(slopes) == 0:
#         return {
#             'Sen Slope': np.nan,
#             'Slope (yearly)': np.nan,
#             'Slope (monthly)': np.nan,
#             'Uncertainty': np.nan,
#             'Uncertainty (yearly)': np.nan,
#             'Uncertainty (monthly)': np.nan
#         }
#     sen_slope = np.median(slopes)
#     se = 1.96 * (np.std(slopes, ddof=1) / np.sqrt(len(slopes)))
#     slope_yearly = sen_slope * 365
#     slope_monthly = slope_yearly / 12
#     se_yearly = se * 365
#     se_monthly = se_yearly / 12
#     return {
#         'Sen Slope': sen_slope,
#         'Slope (yearly)': slope_yearly,
#         'Slope (monthly)': slope_monthly,
#         'Uncertainty': se,
#         'Uncertainty (yearly)': se_yearly,
#         'Uncertainty (monthly)': se_monthly
#     }

# def generate_trend_line(df: pd.DataFrame, slope: float, value_col: str = 'value', time_col: str = 'ordinal_time') -> pd.Series:
#     """
#     Generate a robust trend line using the provided Sen's slope. Instead of using the first
#     data point as the intercept, compute the intercept as:

#         intercept = median(y) - slope * median(x)

#     This provides a trend line centered on the overall data.

#     Args:
#         df: DataFrame containing the time series.
#         slope: Sen's slope value.
#         value_col: Column name for the observed values.
#         time_col: Column name for numeric time.

#     Returns:
#         pd.Series: Trend line values corresponding to df[time_col].
#     """
#     x = df[time_col].values
#     y = df[value_col].values
#     intercept = np.median(y) - slope * np.median(x)
#     return slope * x + intercept

# def detect_change_points(signal: np.ndarray, penalty: int = 6, min_size: int = 10) -> list:
#     """
#     Detect change points in the given signal using the PELT algorithm with an RBF model.
#     Optionally downsample if the signal is too long.

#     Args:
#         signal: 1D array of observed values.
#         penalty: Penalty value for the detection algorithm.
#         min_size: Minimum segment length for detection.

#     Returns:
#         list: Indices indicating the detected change points.
#     """
#     try:
#         # Downsample if the signal is long to improve speed
#         if len(signal) > 5000:
#             signal = np.mean(signal.reshape(-1, 5), axis=1)
#         algo = rpt.Pelt(model="rbf", min_size=min_size).fit(signal)
#         return algo.predict(pen=penalty)
#     except Exception as e:
#         raise RuntimeError(f"Error detecting change points: {e}")

# def mann_kendall_test(df: pd.DataFrame, value_col: str = 'value') -> dict:
#     """
#     Conduct a Mann-Kendall test on the given time series.

#     Args:
#         df: DataFrame containing the time series.
#         value_col: Column name for the variable.

#     Returns:
#         dict: Dictionary of test results.
#     """
#     try:
#         result = mk.original_test(df[value_col])
#         result_dict = {attr: getattr(result, attr) for attr in dir(result) if not attr.startswith('_') and not callable(getattr(result, attr))}
#         return result_dict
#     except Exception as e:
#         raise RuntimeError(f"Error in Mann-Kendall test: {e}")

# def analyze_segment(segment_df: pd.DataFrame, value_col: str = 'value', time_col: str = 'ordinal_time') -> dict:
#     """
#     Analyze a segment of the time series by computing the Mann-Kendall test, calculating Sen's slopes,
#     summarizing Sen's slope, and generating a trend line.

#     Args:
#         segment_df: DataFrame representing a segment of the time series.
#         value_col: Column name for the variable.
#         time_col: Column name for numeric time.

#     Returns:
#         dict: Dictionary containing the Mann-Kendall test result, Sen's slope summary, and the trend line.
#     """
#     if len(segment_df) < 3:
#         return None
#     try:
#         mk_result = mann_kendall_test(segment_df, value_col=value_col)
#         slopes = calculate_sens_slopes(segment_df, value_col=value_col, time_col=time_col)
#         sen_summary = compute_sen_summary(slopes)
#         trend_line = generate_trend_line(segment_df, sen_summary['Sen Slope'], value_col=value_col, time_col=time_col)
#         return {
#             'mk_result': mk_result,
#             'sen_summary': sen_summary,
#             'trend_line': trend_line
#         }
#     except Exception as e:
#         print(f"Segment analysis error: {e}")
#         return None




# # utils/trend_analysis_utils.py

# """
# This module provides core functions for time series analysis, including:
# - Calculation of Sen's slope via pairwise slopes,
# - Computation of uncertainty and conversion to different units,
# - Generation of robust trend lines,
# - Detection of change points in a time series,
# - Mann–Kendall test execution, and
# - Segment-wise analysis.
# """

# import numpy as np
# import pandas as pd
# import pymannkendall as mk
# import ruptures as rpt
# import matplotlib.pyplot as plt
# from sklearn.linear_model import TheilSenRegressor  # Optional: for robust trend fitting

# def calculate_sens_slopes(df, value_col='value', time_col='ordinal_time'):
#     """
#     Calculate pairwise slopes for the time series.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the time series.
#         value_col (str): Column name of the variable to analyze.
#         time_col (str): Column name representing time in numeric form (e.g., ordinal days).

#     Returns:
#         np.ndarray: Array of computed slopes.
#     """
#     slopes = []
#     n = len(df)
#     # Iterate over all unique pairs (i, j) with j > i
#     for i in range(n):
#         for j in range(i + 1, n):
#             dt = df[time_col].iloc[j] - df[time_col].iloc[i]
#             if dt != 0:
#                 slope = (df[value_col].iloc[j] - df[value_col].iloc[i]) / dt
#                 slopes.append(slope)
#     if slopes:
#         return np.array(slopes)
#     else:
#         raise ValueError("Not enough data points to calculate slopes.")

# def compute_sen_summary(slopes):
#     """
#     Compute Sen's slope summary, including median slope and standard error,
#     and convert the slope to yearly and monthly units (assuming time in days).

#     Parameters:
#         slopes (np.ndarray): Array of slopes.

#     Returns:
#         dict: A dictionary with Sen's slope and its uncertainty in original, yearly, and monthly units.
#     """
#     if len(slopes) == 0:
#         raise ValueError("Empty slopes array provided.")

#     s = np.std(slopes)
#     n = len(slopes)
#     se = s / np.sqrt(n) if n > 0 else np.nan
#     sen_slope = np.median(slopes)

#     # Assuming time is in days, convert to yearly and monthly slopes:
#     slope_yearly = sen_slope * 365
#     slope_monthly = slope_yearly / 12
#     se_yearly = se * 365
#     se_monthly = se_yearly / 12

#     return {
#         'Sen Slope': sen_slope,
#         'Slope (yearly)': slope_yearly,
#         'Slope (monthly)': slope_monthly,
#         'Uncertainty': se,
#         'Uncertainty (yearly)': se_yearly,
#         'Uncertainty (monthly)': se_monthly
#     }

# def generate_trend_line(df, slope, value_col='value', time_col='ordinal_time'):
#     """
#     Generate a trend line for the time series using the provided Sen's slope.
#     Instead of starting at the first data point, this version calculates the intercept
#     as the difference between the median value and slope times the median time value,
#     yielding a more robust fit.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the time series.
#         slope (float): Sen's slope value.
#         value_col (str): Column name for the variable.
#         time_col (str): Column name for the numeric time.

#     Returns:
#         pd.Series: Trend line values computed for each time point.
#     """
#     x = df[time_col]
#     y = df[value_col]
#     # Compute median intercept to minimize bias
#     intercept = np.median(y) - slope * np.median(x)
#     trend_line = slope * x + intercept
#     return trend_line

# def detect_change_points(signal, penalty=6):
#     """
#     Detect change points in the signal using the PELT algorithm with an RBF model.

#     Parameters:
#         signal (np.ndarray): 1D array of time series values.
#         penalty (int): Penalty value for the change point detection algorithm.

#     Returns:
#         list: Indices indicating change points in the signal.
#     """
#     try:
#         algo = rpt.Pelt(model="rbf").fit(signal)
#         change_points = algo.predict(pen=penalty)
#         return change_points
#     except Exception as e:
#         raise RuntimeError(f"Error in detect_change_points: {e}")

# def mann_kendall_test(df, value_col='value'):
#     """
#     Conduct a Mann-Kendall trend test on the time series data.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the time series.
#         value_col (str): Column name of the variable to test.

#     Returns:
#         dict: A dictionary of the Mann-Kendall test result attributes.
#     """
#     try:
#         result = mk.original_test(df[value_col])
#         # Convert test result attributes to a dictionary
#         result_dict = {
#             attr: getattr(result, attr)
#             for attr in dir(result)
#             if not attr.startswith('_') and not callable(getattr(result, attr))
#         }
#         return result_dict
#     except Exception as e:
#         raise RuntimeError(f"Error in mann_kendall_test: {e}")

# def analyze_segment(segment_df, value_col='value', time_col='ordinal_time'):
#     """
#     Perform a complete analysis on a time series segment, including:
#       - Mann-Kendall trend test,
#       - Calculation of pairwise slopes and Sen's slope summary,
#       - Generation of a trend line.

#     Parameters:
#         segment_df (pd.DataFrame): DataFrame for the segment.
#         value_col (str): Column name for the variable.
#         time_col (str): Column name for the numeric time.

#     Returns:
#         dict: A dictionary with keys:
#               'mk_result' : Mann-Kendall test result dictionary,
#               'sen_summary': Dictionary of Sen's slope summary,
#               'trend_line': pd.Series with trend line values.
#     """
#     if len(segment_df) < 2:
#         raise ValueError("Segment does not have enough data points for analysis.")

#     # Perform Mann-Kendall test
#     mk_result = mann_kendall_test(segment_df, value_col=value_col)

#     # Calculate pairwise slopes and compute Sen's summary
#     slopes = calculate_sens_slopes(segment_df, value_col=value_col, time_col=time_col)
#     sen_summary = compute_sen_summary(slopes)

#     # Generate a trend line based on the computed Sen's slope
#     trend_line = generate_trend_line(segment_df, sen_summary['Sen Slope'], value_col=value_col, time_col=time_col)

#     return {
#         'mk_result': mk_result,
#         'sen_summary': sen_summary,
#         'trend_line': trend_line
#     }
