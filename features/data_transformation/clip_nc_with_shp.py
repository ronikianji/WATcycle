import os
import tempfile
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import folium_static

from utils.geospatial_utils import load_netcdf_with_engines, clip_dataset_with_shapefile
from utils.saving_netcdf import interactive_save_netcdf

def clip_netcdf_feature():
    st.header("✂️ Clip NetCDF with Shapefile")

    # Load shapefile from session
    shapefile = st.session_state.get("uploaded_shapefile_gdf")
    if shapefile is None:
        st.warning("⚠️ Please upload a shapefile first using the 'Upload Shapefile' section.")
        return

    st.success(f"✅ Shapefile loaded: {st.session_state.get('uploaded_shapefile_name', 'Unnamed')}")

    # Preview map and data
    st.subheader("📍 Shapefile Preview")
    st.dataframe(shapefile.head())

    m = folium.Map(
        location=[shapefile.geometry.centroid.y.mean(), shapefile.geometry.centroid.x.mean()],
        zoom_start=6
    )
    folium.GeoJson(shapefile).add_to(m)
    folium_static(m)

    # Load NetCDF from session or upload
    if "uploaded_nc_file" in st.session_state:
        netcdf_file_path = st.session_state["uploaded_nc_file"]
        st.success("✅ Using NetCDF file uploaded earlier.")
    else:
        netcdf_file = st.file_uploader("📤 Upload NetCDF file to clip", type=["nc"])
        if netcdf_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp_nc:
                tmp_nc.write(netcdf_file.getbuffer())
                netcdf_file_path = tmp_nc.name
                st.session_state["uploaded_nc_file"] = netcdf_file_path
        else:
            st.info("📂 Please upload a NetCDF file.")
            return

    # File naming and conversion
    st.subheader("💾 Output Settings")
    netcdf_filename = st.text_input(
        "Name your NetCDF file:",
        "clipped_output",
        help="Enter a name for your NetCDF file (without .nc extension)"
    )

    # Manual trigger for clipping
    if st.button("✂️ Start Clipping"):
        with st.spinner("Clipping and saving your data..."):
            try:
                ds = load_netcdf_with_engines(netcdf_file_path)

                # Directly clip dataset using already aligned lat/lon
                clipped_ds = clip_dataset_with_shapefile(ds, shapefile)

                output_path = os.path.join(os.getcwd(), f"{netcdf_filename}.nc")
                clipped_ds.to_netcdf(output_path)

                st.success("✨ Download complete!")

            except Exception as e:
                st.error(f"❌ An error occurred during clipping or saving: {e}")

