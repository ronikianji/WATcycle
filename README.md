
# PyPackage

[![Python Version](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/release/python-380/)
[![Open in Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/ronikianji/PyPackage.git)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Folder Structure
graph TD
    %% Main process branches with spacing in reverse order

    subgraph Time_Series_Analysis
        K[Time Series Plotting] --> K1[Trend Analysis]
        K --> K2[Seasonal Analysis]
        K --> K3[Residual Analysis]
        K --> K4[Data Validation]
    end

    subgraph Spatial_Analysis
        J[Spatial Plotting] --> J1[World]
        J --> J2[Shapefile]
    end

    subgraph Data_Preproccesing
        C[Data Transformation and Management] --> C1[Clipping Shapefile Data]
        C --> C2[Finding Missing Time Steps]
        C --> C3[Interpolate NaN Values]
        C --> C4[Merge or Split NC Files]
        C --> C5[Resolution Change]
        C --> C6[Saving NC Files]
    end

    subgraph First_Look
        A[Download Data] --> B[Display Data]
        B --> B1[NC File]
        B1 --> B1A[Summary]
        B1 --> B1B[DataFrame Creation]
    end

    %% Add styling to differentiate sections
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bbf,stroke:#333,stroke-width:2px
    style J fill:#bfb,stroke:#333,stroke-width:2px
    style K fill:#bfb,stroke:#333,stroke-width:2px
