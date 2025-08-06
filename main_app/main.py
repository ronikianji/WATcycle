import sys
import os
from IPython.display import display
import streamlit as st

st.set_page_config(page_title='WATcycle', layout='wide')
st.sidebar.title('Toolbox Navigation')
# Add Final_Toolbox to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import necessary modules
from utils.file_handler import save_uploaded_file, save_uploaded_shapefile, load_dataset_to_dataframe, load_dataset
from utils.merge_netcdf_utils import merge_netcdf_concat, merge_netcdf_merge, smart_merge_netcdf

from features.home import netcdf_standardizer, description
# from features.data_download import gldas_download
from features.data_download import gldas_download_2
from features.upload_files import upload_netcdf, upload_shp
from features.data_transformation import calculator, csv_to_netcdf, clip_nc_with_shp, missing_time_steps, merge_netcdf, split_nc, interpolation, resample_netcdf
from features.time_series_analysis import trend_analysis, seasonal_analysis, taylor_plot, proportional_redistribution
from features.spatial_plotting import global_plot, shp_spatial

# Sidebar Navigation
def main():
    st.sidebar.markdown("""
    <div style='text-align: center; margin-bottom: 20px'>
        <h1 style='color: #1f77b4'>🌊 WATcycle</h1>
    </div>
    """, unsafe_allow_html=True)

    main_section = st.sidebar.radio("Navigation", [
        '🏠 Home',
        '⬇️ Data Download',
        '📤 Upload Files',
        '🔄 Data Transformation',
        '📊 Time Series Analysis',
        '🗺️ Spatial Plotting'
    ])

    if main_section == '🏠 Home':
        choice = st.sidebar.radio('Choose Feature', [
            '📖 Description',
            '📊 NetCDF Standardizer'
        ])

        if choice == '📖 Description':
            description.show_description()
        elif choice == '📊 NetCDF Standardizer':
            netcdf_standardizer.netcdf_standardizer_feature()

    elif main_section == '⬇️ Data Download':
        gldas_download_2.gldas_download_ui()

    elif main_section == '📤 Upload Files':
        choice = st.sidebar.radio('Choose Format', [
            '📄 NetCDF File',
            '🗺️ Shapefile'
        ])
        if choice == '📄 NetCDF File':
            upload_netcdf.upload_netcdf()
        elif choice == '🗺️ Shapefile':
            upload_shp.upload_shp()

    elif main_section == '🔄 Data Transformation':
        choice = st.sidebar.radio('Select Tool', [
            '🔢 Calculator',
            '📝 CSV to NetCDF',
            '✂️ Clip NC with SHP',
            '⏱️ Find Missing Time Steps',
            '🔍 Interpolate Missing Values',
            '🔗 Merge NetCDF Files',
            '⚖️ Resample Resolution',
            '✂️ Split NC file'
        ])
        if choice == '🔢 Calculator':
            calculator.calculator()
        elif choice == '📝 CSV to NetCDF':
            csv_to_netcdf.csv_to_netcdf()
        elif choice == '✂️ Clip NC with SHP':
            clip_nc_with_shp.clip_netcdf_feature()
        elif choice == '⏱️ Find Missing Time Steps':
            missing_time_steps.missing_time_steps_ui()
        elif choice == '🔗 Merge NetCDF Files':
            merge_netcdf.merge_netcdf_ui()
        elif choice == '✂️ Split NC file':
            split_nc.split_netcdf_ui()
        elif choice == '🔍 Interpolate Missing Values':
            interpolation.interpolate_netcdf_ui()
        elif choice == '⚖️ Resample Resolution':
            resample_netcdf.resample_netcdf_ui()

    elif main_section == '📊 Time Series Analysis':
        choice = st.sidebar.radio('Select Analysis', [
            '📈 Trend Analysis',
            '🔄 Seasonal Analysis',
            '✅ Validation',
            '💧 Water Budget Closure'
        ])
        if choice == '📈 Trend Analysis':
            trend_analysis.run_mk_cp_analysis()
        elif choice == '🔄 Seasonal Analysis':
            seasonal_analysis.seasonal_analysis_ui()
        elif choice == '✅ Validation':
            taylor_plot.taylor_plot_ui()
        elif choice == '💧 Water Budget Closure':
            proportional_redistribution.proportional_redistribution_ui()

    elif main_section == '🗺️ Spatial Plotting':
        choice = st.sidebar.radio('Select Plot Type', [
            '🗺️ Regional Plot (SHP)',
            '🌍 Global Plot'
        ])
        if choice == '🗺️ Regional Plot (SHP)':
            shp_spatial.spatial_plotting_ui()
        elif choice == '🌍 Global Plot':
            global_plot.global_plot_ui()


if __name__ == "__main__":
    main()

