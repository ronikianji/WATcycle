import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# Import the seasonal utilities
from utils.seasonal_utils import prepare_seasonal_df, compute_monthly_stats, compute_monthly_anomalies

def seasonal_analysis_ui():
    st.title("🌊 Seasonal Pattern Analysis")
    st.markdown("""
    Analyze seasonal patterns in your time series data through:
    - **Monthly Statistics**: Mean, standard deviation, and range
    - **Yearly Comparisons**: Individual year patterns
    - **Anomaly Detection**: Deviations from seasonal norms
    """)

    if "uploaded_nc_file" not in st.session_state:
        st.warning("📤 Please upload a NetCDF file to begin seasonal analysis!")
        return

    try:
        ds = xr.open_dataset(st.session_state.uploaded_nc_file)
    except Exception as e:
        st.error(f"❌ Error loading dataset: {str(e)}")
        return

    # Variable Selection
    st.subheader("📌 Select Data")
    variable = st.selectbox(
        "Choose variable for analysis",
        options=list(ds.data_vars),
        help="Select the variable you want to analyze seasonally"
    )

    # Data Processing
    try:
        df = prepare_seasonal_df(ds, variable)
    except Exception as e:
        st.error(f"❌ Data preparation error: {str(e)}")
        return

    if df.empty:
        st.warning("⚠️ No valid data found for seasonal analysis.")
        return

    # Data Preview with Styling
    st.subheader("📊 Data Overview")
    with st.expander("View Data Sample"):
        st.dataframe(
            df.head().style.background_gradient(cmap='Blues'),
            use_container_width=True
        )

    # Monthly Statistics with Enhanced Presentation
    try:
        monthly_stats = compute_monthly_stats(df)

        st.subheader("📈 Monthly Statistics")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.dataframe(
                monthly_stats.style
                .background_gradient(subset=['Mean'], cmap='YlOrRd')
                .background_gradient(subset=['Std'], cmap='BuGn')
                .format({
                    'Mean': '{:.2f}',
                    'Std': '{:.2f}',
                    'Min': '{:.2f}',
                    'Max': '{:.2f}'
                }),
                use_container_width=True
            )

        with col2:
            st.markdown("""
            **Statistics Guide:**
            - **Mean**: Average value
            - **Std**: Standard deviation
            - **Min/Max**: Value range
            """)
    except Exception as e:
        st.error(f"❌ Statistics computation error: {str(e)}")
        return

    # Visualization Options
    st.subheader("🎨 Visualization Options")

    col1, col2 = st.columns(2)
    with col1:
        plot_yearly_lines = st.checkbox(
            "Show individual years",
            value=False,
            help="Display trends for each year separately"
        )
        plot_range_shading = st.checkbox(
            "Show value range",
            value=True,
            help="Display min-max range as shaded area"
        )
    with col2:
        # plot_anomalies = st.checkbox(
        #     "Show anomalies",
        #     value=False,
        #     help="Display deviations from seasonal normal"
        # )
        plot_anomalies = False  # Disable anomalies feature
        smooth_line = st.checkbox(
            "Smooth mean line",
            value=True,
            help="Apply smoothing to mean line"
        )

    # Create Enhanced Visualization
    st.subheader("📊 Seasonal Pattern Visualization")

    fig, ax = plt.subplots(figsize=(12, 7))
    # Replace seaborn style with default style and custom formatting
    plt.style.use('default')
    ax.set_facecolor('#f0f2f6')
    fig.patch.set_facecolor('#ffffff')

    # Base Plot with Improved Styling
    if smooth_line:
        from scipy.interpolate import make_interp_spline
        x_smooth = np.linspace(1, 12, 200)
        y_smooth = make_interp_spline(monthly_stats["month"], monthly_stats["Mean"])(x_smooth)
        ax.plot(x_smooth, y_smooth, color='#2E86C1', linewidth=2.5, label="Monthly Mean")
    else:
        ax.plot(monthly_stats["month"], monthly_stats["Mean"],
                marker='o', linestyle='-', color='#2E86C1',
                linewidth=2.5, label="Monthly Mean")

    # Enhanced Range Shading
    if plot_range_shading:
        ax.fill_between(
            monthly_stats["month"],
            monthly_stats["Min"],
            monthly_stats["Max"],
            color='#AED6F1', alpha=0.3,
            label="Value Range"
        )

    # Yearly Lines with Color Gradient
    if plot_yearly_lines:
        years = sorted(df["year"].unique())
        colors = plt.cm.viridis(np.linspace(0, 1, len(years)))
        for year, color in zip(years, colors):
            year_data = df[df["year"] == year].groupby("month")["value"].mean()
            ax.plot(year_data.index, year_data.values,
                   color=color, alpha=0.5, linestyle='--',
                   label=f"Year {year}")

    # Anomalies with Enhanced Styling
    # if plot_anomalies:
    #     try:
    #         df_anom = compute_monthly_anomalies(df)
    #         anom_stats = df_anom.groupby("month")["anomaly"].mean()
    #         ax.plot(anom_stats.index, anom_stats.values,
    #                color='#E74C3C', linestyle=':', linewidth=2,
    #                marker='s', label="Monthly Anomaly")
    #     except Exception as e:
    #         st.warning(f"⚠️ Could not compute anomalies: {str(e)}")

    # Enhanced Plot Styling
    ax.set_xlabel("Month", fontsize=12, fontweight='bold')
    ax.set_ylabel(variable, fontsize=12, fontweight='bold')
    ax.set_title(f"Seasonal Patterns: {variable}",
                 fontsize=14, fontweight='bold', pad=20)

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([
        'January', 'February', 'March', 'April',
        'May', 'June', 'July', 'August',
        'September', 'October', 'November', 'December'
    ], rotation=45)

    ax.grid(True, linestyle=':', alpha=0.4)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Display Plot with Download Option
    st.pyplot(fig)

    # Enhanced Download Options
    col1, col2 = st.columns(2)
    with col1:
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
        buf.seek(0)
        st.download_button(
            "📥 Download Plot (PNG)",
            data=buf.getvalue(),
            file_name=f"seasonal_analysis_{variable}.png",
            mime="image/png"
        )

    with col2:
        # Add CSV download option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Data (CSV)",
            data=csv,
            file_name=f"seasonal_data_{variable}.csv",
            mime="text/csv"
        )

