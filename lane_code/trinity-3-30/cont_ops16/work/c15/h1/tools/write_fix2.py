"""Record the job-name correction and completed local validation."""
import hashlib,json
from pathlib import Path

H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tests=json.loads((H/'evidence/fix2/tests.json').read_text())
assert len(tests)==11 and all(t['status']=='PASS' for t in tests)
for name in ('deterministic','chain_guard','package'):
 assert json.loads((H/f'evidence/fix2/{name}.json').read_text())['status']=='PASS'
text='''The packet submits exactly `a15_cot_ap5ee9da63`; `a15_cot_ap` is the account-mandated opaque prefix.
The job token remains `5ee9da63` in `TOKENS_H1.json` and both IDs records; both IDs records and `payload/go.template.json` carry the full name.
`tools/make_orchard.py` generates the corrected `payload/s.sh`, payload sums, upload archive, `UPLOAD.json` and embedded `orch_h1.sh`.
`REPORT.md` gives the current name in its table and step 8; `DIFF.md` includes the submitter and test patches.
`test_visible_names.py` allows the prefix only in the submitter’s `sbatch -J` argument before a hex suffix; all other forbidden-word checks remain active.
PASS: test_derivation, test_gate_binding, test_staging, and run_fallback fallback_fix2 (the four original checks).
PASS: test_stop_bridge, test_fix1, and test_visible_names, including positive and negative prefix checks.
PASS: tests/review/rv_mut.py, rv_g_a2.py, rv_gate.py, and rv_g_fx.py.
The CPU fallback completes 200 steps, exports m100/m200, reports H1_STOP with stopped_for_resume=false, and verifies the slot.
PASS: all review Python files parse and tests/RERUN_CHAIN.sh passes bash -n.
The chain runner is byte-identical; chain_r1 does not exist. The four-rank cases remain operator-only and were not executed.
PASS: two upload builds match byte for byte; payload sums, archive members and the embedded transport agree.
Configuration identity, admission contract, trainer, derived fixture manifest and batch wrapper remain unchanged.
`evidence/fix2/tests.json` and its logs record all 11 executed checks; `evidence/hash_changes_fix2.json` records changed hashes.
`SHA256SUMS.txt` seals the current packet and evidence. Work stayed local and CPU-only, with no SSH, network, Orchard, GPU, Git or deletion.
'''
assert len(text.splitlines())<=20
(H/'FIX2.md').write_text(text)
before=json.loads((H/'evidence/fix2_before/hashes.json').read_text())
names=set(before)|{'FIX2.md','tools/write_fix2.py'}
names.update(str(p.relative_to(H)) for p in (H/'evidence/fix2').iterdir() if p.is_file())
# The outer manifest seals this record; its own digest cannot appear inside it.
excluded={'SHA256SUMS.txt','evidence/final_checks.json','evidence/hash_changes_fix2.json'}
changes={}
for name in sorted(names-excluded):
 p=H/name
 if p.is_file() and before.get(name)!=sha(p):
  changes[name]=dict(before=before.get(name),after=sha(p))
old=json.loads((H/'evidence/fix2_before/UPLOAD.json').read_text())
new=json.loads((H/'UPLOAD.json').read_text())
record=dict(status='PASS',reason='Restore the account-mandated job-name prefix; regenerate transport and local validation evidence.',
 job_name='a15_cot_ap5ee9da63',job_token='5ee9da63',
 before_manifest_sha256=before['SHA256SUMS.txt'],
 upload_archive=dict(before=old['sha256'],after=new['sha256'],file='build/'+new['archive']),
 changes=changes,outer_seal='SHA256SUMS.txt seals this record and final_checks.json after generation.')
(H/'evidence/hash_changes_fix2.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('Wrote FIX2.md and hash_changes_fix2.json')
