"""Verify the exact trial edits and regression-only source changes against fix3."""
from pathlib import Path
import sys,tarfile,difflib,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
preserved=read_json(ROOT/'work/fix4_archive_inputs.json')['input_sha256']
for path,h in preserved.items():assert sha(path)==h,path
expected={'code/evaluate_v2.py','code/process_guard.py','scripts/gpu_environment.sh','code/test_kit.py'}
for name in expected:
    p=ROOT/'work/fix4_expected'/name
    sha(p)
    assert (ROOT/name).read_bytes()==p.read_bytes(),name
changed=[];diff=[];checked=0
with tarfile.open(ROOT/'out/sb_ktfix3.tar') as tar:
    names=set()
    for member in tar:
        if not member.isfile() or not member.name.startswith(('code/','scripts/','configs/','inputs/')):continue
        name=member.name;names.add(name);checked+=1
        old=tar.extractfile(member).read();p=ROOT/name;new=p.read_bytes();sha(p)
        if old!=new:
            changed.append(name)
            diff.extend(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='sb_ktfix3/'+name,tofile='sb_ktfix4/'+name))
    assert set(changed)==expected|{'code/test_fix3.py'},changed
    additions=[]
    for folder in ('code','scripts','configs','inputs'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and str(p.relative_to(ROOT)) not in names:
                additions.append(str(p.relative_to(ROOT)))
# The reviewed archive intentionally excludes non-delivery scripts; compare its scope.
assert not [n for n in additions if not n.startswith('scripts/')],additions
(ROOT/'out/FIX4_SOURCE.diff').write_text(''.join(diff))
sha(ROOT/'out/FIX4_SOURCE.diff');sha(ROOT/'work/ktchk2_probes/fixtry.patch')
write_json(ROOT/'out/FIX4_DIFF.json',dict(status='PASS',command='bash scripts/cpu.sh work/diff_fix4.py',checked_members=checked,changed=sorted(changed),trial_patch_exact=True,reviewed_archives_unchanged=True,code_sha256=digest(code_pins())))
print(json.dumps(dict(status='PASS',checked_members=checked,changed=sorted(changed),code_sha256=digest(code_pins()))))
