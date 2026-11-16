import json, sys, os, copy
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/review_tree/work'); H = W/'h'
SRC = W/'stage3b/b8e96247a318_t/o/ee000001'
sys.path.insert(0, str(SRC)); sys.path.insert(0, str(H))
os.environ['STUDENT_R2_LOCAL_NODE'] = '1'
import mk
from student_pilot.r2_intake import intake
from student_pilot.p3_provenance import file_pin
OUT = H/'mut3b'; OUT.mkdir(exist_ok=True)
merged = file_pin(SRC/'student_pilot/r2_dev_merged.json')
def run(name, fam, stream, rowlist, with_merged=True):
    d = OUT/name; d.mkdir(exist_ok=True); p = d/(fam+'.jsonl')
    with open(p,'w') as f:
        for r in rowlist: f.write(json.dumps(r)+'\n')
    m = mk.build(fam, p, stream, d)
    if with_merged:
        v = json.load(open(m)); v['dev_scene_exclusions'] = merged; m.write_text(json.dumps(v))
    try: adm, rep = intake(m)
    except Exception as e: return dict(mutation=name, admitted=False, refusal='raised: '+str(e)[:150])
    return dict(mutation=name, admitted=len(adm)==len(rowlist), refusal=[r['reason'][:150] for r in rep['refusals']])
rows = lambda p: [json.loads(l) for l in open(p)]
base = rows(H/'adapted/d0_retrace_object_rel_distance.jsonl')
adm, _ = intake(H/'adapted_env/d0_retrace_object_rel_distance.manifest.json'); q = adm[0]['row']['qid']
base = next(r for r in base if r['qid']==q)
u = rows(H/'adapted4/a0_units.jsonl'); adm,_ = intake(H/'adapted4_env/a0_units.manifest.json'); uq = adm[0]['row']['qid']; u = next(r for r in u if r['qid']==uq)
res = [run('baseline_vqa_merged', 'd0_retrace_object_rel_distance', 'vqa', [base]), run('baseline_units_merged', 'a0_units', 'routing', [u])]
for tag, scene, canon in [('withheld_alias_token','v0e47a88934bd',None),('withheld_native','scene0161_00',None),('withheld_canonical_only',base['scene'],'scannet/scene0161_02')]:
    r = copy.deepcopy(base); r['dataset']='d1'; r['scene']=scene
    if canon: r.setdefault('provenance',{})['canonical']=canon
    res.append(run(tag,'d0_retrace_object_rel_distance','vqa',[r]))
w = copy.deepcopy(u); w['dataset']='d1'; w['scene']='v0e47a88934bd'; w['provenance']['alias']='d1/v0e47a88934bd'; w['provenance']['canonical']='scannet/scene0161_00'
res.append(run('withheld_routing_units','a0_units','routing',[w]))
# pointing/pose-like perception row of a withheld room through the r2 intake (stream pose without target -> perception check)
dev = json.load(open(SRC/'student_pilot/r2_dev_merged.json'))
print('merged keys', list(dev)[:12], 'rooms', len(dev['rooms']))
json.dump(res, open(OUT/'MUTATIONS_3B.json','w'), indent=1)
for x in res: print(('ADMITTED ' if x['admitted'] else 'refused  ')+x['mutation'], '|', x['refusal'])
