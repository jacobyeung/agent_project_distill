"""Exercise the exact proof-only patch in small local bundle fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

H=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='patch8b_',dir=H/'evidence/fix8_admission'))
script=(H/'build/c_patch_8b.sh').read_text()
old=H/'evidence/fix8b_before/payload'
name='a_8c74b291.sh'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((H/'evidence/fix8b_patch_manifest.json').read_text())
assert sha(H/'build/c_patch_8b.sh')==manifest['patch_sha256']
subprocess.run(['/bin/bash','-n',str(H/'build/c_patch_8b.sh')],check=True)
cases=[]
for case in ('pass','old_proof','old_sums','linked_proof','linked_sums','hardlink',
             'public_bundle','backup_exists','backup_link','embedded_corrupt'):
    root=out/case;root.mkdir(mode=0o700)
    bundle=root/'bundle';bundle.mkdir(mode=0o700)
    for n in (name,'sums.txt'):
        (bundle/n).write_bytes((old/n).read_bytes());(bundle/n).chmod(0o600)
    # These mutable operator records must survive verbatim, with no retirement.
    for n in ('go.json','compare.json','review.json','s.sh','jb.sh','ids.json'):
        (bundle/n).write_text('TEST_ONLY sentinel '+n+'\n')
    kh=root/'kh';kh.mkdir(mode=0o700)
    (kh/'SHA256SUMS.txt').write_text('TEST_ONLY KH sentinel\n')
    local=script.replace("B=Path('/project/community/jjyeung/okh7/i_1be16f28')",'B=Path('+repr(str(bundle))+')')
    assert local!=script
    if case in ('old_proof','old_sums'):
        (bundle/(name if case=='old_proof' else 'sums.txt')).write_text('tampered\n')
    if case in ('linked_proof','linked_sums'):
        n=name if case=='linked_proof' else 'sums.txt'
        (bundle/n).rename(root/'target');(bundle/n).symlink_to(root/'target')
    if case=='hardlink':os.link(bundle/name,root/'hardlink')
    if case=='public_bundle':bundle.chmod(0o755)
    if case=='backup_exists':(bundle/'v_8b').mkdir()
    if case=='backup_link':(bundle/'v_8b').symlink_to(root/'absent')
    if case=='embedded_corrupt':
        start=local.index("blob='")+len("blob='")
        local=local[:start]+('A' if local[start]!='A' else 'B')+local[start+1:]
    def state():
        return {p.name:('link',os.readlink(p)) if p.is_symlink() else
                ('dir',p.stat().st_mode) if p.is_dir() else ('file',sha(p),p.stat().st_mode)
                for p in bundle.iterdir()}
    before=state();kh_before=sha(kh/'SHA256SUMS.txt')
    result=subprocess.run(['/bin/bash','-s'],input=local,text=True,capture_output=True)
    (root/'result.log').write_text(result.stdout+result.stderr)
    assert (result.returncode==0)==(case=='pass'),(case,result.stderr)
    if case=='pass':
        assert set(state())==set(before)|{'v_8b'}
        for n in (name,'sums.txt'):
            assert sha(bundle/n)==manifest['new'][n]
            assert sha(bundle/'v_8b'/n)==manifest['old'][n]
            assert (bundle/n).stat().st_mode==before[n][2]
        assert (bundle/'sums.txt').read_bytes()==(H/'payload/sums.txt').read_bytes()
        for n in set(before)-{name,'sums.txt'}:assert state()[n]==before[n]
        installed=state()
        repeat=subprocess.run(['/bin/bash','-s'],input=local,text=True,capture_output=True)
        assert repeat.returncode!=0 and state()==installed
    else:assert state()==before,case
    assert sha(kh/'SHA256SUMS.txt')==kh_before
    cases.append(case)
bindings=json.loads((H/'evidence/fix8b_before/bindings.json').read_text())
for n,h in bindings.items():assert sha(H/n)==h,n
before={n:sha(H/n) for n in ('build/c_patch_8b.sh','evidence/fix8b_patch_manifest.json')}
subprocess.run([sys.executable,'-B',str(H/'tools/build_proof_patch.py')],check=True)
assert before=={n:sha(H/n) for n in before}
report=dict(status='PASS',cases=cases,repeat_refuses=True,deterministic=True,
            path=str(out),unchanged_bindings=bindings,scope='Local fixtures only; no Orchard changes')
(H/'evidence/fix8_admission/patch8b_tests.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',len(cases),'proof-only patch cases; repeat refusal; unchanged bindings; deterministic rebuild')
