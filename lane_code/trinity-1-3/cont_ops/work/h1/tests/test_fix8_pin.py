"""Verify copied native evidence and repeat the final derivation deterministically."""
import copy, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
import selection_check as sc
out=Path(tempfile.mkdtemp(prefix='pin_',dir=H/'evidence/fix8_admission'))
e=H/'evidence/fix7_selection/orchard_equal_6c18a2bf/o'
raw=sc.load(e/'native/receipt.json');reference=sc.load(H/'evidence/derivation/d0/k/pool_selection.json')
for name,value in raw['sources'].items():
    if 'selection' not in value:continue
    index=e/'native'/Path(value['selection']['path']).name
    assert sc.sha(index)==value['selection']['sha256']==reference['sources'][name]['selection']['sha256']
    assert len(sc.load(index))==value['retained']
    value['selection']=reference['sources'][name]['selection']
assert sc.differences(sc.content(raw),sc.content(reference))==[]
assert sc.project(raw)==sc.load(e/'r.json')
over=sc.load(H/'build/over_local.json');dk.validate_selection_equality(over)
assert sc.load(H/'payload/over.json')['selection_equality']['sha256']==sc.sha(e/'q.json')
fixture=H/'evidence/derivation/empty';production=dk.SEALED_MANIFEST
try:
    dk.SEALED_MANIFEST=dk.sha(fixture/'SHA256SUMS.txt')
    result=dk.derive(fixture,out/'derived',dict(over,fixture=True))
finally:dk.SEALED_MANIFEST=production
assert (out/'derived/SHA256SUMS.txt').read_bytes()==(H/'build/fx/SHA256SUMS.txt').read_bytes()
assert result['config_key']==sc.load(H/'ids.json')['config_key']
artifacts=['tools/derive_kit_h1.py','payload/d.py','build/q.sh','build/a_8c74b291.sh',
           'payload/sums.txt','UPLOAD.json','orch_h1.sh','fin_h1.sh','build/c_patch.sh']
before={n:sc.sha(H/n) for n in artifacts}
for script in ('make_deriver.py','package_selection.py','package_proof.py','make_orchard.py','build_config_patch.py'):
    p=subprocess.run([sys.executable,'-B',str(H/'tools'/script)],capture_output=True,text=True)
    (out/(script+'.log')).write_text(p.stdout+p.stderr)
    assert p.returncode==0,p.stderr
after={n:sc.sha(H/n) for n in artifacts}
assert before==after,{n:(before[n],after[n]) for n in before if before[n]!=after[n]}
assert sc.sha(H/'payload/jb.sh')==sc.sha(H/'evidence/fix8_before/payload/jb.sh')
assert sc.sha(H/'EXPORT_OBJECTS.txt')==sc.sha(H/'evidence/fix8_before/EXPORT_OBJECTS.txt')
report=dict(status='PASS',path=str(out),native_indices=12,raw_and_projected_equal=True,
    production_selection_rewritten=False,derivation_manifest=result['manifest_sha256'],
    deterministic_artifacts=after,run_key=result['run_key'],exports_sha256=sc.sha(H/'EXPORT_OBJECTS.txt'))
(H/'evidence/fix8_admission/pin_tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
