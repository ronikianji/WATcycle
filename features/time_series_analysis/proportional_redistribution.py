import streamlit as st
import xarray as xr
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np

from utils.file_handler import save_uploaded_file, get_image_download_button
from utils.proportional_redistribution_utils import (
    monthly_mean_series,
    compute_original_seasonal,
    apply_proportional_redistribution
)

_COLORS = {
    'average_precip':'#1f77b4','average_et':'#ff7f0e',
    'average_runoff':'#2ca02c','average_deltaS':'#d62728',
    'average_res':'#9467bd'
}
_LEGEND = {
    'average_precip':'Average Precipitation',
    'average_et':'Average ET',
    'average_runoff':'Average Runoff',
    'average_deltaS':'Average ΔS',
    'average_res':'Average Residual'
}
_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def proportional_redistribution_ui():
    st.header("🔄 Proportional Redistribution")

    # Upload & save to temp
    p_file  = st.file_uploader("Precipitation (P)", type="nc", key="p_nc")
    et_file = st.file_uploader("Evapotranspiration (ET)", type="nc", key="et_nc")
    r_file  = st.file_uploader("Runoff (R)", type="nc", key="r_nc")
    ds_file = st.file_uploader("ΔS (Change in TWS over time)", type="nc", key="ds_nc")

    if not all([p_file, et_file, r_file, ds_file]):
        st.warning("Please upload P, ET, R, and ΔS files.")
        return

    p_path  = save_uploaded_file(p_file, 'nc')
    et_path = save_uploaded_file(et_file, 'nc')
    r_path  = save_uploaded_file(r_file, 'nc')
    ds_path = save_uploaded_file(ds_file, 'nc')

    # Variable selection
    with st.expander("Select Variables"):
        pr_ds = xr.open_dataset(p_path)
        p_var = st.selectbox("P variable", list(pr_ds.data_vars), key="p_var")

        et_ds = xr.open_dataset(et_path)
        et_var= st.selectbox("ET variable", list(et_ds.data_vars), key="et_var")

        ro_ds = xr.open_dataset(r_path)
        r_var = st.selectbox("R variable", list(ro_ds.data_vars), key="r_var")

        ds_ds = xr.open_dataset(ds_path)
        ds_var= st.selectbox("ΔS variable", list(ds_ds.data_vars), key="ds_var")

    # Extract DataArrays
    pr_da = xr.open_dataset(p_path)[p_var]
    et_da = xr.open_dataset(et_path)[et_var]
    ro_da = xr.open_dataset(r_path)[r_var]
    ds_da = xr.open_dataset(ds_path)[ds_var]

    # Calculate original
    if st.button("Calculate Residual Error"):
        p_ser  = monthly_mean_series(pr_da)
        et_ser = monthly_mean_series(et_da)
        ro_ser = monthly_mean_series(ro_da)
        ds_ser = monthly_mean_series(ds_da)

        orig_df = compute_original_seasonal(p_ser, et_ser, ro_ser, ds_ser)
        st.session_state['orig_df'] = orig_df

    # Always display original table & plot if available
    if 'orig_df' in st.session_state:
        orig_df = st.session_state['orig_df']
        st.subheader("Original Seasonal Table")
        st.dataframe(orig_df)

        fig, ax = plt.subplots(figsize=(10, 6))
        for col in orig_df.columns.drop('month'):
            ax.plot(
                orig_df['month'], orig_df[col],
                color=_COLORS[col],
                linestyle='-' if col!='average_res' else '--',
                linewidth=2,
                label=f"Original {_LEGEND[col]}"
            )
        ax.set_xticks(np.arange(1,13))
        ax.set_xticklabels(_MONTHS, fontsize=12, fontweight='bold')
        ax.set_xlim(1,12)
        ax.set_xlabel("Month", fontsize=14, fontweight='bold')
        ax.set_ylabel("Flux / Residual (mm)", fontsize=14, fontweight='bold')
        ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5,1.15))
        ax.grid(True, linestyle=':', linewidth=0.5)
        st.pyplot(fig)
        get_image_download_button(fig, filename="original_residual_plot.png", label="📥 Download Original Plot")

    # Apply redistribution
    if 'orig_df' in st.session_state and st.button("Apply Proportional Redistribution"):
        orig_df = st.session_state['orig_df']
        corr_df, factors = apply_proportional_redistribution(orig_df)

        st.subheader("Corrected Seasonal Table")
        st.dataframe(corr_df)

        fig, ax = plt.subplots(figsize=(10, 6))
        for col in orig_df.columns.drop('month'):
            ax.plot(
                orig_df['month'], orig_df[col],
                color=_COLORS[col], linestyle='-', linewidth=2,
                label=f"Original {_LEGEND[col]}"
            )
            ax.plot(
                corr_df['month'], corr_df[col],
                color=_COLORS[col], linestyle='--', linewidth=2,
                label=f"Corrected {_LEGEND[col]}"
            )
        ax.set_xticks(np.arange(1,13))
        ax.set_xticklabels(_MONTHS, fontsize=12, fontweight='bold')
        ax.set_xlim(1,12)
        ax.set_xlabel("Month", fontsize=14, fontweight='bold')
        ax.set_ylabel("Flux / Residual (mm)", fontsize=14, fontweight='bold')
        ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5,1.15))
        ax.grid(True, linestyle=':', linewidth=0.5)
        st.pyplot(fig)
        get_image_download_button(fig, filename="corrected_residual_plot.png", label="📥 Download Corrected Plot")
