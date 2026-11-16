from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[1]
B=L/'work/base/work/base/tree_b01ce449'
sys.path[:0]=[str(B),str(L/'work/tests_r3')]
from generator_fixture_r3 import generate
records={kind:generate(B,kind) for kind in ('landscape','nadir_positive')}
(L/'work/generator_baseline_r3.json').write_text(json.dumps(records,sort_keys=True))
