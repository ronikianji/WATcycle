import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib.lines as mlines
from typing import Dict, List, Optional, Union

# ----------------------------
# Core Taylor Diagram Functions
# ----------------------------

def compute_taylor_stats(obs: np.ndarray, model: np.ndarray) -> Optional[Dict[str, Union[str, float]]]:
    """Calculate statistics needed for Taylor diagram visualization."""
    try:
        # Input validation and flattening
        obs = np.asarray(obs, dtype=np.float64).flatten()
        model = np.asarray(model, dtype=np.float64).flatten()

        if obs.size != model.size:
            raise ValueError("Input arrays must have the same dimensions")

        # Mask NaN values
        mask = ~np.isnan(obs) & ~np.isnan(model)
        obs = obs[mask]
        model = model[mask]

        if obs.size < 2 or model.size < 2:
            return None

        # Calculate core statistics
        std_obs = np.std(obs, ddof=1)
        std_model = np.std(model, ddof=1)
        if std_obs == 0 or std_model == 0:
            return None

        # Compute correlation and centered RMSE
        obs_centered = obs - np.mean(obs)
        model_centered = model - np.mean(model)
        corr = np.dot(obs_centered, model_centered) / (std_obs * std_model * obs.size)
        crmse = np.sqrt(np.mean((model_centered - obs_centered) ** 2))

        return {
            "label": None,  # To be populated by caller
            "correlation": np.clip(corr, -1.0, 1.0),
            "std_obs": std_obs,
            "std_model": std_model,
            "crmse": crmse
        }

    except Exception as e:
        st.error(f"Statistical calculation error: {str(e)}")
        return None

def plot_taylor_diagram(stats_list: List[Dict], normalize: bool = False) -> Optional[plt.Figure]:
    """Generate professional Taylor diagram visualization."""
    try:
        if len(stats_list) < 1:
            raise ValueError("No valid datasets provided")

        # Reference dataset setup
        ref_stats = stats_list[0]
        std_obs = ref_stats["std_obs"]
        if std_obs <= 0:
            raise ValueError("Invalid reference standard deviation")

        # Normalization handling
        if normalize:
            scale_factor = std_obs
            std_obs = 1.0
            max_std = 1.5
        else:
            scale_factor = 1.0
            model_stds = [s["std_model"] for s in stats_list[1:]]
            max_std = max(model_stds + [std_obs]) if model_stds else std_obs * 1.5

        # Create visualization canvas
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': 'polar'})
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_thetalim(0, np.pi/2)
        ax.set_ylim(0, max_std * 1.15)

        # Reference elements
        theta_ref = np.linspace(0, np.pi/2, 100)
        ax.plot(theta_ref, [std_obs]*100, '--', color='#444444',
               linewidth=1.5, alpha=0.8, label='Reference STD')
        ax.plot(0, std_obs, 'o', markersize=12, markerfacecolor='white',
               markeredgecolor='#444444', markeredgewidth=2, zorder=3)

        # Axis customization
        corr_ticks = np.linspace(0, 1, 5)
        angle_labels = [f"{t:.1f}" for t in corr_ticks]
        ax.set_thetagrids(np.degrees(np.arccos(corr_ticks)), labels=angle_labels,
                         fontsize=10, color='#333333')

        # Model visualization
        colors = plt.cm.tab20.colors
        legend_handles = []
        for idx, stats in enumerate(stats_list[1:]):
            try:
                scaled_std = stats["std_model"] / scale_factor
                theta = np.arccos(np.clip(stats["correlation"], -1, 1))

                ax.plot(theta, scaled_std, 'o',
                       color=colors[idx % len(colors)],
                       markersize=10,
                       markeredgecolor='white',
                       markeredgewidth=1.5)

                legend_handles.append(
                    mlines.Line2D([], [], color=colors[idx % len(colors)],
                                marker='o', linestyle='None',
                                markersize=10, label=stats["label"])
                )
            except Exception as e:
                st.warning(f"Visualization error for model {idx+1}: {str(e)}")
                continue

        # Final styling
        ax.set_title("Taylor Diagram Analysis\nModel Performance Evaluation",
                    fontsize=14, pad=20, fontweight='bold')
        ax.legend(handles=legend_handles, bbox_to_anchor=(1.25, 1),
                 title="Model Datasets", frameon=True)

        plt.tight_layout()
        return fig

    except Exception as e:
        st.error(f"Visualization failed: {str(e)}")
        return None

# ----------------------------
# Streamlit UI Implementation
# ----------------------------

def taylor_plot_ui():
    """Main Streamlit application interface."""
    # Remove st.set_page_config() from here

    st.title("✅ Model Performance Analysis: Taylor Diagram")
    st.markdown("""
    **Scientific Visualization Tool**
    Evaluate model performance against observational data through:
    - **Correlation**: Pattern similarity (angular position)
    - **Variability**: Standard deviation ratio (radial distance)
    """)

    # Reference data section
    with st.expander("🔍 STEP 1: Upload Reference Dataset", expanded=True):
        obs_file = st.file_uploader("Select observational/reference NetCDF",
                                   type=["nc"], key="obs_data")
        if not obs_file:
            st.info("Upload reference data to begin analysis")
            return

        try:
            with xr.open_dataset(BytesIO(obs_file.read())) as ds:
                obs_ds = ds.load()
            obs_var = st.selectbox("Select reference variable", list(obs_ds.data_vars))
            obs_values = obs_ds[obs_var].values.flatten()

            if np.isnan(obs_values).all():
                st.error("Invalid reference data: All NaN values")
                return

            ref_stats = compute_taylor_stats(obs_values, obs_values)
            if not ref_stats:
                st.error("Failed to compute reference statistics")
                return
            ref_stats["label"] = "Reference"

        except Exception as e:
            st.error(f"Reference data error: {str(e)}")
            return

    # Model comparison section
    with st.expander("📂 STEP 2: Upload Model Datasets", expanded=True):
        model_files = st.file_uploader("Select model NetCDF files",
                                      type=["nc"], accept_multiple_files=True)
        if not model_files:
            st.info("Upload model data for comparison")
            return

        model_stats = []
        for f in model_files:
            try:
                with xr.open_dataset(BytesIO(f.read())) as ds:
                    m_ds = ds.load()
                m_var = st.selectbox(f"Variable selection: {f.name}", list(m_ds.data_vars))
                m_values = m_ds[m_var].values.flatten()

                stats = compute_taylor_stats(obs_values, m_values)
                if stats:
                    stats["label"] = f.name.split(".")[0]  # Clean filename
                    model_stats.append(stats)

            except Exception as e:
                st.warning(f"Skipped {f.name}: {str(e)}")
                continue

    # Visualization controls
    if not model_stats:
        st.warning("No valid model data for comparison")
        return

    with st.expander("⚙️ STEP 3: Visualization Settings", expanded=True):
        normalize = st.toggle("Normalize Statistics", value=True,
                             help="Standardize by reference dataset variability")
        fig = plot_taylor_diagram([ref_stats] + model_stats, normalize=normalize)

    # Results display
    if fig:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.pyplot(fig)
        with col2:
            st.download_button("📥 Download Statistics (CSV)",
                              pd.DataFrame([ref_stats] + model_stats).to_csv(),
                              file_name="taylor_statistics.csv")

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            st.download_button("📥 Download Diagram (PNG)",
                              buf.getvalue(),
                              file_name="taylor_diagram.png")
    else:
        st.error("Failed to generate visualization")
