import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import bootstrap
raise SystemExit(bootstrap(*sys.argv[1:]))
