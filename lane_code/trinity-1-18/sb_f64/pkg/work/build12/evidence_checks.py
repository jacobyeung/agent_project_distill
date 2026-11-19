from pathlib import Path
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1'
def read(p):return json.loads(p.read_text())
def function(path,name):
    s=path.read_text();n=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return '\n'.join(s.splitlines()[n.lineno-1:n.end_lineno])
base=L/'work/base/tree_b01ce449/student_pilot/carrier_c1.py'
old=function(base,'parameter_groups');new=function(T/'student_pilot/carrier_c1.py','parameter_groups')
assert old==new
init_old=function(L.parent/'wn3/work/tree_r1/student_pilot/carrier_c1_run.py','init_from_artifact')
init_new=function(T/'student_pilot/carrier_c1_run.py','init_from_artifact')
assert init_old==init_new
export_old=function(L.parent/'wm/work/tree_r1/student_pilot/carrier_c1_run.py','export')
export_new=function(T/'student_pilot/carrier_c1_run.py','export')
assert export_old==export_new
record=dict(base_group_builder=dict(source=str(base.relative_to(L)),byte_identical=True,sha256=hashlib.sha256(new.encode()).hexdigest()),
            training_initializer=dict(source=str(L.parent/'wn3/work/tree_r1/student_pilot/carrier_c1_run.py'),byte_identical=True,sha256=hashlib.sha256(init_new.encode()).hexdigest()),
            build11_export_producer=dict(source=str(L.parent/'wm/work/tree_r1/student_pilot/carrier_c1_run.py'),byte_identical=True,sha256=hashlib.sha256(export_new.encode()).hexdigest()))
(B/'NATIVE_FUNCTION_EQUALITY.json').write_text(json.dumps(record,indent=2))
prior=read(L.parent/'wm/work/merge11/proofs/eat1/c8r/run/EAT1_REPORT.json')
current=read(B/'proofs/eat1/c8r/run/EAT1_REPORT.json')
a={k:v['status'] for k,v in prior['clauses'].items()};b={k:v['status'] for k,v in current['clauses'].items()}
assert a==b
counts=read(B/'proofs/n1/text/RESULT.json')
expected={'a0_recovery':(1532,0,0),'a0_units':(2000,1186,1102),'a0_pool_abs_distance_reworded':(2000,1222,1119),'a0_room':(476,0,431)}
families=counts.get('families',counts)
for name,want in expected.items():
    got=families[name]['counts'];assert tuple(got[k] for k in ('text','reader','intake'))==want
sweep=read(B/'proofs/depth_sweep/RESULT.json');assert sweep['counts']['identical']==144000 and sweep['counts']['different']==0
(B/'PROOF_EQUALITY.json').write_text(json.dumps(dict(c8r=b,c8r_equal=True,c8r_source=str(L.parent/'wm/work/merge11/proofs/eat1/c8r/run/EAT1_REPORT.json'),
    c8r_offender_counts={k:len(v.get('offenders',[])) for k,v in current['clauses'].items()},
    families=expected,source='proofs/n1/text/RESULT.json',sweep=sweep['counts']),indent=2))
# Regenerate the editable harness patch against its preserved clean source.
clean=B/'harness_base';live=L/'work/build10/eat1';parts=[]
for p in sorted(live.rglob('*')):
    if not p.is_file() or p.suffix!='.py':continue
    rel=p.relative_to(live);q=clean/rel
    before=q.read_text().splitlines(True) if q.exists() else []
    after=p.read_text().splitlines(True)
    if before!=after:parts.extend(difflib.unified_diff(before,after,fromfile='a/eat1/'+str(rel),tofile='b/eat1/'+str(rel)))
(L/'out/EAT1_FIXED_MATH.patch').write_text(''.join(parts))
print(json.dumps(dict(group_builder_equal=True,initializer_equal=True,c8r=b,counts=expected)))
