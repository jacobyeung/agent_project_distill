# Independent VQA cell census on store v7 (review_cprime). Family rule replays type_mix.family (cp/work/tree/student_pilot/type_mix.py:44-72),
# removal keys replay row_removals.row_keys/defects (row_removals.py:9-46). Filters: remove_0..5 (records), n.json, B1 (z.json), exclude_qids['vqa'], scene lists.
import sqlite3,json,collections,sys
sys.path.insert(0,'/scratch/jjyeung/orch_n30/r1_ops6/cp/work/tree')
from student_pilot.type_mix import family
R='/scratch/jjyeung/orch_n30/r1_ops6/cp/work/records/'
def row_keys(row):
    v=[row.get("row_key"),row.get("qid")]
    for f in ("pointing","grounding","provenance"):
        if isinstance(row.get(f),dict): v.append(row[f].get("row_key"))
    v.extend(row.get("label_row_keys",[])); return {str(x) for x in v if x is not None}
def lst(p,defects=None):
    rows=[json.loads(l) for l in open(p) if l.strip()]
    if defects: rows=[r for r in rows if set(r['defect'].split('|'))&set(defects)]
    return {r['row_key'] for r in rows}
base=set()
for i in range(6): base|=lst(R+f'remove_{i}.jsonl',['identity','absent','merged'] if i==3 else None)
N=lst('/scratch/jjyeung/orch_n30/r1_ops6/snapm/snap_9dd2fbb7/out/records/n.json')
B=lst('/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json')
xq=set(json.load(open(R+'66c427e2.json'))['vqa'])
def strings(o,acc):
    if isinstance(o,str): acc.add(o)
    elif isinstance(o,list): [strings(x,acc) for x in o]
    elif isinstance(o,dict): [strings(x,acc) for x in o.values()]+[acc.add(k) for k in o]
    return acc
sc=set(); strings(json.load(open(R+'benchmark_scene_exclusions.json')),sc); strings(json.load(open(R+'dev_scene_exclusions.json')),sc); strings(json.load(open(R+'dafa4a9c.json')),sc)
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?immutable=1&mode=ro',uri=True)
pre=collections.Counter(); post=collections.Counter(); hits=collections.Counter()
for i,r,t in c.execute("select i,row,target from rows"):
    d=json.loads(r); fam=family(d,'vqa'); k=row_keys(d)
    excl_scene=(f"{d.get('dataset')}/{d.get('scene')}" in sc) or (d.get('scene') in sc)
    tags=[n for n,s in (('base',base),('n',N),('B1',B)) if k&s]+(['xq'] if d['qid'] in xq else [])+(['scene'] if excl_scene else [])
    for tg in tags: hits[(fam,tg)]+=1
    if not (k&base or k&N or d['qid'] in xq or excl_scene): pre[fam]+=1
    if not tags: post[fam]+=1
cells=json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/cp/out/config.json'))['type_mix']['streams']['vqa']['cells']
tab={f:dict(cents=cells.get(f,{}).get('cents'),eligible_preB1=pre[f],eligible=post[f],cap_cents=post[f]*400//1000,draws_1000=-(-1000*cells.get(f,{'cents':0})['cents']//100),
            draws_201_600=400*cells.get(f,{'cents':0})['cents']/100) for f in sorted(set(pre)|set(cells))}
for f,v in tab.items(): v['ok']=v['cents'] is None or v['cents']<=v['cap_cents']
res=dict(table=tab,hits={f"{a}|{b}":v for (a,b),v in hits.items()},cents_sum=sum(v['cents'] for v in cells.values()))
json.dump(res,open('../out/CENSUS_MINE.json','w'),indent=1)
for f,v in tab.items(): print(f,v)
print(res['hits']); print('sum',res['cents_sum'])
