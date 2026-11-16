import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
for d in ('launcher','reader','reader/evaluator','cohort','proof'):sys.path.insert(0,str(ROOT/d))
os.environ['PYTHONDONTWRITEBYTECODE']='1'
