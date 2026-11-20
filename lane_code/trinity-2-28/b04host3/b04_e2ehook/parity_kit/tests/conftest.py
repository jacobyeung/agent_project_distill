"""Keep test outputs in the kit, including the existing suite's proof report."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from parity_kit.common import install
install()
