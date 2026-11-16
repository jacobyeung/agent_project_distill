import json,re,ast,sys
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/native_r2')
LOG='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
full=json.load(open(L/'builds/01_c8/out/coverage/full/coverage.json'))['files']
pil8=json.load(open(L/'builds/01_c8/out/coverage/pilot/coverage.json'))['files']
pilr=json.load(open(L/'builds/02_c8r/out/coverage/pilot/coverage.json'))['files']
testsr={}
for p in (L/'builds/02_c8r/out/coverage/tests').rglob('coverage.json'):
    for f,v in json.load(open(p))['files'].items(): testsr.setdefault(f,set()).update(v['executed_lines'])
def key(files,rel):
    for f in files:
        if f.endswith('/milestone/'+rel) or f.endswith(rel) and 'milestone' in f: return f
out=[]
# 1. full-mode unexecuted lines per milestone file (C8 run)
rows=[]
for f,v in sorted(full.items()):
    if '/milestone/' not in f: continue
    rel=f.split('/milestone/')[1]
    rows.append((rel,v['summary']['covered_lines'],v['summary']['missing_lines'],v['missing_lines']))
with open(L/'out/c8_ready/FULL_MODE_UNEXECUTED_C8.md','w') as o:
    o.write('# C8 full-mode rehearsal (builds/01_c8/work/rh_full_01): unexecuted lines per file\nSource: builds/01_c8/out/coverage/full/coverage.json (coverage 7.10.7, branch). "also in pilot" = executed by the C8 pilot rehearsal.\n\n| file | executed | unexecuted | unexecuted lines (also executed in C8 pilot marked *) |\n|---|---:|---:|---|\n')
    for rel,c,m,miss in rows:
        pk=key(pil8,rel); pe=set(pil8[pk]['executed_lines']) if pk else set()
        o.write(f'| {rel} | {c} | {m} | '+', '.join(str(x)+('*' if x in pe else '') for x in miss)+' |\n')
# 2. functions that must be fully executed in full mode
src=(L/'builds/01_c8/out/c8/sources/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py').read_text()
fn=[n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='full'][0]
wk=key(full,'orchard_native/native_worker.py'); ex=set(full[wk]['executed_lines'])
stmts=sorted({n.lineno for n in ast.walk(fn) if isinstance(n,ast.stmt)})
miss_full=[x for x in stmts if x not in ex]
print('native_worker.full statements',len(stmts),'unexecuted',miss_full)
# 3. C8r-vs-C8 added lines and their execution in C8r pilot rehearsal / C8r tests / C8 full
patch=(L/'builds/02_c8r/out/C8R_DIFF_vs_C8.patch').read_text().splitlines()
added={};cur=None;n=0
for line in patch:
    if line.startswith('+++ '):cur=line[4:].split('\t')[0];cur=cur.split('/milestone/')[-1] if '/milestone/' in cur else cur;continue
    m=re.match(r'@@ -\d+(?:,\d+)? \+(\d+)',line)
    if m:n=int(m.group(1));continue
    if cur is None or line.startswith('---'):continue
    if line.startswith('+'):added.setdefault(cur,[]).append((n,line[1:]));n+=1
    elif line.startswith('-'):pass
    else:n+=1
with open(L/'out/c8_ready/C8R_LINES_VS_C8_COVERAGE.md','w') as o:
    o.write('# C8r lines added vs C8, and where each is executed\nColumns: P = C8r whole-worker pilot rehearsal (builds/02_c8r/work/rh_pilot_op2, out/coverage/pilot), T = C8r unit tests (out/coverage/tests), F = C8 full rehearsal (same line number only if file unchanged). Non-code lines (blank, comment, docstring, JSON) are listed as "-".\n\n')
    tot=dict(code=0,P=0,T=0,none=0)
    for rel,lines in sorted(added.items()):
        if not rel.endswith('.py'):
            o.write(f'## {rel}: {len(lines)} added lines (data, not code)\n\n');continue
        pk=key(pilr,rel);tk=key(testsr,rel)
        pe=set(pilr[pk]['executed_lines']) if pk else set(); te=set(testsr.get(tk,[])) if tk else set()
        allst=set(pilr[pk]['executed_lines'])|set(pilr[pk]['missing_lines']) if pk else set()
        o.write(f'## {rel}\n\n| line | P | T | text |\n|---:|---|---|---|\n')
        for no,text in lines:
            if allst and no not in allst: o.write(f'| {no} | - | - | `{text.strip()[:90]}` |\n');continue
            tot['code']+=1;p=no in pe;t=no in te;tot['P']+=p;tot['T']+=t;tot['none']+=(not p and not t)
            o.write(f'| {no} | {"x" if p else ""} | {"x" if t else ""} | `{text.strip()[:90]}` |\n')
        o.write('\n')
    o.write(f'\nTotals over statement lines: {tot}\n')
print('C8r added statement lines',tot)
