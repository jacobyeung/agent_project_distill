"""H1 read configuration over the reader lane's single generator."""
import sys
from pathlib import Path
K=Path(__file__).resolve().parents[1]
READER=K/'h1eval/reader_core'
for path in (str(READER),str(K/'tree')):
    if path not in sys.path: sys.path.insert(0,path)
