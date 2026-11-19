"""Verify the ordered review series using bounded touched-file copies."""
from pathlib import Path
import runpy
import sys
if len(sys.argv) != 2:
    raise SystemExit('Usage: work/verify_patches.py FRESH_DESTINATION_UNDER_WORK')
runpy.run_path(str(Path(__file__).with_name('verify_review_patches.py')), run_name='__main__')
