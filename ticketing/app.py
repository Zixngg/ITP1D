from importlib.util import module_from_spec, spec_from_file_location  # Load the local pricing file.
from pathlib import Path  # Resolve the library relative to this app.
from ticketing_layout import render_ticketing_page

# Reload the library on each rerun to avoid conflicting imports.
library_path = Path(__file__).resolve().with_name("mylibrary.py")
library_spec = spec_from_file_location("ticketing_mylibrary", library_path)
mylibrary = module_from_spec(library_spec)
library_spec.loader.exec_module(mylibrary)

render_ticketing_page(mylibrary)
