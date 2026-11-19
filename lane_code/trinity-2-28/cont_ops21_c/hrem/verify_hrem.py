"""Compile the Orchard kit under Python 3.6 and verify streamed assets and shell syntax."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import py_compile
import subprocess
import sys
HERE=Path(__file__).resolve().parent
assert sys.version_info[:2]==(3,6)
compiled=[]
for p in sorted(HERE.glob('*.py')):
    py_compile.compile(str(p),doraise=True);compiled.append(p.name)
scripts=[]
for p in sorted(HERE.glob('*.sh')):
    subprocess.run(['bash','-n',str(p)],check=True);scripts.append(p.name)
source=(HERE/'o_build_hrem.sh').read_text();body=source.split("<<'PYASSETS'\n",1)[1].split('\nPYASSETS',1)[0]
compile(body,'embedded_assets','exec')
assignment=next(n for n in ast.parse(body).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='assets' for t in n.targets))
assets=ast.literal_eval(assignment.value)
for name,pin in assets.items():
    raw=gzip.decompress(base64.b64decode(pin['data']))
    assert hashlib.sha256(raw).hexdigest()==pin['sha256']
    assert raw==(HERE/name).read_bytes(),name
    if name.endswith('.py'):compile(raw,name,'exec')
sub=(HERE/'sub_guard_hrem.sh').read_text()
assert 'squeue -u jjyeung -p general -h' in sub and 'test ! -s "$P/a/9.txt"' in sub
assert (HERE/'cpu_guard_hrem.sh').read_bytes()==(HERE/'in/hcam/o_cpu_H.sh').read_bytes()
original=(HERE/'in/hcam/o_sub_H.sh').read_text()
expected=original.replace("assert op['COUNTS']==(300,300,300,0,0) and op['SCHEDULE']==((0,0),(0,1),(0,2))", "with tarfile.open(str(p/'0.tgz')) as archive:\n    plan=json.load(archive.extractfile('9.json'))\nassert op['COUNTS']==tuple(plan['remainder']['counts'])\nassert op['SCHEDULE']==tuple(tuple(x) for x in plan['remainder']['schedule'])")
assert sub==expected
result=dict(passed=True,python=sys.version.split()[0],compiled=compiled,bash_syntax=scripts,embedded_assets=len(assets),all_submission_guards_preserved=True)
(HERE/'SYNTAX_TEST_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
