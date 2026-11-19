import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import snapshot
snapshot(*sys.argv[1:],kit=Path(__file__).resolve().parents[1])
