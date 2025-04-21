import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from typing import Dict, List, Optional, Union

def compute_taylor_stats(obs: np.ndarray, model: np.ndarray) -> Optional[Dict[str, Union[str, float]]]:
    try:
        obs = np.asarray(obs).flatten()
        model = np.asarray(model).flatten()

        if obs.size != model.size:
            raise ValueError("Observation and model arrays must have the same size")

        # Mask out any NaNs
        mask = ~np.isnan(obs) & ~np.isnan(model)
        obs = obs[mask]
        model = model[mask]

        if obs.size < 2:
            return None

        # Remove mean for correlation calculation
        obs_demean = obs - obs.mean()
        model_demean = model - model.mean()

        # Compute statistics
        std_obs = float(np.std(obs, ddof=1))  # Using ddof=1 for sample standard deviation
        std_model = float(np.std(model, ddof=1))

        # Handle zero standard deviations
        if std_obs == 0 or std_model == 0:
            return None

        corr = float(np.sum(obs_demean * model_demean) / (obs.size * std_obs * std_model))
        crmse = float(np.sqrt(np.mean((model_demean - obs_demean) ** 2)))

        return {
            "label": None,  # filled in by caller
            "correlation": np.clip(corr, -1.0, 1.0),  # ensure correlation is in [-1,1]
            "std_obs": std_obs,
            "std_model": std_model,
            "crmse": crmse
        }

    except Exception as e:
        print(f"Error in compute_taylor_stats: {str(e)}")
        return None

def plot_taylor_diagram(stats_list, normalize=False, show_legend=True):
    try:
        if not stats_list or len(stats_list) < 1:
            raise ValueError("stats_list must contain at least one item")

        std_obs = stats_list[0].get("std_obs")
        if std_obs is None or std_obs <= 0:
            raise ValueError("Invalid reference standard deviation")

        # Handle normalization first
        original_std_obs = std_obs
        if normalize:
            for s in stats_list:
                if s["std_model"] is not None:
                    s["std_model"] /= original_std_obs
                if s["crmse"] is not None:
                    s["crmse"] /= original_std_obs
            std_obs = 1.0
            max_std = 1.5
        else:
            model_stds = [s["std_model"] for s in stats_list[1:] if s["std_model"] is not None]
            max_std = max(model_stds + [std_obs]) if model_stds else std_obs * 1.5

        # Setup figure with professional styling
        plt.style.use('seaborn-whitegrid')
        fig = plt.figure(figsize=(12, 9), dpi=100)
        ax = fig.add_subplot(111, polar=True)

        # Configure polar plot
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_thetalim(0, np.pi/2)
        ax.set_ylim(0, max_std * 1.15)

        # Set up color palette
        colors = plt.cm.tab20.colors  # Using high-contrast categorical palette

        # --- Plot Elements ---
        # Reference line with professional styling
        theta_ref = np.linspace(0, np.pi/2, 100)
        ax.plot(theta_ref, [std_obs]*100, '--', color='#444444',
               linewidth=1.5, alpha=0.8, label='Reference STD')

        # Reference point
        ax.plot(0, std_obs, 'o', markersize=12, markerfacecolor='white',
               markeredgecolor='#444444', markeredgewidth=2, zorder=3)

        # --- Axis Styling ---
        # Correlation axis
        corr_ticks = np.linspace(0, 1, 5)
        angles = np.arccos(corr_ticks)
        ax.set_thetagrids(np.degrees(angles),
                         labels=[f"{c:.1f}" for c in corr_ticks],
                         fontsize=12, fontweight='semibold', color='#333333')

        # STD axis
        std_ticks = np.linspace(0, max_std, 6)[1:]
        ax.set_rgrids(std_ticks, angle=135,
                     fontsize=12, fontweight='semibold', color='#333333',
                     linestyle='--', linewidth=1, alpha=0.7)

        # --- Plot Models ---
        legend_handles = []
        for idx, s in enumerate(stats_list[1:]):
            try:
                corr = s.get("correlation")
                stdm = s.get("std_model")
                if corr is None or stdm is None:
                    continue

                theta = np.arccos(np.clip(corr, -1, 1))
                ax.plot(theta, stdm, 'o',
                       color=colors[idx % len(colors)],
                       markersize=10,
                       markeredgewidth=1.5,
                       markeredgecolor='white')

                legend_handles.append(
                    mlines.Line2D([], [], color=colors[idx % len(colors)],
                                marker='o', linestyle='None',
                                markersize=10, markeredgewidth=1.5,
                                label=s.get("label", f"Model {idx+1}"))
                )
            except Exception as e:
                print(f"Error plotting model {idx+1}: {e}")
                continue

        # --- Professional Annotations ---
        ax.set_title("Taylor Diagram Analysis",
                    fontsize=16, fontweight='bold', pad=20, color='#333333')

        # Add explanatory text box
        fig.text(0.95, 0.05,
                'Angular Position = Correlation Coefficient\n'
                'Radial Distance = Standard Deviation',
                ha='right', va='bottom',
                fontsize=11, style='italic',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

        # --- Legend ---
        if show_legend and legend_handles:
            leg = ax.legend(handles=legend_handles,
                          loc='upper left',
                          bbox_to_anchor=(1.05, 1),
                          fontsize=11,
                          title="Model Dataset",
                          title_fontsize=12,
                          frameon=True,
                          framealpha=0.95,
                          edgecolor='#cccccc')
            leg.get_frame().set_facecolor('white')
            leg.get_title().set_fontweight('bold')

        plt.tight_layout()
        return fig

    except Exception as e:
        print(f"Error in plot_taylor_diagram: {str(e)}")
        return None
