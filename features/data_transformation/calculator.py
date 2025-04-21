import streamlit as st
import pandas as pd
import xarray as xr

def calculator():
    st.title("🧮 Calculator")

    st.markdown("""
    Perform mathematical operations on your NetCDF variables.
    Create new variables by combining existing ones using mathematical expressions.
    """)

    # Check if NetCDF file is uploaded
    if "uploaded_nc_file" not in st.session_state:
        st.warning("⚠️ Please upload a NetCDF file in the File Upload section first!")
        return

    file_path = st.session_state.uploaded_nc_file

    try:
        # Load NetCDF dataset
        ds = xr.open_dataset(file_path)

        # Variable selection with improved UI
        st.subheader("📊 Select Variables")
        variable_list = list(ds.data_vars.keys())
        variable_selection = st.multiselect(
            "Choose variables for calculation:",
            variable_list,
            default=[],
            help="Select one or more variables from your NetCDF file"
        )

        if variable_selection:
            df = ds[variable_selection].to_dataframe().reset_index()
            st.subheader("DataFrame")
            st.dataframe(df)

            # Calculator section
            st.subheader("🔢 Calculator")
            column_options = list(df.columns)

            with st.form("MathExpressionForm"):
                st.markdown("### Create New Variable")
                selected_columns = st.multiselect(
                    "Select input variables:",
                    column_options,
                    help="Choose variables to use in your calculation"
                )

                st.markdown("#### Enter Mathematical Expression")
                st.markdown("""
                Examples:
                - Basic: `variable1 + variable2`
                - Complex: `(variable1 * 2) + (variable2 / 100)`
                """)

                expression = st.text_area(
                    "Expression",
                    placeholder="Enter your mathematical expression here"
                )

                new_column_name = st.text_input(
                    "Name of new variable:",
                    value="calculated_result",
                    help="Enter a name for your new calculated variable"
                )

                submit = st.form_submit_button("✨ Calculate")

                if submit:
                    if selected_columns:
                        try:
                            safe_df = df[selected_columns].copy()
                            result = pd.eval(expression, local_dict=safe_df)
                            df[new_column_name] = result
                            st.success("✅ Calculation applied successfully!")

                            st.subheader("Results")
                            st.dataframe(df)

                            # Download section
                            st.markdown("### 📥 Export Results")
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "Download Results as CSV",
                                data=csv,
                                file_name="calculated_variables.csv",
                                mime="text/csv",
                                help="Download the complete dataset including your calculated variable"
                            )
                        except Exception as e:
                            st.error(f"❌ Calculation Error: {str(e)}")
                    else:
                        st.error("❌ Please select at least one variable for calculation.")

    except Exception as e:
        st.error(f"❌ Error loading NetCDF file: {str(e)}")
