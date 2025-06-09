import os
import tempfile
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import folium_static
from io import BytesIO

def upload_shp():
    st.title("📍 Shapefile Viewer")

    st.markdown("""
    **Required Shapefile Components:**
    - `.shp` - Shape format (geometry)
    - `.shx` - Shape index format
    - `.dbf` - Attribute format
    - `.prj` - Projection format (optional)
    - `.cpg` - Character encoding (optional)
    """)

    # Check if a file has already been uploaded
    if "uploaded_shapefile_gdf" in st.session_state:
        st.info(f"Current shapefile: {st.session_state.get('uploaded_shapefile_name', 'Unnamed')}")
        if st.button("Clear shapefile"):
            del st.session_state.uploaded_shapefile_gdf
            if "uploaded_shapefile_name" in st.session_state:
                del st.session_state.uploaded_shapefile_name
            st.rerun()

    uploaded_files = st.file_uploader(
        "Upload shapefile components",
        type=['shp', 'shx', 'dbf', 'prj', 'cpg'],
        accept_multiple_files=True
    )

    # Select CRS if not found in shapefile
    crs_options = {
        "WGS84 (EPSG:4326)": "EPSG:4326",
        "UTM Zone 33N (EPSG:32633)": "EPSG:32633",
        "Web Mercator (EPSG:3857)": "EPSG:3857",
        "NAD83 (EPSG:4269)": "EPSG:4269",
        "ETRS89 (EPSG:4258)": "EPSG:4258",
    }
    selected_crs = st.selectbox("Select CRS (if .prj is missing):", list(crs_options.keys()))

    # Checkbox for Folium map
    show_interactive_map = st.checkbox("Show interactive map (Folium)", value=False)

    def process_and_display_shapefile(shapefile, file_name=None):
        """Helper function to process and display shapefile data"""
        if shapefile.crs is None:
            st.warning("⚠️ No CRS found in shapefile. Using manually selected CRS.")
            shapefile.set_crs(crs_options[selected_crs], inplace=True)

        st.success(f"✅ CRS: {shapefile.crs}")

        if file_name:
            st.session_state.uploaded_shapefile_name = file_name
        st.session_state.uploaded_shapefile_gdf = shapefile

        st.subheader("📄 Shapefile Data")
        st.dataframe(shapefile)

        # Plot using matplotlib
        fig, ax = plt.subplots(figsize=(8, 6))
        shapefile.plot(ax=ax, edgecolor='black', facecolor='lightgray')
        ax.set_title("Shapefile Outline" if file_name else "Area of Interest")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        st.pyplot(fig)

        # Add download button for the figure
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(
            label="📥 Download Map",
            data=buf.getvalue(),
            file_name="shapefile_map.png",
            mime="image/png"
        )
        plt.close(fig)

        # Optional interactive map
        if show_interactive_map:
            m = folium.Map(
                location=[
                    shapefile.geometry.centroid.y.mean(),
                    shapefile.geometry.centroid.x.mean()
                ],
                zoom_start=6
            )
            folium.GeoJson(shapefile).add_to(m)
            folium_static(m)

    if uploaded_files:
        uploaded_file_names = [file.name for file in uploaded_files]
        required_extensions = [".shp", ".shx", ".dbf"]
        missing_files = [ext for ext in required_extensions if not any(ext in name for name in uploaded_file_names)]

        if missing_files:
            st.error(f"❌ Missing required files: {', '.join(missing_files)}")
            return

        shp_file = next((file for file in uploaded_files if file.name.endswith(".shp")), None)

        with tempfile.TemporaryDirectory() as tmpdir:
            for file in uploaded_files:
                with open(os.path.join(tmpdir, file.name), "wb") as f:
                    f.write(file.getbuffer())

            shp_path = os.path.join(tmpdir, shp_file.name)

            try:
                shapefile = gpd.read_file(shp_path)
                process_and_display_shapefile(shapefile, shp_file.name)
            except Exception as e:
                st.error(f"❌ Error reading shapefile: {e}")

    # Show already loaded shapefile if user just navigated here
    elif "uploaded_shapefile_gdf" in st.session_state:
        shapefile = st.session_state.uploaded_shapefile_gdf
        st.success("✅ Active shapefile: " + st.session_state.uploaded_shapefile_name)
        process_and_display_shapefile(shapefile)
