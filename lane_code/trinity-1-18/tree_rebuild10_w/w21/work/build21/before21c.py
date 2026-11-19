from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from naming21 import scan_decoded
try:
    scan_decoded(B/'kits/q')
except ValueError as error:
    message=str(error)
    assert 'k/benchmark_scene_exclusions.json' in message,message
    result=dict(status='EXPECTED_REFUSAL',error=message)
else:raise AssertionError('Base kit must fail the new scanner')
(C/'FAILING_BEFORE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
