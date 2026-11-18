#!/usr/bin/env python3
"""Rescued-gap split for job 1 distance: items where null_argmax had a not-seen call or capped and candidates_argmax returned."""
import json,statistics,sys
from pathlib import Path
import tower_pair as tp
scorers,_=tp.configure('src')
items={i['id']:i for i in json.loads(Path('src/items/devs1_routed.json').read_text())['items']}
own,_=tp.load(['/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/%s/items.jsonl'%j for j in ('170631','170706','170694')],items,'own')
null,_=tp.load(['work/ret/metadata/reads/0'],items,'tower','null_argmax')
cand,_=tp.load(['work/ret/metadata/reads/1'],items,'tower','candidates_argmax')
sc=lambda r:scorers.accuracy(r['output'],items[r['id']])['task_accuracy']
def info(r):
 st=[tp.status(c) for c in scorers.records(r['output'])]
 return dict(capped=r['output'].get('finish') in ('max_calls','max_new_tokens'),notseen='not seen' in st,unserved='unserved' in st,returned='returned' in st)
D=[k for k in cand if items[k]['question_type']==tp.DISTANCE]
rows=[]
for k in D:
 n,c=info(null[k]),info(cand[k])
 nfail=n['capped'] or n['notseen'] or n['unserved']
 cok=not c['capped'] and not c['notseen'] and c['returned']
 rows.append(dict(id=k,room=items[k]['room_key'],null_fail=nfail,null_capped=n['capped'],null_notseen=n['notseen'],cand_ok=cok,
   metre=scorers.unit_factor(items[k]['question'])==1,own=sc(own[k]),null=sc(null[k]),cand=sc(cand[k])))
def m(sub,key):return round(100*statistics.mean(r[key] for r in sub),2) if sub else None
sets={'all':rows,'gap (null failed, cand returned)':[r for r in rows if r['null_fail'] and r['cand_ok']],
 'gap, null capped':[r for r in rows if r['null_capped'] and r['cand_ok']],
 'gap, null not seen (not capped)':[r for r in rows if r['null_notseen'] and not r['null_capped'] and r['cand_ok']],
 'null failed, cand also failed':[r for r in rows if r['null_fail'] and not r['cand_ok']],
 'null ok':[r for r in rows if not r['null_fail']],
 'gap metre questions':[r for r in rows if r['null_fail'] and r['cand_ok'] and r['metre']]}
out={name:dict(n=len(s),mra_own=m(s,'own'),mra_null=m(s,'null'),mra_cand=m(s,'cand'),cand_minus_null=(round(m(s,'cand')-m(s,'null'),2) if s else None)) for name,s in sets.items()}
Path('work/scores/GAP.json').write_text(json.dumps(dict(summary=out,rows=rows),indent=1)+'\n')
for k,v in out.items():print(k,v)
