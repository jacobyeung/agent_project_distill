import json,sqlite3,hashlib,sys,re,collections
V='/scratch/jjyeung/orch_n30/rows_rebuild3/work/validator/trace_grammar.py'
print(hashlib.sha256(open(V,'rb').read()).hexdigest())
sys.path.insert(0,'/scratch/jjyeung/orch_n30/rows_rebuild3/work/validator');import trace_grammar as tg
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
bad=collections.Counter()
for r in rows:
    for e in tg.validate_row(r):bad[e.rule_id]+=1
print('validator failures',bad,len(rows))
# my own grammar checks
c=collections.Counter();qs=collections.Counter()
for r in rows:
    t=r['target'];body,tail=t.split('</think>')
    if tail!='\n\n'+r['answer'] or not re.fullmatch(r'[A-D]',r['answer']):c['tail']+=1
    b=body.replace('<think>\n','')
    s=re.sub(r'Step \d+:','',b);s=re.sub(r'frame \d+','',s)
    if re.search(r'\d',s):c['digit']+=1
    if re.search(r'\b(m|cm|meters?|metres?|degrees?|feet|ft|inch(es)?|°|%)\b',b,re.I):c['unit']+=1
    for fr in map(int,re.findall(r'frame (\d+)',b)):
        if not 1<=fr<=len(r['student_input']['frame_indices']):c['frame_oob']+=1
    loc=re.findall(r'locate the (.+?), first seen in frame (\d+)\.',b)
    if len(loc)!=len(r['provenance']['instances']):c['locate_count']+=1
    if 'camera' in ' '.join(l for l,_ in loc):c['camera_located']+=1
    qs[r['student_input']['question']]+=1
    c['n='+str(len(r['student_input']['frame_indices']))]+=1
print(c)
print('duplicate questions',sum(v-1 for v in qs.values() if v>1))
# benchmark collisions
bq=set()
for l in open('/scratch/jjyeung/orch_n30/vsti_diag/work/FAILING_ITEMS.md'):
    if l.startswith('Q: '):bq.add(l[3:].split(" ['")[0].strip())
print('bench Q lines',len(bq),'exact collisions',sum(1 for r in rows if r['student_input']['question'] in bq))
coll=[r['student_input']['question'] for r in rows if r['student_input']['question'] in bq];print(coll[:5])
