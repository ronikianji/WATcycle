# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'WATcycle Documentation'
copyright = '2024, Roniki Anjaneyulu, Praveen Kashyap'
author = 'Roniki Anjaneyulu, Praveen Kashyap'
release = '1.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',     # Automatically generate documentation from docstrings
    'sphinx.ext.napoleon',    # Support for Google-style and NumPy-style docstrings
    'sphinx.ext.viewcode',    # Add links to source code
    'sphinx.ext.todo',        # Handle TODO comments
    'sphinx.ext.intersphinx', # Link to other documentation (e.g., Python docs)
]

autodoc_default_options = {
    'members': True,         # Document all class members
    'undoc-members': True,   # Include undocumented members
    'private-members': False # Exclude private methods
}


templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
