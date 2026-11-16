"""Trace the unchanged checker in a CPU-only subprocess."""
from pathlib import Path
import runpy
import sys
from line_capture import capture
script=sys.argv[1]
sys.argv=sys.argv[1:]
output=Path(sys.argv[sys.argv.index('--output')+1]).with_name('CHECK_LINES.json')
with capture(output):
    runpy.run_path(script,run_name='__main__')
