# # utils/plotting_utils.py

# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import numpy as np
# import pandas as pd

# def set_common_plot_style(ax, xlabel="Time", ylabel="Value", title="Time Series Analysis"):
#     """
#     Apply a common style to a matplotlib Axes object.

#     Parameters:
#         ax (matplotlib.axes.Axes): The axes to style.
#         xlabel (str): Label for the x-axis.
#         ylabel (str): Label for the y-axis.
#         title (str): Plot title.
#     """
#     ax.set_xlabel(xlabel, fontsize=14, fontweight='bold', color='black')
#     ax.set_ylabel(ylabel, fontsize=14, fontweight='bold', color='black')
#     ax.set_title(title, fontsize=16, fontweight='bold')
#     ax.tick_params(axis='both', which='major', labelsize=12, labelcolor='black')
#     ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.7, color='gray')

#     # Improve date formatting on x-axis if dates are used
#     try:
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#         plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
#     except Exception:
#         pass  # In case x-axis is not date-formatted

# def plot_time_series_with_trend(df, trend_line, time_col='time', value_col='value',
#                                 data_label="Original Data", trend_label="Trend Line", figsize=(14,6)):
#     """
#     Plot a time series with an overlaid trend line.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the time series.
#         trend_line (pd.Series or np.array): Trend line values corresponding to df[time_col].
#         time_col (str): Name of the time column in df.
#         value_col (str): Name of the variable column in df.
#         data_label (str): Label for the original data line.
#         trend_label (str): Label for the trend line.
#         figsize (tuple): Figure size.

#     Returns:
#         matplotlib.figure.Figure: The generated figure.
#     """
#     fig, ax = plt.subplots(figsize=figsize)
#     ax.plot(df[time_col], df[value_col], label=data_label, color='black', linewidth=1.5)
#     ax.plot(df[time_col], trend_line, label=trend_label, color='red', linestyle='--', linewidth=2)
#     set_common_plot_style(ax, xlabel="Time", ylabel=value_col, title="Time Series with Trend Line")
#     ax.legend()
#     return fig

# def plot_trend_segments(df, change_points, segment_results, time_col='time', value_col='value', figsize=(14,6)):
#     """
#     Plot a time series along with segmented trend lines and mark change points.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the time series.
#         change_points (list): List of indices indicating change points.
#         segment_results (list): List of dictionaries for each segment containing keys:
#             - 'sen_summary': dictionary with key 'Sen Slope'
#             - 'trend_line': pd.Series with trend line values for the segment.
#         time_col (str): Name of the time column in df.
#         value_col (str): Name of the variable column in df.
#         figsize (tuple): Figure size.

#     Returns:
#         matplotlib.figure.Figure: The generated figure.
#     """
#     fig, ax = plt.subplots(figsize=figsize)

#     # Plot the original time series
#     ax.plot(df[time_col], df[value_col], label="Original Data", color='black', linewidth=1.5)

#     # Plot trend lines for each segment and annotate segments
#     prev_cp = 0
#     colors = ['red', 'blue', 'green', 'purple', 'orange']
#     for idx, cp in enumerate(change_points):
#         segment_df = df.iloc[prev_cp:cp].reset_index(drop=True)
#         if idx < len(segment_results) and segment_results[idx]:
#             seg_trend = segment_results[idx]['trend_line']
#             label = f"Segment {idx+1} (slope={segment_results[idx]['sen_summary']['Slope (monthly)']:.2f} m/mo)"
#             color = colors[idx % len(colors)]
#             ax.plot(segment_df[time_col], seg_trend, linestyle='--', linewidth=2, color=color, label=label)
#         prev_cp = cp

#     # Mark change points with vertical dashed lines
#     for cp in change_points[:-1]:
#         try:
#             ax.axvline(df[time_col].iloc[cp], color='gray', linestyle='--', linewidth=1.5, label='Change Point')
#         except Exception:
#             continue  # In case cp is out-of-bounds

#     set_common_plot_style(ax, xlabel="Time", ylabel=value_col, title="Segmented Trend Analysis")
#     ax.legend()
#     return fig

# def plot_seasonal_cycle(seasonal_df, time_col='Month', value_col='Value', figsize=(10,6)):
#     """
#     Plot a seasonal cycle showing mean values with error bands (e.g., ± std).

#     Parameters:
#         seasonal_df (pd.DataFrame): DataFrame with seasonal aggregated statistics.
#             Expected columns: time_col (e.g., Month), value_col (mean), and optionally 'std'.
#         time_col (str): Column name representing the season or month (e.g., "Month").
#         value_col (str): Column name for the mean value.
#         figsize (tuple): Figure size.

#     Returns:
#         matplotlib.figure.Figure: The seasonal cycle plot.
#     """
#     fig, ax = plt.subplots(figsize=figsize)
#     ax.plot(seasonal_df[time_col], seasonal_df[value_col], marker='o', linestyle='-', label="Mean")
#     if 'std' in seasonal_df.columns:
#         upper = seasonal_df[value_col] + seasonal_df['std']
#         lower = seasonal_df[value_col] - seasonal_df['std']
#         ax.fill_between(seasonal_df[time_col], lower, upper, color='gray', alpha=0.3, label="± Std")
#     set_common_plot_style(ax, xlabel="Season/Month", ylabel=value_col, title="Seasonal Cycle")
#     ax.legend()
#     return fig
