"""Exercise pinned dependency extraction and aggregate import failures with tiny local tars."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'tools'))
import selection_runtime as runtime
out = Path(tempfile.mkdtemp(prefix='runtime_', dir=H / 'evidence/fix7_selection'))

def archive(label, additions=(), tokenizers=None):
    path = out / (label + '.tar')
    base = runtime.SITE
    entries = [
        (base + 'tokenizers/__init__.py', tokenizers or b'__version__="0.22.2"\n', tarfile.REGTYPE),
        (base + 'tokenizers-0.22.2.dist-info/METADATA', b'Name: tokenizers\nVersion: 0.22.2\n', tarfile.REGTYPE),
        (base + 'tokenizers-0.22.2.dist-info/WHEEL', b'Tag: cp39-abi3-manylinux_2_17_x86_64\n', tarfile.REGTYPE),
        (base + 'torch-2.11.0.dist-info/METADATA', b'Name: torch\nVersion: 2.11.0\n', tarfile.REGTYPE),
        (base + 'numpy-2.4.0.dist-info/METADATA', b'Name: numpy\nVersion: 2.4.0\n', tarfile.REGTYPE),
        (base + 'unused/__init__.py', b'raise RuntimeError("must not import")\n', tarfile.REGTYPE),
        (runtime.ROOT + '/bin/python3', b'', tarfile.SYMTYPE),
    ] + list(additions)
    with tarfile.open(path, 'w') as tf:
        for name, data, kind in entries:
            member = tarfile.TarInfo(name); member.size = len(data); member.type = kind
            if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE): member.linkname = '/outside'
            tf.addfile(member, io.BytesIO(data))
    data = path.read_bytes()
    return dict(file=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

pin = archive('good')
a = runtime.Archive(pin)
dest = out / 'd'; dest.mkdir(mode=0o700)
assert a.extract('tokenizers', dest)['version'] == '0.22.2'; a.close()
assert dest.stat().st_mode & 0o777 == 0o700
assert sorted(p.name for p in dest.iterdir()) == ['tokenizers', 'tokenizers-0.22.2.dist-info']
r = subprocess.run([sys.executable, '-I', '-B', '-c',
    'import sys;sys.path.insert(0,sys.argv[1]);import tokenizers;print(tokenizers.__version__)', str(dest)],
    text=True, capture_output=True, check=True)
assert r.stdout.strip() == '0.22.2'
refusals = []
for label, additions in [
    ('symlink', [(runtime.SITE + 'tokenizers/link', b'', tarfile.SYMTYPE)]),
    ('hardlink', [(runtime.SITE + 'tokenizers/link', b'', tarfile.LNKTYPE)]),
    ('extra_path', [('extra/__init__.py', b'', tarfile.REGTYPE)]),
    ('traversal', [(runtime.SITE + 'tokenizers/../escape', b'', tarfile.REGTYPE)]),
    ('absolute', [('/escape', b'', tarfile.REGTYPE)]),
    ('non_abi3', [(runtime.SITE + 'tokenizers/core.cpython-312.so', b'\x7fELF', tarfile.REGTYPE)]),
    ('disguised_native', [(runtime.SITE + 'tokenizers/data', b'\x7fELF', tarfile.REGTYPE)]),
]:
    candidate = archive(label, additions)
    target = out / (label + '_d'); target.mkdir(mode=0o700)
    a = None
    try:
        a = runtime.Archive(candidate); a.extract('tokenizers', target)
    except ValueError: refusals.append(label)
    else: raise AssertionError('Accepted ' + label)
    finally:
        if a: a.close()
    assert not list(target.iterdir())
for field, value in [('sha256', '0' * 64), ('bytes', pin['bytes'] + 1)]:
    try: runtime.Archive(dict(pin, **{field: value}))
    except ValueError: refusals.append('wrong_' + field)
    else: raise AssertionError(field)

# Run the exact isolated bootstrap/selection_check entrypoint against authenticated
# code/records. Failed imports must produce q.json before native output is created.
script = r'''
import builtins,json,runpy,sys
from pathlib import Path
h,out,pin,mode=Path(sys.argv[1]),Path(sys.argv[2]),json.loads(sys.argv[3]),sys.argv[4]
sys.path.insert(0,str(h/'tools'))
import selection_runtime as rt
records=out/'records';records.mkdir()
for name,source in [('a.json','evidence/derivation/d0/k/pool_selection.json'),
                    ('b.json','payload/d_f232d4160d75b582.json'),('c.json','payload/7.json'),
                    ('f.json','build/fx_r7/'+json.loads((h/'build/fx_r7/k/launch.json').read_text())['config']['file'])]:
 (records/name).write_bytes((h/source).read_bytes())
(records/'e.json').write_text(json.dumps(dict(venv=pin,imports=rt.closure(h/'build/tree'))))
original=builtins.__import__
if mode=='missing':
 def missing(name,*args,**kwargs):
  if name.split('.')[0] in ('scipy','torch','numpy'):
   raise ModuleNotFoundError('fixture missing '+name,name=name)
  return original(name,*args,**kwargs)
 builtins.__import__=missing
 # importlib.import_module bypasses __import__ for the requested root.
 class Missing:
  def find_spec(self,name,path=None,target=None):
   if name.split('.')[0] in ('scipy','torch','numpy'):
    raise ModuleNotFoundError('fixture missing '+name,name=name)
 sys.meta_path.insert(0,Missing())
output=out/'o'
if mode=='missing':
 sys.argv=['selection_check','--kit',str(out/'absent'),'--tree',str(h/'build/tree'),
 '--records',str(records),'--out',str(output),'--runtime',str(h/'tools/selection_runtime.py')]
 try:runpy.run_path(str(h/'tools/selection_check.py'),run_name='__main__')
 except SystemExit as exc:assert exc.code==2
 q=json.loads((output/'q.json').read_text());assert q['status']=='BLOCKED' and not q['regenerated']
 assert not (output/'native').exists()
 assert {'numpy','torch','scipy'} <= set(q['runtime']['missing_modules']),q
 assert q['runtime']['imported_versions']['tokenizers']=='0.22.2'
else:
 sys.path.insert(0,str(h/'build/tree'));report={}
 rt.prepare(h/'build/tree',records/'d',json.loads((records/'e.json').read_text()),report)
 assert not report['missing_modules'] and not report['import_errors'],report
 assert report['imported_versions']['tokenizers']=='0.22.2'
 assert {'torch','numpy','tokenizers'} <= report['imported_versions'].keys()
 (out/'report.json').write_text(json.dumps(report,indent=2))
'''
for mode in ('pass', 'missing'):
    case = out / mode; case.mkdir(mode=0o700)
    r = subprocess.run([sys.executable, '-I', '-B', '-', str(H), str(case), json.dumps(pin), mode],
                       input=script, text=True, capture_output=True)
    (case / 'log').write_text(r.stdout + r.stderr)
    assert r.returncode == 0, r.stderr

# A missing pure-Python dependency, including a transitive dependency, is recovered
# in this same process from the pinned archive; unrelated packages remain absent.
def package(name, body):
    return [(runtime.SITE + name + '/__init__.py', body, tarfile.REGTYPE),
            (runtime.SITE + name + '-1.dist-info/METADATA', ('Name: '+name+'\nVersion: 1\n').encode(), tarfile.REGTYPE),
            (runtime.SITE + name + '-1.dist-info/WHEEL', b'Tag: py3-none-any\n', tarfile.REGTYPE)]
recovery = archive('recovery', package('fixture_dep_a', b'import fixture_dep_b\n') +
                   package('fixture_dep_b', b'value=1\n'), tokenizers=b'import fixture_dep_a\n__version__="0.22.2"\n')
case = out / 'recovery'; case.mkdir(mode=0o700)
r = subprocess.run([sys.executable, '-I', '-B', '-', str(H), str(case), json.dumps(recovery), 'pass'],
                   input=script, text=True, capture_output=True)
(case / 'log').write_text(r.stdout + r.stderr)
assert r.returncode == 0, r.stderr
report = json.loads((case/'report.json').read_text())
assert {r['module'] for r in report['recovered']} == {'tokenizers','fixture_dep_a','fixture_dep_b'}
result = dict(status='PASS', path=str(out), refusals=refusals, isolated_fake_tokenizers=True,
              all_missing_in_q_json=True, pure_python_transitive_recovery=True)
(H/'evidence/fix7_selection/runtime_tests.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
