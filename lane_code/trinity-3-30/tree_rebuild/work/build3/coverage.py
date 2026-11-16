"""Changed-statement union from hash-authenticated source snapshots; no coverage package."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';BASE=L/'work/base/tree_b01ce449';O=L/'out'
read=lambda p:json.loads(p.read_text())
history=[]
kit=L/'work/build2/kits/b0b0b0b0'
build=read(kit/'BUILD.json');cfg=read(kit/build['config']['path'])
old=read(kit/cfg['r2_build2']['source']['path'])['files']
old_sources={}
for path in T.rglob('*.py'):
    name=str(path.relative_to(T));key=hashlib.sha256(name.encode()).hexdigest()
    if key in old:
        pin=old[key];raw=(kit/pin['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Prior source snapshot differs')
        old_sources[name]=raw.decode().splitlines()
history.append((read(O/'B2_COMBINED_COVERAGE.json'),old_sources,'B2_COMBINED_COVERAGE.json'))
for snapshot in sorted((L/'work/build3/snapshots').iterdir()):
    report=O/(snapshot.name+'COVERAGE.json')
    if not report.exists():continue
    sources={}
    for name,h in read(snapshot/'0.json').items():
        raw=(snapshot/(h+'.dat')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Test source snapshot differs')
        sources[name]=raw.decode().splitlines()
    history.append((read(report),sources,report.name))
result={};missing=[];proofs={}
for path in sorted(T.rglob('*.py')):
    name=str(path.relative_to(T));source=path.read_text();base=BASE/name
    original=base.read_text() if base.exists() else ''
    if source==original:continue
    changed=set()
    current=source.splitlines()
    for tag,_,_,a,b in difflib.SequenceMatcher(a=original.splitlines(),b=current,autojunk=False).get_opcodes():
        if tag in ('insert','replace'):changed.update(range(a+1,b+1))
    statements={n.lineno for n in ast.walk(ast.parse(source)) if isinstance(n,ast.stmt)
                and not isinstance(n,(ast.Global,ast.Nonlocal))
                and not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant))
                and changed.intersection(range(n.lineno,n.end_lineno+1))}
    hits=set();evidence=[]
    for run,sources,label in history:
        if name not in sources or name not in run:continue
        mapping={a+i+1:b+i+1 for a,b,n in difflib.SequenceMatcher(a=sources[name],b=current,autojunk=False).get_matching_blocks()
                 for i in range(n)}
        preserved={mapping[line] for line in run[name]['executed_lines'] if line in mapping}&statements
        hits.update(preserved)
        evidence.append(dict(report=label,source_sha256=hashlib.sha256('\n'.join(sources[name]).encode()).hexdigest(),
                             preserved_executed_lines=sorted(preserved)))
    result[name]=dict(changed_statements=len(statements),executed=len(hits),executed_lines=sorted(hits),uncovered=sorted(statements-hits))
    proofs[name]=evidence
    for line in sorted(statements-hits):
        text=current[line-1]
        category='CPU-only';reason='No execution evidence yet'
        if name=='student_pilot/r2_materialize.py' and text.strip() in (
            "if os.environ.get('STUDENT_R2_FRAME_HOST') != '1':",
            "raise ValueError('Full materialization requires an explicit frame-host admission')",'limit = None'):
            category='frame-host';reason='Full-store branch is prohibited on Trinity'
        if name=='launch_r2/host.py' and text.strip() in (
            "raise ValueError('Missing delivered init archive and member inventory')",
            "os.environ['STUDENT_R2_FRAME_HOST'] = '0'",'try:',
            "materialize(paths['manifests'], output/'e', full=True)",
            "if str(error) != 'Full materialization requires an explicit frame-host admission':",'raise',
            "raise ValueError('Full-store admission mutation unexpectedly passed')") and line>200:
            category='frame-host';reason='Full-mode admission mutation requires the real sealed pose inputs and an off-Trinity host'
        if (name in ('launch_r2/host.py','student_pilot/carrier_c1_run.py')
                and ('CPU boundary received a GPU tensor' in text or 'Encoding-only admission requires CPU tensors' in text)):
            category='GPU';reason='Negative tensor-device branch requires a CUDA tensor; actual CUDA is forbidden in this build'
        missing.append(dict(file=name,line=line,statement=text,category=category,reason=reason))
summary=dict(schema='build3-changed-statement-coverage-v1',
    definition='Executable AST statements intersecting changed lines; docstrings and compile-time global/nonlocal declarations excluded',
    total=sum(x['changed_statements'] for x in result.values()),executed=sum(x['executed'] for x in result.values()),
    production_total=sum(x['changed_statements'] for k,x in result.items() if not k.startswith('tests/')),
    production_executed=sum(x['executed'] for k,x in result.items() if not k.startswith('tests/')),
    unexecuted_by_class={key:sum(s['category']==key for s in missing if not s['file'].startswith('tests/'))
                         for key in ('CPU-only','frame-host','model-loader','GPU')},
    statements=missing,strict_cpu_gate=not any(s['category']=='CPU-only' for s in missing if not s['file'].startswith('tests/')))
(O/'B3_COMBINED_COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n')
(O/'B3_COVERAGE_REMAP.json').write_text(json.dumps(proofs,indent=2)+'\n')
(O/'B3_COVERAGE_CLASSIFIED.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='statements'},indent=2))
for value in missing:
    if not value['file'].startswith('tests/'):
        print(value['category'],value['file'],value['line'],value['statement'].strip())
