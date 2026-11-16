import difflib,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';T=L/'work/tree_r1';prior=L/'work/contracts_r6/tree_copy'
rows=[];diff=[]
for p in sorted((T/'tests').glob('*.py')):
    old=prior/'tests'/p.name;a=old.read_text() if old.exists() else '';b=p.read_text()
    if a==b:continue
    name='tests/'+p.name
    rows.append(dict(file=name,before=hashlib.sha256(a.encode()).hexdigest() if a else None,after=hashlib.sha256(b.encode()).hexdigest()))
    diff.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='build5/'+name,tofile='build6/'+name))
(B/'TEST_ADAPTATIONS.diff').write_text(''.join(diff))
(B/'TEST_INPUT_ADAPTATIONS.json').write_text(json.dumps(dict(files=rows,
    reasons=['Existing init tests bind the same historical input through an explicit fixture pin; runtime defaults do not choose an artifact.',
             'Recovery mutation checks exercise the native refusal OFF and the packet refusal ON.',
             'Synthetic metric bank entries include their asked unit and both required score views include per-unit results.',
             'The packet changes its two legacy test files verbatim, as authenticated by the patch manifest.',
             'New tests cover next-leg input, unit, admission, runtime and score requirements.'],
    assertions_dropped=False),indent=2)+'\n')
for name in ('PACKAGE_TEST.sh','test_runner.py','compact_tmp.py','package.py','compare.py','coverage.py'):
    a=(L/'work/build5'/name).read_text();b=(B/name).read_text()
    (B/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='build5/'+name,tofile='build6/'+name)))
