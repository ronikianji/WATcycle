import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import pymannkendall as mk
import ruptures as rpt
import matplotlib.pyplot as plt
from io import BytesIO
from utils.file_handler import load_dataset
# ─────────────────────────  Functions ──────────────────────────

def calculate_sens_slopes(df, value_col='value', time_col='ordinal_time'):
    slopes = []
    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):
            dt = df[time_col].iloc[j] - df[time_col].iloc[i]
            if dt != 0:
                slope = (df[value_col].iloc[j] - df[value_col].iloc[i]) / dt
                slopes.append(slope)
    return np.array(slopes)

def compute_sen_summary(slopes):
    s = np.std(slopes)
    n = len(slopes)
    se = s / np.sqrt(n) if n > 0 else np.nan
    sen_slope = np.median(slopes) if n > 0 else np.nan
    slope_yearly = sen_slope * 365 if not np.isnan(sen_slope) else np.nan
    slope_monthly = slope_yearly / 12 if not np.isnan(slope_yearly) else np.nan
    se_yearly = se * 365 if not np.isnan(se) else np.nan
    se_monthly = se_yearly / 12 if not np.isnan(se_yearly) else np.nan
    return {
        'Sen Slope': sen_slope,
        'Slope (yearly)': slope_yearly,
        'Slope (monthly)': slope_monthly,
        'Uncertainty': se,
        'Uncertainty (yearly)': se_yearly,
        'Uncertainty (monthly)': se_monthly
    }

def generate_trend_line(df, slope, value_col='value', time_col='ordinal_time'):
    x = df[time_col]
    y = df[value_col]
    x_mean = x.mean()
    y_mean = y.mean()
    intercept = y_mean - slope * x_mean
    return slope * x + intercept

def detect_change_points(signal, penalty=6, model="rbf"):
    algo = rpt.Pelt(model=model).fit(signal)
    return algo.predict(pen=penalty)    

def analyze_segment(segment_df):
    if len(segment_df) < 2:
        return None
    mk_result = mk.original_test(segment_df['value'])
    slopes = calculate_sens_slopes(segment_df)
    sen_summary = compute_sen_summary(slopes)
    trend_line = generate_trend_line(segment_df, sen_summary['Sen Slope'])
    return {
        'mk_result': mk_result,
        'sen_summary': sen_summary,
        'trend_line': trend_line
    }

