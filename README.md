![Image: Python Logo](https://github.com/ronikianji/WATcycle/blob/5d731b06376360baad7d824a21a7ce91fd338602/assets/Cover%20Image.jpg)
# WATcycle

[![Python Version](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/release/python-380/)
[![Open in Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ronikianji/WATcycle)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/ronikianji/WATcycle/blob/1338c4fb71dde76a90d6fe632918d0dcc35b1b5c/LICENSE)

A comprehensive toolbox for performing advanced hydrological analysis, including data preprocessing, statistical calculations, and visualizations. 
This repository contains Jupyter Notebooks organized into folders and subfolders. The development of such a resource is intended to enable users in conducting their hydrological research and extend it to their relevant activities.

## Table of Contents
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Contributors](#contributors)
- [License](#license)

## Folder Structure
```mermaid
graph TD
        A[Download Data] --> B[Display Data]
        B --> B1[NC File]
        B1 --> B1A[Summary]
        B1 --> B1B[DataFrame Creation]
```
```mermaid
graph TD
        C[Data Transformation and Management] --> C1[Clipping Shapefile Data]
        C --> C2[Finding Missing Time Steps]
        C --> C3[Interpolate NaN Values]
        C --> C4[Merge or Split NC Files]
        C --> C5[Resolution Change]
        C --> C6[Saving NC Files]
```
```mermaid
graph TD
                J[Spatial Plotting] --> J1[World]
                J --> J2[Shapefile]
```
```mermaid
graph TD
        K[Time Series Plotting] --> K1[Trend Analysis]
        K --> K2[Seasonal Analysis]
        K --> K3[Residual Analysis]
        K --> K4[Data Validation]
```
## Installation
```bash
# Navigate to the main_app folder
main_app --> main.py

# Install the required dependencies
pip install -r requirements.txt

# Run the WATcycle application
streamlit run main.py
```
## Contributors
This toolbox is designed to support hydrological analysis. Contributions are welcome to improve the toolbox, add new features, or enhance its functionality for the hydrological community. 
Your feedback and involvement are highly appreciated, and we thank all those who have contributed or plan to contribute in the future.

## License
This project is licensed under the MIT License. You can use, modify, and distribute it as long as you include the original license in your copies. 
Use this DOI for citation: [DOI: [DOI here]]
