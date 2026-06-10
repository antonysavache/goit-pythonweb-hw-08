import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Contacts API"
author = "GoIT HW"
release = "1.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
