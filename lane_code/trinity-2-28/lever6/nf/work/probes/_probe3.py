import json, re, collections
R='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/n13/ret/native'
META='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/meta/x/sj/orch_cd'
d=json.load(open(R+'/R1.json'))
tasks={}
for l in open(META+'/legs1_routed/out2/CAMERA_TASKS.jsonl'):
    t=json.loads(l); tasks['devrows:'+t['id']]=t
U=[x for x in d['arms']['unflagged'] if x['question_type'].startswith('camera')]
pat=collections.Counter(); ex={}
for x in U:
    t=x['decode']['text']; tail=t.rsplit('</think>',1)[-1]
    ans=tail.replace('<|im_end|>','').strip()
    resp=x['decode']['calls'][-1]['response']
    qt=x['question_type']
    if qt=='camera_displacement':
        m=re.search(r'distance = (\S+) m',resp); k='disp copy' if m and m.group(1)==ans else 'disp other'
    elif qt=='camera_rotation':
        m=re.search(r'turn = ([+-]\d+) deg',resp); k='rot copy' if m and int(m.group(1))==int(ans) else 'rot other'
        k+=(' plus' if ans.startswith('+') else '')
    else:
        m=re.search(r'Scoring each option by the matching component: (.*?)\.\n\nThe largest is (\w+)\. That matches option ([A-D])\.',t,re.S)
        k='dir template' if m and m.group(3)==ans else 'dir other'
        if m: ex.setdefault('opts',(tasks[x['key']]['options'], m.group(1), m.group(2), ans))
    pat[k]+=1
    if k.endswith('other'): ex.setdefault(k, (ans, resp, t[-300:]))
    pat['ncalls%d'%len(x['decode']['calls'])]+=1
print(pat); print(json.dumps(ex,indent=0)[:3000])
t=tasks[U[0]['key']]; print(sorted(t.keys()))
