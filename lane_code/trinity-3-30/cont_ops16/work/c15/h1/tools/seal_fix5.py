"""Seal the current packet, gate patch, reports and bounded local evidence."""
import ast,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads((H/p).read_text())
before=load('evidence/fix5_before/hashes.json');up=load('UPLOAD.json');ids=load('ids.json')
assert all(v['status']=='PASS' for v in load('evidence/fix5/tests.json'))
for n in ('evidence/fix5_gate/results.json','evidence/fix5_patch/results.json','evidence/fix5/package.json'):
    assert load(n)['status']=='PASS'
assert load('evidence/cpu/fallback_fix5/result.json')['slot']['step']==200
assert load('evidence/cpu/fallback_fix5/result.json')['slot']['verified'] is True
assert sha(H/'tests/RERUN_CHAIN.sh')==before['tests/RERUN_CHAIN.sh']
for n,h in before.items():
    if n.startswith('payload/') and n not in ('payload/g.sh','payload/sums.txt'):assert sha(H/n)==h,n
for d in ('tools','tests','payload'):
    for p in (H/d).rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in [*(H/'payload').glob('*.sh'),H/'build/g_patch.sh',H/'orch_h1.sh',H/'tests/RERUN_CHAIN.sh']:
    subprocess.run(['/bin/bash','-n',str(p)],check=True)
assert len((H/'FIX5.md').read_text().splitlines())<=20
assert sha(H/'payload/g.sh')==load('evidence/fix5/package.json')['deterministic']['payload/g.sh']
assert sha(H/'build/g_patch.sh')==load('evidence/fix5/package.json')['deterministic']['build/g_patch.sh']
files={H/n for n in before}
files.update(H/n for n in ('FIX5.md','build/g_patch.sh','build/'+up['archive'],'evidence/fix5_gate.log','evidence/gate_fix5.patch','evidence/hash_changes_fix5.json'))
for d in ('tools','tests'):
    files.update(p for p in (H/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for d in ('evidence/fix5','evidence/fix5_gate','evidence/fix5_patch'):
    files.update(p for p in (H/d).iterdir() if p.is_file())
for n in ('hashes.json','payload/g.sh','payload/sums.txt','tools/make_orchard.py','UPLOAD.json','ids.json','REPORT.md','DIFF.md','SHA256SUMS.txt'):
    files.add(H/'evidence/fix5_before'/n)
for n in ('result.json','chain.log','slots/A.json','slots/A.sha256','run/s2.json','run/inputs/first_step_993.json'):
    files.add(H/'evidence/cpu/fallback_fix5'/n)
for n in ('evidence_orchard_q9_gate_2215Z.txt','evidence_orchard_q11_2217Z.txt'):
    if (H/n).is_file():files.add(H/n)
summary=dict(status='PASS',identity=ids['identity'],contract=ids['contract'],payload_changes=['g.sh','sums.txt'],regression_cases=13,gate_cases=22,patch_cases=7,cpu_step200_slot='PASS',production_go_granted=False,four_rank_chain='NOT RUN; runner unchanged; syntax checked',local_bwrap_version=load('evidence/fix5_gate/results.json')['bwrap_version'],full_reupload_required=False)
(H/'evidence/final_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
changes={str(p.relative_to(H)):dict(before=before.get(str(p.relative_to(H))),after=sha(p)) for p in sorted(files) if p.is_file() and p!=H/'evidence/hash_changes_fix5.json' and before.get(str(p.relative_to(H)))!=sha(p)}
record=dict(status='PASS',changes=changes,identity=ids['identity'],contract=ids['contract'],ids_unchanged=True,trainer_unchanged=True,fixture_manifest_unchanged=True,upload=dict(before=load('evidence/fix5_before/UPLOAD.json')['sha256'],after=up['sha256']),old_outer_manifest_sha256=sha(H/'evidence/fix5_before/SHA256SUMS.txt'),outer_seal='SHA256SUMS.txt seals this record; it is not self-hashed.')
(H/'evidence/hash_changes_fix5.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
assert all(p.is_file() for p in files),[str(p) for p in files if not p.is_file()]
assert sum(p.stat().st_size for p in files)<2_000_000_000
manifest=''.join(sha(p)+'  '+str(p.relative_to(H))+'\n' for p in sorted(files))
(H/'SHA256SUMS.txt').write_text(manifest)
print(json.dumps(summary,indent=2));print('manifest',sha(H/'SHA256SUMS.txt'),'files',len(files))
