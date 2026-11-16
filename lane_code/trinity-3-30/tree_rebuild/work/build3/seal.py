"""Refresh the shared tree artifacts with the build-specific inventory schema."""
import json
from pathlib import Path
import runpy

L=Path(__file__).resolve().parents[2]
runpy.run_path(str(L/'work/build2/seal.py'),run_name='__main__')
path=L/'out/TREE_SEAL.json'
value=json.loads(path.read_text())
value['schema']='build3-source-inventory-v1'
path.write_text(json.dumps(value,indent=2)+'\n')
