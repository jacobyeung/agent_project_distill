"""Bind line observations and unchanged-function evidence to current source bytes."""
from pathlib import Path
from collections import Counter
import ast,difflib,hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1'
sources=[p.parent for p in (B/'proofs').rglob('source_hashes.json')
    if 'frozen' not in p.parts and (p.parent/'hits.json').exists() and (p.parent/'results.json').exists()]
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/n1fix2/coverage.py'),*map(str,sources)],check=True)
value=json.loads((L/'work/n1fix2/CHANGED_COVERAGE.json').read_text())
priors=[(B/'inherited11/CHANGED_COVERAGE.json',L.parent/'wm/work/tree_r1'),
        (B/'inherited3/CHANGED_COVERAGE.json',L.parent/'wn3/work/tree_r1')]
byline={(r['file'],r['line']):r for r in value['statements']}
bindings=[]
for receipt,root in priors:
    old=json.loads(receipt.read_text());maps={}
    for prior in old['statements']:
        name=prior['file'];p=T/name
        if not p.exists():continue
        if name not in maps:
            a=(root/name).read_bytes();b=p.read_bytes()
            assert hashlib.sha256(a).hexdigest()==prior['sha256']
            al=a.decode().splitlines();bl=b.decode().splitlines();line_map={};function_map={}
            for tag,i,j,k,m in difflib.SequenceMatcher(None,al,bl,autojunk=False).get_opcodes():
                if tag=='equal':line_map.update({n+1:k+n-i+1 for n in range(i,j)})
            old_funcs=[n for n in ast.walk(ast.parse(a)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            new_funcs=[n for n in ast.walk(ast.parse(b)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            for fn in old_funcs:
                body='\n'.join(al[fn.lineno-1:fn.end_lineno])
                candidates=[n for n in new_funcs if n.name==fn.name and '\n'.join(bl[n.lineno-1:n.end_lineno])==body]
                if len(candidates)==1:
                    dest=candidates[0]
                    for n in range(fn.lineno,fn.end_lineno+1):
                        function_map[n]=(dest.lineno+n-fn.lineno,hashlib.sha256(body.encode()).hexdigest(),fn.name)
            maps[name]=(line_map,function_map,hashlib.sha256(b).hexdigest())
        lines,funcs,current=maps[name]
        line=lines.get(prior['line']);row=byline.get((name,line))
        if not row or row['executed']:continue
        if prior['executed'] and (prior['sha256']==current or prior['line'] in funcs):
            evidence=dict(source=str(receipt.relative_to(L)),prior_sha256=prior['sha256'],current_sha256=current,
                          prior_line=prior['line'],current_line=line)
            if prior['sha256']!=current:
                dest,sha,fn=funcs[prior['line']]
                if dest!=line:continue
                evidence.update(function=fn,function_source_sha256=sha)
            row.update(executed=True,classification='observed',inherited_observation=evidence)
            bindings.append(evidence)
        elif prior['classification'] in ('frame-host','GPU','model-loader'):
            row.update(classification=prior['classification'],reason=prior.get('reason'),classification_source=str(receipt.relative_to(L)))
# These adapter bodies follow an unconditional sealed refusal. Exercise that
# refusal, rather than bypassing it merely to claim an otherwise dead assignment.
guard_source=T/'student_pilot/r2_policy.py'
guard=next(n for n in ast.parse(guard_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='unsupported_entry')
assert isinstance(guard.body[-1],ast.Raise) and len(guard.body)==2
edge=B/'proofs/loader_edges'
edge_result=json.loads((edge/'results.json').read_text())
assert edge_result['complete'] and not edge_result['errors'] and not edge_result['failures']
edge_hashes=json.loads((edge/'source_hashes.json').read_text());edge_hits=json.loads((edge/'hits.json').read_text())
for row in value['statements']:
    if row['classification']!='CPU-reachable unresolved' or row['text'] not in (
            'model.readout_evaluation_config = cfg','model.readout_evaluation_config = native_cfg'):continue
    path=T/row['file'];parsed=ast.parse(path.read_text())
    fn=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name==row['function'])
    body=[n for n in fn.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant))]
    if len(body)<2 or not isinstance(body[1],ast.Expr) or not isinstance(body[1].value,ast.Call):continue
    call=body[1].value
    if not isinstance(call.func,ast.Name) or call.func.id!='unsupported_entry':continue
    assert body[1].lineno in edge_hits[row['file']]
    assert edge_hashes[row['file']]==row['sha256']
    row.update(classification='unreachable-after-sealed-refusal',
        reason='The function raises through the unchanged unconditional unsupported_entry gate before this assignment. The current guard path executes in proofs/loader_edges; it is not bypassed for coverage.',
        classification_source='proofs/loader_edges/results.json')
value['classes']=dict(Counter(r['classification'] for r in value['statements']))
value['executed']=sum(r['executed'] for r in value['statements'])
value['inherited_method']='Only exact file hashes or byte-identical complete function bodies reuse prior observed lines; every reuse records both file hashes and the function hash. Current CPU proofs use compiled-source monitoring. Reused observations are coverage evidence, not fresh behavioral tests.'
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(value,indent=2)+'\n')
gaps=[r for r in value['statements'] if r['classification']=='CPU-reachable unresolved']
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(dict(classes=value['classes'],gaps=[(r['file'],r['line'],r['text']) for r in gaps])))
