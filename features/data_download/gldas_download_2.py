import os
import tempfile
import requests
import xarray as xr
import streamlit as st

# ---- Helpers ----

def read_urls_from_uploaded_file(uploaded_file):
    text = uploaded_file.read().decode("utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]

def download_files(urls, token, progress_callback=None):
    download_dir = tempfile.mkdtemp(prefix="gldas_")
    filepaths = []
    for i, url in enumerate(urls):
        filename = os.path.basename(url)
        filepath = os.path.join(download_dir, filename)
        headers = {'Authorization': f'Bearer {token}'}
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        filepaths.append(filepath)
        if progress_callback:
            progress_callback((i + 1) / len(urls))
    return filepaths, download_dir

def merge_netcdf_files(filepaths, output_dir, output_filename="merged_gldas.nc"):
    ds = xr.open_mfdataset(filepaths, combine="by_coords", engine="netcdf4")
    out_path = os.path.join(output_dir, output_filename)
    ds.to_netcdf(out_path)
    return out_path, ds

# ---- UI ----

def gldas_download_ui():
    st.title("📥 GLDAS Data Download & Merge")
    st.markdown(
        "1️⃣ Upload your `.txt` list of GLDAS URLs & enter Earthdata token, then click **Process URLs**.  \n"
        "2️⃣ Once processed, download the full merge or apply filters below."
    )

    # --- Inputs ---
    urls_file = st.file_uploader("🔗 Upload GLDAS URL list (.txt)", type="txt")
    token     = st.text_input("🔑 Earthdata Login Token", type="password")

    # --- Step 1: Process URLs ---
    if st.button("Process URLs") and urls_file and token:
        try:
            urls = read_urls_from_uploaded_file(urls_file)
            urls = [u for u in urls if u.endswith((".nc", ".nc4"))]
            if not urls:
                st.error("No valid .nc/.nc4 URLs found.")
            else:
                progress    = st.progress(0)
                status_text = st.empty()

                def _update(p):
                    progress.progress(p)
                    status_text.text(f"Downloading: {int(p*100)}%")

                st.info("Downloading files…")
                filepaths, tmp_dir = download_files(urls, token, _update)

                status_text.text("Merging files…")
                merged_path, merged_ds = merge_netcdf_files(filepaths, tmp_dir)

                st.success("✅ Merge complete!")
                # persist in session
                st.session_state["merged_ds"]   = merged_ds
                st.session_state["merged_path"] = merged_path
                st.session_state["tmp_dir"]     = tmp_dir

        except Exception as e:
            st.error(f"❌ Error during processing: {e}")

    # --- Step 2: Download + Filter (only if merged_ds exists) ---
    if "merged_ds" in st.session_state:
        st.markdown("---")
        st.subheader("2️⃣ Download & Filter")

        # 2a) Full merged download
        merged_path = st.session_state["merged_path"]
        with open(merged_path, "rb") as f:
            st.download_button(
                label="📥 Download Complete Merged NetCDF",
                data=f,
                file_name=os.path.basename(merged_path),
                mime="application/netcdf"
            )

        st.markdown("— or —")

        # 2b) Filter UI
        merged_ds = st.session_state["merged_ds"]
        tmp_dir   = st.session_state["tmp_dir"]

        st.markdown("**Filter variables and time range**")

        # Variables
        vars_list     = list(merged_ds.data_vars)
        selected_vars = st.multiselect("Select variables", vars_list)
        if not selected_vars:
            st.info("⚠️ Pick at least one variable to enable filtered download.")

        # # Time (if available)
        # if "time" in merged_ds.coords:
        #     tv = merged_ds.time.values
        #     default_start = str(tv.min())[:10]
        #     default_end   = str(tv.max())[:10]
        #     trange = st.date_input("Select time range", [default_start, default_end])
        #     if isinstance(trange, (list, tuple)):
        #         start_date, end_date = trange
        #     else:
        #         start_date = end_date = trange

        # Two separate date inputs
        tv = merged_ds.time.values
        default_start = str(tv.min())[:10]
        default_end   = str(tv.max())[:10]

        start_date = st.date_input("📅 Start date", default_start)
        end_date   = st.date_input("📅 End date",   default_end)

        #Guard against inversion
        if start_date > end_date:
            st.warning("Start date must be on or before end date.")
        else:
            st.error("⛔ No time coordinate found; filtering by time disabled.")
            start_date = end_date = None

        # Filename
        out_fname = st.text_input("Output filename (.nc)", "filtered_gldas.nc")
        if not out_fname.endswith(".nc"):
            out_fname += ".nc"

        # Filter & Download button
        if st.button("📤 Download Filtered NetCDF"):
            # validations
            if not selected_vars:
                st.warning("Please select one or more variables.")
            elif start_date and end_date and start_date > end_date:
                st.warning("Start date must be before end date.")
            else:
                try:
                    subset = merged_ds[selected_vars]
                    if start_date and end_date:
                        subset = subset.sel(time=slice(str(start_date), str(end_date)))
                    fp = os.path.join(tmp_dir, out_fname)
                    subset.to_netcdf(fp)

                    with open(fp, "rb") as f:
                        st.download_button(
                            label="📥 Download Filtered NetCDF",
                            data=f,
                            file_name=out_fname,
                            mime="application/netcdf"
                        )
                except Exception as e:
                    st.error(f"❌ Filtering failed: {e}")

if __name__ == "__main__":
    gldas_download_ui()
