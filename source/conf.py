# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import datetime
import sphinx_rtd_theme

# -- Project information -----------------------------------------------------

project = 'docs.cstevens.io'
copyright = '2020, Chris Stevens'
author = 'Chris Stevens'

# -- Helper function for generating datever

def get_date_version():
    """ Generates a date-version

        Output format is YYYY.MM.DD.24HR.MM
    """

    dt = datetime.datetime.now()
    date_version = dt.strftime("%Y.%m.%d.%H.%M")
    return date_version

version = get_date_version()
release = get_date_version()

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.githubpages',
    'sphinx_rtd_theme'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_theme_options = {
    'style_external_links': True,
    'display_version': True,
    'sidebarwidth': 100
}

html_context = {
    'display_github': True,
    'github_user': 'splooge',
    'github_repo': 'splooge.github.io',
    'github_version': 'master/source/' ,
}

html_css_files = [
    'custom.css',
]
