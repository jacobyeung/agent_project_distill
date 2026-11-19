import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import stage_inputs
print(json.dumps(stage_inputs(*sys.argv[1:])))
