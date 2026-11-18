import json,os,sys,sqlite3,base64,hashlib,collections
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_tree11/work/n1');K=W/'pkg';T=K/'work/tree_r1'
os.environ.update(R2_FIXTURES=str(K/'fixtures'))
sys.path[:0]=[str(T)]
from student_pilot.p3_provenance import file_pin
from student_pilot.scene_division_gate import check_rows
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions
out={}
s=json.loads(base64.b64decode(json.load(open(K/'work/merge11/kits/r1/k/s.json'))['payload']))
kl=base64.b64decode(s['entries']['u/bd7843ded9961b087cab8bfe3355c39549c20038eddf380c17a7eefb0824faef']['payload'])
n=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json').read_bytes()
out['kit_list_sha']=hashlib.sha256(kl).hexdigest();out['kit_list_equals_r1_ops_bytes']=kl==n
keys=[json.loads(l)['row_key'] for l in kl.decode().splitlines() if l.strip()];out['kit_list_keys']=len(keys);out['unique']=len(set(keys))
(W/'tmp/list.jsonl').write_bytes(kl)
F=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k')
div=file_pin(Path('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json'))
assert div['sha256'].startswith('0d28fdd4')
rule=Exclusions(file_pin(T/'student_pilot/r2_dev_merged.json'),file_pin(F/'benchmark_scene_exclusions.json'))
rem=[file_pin(F/f'remove_{i}.jsonl') for i in range(6)]
kitpins=['62113ff3','4701e195','6eb00a2d','8a97fcc4','e3b0c442','e3b0c442']
out['remove_0_5_match_kit']=[p['sha256'][:8] for p in rem]==kitpins
DB='/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
def rows():
    c=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
    for r, in c.execute('SELECT row FROM rows ORDER BY i'):yield json.loads(r)
for name,files in (('with_list',rem+[file_pin(W/'tmp/list.jsonl')]),('without_list',rem)):
    try:out['vqa_'+name]=check_rows(rows(),div,removals=Removals(files),scene_filter=rule,stream='vqa')
    except ValueError as e:out['vqa_'+name]='REFUSED '+str(e)
# one row outside train_scenes refuses even when everything else passes
d=json.load(open(div['path']));train=set(d['train_scenes'])
first=next(rows());bad=dict(first,scene='zz_not_in_division',qid='x1')
try:check_rows([first,bad],div);out['synthetic_outside']='ADMITTED'
except ValueError as e:out['synthetic_outside']=str(e)
# routing sources bound for N: scenes vs division
from student_pilot.r2_adapters import normalize
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
for fam,p in (('recovery',R/'recovery_v3/rows.jsonl'),('absolute_distance',R/'vehN_pool_abs_distance/repaired/rows.jsonl'),('units',R/'vehN_units/repaired/rows_slice.jsonl')):
    c=collections.Counter()
    for l in open(p):
        r=json.loads(l);sc=r.get('dataset','?')+'/'+r.get('scene','?');c['in_train' if sc in train else 'outside']+=1;c['heldout']+=sc in set(d['heldout_scenes'])
    out['routing_'+fam]=dict(c)
print(json.dumps(out,indent=1));(W/'F6.json').write_text(json.dumps(out,indent=1))
