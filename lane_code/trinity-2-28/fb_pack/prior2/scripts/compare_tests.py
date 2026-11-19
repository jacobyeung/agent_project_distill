import json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out'
def load(n):return json.loads((O/n).read_text())
def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
base=load('CPU_FINAL_base.json');new=load('CPU_FINAL_new.json');census=load('CENSUS_LOADER.json')
rank={'PASS':0,'SKIP':1,'FAIL':2,'ERROR':3}
def states(result):
 out={}
 for r in result['records']:
  if r['id'] not in out or rank[r['status']]>rank[out[r['id']]['status']]:out[r['id']]=r
 return out
bs,ns=states(base),states(new)
regressions=[dict(test=k,base=bs[k],new=ns.get(k,'MISSING')) for k in bs if k not in ns or rank[ns[k]['status']]>rank[bs[k]['status']]]
newtests=[v for k,v in ns.items() if k not in bs];bad_new=[v for v in newtests if v['status']!='PASS']
old_failures={(r['id'],r['status']) for r in base['failed_cases']}
new_failures=[r for r in new['failed_cases'] if (r['id'],r['status']) not in old_failures]
record={'status':'NO_NEW_FAILURE' if not regressions and not bad_new and not new_failures else 'REGRESSIONS_REQUIRE_REVIEW',
 'production_gate':'MISSING',
 'full_cpu':{label:{k:r[k] for k in ('modules_attempted','tests_run','failures','errors','skips','seconds','restrictions')} for label,r in [('base',base),('new',new)]},
 'regressions':regressions,'new_tests':newtests,'new_failed_cases_including_subtests':new_failures,
 'checks':{'base_seal':'PASS','patch_applies_to_sealed_base':'PASS','optional_absent_all_cells_in_diagnostic_harness':'PASS',
  'optional_absent_all_cells_production':'MISSING','optional_present_production_non_direction_identity':'MISSING',
  'optional_present_diagnostic_non_direction_identity':'PASS','toward_hard_count_and_other_positions':'PASS_DIAGNOSTIC',
  'away_and_other_clause_shares':'PASS_DIAGNOSTIC','max_four_draws':'PASS_DIAGNOSTIC',
  'tampered_weight_refuses':'PASS','resume_deterministic':'PASS','production_loader_facing_pair_inclusion':'PASS_UNIT_TEST',
  'production_full_population':'MISSING'},
 'base_negative_controls':census['base_negative_controls'],
 'inputs':[pin(O/n) for n in ('CPU_FINAL_base.json','CPU_FINAL_new.json','CPU_FINAL_base.log','CPU_FINAL_new.log','CENSUS_LOADER.json','FILES_TOUCHED.json','MISSING_INPUTS.json')]+[pin(Path(__file__).resolve())],
 'commands':['OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python scripts/cpu_run.py '+label for label in ('base','new')]}
(O/'TESTS.json').write_text(json.dumps(record,indent=2)+'\n')
print('regressions',len(regressions),'new tests',len(newtests),'bad new',len(bad_new),'new failure cases',len(new_failures))
for r in regressions:print(r)
for r in new_failures:print(r['id'],r['status'])
