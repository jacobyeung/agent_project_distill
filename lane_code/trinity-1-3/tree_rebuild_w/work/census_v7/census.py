"""Full-store v7 division census with build 9fix's gate code (lane tree_rebuild6, read-only inputs)."""
import json, sqlite3, sys, hashlib
from collections import Counter
T='/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f/work/tree_r1'; sys.path.insert(0,T)
from student_pilot.scene_division_gate import check_rows
from student_pilot.row_removals import Removals
B=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f/work/build9fix/F6_BINDING.json'))
DB='/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
div=json.load(open(B['division']['path'])); train=set(div['train_scenes']); held=set(div['heldout_scenes'])
lst=[json.loads(l) for l in open(B['remove']['path'])]; listed={r['row_key'] for r in lst}
def rows():
    c=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
    for r, in c.execute('SELECT row FROM rows ORDER BY i'): yield json.loads(r)
outside=set(); heldhits=0; n=0; fam=Counter(); qt=Counter()
for r in rows():
    n+=1; s=r['dataset']+'/'+r['scene']
    if s not in train: outside.add(r['qid']); fam[r.get('pool') or r.get('source') or '?']+=1; qt[r.get('question_type','?')]+=1
    heldhits+= s in held
res=dict(db=DB, db_sha_expected='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443', division=B['division'], remove=B['remove'], rows=n,
 outside_no_filters=len(outside), heldout_hits=heldhits, outside_by_pool=fam, outside_by_type=qt,
 list_keys=len(listed), outside_equals_list=outside==listed, outside_minus_list=sorted(outside-listed)[:50], list_minus_outside=sorted(listed-outside)[:50])
try: check_rows(rows(), B['division']); res['gate_without_list']='PASSED (unexpected)'
except ValueError as e: res['gate_without_list']=str(e)
try: res['gate_with_list']=check_rows(rows(), B['division'], removals=Removals([B['remove']]))
except ValueError as e: res['gate_with_list']='REFUSED: '+str(e)
res['scope']='full store, no scene filter and no remove_0..5 applied (the 601 list was derived after those); routing stream not censused here'
json.dump(res, open('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/census_v7/RESULT.json','w'), indent=1, default=dict); print(json.dumps(res, default=dict)[:1500])
