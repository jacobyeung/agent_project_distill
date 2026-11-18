"""Seal the proof repair using a bounded changed-file inventory."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parents[1]
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def load(n): return json.loads((H/n).read_text())
def write(n, v): (H/n).write_text(json.dumps(v, indent=2, sort_keys=True)+'\n')

bindings = load('evidence/fix8c_before/bindings.json')
for n, digest in bindings.items(): assert sha(H/n) == digest, n
authority = load('evidence/fix8_admission/proof_authority.json')
for n, digest in authority['runtime'].items(): assert sha(H/'build/fx'/n) == digest, n
patch = load('evidence/fix8c_patch_manifest.json')
proof_sha = sha(H/'build/a_8c74b291.sh')
patch_sha = sha(H/'build/c_patch_8c.sh')
assert proof_sha == patch['new']['a_8c74b291.sh']
assert patch_sha == patch['patch_sha256']
for n, digest in patch['old'].items(): assert sha(H/'evidence/fix8c_before/payload'/n) == digest
old_lines = (H/'evidence/fix8c_before/payload/sums.txt').read_text().splitlines()
new_lines = (H/'payload/sums.txt').read_text().splitlines()
assert [x for x in old_lines if not x.endswith('  a_8c74b291.sh')] == [
    x for x in new_lines if not x.endswith('  a_8c74b291.sh')]
for line in new_lines:
    digest, n = line.split('  ', 1)
    assert sha(H/'payload'/n) == digest, n
up = load('UPLOAD.json')
assert sha(H/'build'/up['archive']) == up['sha256']
for row in up['files']: assert sha(H/'payload'/row['name']) == row['sha256']
tests = ('environment8c_tests', 'proof_tests', 'patch8c_tests', 'submit_tests', 'pin_tests')
for n in tests: assert load('evidence/fix8_admission/'+n+'.json')['status'] == 'PASS'
write('evidence/fix8c_checks.json', dict(status='LOCAL_PACKET_PASS',
    tests={n: 'PASS' for n in tests}, proof_sha256=proof_sha, patch_sha256=patch_sha,
    unchanged=bindings, production_preparation='NOT RUN',
    receipt_schema_unchanged=True, s_sh_unchanged=True,
    payload_changes=['a_8c74b291.sh', 'sums.txt']))
note=f'''Review and fixes are complete; the full dependency inventory is in [REVIEW8c.md](REVIEW8c.md).

| Review finding | Resolution / file:line |
|---|---|
| Host bwrap is unavailable | `tools/proof_prepare.py:45` reads certified k/0.json, checks absolute executable and SHA256; no PATH fallback. |
| Non-login host/environment assumptions | `proof_prepare.py:23` checks Python >=3.9 and all host programs; :29 normalizes environment; `tools/package_proof.py:17` uses Bash -p and absolute isolated Python. |
| Nested namespaces and absent O/r | `proof_prepare.py:54` probes production namespace flags before staging; :109 keeps writable proc/PID/dev, explicitly creates a user namespace, shares host network and overlays O/r; :81 creates private fresh /tmp storage. |
Tests: pinned-only bwrap with host binary masked, wrong SHA/missing/non-executable/relative pin refusals, verbatim nested tk_bwrap, absent O/r, clean environment, fresh /tmp and isolation PASS; 10 patch cases plus repeat refusal and 13 submission cases PASS.
Rebuild: exact selection/derivation, proof, upload, sums, transport and guarded patches are deterministic; evidence/fix8c_checks.json records results and unchanged bindings.
Production jb.sh/job.sh/b/c.sh/b/r.sh, KH manifest, identity, contract, go binding, receipt schema, s.sh and exports remain unchanged; the real job reuses nothing.
Proof: `build/a_8c74b291.sh` SHA256 `{proof_sha}`.
Patch: `build/c_patch_8c.sh` SHA256 `{patch_sha}`; checks old proof f1f6a151… and current sums 80bb318e…; changes only proof + sums line; retains both in BUN/v_8c.
Operator: deliver that patch as `/project/community/jjyeung/okh7/t_8c.sh`, then run `printf '%s  %s\\n' {patch_sha} /project/community/jjyeung/okh7/t_8c.sh | sha256sum -c - && bash /project/community/jjyeung/okh7/t_8c.sh`.
Then submit a fresh CPU-only proof using the existing command; KH/o/<job>.proof.json must PASS before s.sh accepts PROOF_JOB. Do not apply the full-bundle c_patch.sh to the installed round-8b state.
Validation was local and CPU-only; no SSH, network, Orchard job, GPU, Git or deletion. Orchard kernel policy and full preparation remain runtime checks.
'''
assert len(note.splitlines()) <= 15
(H/'FIX8c.md').write_text(note)

# Retain hashes of untouched evidence; refresh only files rebuilt in this round.
sealed = {n: digest for digest, n in (
    line.split('  ', 1) for line in (H/'evidence/fix8c_before/SHA256SUMS.txt').read_text().splitlines())}
changed = {'FIX8c.md', 'REVIEW8c.md', 'FIX8.md', 'REPORT.md', 'DIFF.md', 'UPLOAD.json',
    'orch_h1.sh', 'fin_h1.sh', 'tools/proof_prepare.py', 'tools/package_proof.py',
    'tools/build_proof_patch_8c.py', 'tools/seal_fix8c.py', 'tools/write_fix8.py',
    'tests/test_fix8_proof.py', 'tests/test_fix8c_environment.py', 'tests/test_fix8c_patch.py',
    'build/a_8c74b291.sh', 'build/c_patch_8c.sh', 'build/c_patch.sh', 'build/upload.tar',
    'build/'+up['archive'], 'payload/a_8c74b291.sh', 'payload/sums.txt',
    'evidence/fix8c_checks.json', 'evidence/fix8c_patch_manifest.json',
    'evidence/fix8c_before/bindings.json', 'evidence/fix8c_before/SHA256SUMS.txt',
    'evidence/fix8c_before/payload/a_8c74b291.sh', 'evidence/fix8c_before/payload/sums.txt',
    'evidence/fix8_admission/proof_authority.json'}
for n in tests:
    index = 'evidence/fix8_admission/'+n+'.json'
    changed.add(index)
    root = Path(load(index)['path'])
    changed.update(str(p.relative_to(H)) for p in root.glob('*.log'))
for n in sorted(changed): sealed[n] = sha(H/n)
delivery = load('evidence/fix8_admission/delivery.json')
delivery['files'].update({n: sealed[n] for n in changed})
delivery['proof_repair'] = 'FIX8c.md'
write('evidence/fix8_admission/delivery.json', delivery)
sealed['evidence/fix8_admission/delivery.json'] = sha(H/'evidence/fix8_admission/delivery.json')
(H/'SHA256SUMS.txt').write_text(''.join(digest+'  '+n+'\n' for n,digest in sorted(sealed.items())))
print('PASS: unchanged production bindings; payload/upload checks; bounded packet seal;',
      len(note.splitlines()), 'handoff lines')
