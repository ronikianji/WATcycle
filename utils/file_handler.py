import os
import tempfile
import streamlit as st
# Data File handler
def save_uploaded_file(uploaded_file, file_extension):
    """Saves uploaded file to a temporary location."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
            tmp.write(uploaded_file.getbuffer())
            return tmp.name
    except Exception as e:
        return None

# SHP File handler
def save_uploaded_shapefile(uploaded_files):
    """Saves shapefile components to temporary files."""
    saved_files = []
    try:
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getbuffer())
                saved_files.append(tmp.name)
        return saved_files
    except Exception as e:
        return None

# Flattened DataFrame from the uploaded NetCDF file
import xarray as xr
import pandas as pd

import xarray as xr
import pandas as pd
import streamlit as st

def load_dataset():
    """
    Safely load the NetCDF dataset stored in session_state.
    Returns xarray.Dataset or None (if not yet uploaded).
    """
    file_path = st.session_state.get("uploaded_nc_file")
    if not file_path:
        # nothing uploaded yet
        return None
    try:
        return xr.open_dataset(file_path)
    except Exception as e:
        st.error(f"Error opening NetCDF file: {e}")
        return None

def load_dataset_to_dataframe():
    """
    Safely load the NetCDF as a flattened pandas DataFrame.
    Returns DataFrame or None.
    """
    file_path = st.session_state.get("uploaded_nc_file")
    if not file_path:
        return None
    try:
        ds = xr.open_dataset(file_path)
        return ds.to_dataframe().reset_index()
    except Exception as e:
        st.error(f"Error converting NetCDF to DataFrame: {e}")
        return None


# Image File handler
from io import BytesIO
import base64

def get_image_download_button(fig, filename="plot.png", label="📥 Download Plot"):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">{label}</a>'
    return st.markdown(href, unsafe_allow_html=True)
