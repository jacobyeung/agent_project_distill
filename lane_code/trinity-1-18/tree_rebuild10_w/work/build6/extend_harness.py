"""Keep build-5 harness logic; isolate current proof and package destinations."""
from pathlib import Path
import difflib
L=Path(__file__).resolve().parents[2];B=L/'work/build6';old=L/'work/build5'
for name in ('PACKAGE_TEST.sh','test_runner.py','compact_tmp.py','package.py','compare.py','coverage.py','seal.py','run_delivery.py'):
    source=(old/name).read_text();s=source.replace('work/build5','work/build6').replace('BUILD5_ROOT','BUILD6_ROOT').replace('build5-tree-seal','build6-tree-seal')
    if name=='package.py':
        s=s.replace("('work/tree_r1','work/base/tree_b01ce449','fixtures','work/build6/kits')", "('work/tree_r1','work/base/tree_b01ce449','fixtures','work/build6/kits','work/contracts_r6/tests_r6')")
        s=s.replace("root=L/'work/tmp/package'", "root=L/'work/tmp/package6'")
    (B/name).write_text(s)
    (B/(name+'.diff')).write_text(''.join(difflib.unified_diff(source.splitlines(True),s.splitlines(True),fromfile='build5/'+name,tofile='build6/'+name)))
print('Build-5 harness extended into build6; original retained.')
