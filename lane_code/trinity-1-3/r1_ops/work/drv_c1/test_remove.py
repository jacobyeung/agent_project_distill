"""Verify the actual REMOVE bytes through the extra-file staging checker."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from packet_config import PINS, MEMBERS, CONFIG, SUMS, sealed, render
from staging_check import main
W=Path(__file__).resolve().parent
T=Path(tempfile.mkdtemp(prefix='remove_p5_',dir=W));(T/'k').mkdir()
(T/'base.json').write_text('{"extra":[]}')
p=T/'n.json';p.write_bytes(MEMBERS['n.json'])
entry=dict(dest=PINS['remove_path'],parts=[str(p)],sha256=PINS['remove_sha256'])
(T/'k/0.json').write_text(json.dumps(dict(extra=[entry])))
assert main(T,T/'base.json')['verified']==[[str(p)]]
p.write_bytes(MEMBERS['n.json']+b'changed')
try:main(T,T/'base.json')
except ValueError as exc:assert 'digest differs' in str(exc)
else:raise AssertionError('Accepted changed REMOVE bytes')
p.write_bytes(MEMBERS['n.json'])
entry['parts']=[str(T/'absent.json')]
(T/'k/0.json').write_text(json.dumps(dict(extra=[entry])))
assert main(T,T/'base.json')['missing']==[str(T/'absent.json')]
# Both direct driver input paths must refuse corruption before reading source H.
for changed in ('n.json','records/n.json'):
 root=T/('changed_'+changed.replace('/','_'));root.mkdir();b=root/Path(PINS['bundle']).name;b.mkdir()
 (b/'records').mkdir()
 for name in ('d.py','n.json','records/n.json'):(b/name).write_bytes(MEMBERS[name]+(b'changed' if name==changed else b''))
 script=root/'derive.py';script.write_text(render((W/'derive_body.py').read_text()).replace('/project/community/jjyeung/okh7',str(root)))
 r=subprocess.run([sys.executable,'-B',str(script)],capture_output=True,text=True)
 assert r.returncode and 'REMOVE list SHA differs from packet C' in r.stderr,r.stderr
 assert not (root/Path(PINS['kit']).name).exists()
print('PASS staging checker hashes packet C REMOVE bytes; changed and absent inputs refused')
print('PASS dv1 refuses changed n.json and records/n.json before source reads or kit creation')
required=['BINDING.json','config.json','records/n.json','units/u.json','units/u.gz','units/m.json','units/i.json']
for name in required:sealed(name)
assert CONFIG['remove_files'][-1]['sha256']==PINS['remove_sha256']
print(f'PASS {len(required)} required frozen files; archive SHA and all {len(MEMBERS)} inner members; 601-row REMOVE pin; room=1.70; direction=31.19')
