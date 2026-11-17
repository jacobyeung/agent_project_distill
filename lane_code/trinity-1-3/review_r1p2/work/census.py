import sqlite3,json,sys,re,copy,hashlib
from collections import Counter
sys.path[:0]=['s5/work/tree','s5/work/tree/generator/derivgen_v7']
from student_pilot.type_mix import room_trace, family
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1',uri=True)
n=0;pools=Counter();roomtype=Counter();fam=Counter();mine=Counter();away=Counter();facing=Counter();suffix=Counter()
traced=[];oneline=[];room_other=[]
for i,r,t in c.execute('select i,row,target from rows order by i'):
    n+=1;d=json.loads(r);typ=d.get('question_type');pools[d.get('pool')]+=1
    fam[family(d,'vqa')]+=1
    # independent classification
    if typ in ('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','relative_direction_object','absolute_direction_object'):
        mine['facing' if d.get('facing') in ('toward','away') else 'direction']+=1
    if typ in ('object_counting','absolute_count','relative_count'): mine['totals' if d.get('count_kind')=='total' else 'counting']+=1
    if d['qid'].endswith('_away_opp'):
        suffix['away_opp']+=1; away[(d.get('pool'),d.get('facing'),typ)]+=1
    if typ in ('room_size_estimation','absolute_size_room'):
        roomtype[(d.get('pool'),room_trace(d))]+=1
        tg=d.get('target','')
        if d.get('pool')=='r1_room_traced': traced.append((i,d))
        else: room_other.append((i,d))
print('rows',n); print('pools',dict(pools)); print('room',dict(roomtype)); print('away_opp',suffix,dict(away))
print('family',dict(fam)); print('mine',dict(mine))
# line shapes of non-traced room rows
shape=Counter()
for i,d in room_other:
    tg=d.get('target','');m=re.fullmatch(r'\s*<think>\s*(.*?)\s*</think>.*',tg,re.S)
    shape[(len([l for l in (m[1] if m else '').splitlines() if l.strip()]), bool(m))]+=1
print('other room target shapes (think lines, has think)',dict(shape))
json.dump([i for i,_ in traced],open('traced_i.json','w'))
# mutants
def mut(d,kind):
    d=copy.deepcopy(d);tg=d['target'];m=re.fullmatch(r'(\s*<think>\s*)(.*?)(\s*</think>\s*)(\S+)(\s*)',tg,re.S);pre,th,mid,ans,post=m.groups()
    lines=th.split('\n')
    if kind=='frame_oob': th=re.sub(r'frame \d+','frame 33',th,count=1)
    elif kind=='frame0': th=re.sub(r'frame \d+','frame 0',th,count=1)
    elif kind=='no_relation': th='\n'.join(l for l in lines if l.strip().startswith('Seen:') or l.strip().startswith('The question'))
    elif kind=='two_relations': th=th+'\n'+lines[-1]
    elif kind=='digit_in_relation': th=th.rstrip()+' about 4 meters apart.'
    elif kind=='spelled': th=th.rstrip()+' They are roughly five meters apart.'
    elif kind=='area_stmt': th=th+'\nThe area is about 20.'
    elif kind=='wrong_pool': d['pool']='x'
    elif kind=='bad_pin': d['student_input']['frames'][int(re.search(r'frame (\d+)',th)[1])-1]['sha256']='z'*64
    elif kind=='no_seen': th='\n'.join(l for l in lines if not l.strip().startswith('Seen:'))
    elif kind=='nonnum_answer': ans='large'
    elif kind=='text_after': post=' sq m'
    elif kind=='relation_kw_missing': th='\n'.join(lines[:-1]+['The objects are distributed.'])
    elif kind=='prefix_text': th='Locate the shelf.\n'+th
    elif kind=='seen_digit_extra': th=th.replace('Seen:','Seen: 3',1)
    d['target']=pre+th+mid+ans+post;return d
kinds=['frame_oob','frame0','no_relation','two_relations','digit_in_relation','spelled','area_stmt','wrong_pool','bad_pin','no_seen','nonnum_answer','text_after','relation_kw_missing','prefix_text','seen_digit_extra']
res={k:Counter() for k in kinds}
for i,d in traced:
    for k in kinds: res[k][room_trace(mut(d,k))]+=1
for k in kinds: print('mutant',k,dict(res[k]))