def run_mk_cp_analysis():
    st.title("📈 Time Series Trend Analysis")
    st.markdown("""
    This tool performs comprehensive trend analysis on your time series data using:
    - **Mann-Kendall Test**: Detects presence and significance of trends
    - **Sen's Slope**: Estimates trend magnitude
    - **Change Point Detection**: Identifies significant shifts in the series
    """)

    if "uploaded_nc_file" not in st.session_state:
        st.warning("🚫 Please upload a NetCDF file to begin analysis!")
        return

    with st.spinner("📊 Processing your data..."):
        ds = load_dataset()

        # Data Selection
        st.subheader("📌 Select Data")
        variable = st.selectbox(
            "Choose the variable to analyze",
            options=list(ds.data_vars),
            help="Select the variable from your dataset for trend analysis"
        )

        if "time" not in ds.dims:
            st.error("❌ Time dimension not found in the dataset!")
            return

        # Data Processing
        time = pd.to_datetime(ds['time'].values)
        dims_to_average = [dim for dim in ds[variable].dims if dim != "time"]
        values = ds[variable].mean(dim=dims_to_average).values

        df = pd.DataFrame({'time': time, 'value': values})
        df.dropna(inplace=True)
        df['ordinal_time'] = df['time'].apply(lambda x: x.toordinal())

        # Global Analysis
        with st.container():
            st.subheader("🌍 Overall Trend Analysis")
            st.markdown("Analysis of the entire time series")

            col1, col2 = st.columns(2)

            # Significance level input
            alpha = col1.number_input(
                "Significance level (alpha)", min_value=0.0, max_value=1.0, value=0.05, step=0.01,
                help="Type your desired significance level for the Mann-Kendall test"
            )

            with col1:
                global_mk = mk.original_test(df['value'])
                global_mk_dict = {
                    'Trend': global_mk.trend,
                    'p-value': f"{global_mk.p:.4f}",
                    'Significance': "✅ Significant" if global_mk.p < alpha else "❌ Not Significant",
                    'Confidence Level': f"{int((1-alpha)*100)}%"
                }
                st.write("**Mann-Kendall Test Results:**")
                for key, value in global_mk_dict.items():
                    st.markdown(f"- {key}: **{value}**")

            with col2:
                global_slopes = calculate_sens_slopes(df)
                global_sen_summary = compute_sen_summary(global_slopes)
                st.write("**Sen's Slope Estimates:**")
                for key in ['Slope (monthly)', 'Slope (yearly)']:
                    st.markdown(f"- {key}: **{global_sen_summary[key]:.4f}**")

        # Change Point Analysis
        st.subheader("🔄 Change Point Detection")
        st.markdown("Identify significant shifts in the time series")

        enable_cp = st.checkbox("Enable Change Point Detection", value=False)

        if enable_cp:
            col1, col2 = st.columns([2, 1])
            with col1:
                penalty = st.slider(
                    "Sensitivity (higher = fewer change points)",
                    min_value=1,
                    max_value=20,
                    value=6,
                    help="Adjust to control the number of detected change points"
                )
                model = st.selectbox(
                    "Select PELT model",
                    options=["rbf", "l1", "l2", "normal", "ar", "ma"],
                    index=0,
                    help="Choose the cost function model for change point detection"
                )

            signal = df['value'].values
            change_points = detect_change_points(signal, penalty=penalty, model=model)
            with col2:
                st.metric("Detected Changes", len(change_points) - 1)
        else:
            change_points = [0, len(df)]

        # Plot options
        plot_std = st.checkbox("Plot ±1 std deviation range", value=False)
        plot_minmax = st.checkbox("Plot min-max envelope", value=False)

        # Visualization
        st.subheader("📈 Trend Visualization")
        fig, ax = plt.subplots(figsize=(14, 7))

        plt.style.use('default')
        ax.set_facecolor('#f0f2f6')
        fig.patch.set_facecolor('#ffffff')

        ax.plot(df['time'], df['value'], label="Time Series", color='#2E86C1', linewidth=1.5, alpha=0.8)

        # plot envelopes
        if plot_std:
            std = df['value'].std()
            ax.fill_between(df['time'], df['value'] - std, df['value'] + std, alpha=0.2, label='±1 std')
        if plot_minmax:
            ax.fill_between(df['time'], df['value'].min(), df['value'].max(), alpha=0.1, label='Min-Max')

        # Add overall trend line
        overall_trend = generate_trend_line(df, global_sen_summary['Sen Slope'])
        ax.plot(df['time'], overall_trend,
                label=f"Overall Trend ({global_sen_summary['Slope (monthly)']:.2f})",
                color='#E67E22', linestyle='--', linewidth=2)

        # Plot segments only if change point detection is enabled
        if enable_cp and len(change_points) > 1:
            colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
            prev_cp = 0
            for idx, cp in enumerate(change_points):
                segment_df = df.iloc[prev_cp:cp].reset_index(drop=True)
                analysis = analyze_segment(segment_df)
                if analysis:
                    color = colors[idx % len(colors)]
                    label = f"Segment {idx+1}: {analysis['sen_summary']['Slope (monthly)']:.2f}"
                    ax.plot(segment_df['time'], analysis['trend_line'], linestyle='--', linewidth=2, color=color, label=label)
                prev_cp = cp

            # Plot change points
            for cp in change_points[:-1]:
                ax.axvline(df['time'].iloc[cp], color='#34495E', linestyle='--', alpha=0.5,
                          label='Change Point' if cp == change_points[0] else "")

        ax.set_xlabel("Time", fontsize=12)
        ax.set_ylabel(variable, fontsize=12)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, linestyle=':', alpha=0.3)

        plt.title("Time Series Trend Analysis", pad=20, fontsize=14, fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig)

        # Download Options
        col1, col2 = st.columns(2)
        with col1:
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
            buf.seek(0)
            st.download_button(
                "📥 Download Plot (PNG)",
                data=buf.getvalue(),
                file_name=f"trend_analysis_{variable}.png",
                mime="image/png"
            )

        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Data (CSV)",
                data=csv,
                file_name=f"trend_data_{variable}.csv",
                mime="text/csv"
            )

