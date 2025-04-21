import streamlit as st

def show_description():
    # Header and main content with custom styling
    st.markdown("""
    <div style='text-align: center; padding: 20px; margin-bottom: 30px'>
        <h1 style='color: #1f77b4'>🌊 Welcome to WATcycle</h1>
    </div>

    <div style='background-color: #f0f2f6; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin: 20px auto; max-width: 1000px'>
        <p style='font-size: 18px; line-height: 1.8; text-align: justify; color: #2c3e50'>
            WATcycle is a comprehensive hydrological analysis platform that seamlessly integrates data processing,
            analysis, and visualization capabilities. Our software simplifies complex water cycle modeling tasks through
            an intuitive interface, enabling users to effortlessly handle various data formats, perform statistical
            analyses, and generate insightful visualizations. From downloading and preprocessing data to advanced
            statistical analysis and spatial plotting, WATcycle provides researchers, hydrologists, and environmental
            scientists with the essential tools needed for sophisticated water resource analysis.
        </p>
        <div style='text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc'>
            <p style='color: #666; font-size: 16px'>Use the sidebar navigation to explore the tools and features </p>
        </div>
    </div>
    """, unsafe_allow_html=True)