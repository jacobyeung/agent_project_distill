"""Assemble the current review delivery from its exact verification logs."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('write_review_report.py')), run_name='__main__')
