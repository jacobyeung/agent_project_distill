"""Current compiled-source observations plus byte-identical build-12 functions."""
from pathlib import Path
from collections import Counter
import ast,difflib,hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1'
sources=[]
for root in (B/'proofs',L/'work/build12/proofs'):
    for p in root.rglob('source_hashes.json'):
        if set(p.parts)&{'frozen','mutations','prior_frozen','prior_kits'}:continue
        if (p.parent/'hits.json').exists() and (p.parent/'results.json').exists():sources.append(p.parent)
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/n1fix2/coverage.py'),*map(str,sources)],check=True)
value=json.loads((L/'work/n1fix2/CHANGED_COVERAGE.json').read_text())
prior=json.loads((L/'work/build12/CHANGED_COVERAGE.json').read_text())
lookup={(r['file'],r['line']):r for r in value['statements']};maps={}
for old in prior['statements']:
    name=old['file'];p=T/name;q=B/'prior12'/name
    if not p.exists() or not q.exists():continue
    if name not in maps:
        a=q.read_bytes();b=p.read_bytes();assert hashlib.sha256(a).hexdigest()==old['sha256']
        al=a.decode().splitlines();bl=b.decode().splitlines();lines={};funcs={}
        for tag,i,j,k,m in difflib.SequenceMatcher(None,al,bl,autojunk=False).get_opcodes():
            if tag=='equal':lines.update({n+1:k+n-i+1 for n in range(i,j)})
        aa=[x for x in ast.walk(ast.parse(a)) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
        bb=[x for x in ast.walk(ast.parse(b)) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
        for fn in aa:
            body='\n'.join(al[fn.lineno-1:fn.end_lineno])
            matches=[x for x in bb if x.name==fn.name and '\n'.join(bl[x.lineno-1:x.end_lineno])==body]
            if len(matches)==1:
                for n in range(fn.lineno,fn.end_lineno+1):
                    funcs[n]=(matches[0].lineno+n-fn.lineno,hashlib.sha256(body.encode()).hexdigest(),fn.name)
        maps[name]=(lines,funcs,hashlib.sha256(b).hexdigest())
    lines,funcs,current=maps[name];line=lines.get(old['line']);row=lookup.get((name,line))
    if not row or row['executed']:continue
    if old['executed'] and (old['sha256']==current or old['line'] in funcs):
        evidence=dict(source='work/build12/CHANGED_COVERAGE.json',prior_sha256=old['sha256'],
                      current_sha256=current,prior_line=old['line'],current_line=line)
        if current!=old['sha256']:
            dest,h,fn=funcs[old['line']]
            if dest!=line:continue
            evidence.update(function=fn,function_source_sha256=h)
        row.update(executed=True,classification='observed',inherited_observation=evidence)
    elif old['classification'] in ('frame-host','GPU','model-loader','unreachable-after-sealed-refusal'):
        row.update(classification=old['classification'],reason=old.get('reason'),classification_source='work/build12/CHANGED_COVERAGE.json')
for r in value['statements']:
    if r['executed']:continue
    if r['text'].strip().startswith(('nonlocal ', 'global ')):
        node=next(n for n in ast.walk(ast.parse((T/r['file']).read_text()))
                  if isinstance(n,(ast.Nonlocal,ast.Global)) and n.lineno==r['line'])
        r.update(classification='compile-time declaration',reason='Scope declaration has no executable statement or runtime line event.')
    if r['file']=='launch_r1/entry.py' and r['function']=='frame_host':
        r.update(classification='frame-host',reason='Real authenticated staging closure, native catalogs, full frame inventory and host admission are unavailable on Trinity; the production audit remains refused here.')
    if r['file']=='student_pilot/s1_admission.py' and r['function']=='prepare_phase':
        r.update(classification='frame-host',reason='Native full-stream preparation requires the frame-host stores; compose_native and its native builders/readers execute separately on bounded CPU fixtures.')
value['classes']=dict(Counter(r['classification'] for r in value['statements']))
value['executed']=sum(r['executed'] for r in value['statements'])
value['method']+=' Prior observations transfer only for exact file bytes or a byte-identical complete function, with both file hashes and function hash recorded.'
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(value,indent=2))
gaps=[r for r in value['statements'] if r['classification']=='CPU-reachable unresolved']
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2))
print(json.dumps(dict(classes=value['classes'],gaps=[(r['file'],r['line'],r['text']) for r in gaps])))
