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

import dask_chtc

# -- Project information -----------------------------------------------------

project = "Dask-CHTC"
copyright = "2020, Josh Karpel"
author = "Josh Karpel"

# The full version, including alpha/beta/rc tags
release = dask_chtc.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "nbsphinx",
    "IPython.sphinxext.ipython_console_highlighting",
    "sphinx_click.ext",
    "sphinx_issues",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["**/.ipynb_checkpoints"]

pygments_style = "colorful"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
import sphinx_rtd_theme

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Extension Configuration -------------------------------------------------

autoclass_content = "both"

intersphinx_mapping = {
    "https://docs.python.org/3/": None,
    "htcondor": (
        "https://htcondor.readthedocs.io/en/latest/",
        "https://htcondor.readthedocs.io/en/latest/objects.inv",
    ),
    "classad": (
        "https://htcondor.readthedocs.io/en/latest/",
        "https://htcondor.readthedocs.io/en/latest/objects.inv",
    ),
    "dask": ("https://docs.dask.org/en/latest/", "https://docs.dask.org/en/latest/objects.inv",),
    "dask.distributed": (
        "https://distributed.dask.org/en/latest/",
        "https://distributed.dask.org/en/latest/objects.inv",
    ),
    "dask_jobqueue": (
        "https://jobqueue.dask.org/en/latest/",
        "https://jobqueue.dask.org/en/latest/objects.inv",
    ),
}
