"""Write the gate delivery report from verified packet artifacts."""
import difflib,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads((H/p).read_text())
ids=load('ids.json');up=load('UPLOAD.json');old=load('evidence/fix5_before/UPLOAD.json')
assert len(load('evidence/fix5/tests.json'))==13
assert all(v['status']=='PASS' for v in load('evidence/fix5/tests.json'))
assert load('evidence/fix5_gate/results.json')['status']=='PASS'
assert load('evidence/fix5_patch/results.json')['status']=='PASS'
assert load('evidence/fix5/package.json')['status']=='PASS'
changes={n:dict(before=sha(H/'evidence/fix5_before'/n),after=sha(H/n)) for n in ('payload/g.sh','payload/sums.txt','tools/make_orchard.py','UPLOAD.json')}
patch=H/'build/g_patch.sh'
text=f'''Cause: binding `/` read-only prevents missing logical parents; bwrap status 1 was mistaken for a measured gate failure.
`payload/g.sh:95`: build a tmpfs root with read-only host entries, recreated symlinks, private /dev, /proc and /tmp, and writable logical ancestors.
`payload/g.sh:119`: mount both pinned receipt aliases and writable BUN; retain user/uid/gid mapping, nice 19, offline settings and BUN/c caches.
`payload/g.sh:18,36,78`: refuse an existing gate.json; verify/reuse t/u against the archive bytes and pinned receipt/SQLite hashes, without deletion or overwrite.
`payload/g.sh:123`: require fresh bound JSON; pass is 0, measured false is 1, missing/invalid output or runtime failure is 2.
`tools/make_orchard.py:25`: package canonical g.sh unchanged so rebuilding cannot restore the broken sandbox; no other deployed executable changes.
`tools/build_gate_patch.py:1`, `build/g_patch.sh:1`: deterministic {patch.stat().st_size}-byte patch verifies old/new digests and retains g.sh.r4/sums.txt.r4.
Patch compatibility: p/e/staging/archive remain valid; z.sh derive/certify and s.sh use updated sums and bind the new g.sh in final external review; no full re-upload is required.
Apply the patch before gate/final evidence; its preflight refuses existing gate/ready/compare records or backups. Carry its body through the authorized wrapper, then rerun g.sh.
`tests/test_gate_sandbox.py:1`: real f.py/trainer and SQLite fixture; round-4 fails on an absent top-level parent, fixed script reuses its t/u and passes.
Gate tests PASS: failure->2, below-threshold->1, pass->0, missing/import/invalid reports, receipt binding, existing top-level parent, mount properties and tamper refusal.
PASS: four originals, stop_bridge, fix1, visible_names, sealed_modes, runtime_inventory, four runnable reviewer checks; review harness syntax only (`evidence/fix5/tests.json`).
PASS: patch preservation/refusal tests and repeated deterministic transport/patch builds (`evidence/fix5_patch/results.json`, `evidence/fix5/package.json`).
g.sh SHA256: {changes['payload/g.sh']['before']} -> {changes['payload/g.sh']['after']}.
sums.txt SHA256: {changes['payload/sums.txt']['before']} -> {changes['payload/sums.txt']['after']}.
Upload SHA256: {old['sha256']} -> {up['sha256']}; orch_h1.sh: {sha(H/'orch_h1.sh')}.
Patch SHA256: {sha(patch)}. All affected hashes are in evidence/hash_changes_fix5.json and sealed by SHA256SUMS.txt.
Identity {ids['identity']} and contract {ids['contract']} are unchanged; trainer, fixture manifest and batch wrapper are unchanged.
Tests used local bubblewrap 0.4.0; Orchard 0.9.0 remains untested here. Work was local/CPU-only; no SSH/network/Orchard/GPU/Git/deletion or chain creation/runner edit occurred.
'''
assert len(text.splitlines())<=20
(H/'FIX5.md').write_text(text)
report=(H/'evidence/fix5_before/REPORT.md').read_text()
first=report.index('\n\n')
report='The login gate creates missing receipt-mount parents inside bubblewrap, reuses verified extracted inputs, and classifies results from a fresh receipt-bound gate.json. The full local CPU regression suite passes. A 13,979-byte guarded patch updates the prepared bundle without a full re-upload. Submission still requires independent review and a separate GO. The four-rank chain was not executed; all work stayed local and CPU-only.'+report[first:]
report=report.replace(old['sha256'],up['sha256']).replace(old['archive'],up['archive'])
report=report.replace('Changed: manifest-scoped source reads, copies and mode comparisons.','Gate sandbox, extraction reuse and JSON verdict checks; all other carried executables retain their bytes.')
report=report.replace('evidence/hash_changes_fix4.json','evidence/hash_changes_fix5.json').replace('`FIX4.md` records the local test results.','`FIX5.md` records the gate changes and local tests.')
report=report.replace('`g.sh` invokes `r.py copy`,','When a.json is absent, `g.sh` invokes `r.py copy`,')
report=report.replace('`g.sh` rechecks that archive digest before extraction and verifies the receipt/SQLite pins afterward.', '`g.sh` rechecks that archive digest, extracts into fresh directories or verifies every existing file against its tar member, rejects extra files and links, and verifies the receipt/SQLite pins. It preserves existing verified t/u directories and refuses an existing gate.json.')
anchor='No routing archive was copied on Orchard during this task.'
report=report.replace(anchor,anchor+'\n\nThe sandbox starts with bubblewrap’s tmpfs root. It binds host entries read-only, recreates symlinks, and builds a writable directory skeleton only along the logical receipt roots. This also handles existing top-level directories whose deeper parents are absent. The interpreter can still reach its venv and base installation through the preserved host paths. `/dev`, `/proc` and `/tmp` receive dedicated mounts; both logical roots expose u read-only, and BUN stays writable. User mapping, nice 19, offline settings and BUN/c caches remain active.\n\nA fresh gate.json must contain a boolean passes field and the pinned receipt hash. A passing report plus a successful interpreter exit yields 0; a bound false report yields 1. Missing/invalid reports, hash mismatches and runtime failures yield 2 with a reason. Parent-directory permission refusals retain the existing entrypoint status 3.')
report=report.replace('`evidence/fix4/tests.json` records the eleven original and reviewer regressions.','`evidence/fix5/tests.json` records the thirteen current regression checks.')
report=report.replace('`payload/g.sh:36–37`','`payload/g.sh:89–90`').replace('run_fallback.py fallback_fix4','run_fallback.py fallback_fix5')
fallback=load('evidence/cpu/fallback_fix5/result.json')
report=report.replace('30.93 seconds',format(fallback['run']['elapsed_seconds'],'.2f')+' seconds').replace('fdbcc4df2999a5013f7fa5ca2beda64fc290b52ef67ee9daf0eb36d6da03898e',fallback['slot']['archive_sha256'])
anchor='The CPU fallback completed'
i=report.index(anchor)
report=report[:i]+('`tests/test_gate_sandbox.py` runs real bubblewrap, the shipped f.py and trainer, and a tiny SQLite receipt. Test copies relocate only physical/logical paths and receipt/SQLite pins. The absent-top-level fixture reproduces the round-4 read-only failure, then passes using the fixed script and the same extracted files. Additional cases cover false verdicts, sandbox/import failures, invalid reports, bound receipt hashes, read-only mounts, caches, priority and tampered extractions. Local bubblewrap is 0.4.0; Orchard’s 0.9.0 was not run. `evidence/fix5_gate/results.json` records all 22 cases.\n\n')+report[i:]
start=report.index('2. Verify `sha256sum -c SHA256SUMS.txt`.')
end=report.index('\n3. ',start)
report=report[:start]+'''2. Verify `sha256sum -c SHA256SUMS.txt`. For the prepared bundle with good p/e/staging/archive evidence, carry `build/g_patch.sh` as the authorized wrapper’s script body. It verifies both old file digests and all immutable payload sums before changing either file, checks the embedded new bytes, preserves g.sh.r4 and sums.txt.r4, and checks the resulting sums. It refuses changed inputs, existing backups, or gate/final evidence. No full re-upload is required for this state. For a fresh bundle, carry `orch_h1.sh` or the hash-checked opaque archive; the target-exists guard still applies.\n''' .rstrip()+report[end:]
report=report.replace('3. `o.sh` derives the BLOCKED candidate,','3. On a fresh bundle, `o.sh` derives the BLOCKED candidate,').replace('Run `g.sh` with an installed CPU `PY_GATE` and optional `BW_GATE`.','On the patched prepared bundle, retain that evidence and rerun only `g.sh` with the installed CPU `PY_GATE` and optional `BW_GATE`.')
anchor='All executable files, config overrides and `4.json` remain checksum-pinned.'
report=report.replace(anchor,anchor+' The gate patch leaves every derivation input and final kit manifest unchanged for the same attestations. Final derivation hashes the patched g.sh from the new sums into its external content-review record; certify and submission validate those bytes. The archive hash and transport inventory describe the complete new upload, while the two retained .r4 files are outside the active sums and final external record.')
(H/'REPORT.md').write_text(report)
patchtext=''
for n in ('payload/g.sh','tools/make_orchard.py'):
    patchtext+=''.join(difflib.unified_diff((H/'evidence/fix5_before'/n).read_text().splitlines(True),(H/n).read_text().splitlines(True),fromfile='round4/'+n,tofile='current/'+n))
(H/'evidence/gate_fix5.patch').write_text(patchtext)
intro='''The login gate mounts missing logical parents inside bubblewrap and validates a fresh gate.json before reporting its verdict. It reuses t/u only after archive-content and receipt/SQLite verification. `payload/g.sh` is the only changed deployed executable. `tools/make_orchard.py` now packages that canonical script; `tools/build_gate_patch.py` builds the required two-file update. Tests, packaging checks, reports and generated transport/checksums account for the remaining changes.

The exact gate and generator diff is [evidence/gate_fix5.patch](evidence/gate_fix5.patch). [FIX5.md](FIX5.md) maps changes to lines, tests and hashes. The patch keeps the prepared evidence and all downstream derivation/certification/submission bindings consistent; no full re-upload is required before gate/final evidence exists. Configuration identity, admission contract, trainer and fixture manifest remain unchanged.

'''
(H/'DIFF.md').write_text(intro+(H/'evidence/fix5_before/DIFF.md').read_text().replace('evidence/cpu/fallback_fix4/result.json','evidence/cpu/fallback_fix5/result.json'))
print('FIX5.md',len(text.splitlines()),'lines')
