import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Anomalies Detection in IoT'
copyright = '2026, Group C - Yingying Gao, Nouha Madiouni, Estela Mora Barba'
author = 'Group C - Yingying Gao, Nouha Madiouni, Estela Mora Barba'

version = '1.0'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.insert(0, os.path.abspath('../../edge'))
sys.path.insert(0, os.path.abspath('../../cloud'))
sys.path.insert(0, os.path.abspath('../../attacks'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx.ext.autosummary',
    'sphinx_simplepdf',
    'sphinxcontrib.mermaid'
]

# Enable automatic member detection
autodoc_default_options = {
    'members': True,          # Auto-document all members
    'member-order': 'bysource', # Follow source order
    'undoc-members': True,    # Show undocumented members
    'show-inheritance': True, # Display inheritance
    'special-members': '__init__', # Document __init__ methods
}

autodoc_mock_imports = [
    'google',
    'paho',
    'connexion',
    'six',
    'flask',
    'cv2',
    'PIL',
    'ultralytics',
    'tqdm',
    'numpy',
    'streamlit',
    'streamlit_autorefresh',
    'pandas',
    'sklearn',
    'pm4py',
    'pytz'                  
]

# Enable automatic module discovery
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []
suppress_warnings = ['epub.unknown_project_files']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
