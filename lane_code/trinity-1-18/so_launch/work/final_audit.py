"""Audit the current review delivery and regenerate output checksums."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('audit_review_delivery.py')), run_name='__main__')
