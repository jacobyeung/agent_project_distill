"""Independent ON-vs-base text diff over the builder's r5 row families (read-only)."""
import json,re,sys,difflib
from pathlib import Path
from collections import Counter
W=Path('/scratch/jjyeung/orch_n30/contracts_rebuild/work/row_families_r5')
def load(arm):
    rs=json.loads((W/f'{arm}.json').read_text())['results']
    for extra in (W/f'supplement_{arm}.json',W/f'keypoints_{arm}.json'):
        if extra.exists(): rs+=json.loads(extra.read_text())['results']
    return {(r['family'],r['variant']):r for r in rs}
b,o,n=load('base'),load('off'),load('on')
print('samples',len(b),len(o),len(n),'rendered',*(sum(r['status']=='rendered' for r in x.values()) for x in (b,o,n)))
enc=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'))
offbad=[k for k in b if (b[k]['status'],enc(b[k].get('row')))!=(o[k]['status'],enc(o[k].get('row')))]
print('OFF!=base:',len(offbad),offbad[:5])
cnt=Counter(); errs=[]; out=open(sys.argv[1],'w')
for k in sorted(b):
    if b[k]['status']!='rendered' or n[k]['status']!='rendered':
        if b[k]['status']!=n[k]['status']: cnt['status_change']+=1; out.write(f'STATUS {k} {b[k]["status"]}->{n[k]["status"]} {n[k].get("error")}\n')
        continue
    t0=b[k]['row'].get('target') or b[k]['row'].get('suffix') or ''
    t1=n[k]['row'].get('target') or n[k]['row'].get('suffix') or ''
    if t0==t1: cnt['same']+=1; continue
    cnt['diff']+=1
    for d in difflib.ndiff(t0.splitlines(),t1.splitlines()):
        if d[:1] in '+-':
            out.write(f'{k} {d}\n')
            if d.startswith('+') and 'error:' in d: errs.append((k,d))
print(dict(cnt)); print('ON lines containing error:',len(errs)); [print(' ',e) for e in errs[:10]]
