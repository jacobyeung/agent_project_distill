cd /scratch/jjyeung/orch_n30/n_review
cat > scan_vqa.py <<'PYEOF'
import sqlite3,json,hashlib,random,sys,os,re,collections
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
db='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
SEED=20261119
rem=set()
for f in ['w17b/work/build17/inputs/s.json','w18/work/build18/inputs/u.json','w21/work/build21/inputs/u_union.json','inputs/records/n.json','inputs/records/z.json']:
    for line in open(os.path.join(W,f)):
        if line.strip(): rem.add(json.loads(line)['row_key'])
for r in json.load(open(os.path.join(W,'w22/work/build22/inputs/naming_remove.json')))['rows']: rem.add(r['qid'])
PROG={'object_abs_distance','absolute_distance_object','room_size_estimation','absolute_size_room','camera_displacement','camera_movement_direction','camera_rotation'}
UNIT=re.compile(r'\b\d+(?:\.\d+)?\s*(?:m|meters?|metres?|cm|centimet(?:er|re)s?|mm|millimet(?:er|re)s?|ft|feet|foot|inch(?:es)?|degrees?|deg|square|sq)\b|\d+(?:\.\d+)?\s*°',re.I)
DEC=re.compile(r'(?<![\w.])\d+\.\d+')
CALL=re.compile(r'<call|</call|<tool|tool_call|\bCall\b|\bcall\(|<response|\bresponse:',re.I)
c=sqlite3.connect('file:'+db+'?mode=ro&immutable=1',uri=True)
st=collections.defaultdict(collections.Counter); ex=collections.defaultdict(list); ids=collections.defaultdict(list)
for i,row in c.execute('select i,row from rows'):
    r=json.loads(row)
    if r.get('qid') in rem: continue
    t=r.get('question_type'); tg=r.get('target') or ''
    m=re.search(r'<think>(.*?)</think>',tg,re.S); body=m.group(1).strip() if m else ''
    s=st[t]; s['rows']+=1; ids[t].append(i)
    flags=[]
    if not body: flags.append('answer_only')
    if t not in PROG and UNIT.search(body): flags.append('unit_number')
    if t not in PROG and DEC.search(body): flags.append('decimal')
    if t not in PROG and (CALL.search(body) or r.get('head_program')): flags.append('call_in_direct')
    for f in flags:
        s[f]+=1
        if len(ex[(t,f)])<3: ex[(t,f)].append(dict(i=i,qid=r.get('qid'),target=tg[:700]))
res=dict(db='210b25349b23af5b',removal_keys=len(rem),per_type={k:dict(v) for k,v in st.items()},examples={f'{k[0]}|{k[1]}':v for k,v in ex.items()})
json.dump(res,open('/scratch/jjyeung/orch_n30/n_review/vqa_scan.json','w'),indent=1)
print(json.dumps(res['per_type'],indent=0))
for k,v in res['examples'].items(): print('EX',k,json.dumps(v)[:1500])
PYEOF
OMP_NUM_THREADS=2 nice -n 10 timeout 1500 python3 scan_vqa.py
