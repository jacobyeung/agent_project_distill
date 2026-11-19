import difflib,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';T=L/'work/tree_r1';prior=L/'work/contracts_r6/tree_copy'
rows=[];diff=[]
for p in sorted(T.rglob('*.py')):
    if 'artifacts' in p.parts or (p.relative_to(T).parts[0]!='tests' and not p.name.startswith('test')):continue
    old=prior/p.relative_to(T);a=old.read_text() if old.exists() else '';b=p.read_text()
    if a==b:continue
    name=str(p.relative_to(T))
    rows.append(dict(file=name,before=hashlib.sha256(a.encode()).hexdigest() if a else None,after=hashlib.sha256(b.encode()).hexdigest()))
    diff.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='build5/'+name,tofile='build6/'+name))
(B/'TEST_ADAPTATIONS.diff').write_text(''.join(diff))
(B/'TEST_INPUT_ADAPTATIONS.json').write_text(json.dumps(dict(files=rows,
    reasons=['Existing init tests bind the same historical input through an explicit fixture pin; runtime defaults do not choose an artifact.',
             'The missing-vocabulary fixture supplies the required init identity and asserts the specific witness error, preserving the intended refusal branch.',
             'Recovery mutation checks exercise the native refusal OFF and the packet refusal ON.',
             'The qualified-name fixture retains its OFF refusal and tests the earlier exact-name refusal ON.',
             'The validation fixture retains its nonmutation check and authenticates the implicit heading threshold added by the accepted identity contract.',
             'The memory fixture retains the legacy configuration and FP32 output hashes, and checks ON threshold binding plus explicit OFF identity semantics.',
             'The byte-level memory fixture explicitly uses its original one-thread CPU reduction order and restores the previous setting; proofs/tensor_threads/RESULTS.json reproduces the original hashes and the eight-thread difference without changing encoder source.',
             'The launch-gate equality assertion remains; added cases require its standalone identity mirror to match the native ON/OFF and invalid-threshold rules.',
             'Synthetic metric bank entries include their asked unit; both score views use ordered unit rows that preserve order under native serialization.',
             'The packet changes its two legacy test files verbatim, as authenticated by the patch manifest.',
             'New tests cover next-leg input, unit, admission, runtime and score requirements.'],
    assertions_dropped=False),indent=2)+'\n')
for name in ('PACKAGE_TEST.sh','test_runner.py','compact_tmp.py','package.py','compare.py','coverage.py'):
    a=(L/'work/build5'/name).read_text();b=(B/name).read_text()
    (B/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='build5/'+name,tofile='build6/'+name)))
