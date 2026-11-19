"""Run the review's mutation bodies against current published slices and envelope."""
import copy
import json
import os
from pathlib import Path
import sys
import types
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
sys.path.insert(0,str(L/'work/build4'))
os.environ['R2_FIXTURES']=str(L/'fixtures')
from rows_proof import envelope
from student_pilot.r2_intake import intake
from student_pilot.p3_provenance import load,write
output=Path(sys.argv[1]).resolve()
output.mkdir(parents=True,exist_ok=False)
from student_pilot.source_seal import inventory
write(output/'SOURCE.json',inventory(L/'work/tree_r1'))
def first_ok(family, source):
    group='slices_final' if source=='adapted4' else 'slices_v3'
    man=L/'work/build4/rows_complete'/group/family/'manifest.json'
    items,report=intake(man)
    return items[0]['row']
def build(family,p,stream,d):
    man=envelope(p,d/'env')
    record=load(man);record['stream']=stream;man.write_text(json.dumps(record))
    return man
source=(L/'work/review1/evidence/mutate.py').read_text()
body=source[source.index('def run('):source.index("json.dump(res,")]
namespace=dict(copy=copy,json=json,OUT=output,mk=types.SimpleNamespace(build=build),intake=intake,first_ok=first_ok)
exec(compile(body,'review_mutation_body','exec'),namespace)
result=namespace['res']
write(output/'MUTATIONS.json',result)
probe=(L/'work/review1/evidence/probe_bank.py').read_text()
probe=probe[:probe.index("json.dump(out,")]
namespace={'__name__':'review_bank_probe'}
exec(compile(probe,'review_bank_body','exec'),namespace)
write(output/'PROBE_BANK.json',namespace['out'])
print(json.dumps(dict(mutations=len(result),admitted=[r['mutation'] for r in result if r['admitted']])))
