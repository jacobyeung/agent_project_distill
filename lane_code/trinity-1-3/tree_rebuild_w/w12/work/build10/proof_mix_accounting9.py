"""Account for repaired populations without inventing the other cell populations."""
import json,sys
from fractions import Fraction
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1';O=L/'work/build12/proofs/mix_accounting'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.routing_requirements import require
cfg=load(B/'inputs/config.json');card=load(pinned(cfg['r1_training']['mix']))
evidence=json.loads((L/'work/build12/proofs/extent_admission/RESULT.json').read_text())
mix={'cells':[dict(c,numerator=Fraction(str(c['rows_per_step'])).numerator,
                     denominator=Fraction(str(c['rows_per_step'])).denominator) for c in card['cells']]}
counts=evidence['routing_counts'];assert require(mix,counts)==counts
refusals=[]
for name,bad in [('recovery',dict(counts,recovery=0)),*[(u,dict(counts,units={**counts['units'],u:0})) for u in ('cm','ft','in')]]:
    try:require(mix,bad)
    except ValueError as error:refusals.append(dict(missing=name,reason=str(error)))
    else:raise AssertionError('Required population disappeared')
known={key:evidence['families'][family]['counts']['intake'] for key,family in (
    ('recovery','recovery'),('units','units'),('absolute_distance','absolute_distance'))}
accounting={}
for cell in card['cells']:
    if cell['type'] not in known:continue
    n=known[cell['type']];requested=int(Fraction(str(cell['rows_per_step']))*card['steps'])
    accounting[cell['type']]=dict(eligible=n,requested_draws=requested,repeat_ceiling=4*n,
        maximum_bound_draws=min(requested,4*n),draws_requiring_reallocation=max(0,requested-4*n))
unknown=[c['type'] for c in card['cells'] if c['type'] not in known]
result=dict(card=cfg['r1_training']['mix'],population_evidence=file_pin(L/'work/build12/proofs/extent_admission/RESULT.json'),
    required_families='PASS',routing_counts=counts,missing_family_refusals=refusals,known_cells=accounting,
    full_allocation='BLOCKED: other post-filter populations and native sampler indices remain unbound',unknown_cells=unknown,
    scope='Known-cell accounting only. No row plan, quota, threshold or unknown population was invented.')
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');monitor.save(O);print(json.dumps(result))
