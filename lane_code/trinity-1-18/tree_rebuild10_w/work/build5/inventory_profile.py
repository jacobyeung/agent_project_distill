"""Measure the read-only scratch census; never touch active test products."""
import json
from pathlib import Path
import sys
import time
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from compact_tmp import inventory
start=time.monotonic();files=inventory(L/'work/tmp');elapsed=time.monotonic()-start
record=dict(source='work/tmp',files=len(files),bytes=sum(files.values()),census_seconds=elapsed)
output=L/'work/build5/proofs/inventory';output.mkdir(parents=True,exist_ok=True)
(output/'CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
