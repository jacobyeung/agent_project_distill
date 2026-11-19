"""Publish the build-8 final evidence."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("report8.py")),run_name="__main__")
