import numpy as np
import pandas as pd

def monthly_mean_series(da):
    """
    Compute monthly means (1–12) from a DataArray with a 'time' coordinate.
    Returns a pandas Series indexed by month.
    """
    df = da.to_dataframe().reset_index()
    if 'time' not in df:
        raise ValueError("DataArray must have a 'time' coordinate.")
    df['month'] = df['time'].dt.month
    ser = df.groupby('month')[da.name].mean()
    ser.index.name = 'month'
    ser.name = da.name
    return ser

def compute_original_seasonal(p_ser, et_ser, ro_ser, ds_ser):
    """
    Build the original seasonal DataFrame:
    month, average_precip, average_et, average_runoff, average_deltaS, average_res
    """
    df = pd.DataFrame({
        'month':          p_ser.index,
        'average_precip': p_ser.values,
        'average_et':     et_ser.values,
        'average_runoff': ro_ser.values,
        'average_deltaS': ds_ser.values
    })
    df['average_res'] = (
        df['average_precip']
      - (df['average_et'] + df['average_runoff'] + df['average_deltaS'])
    )
    return df

def apply_proportional_redistribution(residual_season):
    """
    Apply the RSE‐paper proportional redistribution logic.
    Returns (corrected_df, correction_factors_df).
    """
    df = residual_season.copy()
    G = np.array([-1, 1, 1, 1])  # signs for P, ET, Q, dS

    # 1) Compute absolute proportions, avoiding zero‐sum
    comps = df[['average_precip','average_et','average_runoff','average_deltaS']].abs()
    sum_abs = comps.sum(axis=1)
    zero_mask = sum_abs == 0
    sum_abs[zero_mask] = np.nan
    props = comps.div(sum_abs, axis=0).fillna(1/4)

    # 2) Compute first‐order corrections
    R = df['average_res']
    P_corr  = R * G[0] * props['average_precip']
    ET_corr = R * G[1] * props['average_et']
    Q_corr  = R * G[2] * props['average_runoff']
    dS_corr = R * G[3] * props['average_deltaS']

    # 3) Apply corrections
    updated = df.copy()
    updated['average_precip']   += P_corr
    updated['average_et']       += ET_corr
    updated['average_runoff']   += Q_corr
    updated['average_deltaS']   += dS_corr

    # 4) Redistribute any negatives in P, ET, Q according to RSE logic
    def _redistribute(col, others, corrs, flip=False):
        idx = updated.index[updated[col] < 0]
        if not len(idx):
            return
        abs_r = updated.loc[idx, col].abs()
        updated.loc[idx, col] = 0
        K = np.vstack([c.loc[idx].abs() for c in corrs]).T
        K = K / K.sum(axis=1)[:,None]
        if flip:
            K[:,1:] *= -1
        updated.loc[idx, others] += abs_r.values[:,None] * K

    _redistribute(
        'average_precip',
        ['average_et','average_runoff','average_deltaS'],
        [ET_corr, Q_corr, dS_corr]
    )
    _redistribute(
        'average_et',
        ['average_precip','average_runoff','average_deltaS'],
        [P_corr, Q_corr, dS_corr],
        flip=True
    )

    # Runoff redistribution is row‐wise because sign logic can vary
    idx = updated.index[updated['average_runoff'] < 0]
    if len(idx):
        abs_r = updated.loc[idx, 'average_runoff'].abs()
        updated.loc[idx, 'average_runoff'] = 0
        K = np.vstack([
            P_corr.loc[idx].abs(),
            ET_corr.loc[idx].abs(),
            dS_corr.loc[idx].abs()
        ]).T
        K = K / K.sum(axis=1)[:,None]
        for i, rid in enumerate(idx):
            if abs_r.iloc[i] * K[i,1] < updated.loc[rid, 'average_et']:
                K[i,1:] *= -1
            else:
                K[i,1] = 0
                row = K[i] / K[i].sum()
                row[1:] *= -1
                K[i] = row
        updated.loc[idx, ['average_precip','average_et','average_deltaS']] += abs_r.values[:,None] * K

    # 5) Recompute residual and sanity‐check
    updated['average_res'] = (
        updated['average_precip'] * G[0]
      + updated['average_et']       * G[1]
      + updated['average_runoff']   * G[2]
      + updated['average_deltaS']   * G[3]
    )
    if updated['average_res'].abs().max() > 0.01:
        raise AssertionError("Residual non-zero after redistribution")

    # 6) Build correction factors DataFrame
    factors = pd.DataFrame({
        'P_correction':  P_corr,
        'ET_correction': ET_corr,
        'Q_correction':  Q_corr,
        'dS_correction': dS_corr
    })

    return updated, factors
