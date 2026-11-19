"""Generate the current review report from measured receipts."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("write_round2_report.py")),run_name="__main__")
