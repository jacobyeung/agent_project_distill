import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import seal
print(seal(sys.argv[1]))
