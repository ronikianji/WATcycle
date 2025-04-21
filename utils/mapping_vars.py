import streamlit as st

def get_standard_mapping(required_keys=None, dataset=None):
    """
    Fetch the standard variable mapping from session state.

    Parameters:
    - required_keys: list of keys that must not be None (e.g., ["time", "lat", "lon"])
    - dataset: optional xarray dataset to check if mapped variables exist

    Returns:
    - dict: The mapping dictionary
    """
    mapping = st.session_state.get("standard_var_mapping")

    if mapping is None:
        st.warning("⚠️ Please complete variable mapping first.")
        st.stop()

    if required_keys:
        for key in required_keys:
            mapped_var = mapping.get(key)
            if not mapped_var:
                st.warning(f"⚠️ Required dimension '{key}' is not mapped.")
                st.stop()
            if dataset is not None and mapped_var not in dataset.dims and mapped_var not in dataset.variables:
                st.warning(f"⚠️ Mapped variable '{mapped_var}' for '{key}' not found in dataset.")
                st.stop()

    return mapping



# import streamlit as st

# def get_standard_mapping(required_keys=None, dataset=None):
#     """
#     Fetch and optionally filter the standard variable mapping from session state.

#     Parameters:
#     - required_keys: list of keys (e.g., ["time", "lat", "lon"]) that must be mapped (not None)
#     - dataset: optional xarray.Dataset to filter mapping by variables/dimensions

#     Returns:
#     - dict: Filtered mapping dictionary
#     """
#     mapping = st.session_state.get("standard_var_mapping")

#     if mapping is None:
#         st.warning("⚠️ Please complete variable mapping first.")
#         st.stop()

#     if required_keys:
#         for key in required_keys:
#             if not mapping.get(key):
#                 st.warning(f"⚠️ Required dimension '{key}' is not mapped.")
#                 st.stop()

#     # Optional filtering by dataset
#     if dataset is not None:
#         # Only keep mapping keys whose values exist as variables or dimensions in the dataset
#         mapping = {k: v for k, v in mapping.items() if v in dataset.variables or v in dataset.dims}

#     return mapping
