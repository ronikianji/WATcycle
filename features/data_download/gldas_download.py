import os
import tempfile
import requests
import xarray as xr
import streamlit as st

def read_urls_from_uploaded_file(uploaded_file):
    """Read and clean list of URLs from uploaded text file."""
    text = uploaded_file.read().decode("utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]

def download_files(urls, token, progress_callback=None):
    """Download files from URL list using Earthdata token into a temporary folder."""
    download_dir = tempfile.mkdtemp(prefix="gldas_")
    filepaths = []

    for i, url in enumerate(urls):
        filename = os.path.basename(url)
        filepath = os.path.join(download_dir, filename)
        headers = {'Authorization': f'Bearer {token}'}

        with requests.get(url, stream=True, headers=headers) as response:
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        filepaths.append(filepath)

        if progress_callback:
            progress_callback((i + 1) / len(urls))

    return filepaths, download_dir

def merge_netcdf_files(filepaths, output_dir, output_filename="merged_gldas.nc"):
    """Merge NetCDF files into a single dataset and save."""
    merged_ds = xr.open_mfdataset(filepaths, combine="by_coords", engine="netcdf4")
    output_path = os.path.join(output_dir, output_filename)
    merged_ds.to_netcdf(output_path)
    return output_path

def gldas_download_ui():
    st.title("📥 GLDAS Data Download & Merge")
    st.markdown("""
    Upload a `.txt` file with GLDAS data URLs (one per line), provide your Earthdata token, and download the merged NetCDF.
    """)

    urls_file = st.file_uploader("🔗 Upload GLDAS URL list (.txt)", type="txt")
    token = st.text_input("🔑 Earthdata Login Token", type="password")

    if not urls_file or not token:
        st.info("Please upload a URL list and provide your Earthdata token.")
        return

    if st.button("🚀 Download & Merge"):
        try:
            urls = read_urls_from_uploaded_file(urls_file)
            # Read the list of URLs and filter only NetCDF files
            urls = [url for url in urls if url.endswith(".nc4") or url.endswith(".nc")]

            if not urls:
                st.error("No URLs found in uploaded file.")
                return

            progress = st.progress(0)
            status_text = st.empty()

            def update_progress(fraction):
                progress.progress(fraction)
                status_text.text(f"Downloading: {int(fraction * 100)}%")

            st.info("Downloading files. This may take a few minutes...")
            filepaths, tmp_dir = download_files(urls, token, update_progress)

            status_text.text("Merging files...")
            merged_path = merge_netcdf_files(filepaths, tmp_dir)

            status_text.text("✅ Merge complete!")
            st.success("Download your merged NetCDF file below:")

            with open(merged_path, "rb") as f:
                st.download_button(
                    label="📥 Download Merged NetCDF",
                    data=f,
                    file_name=os.path.basename(merged_path),
                    mime="application/netcdf"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
