import difflib,hashlib,json,re
from pathlib import Path
T=Path(__file__).resolve().parent
PRIVATE=T.parent/'kc_guard';BASE=T.parent.parent/'kc';BRIEF=T.parent/'kc_guard_brief'
W=PRIVATE/'k1_build/work/kit_k1a/work'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=['k1_cli.py','k1_pipeline.py','k1_guard.py','gravity_guard.py','test_k1_guard.py']
diffs=[];hashes=[]
for name in files:
 rel=Path('k1_build/work/kit_k1a/work')/name
 old=BASE/rel;new=PRIVATE/rel
 diff=''.join(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],new.read_text().splitlines(True),fromfile='a/'+str(rel) if old.exists() else '/dev/null',tofile='b/'+str(rel)))
 assert diff
 diffs.append((str(rel),diff));hashes.append((str(rel),sha(new)))
for name in ['convert7','k1_downstream']:
 old=T.parent/(name+'.sh');new=BRIEF/(name+'.guard.sh')
 diff=''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='original-work/'+old.name,tofile='kc_guard_brief/'+new.name))
 diffs.append(('kc_guard_brief/'+new.name,diff));hashes.append(('kc_guard_brief/'+new.name,sha(new)))
(BRIEF/'PATCH.diff').write_text(''.join(d for _,d in diffs))
proof=json.loads((T/'identity_proof.json').read_text())
for key in ['private_after','bound_after']:
 for path,digest in proof[key].items():assert sha(path)==digest,(key,path)
assert sha(W/'gravity_guard.py')=='b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79'
for name in ['k1_report.py','k1_phases.py']:
 assert (W/name).read_bytes()==(BASE/'k1_build/work/kit_k1a/work'/name).read_bytes()
extra=[]
for name in ['test_kit.py','test_guards.py']:
 rel=Path('k1_build/work/kit_k1a/native_kit')/name
 assert sha(PRIVATE/rel)==sha(BASE/rel)
 extra.append((str(rel),sha(PRIVATE/rel)))
for name in ['convert7','k1_downstream']:
 for digest,var,rel in re.findall(r'^([0-9a-f]{64})  \$(KIT|KC)/(\S+)$',(BRIEF/(name+'.guard.sh')).read_text(),re.M):
  assert sha((W.parent if var=='KIT' else W)/rel)==digest
log=(T/'unit_v3.log').read_text();assert 'Ran 10 tests' in log and log.rstrip().endswith('OK')
for name,n in [('test_kit',19),('test_guards',7)]:
 s=(T/(name+'.log')).read_text();assert f'Ran {n} tests' in s and s.rstrip().endswith('OK')
coverage=json.loads((T/'guard_coverage.json').read_text())
def ranges(nums):
 groups=[]
 for n in sorted(set(nums)-{0}):
  if groups and n==groups[-1][-1]+1:groups[-1].append(n)
  else:groups.append([n])
 return ', '.join(str(g[0]) if len(g)==1 else f'{g[0]}–{g[-1]}' for g in groups) or 'none'
parts=[f'''The guarded K1 convert, tables, and render path is ready for review. All required checks pass. The real canary produces three guarded cache receipts, including `arkitscenes/41069175`, and halts only when capture 4 lacks its own output.

The patch changes two existing runtime files (`k1_cli.py`, `k1_pipeline.py`) and adds `k1_guard.py`, the byte-identical reviewed `gravity_guard.py`, and a CPU regression suite. `k1_phases.py`, `k1_report.py`, the manifest, selection rules, scoring, GT sets, admission, refit, and all source-bound files remain unchanged.

**Runtime behavior**

- `k1_guard.install()` calls the reviewed install once per process, before geometry loading. The installer checks the sealed validate hash. Its vendored SHA-256 is `b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79`.
- The CLI wrapper temporarily replaces the module global `F.convert`; `F.run` and its producer hash remain unchanged. Only `GeometryError('reference_camera_up_opposes_gravity')` with a recorded reviewed refusal becomes nonfatal. Every other exception propagates into the unchanged halt path.
- Every completed cache receipt includes `gravity_guard=gravity_guard.identity()` and `gravity_verdict={{sealed_refused, reviewed_refused}}`. Refused receipts bind capture, checkpoint, synthetic flag, sources, file pins, `geometry=None`, and refusal code/message. Both proposal files are copied unchanged.
- The sealed converter writes geometry before validation. Under the no-deletion rule, a refused file is renamed to `REFUSED_GEOMETRY.npz` and pinned as evidence. The capture has no `geometry.npz`. `cached()` returns `geo=None` and never loads the preserved evidence.
- `cached()` checks guard identity, verdicts, source identity, capture identity, disposition, file membership, destination paths, and content pins. Resume restores refused verdicts into the recorder; passing caches load geometry under the guard and verify its verdict.
- Tables emit no candidate/pair rows for refusals and retain the capture-to-code map in `TABLE_RECEIPT.json.geometry_refused`. Tables and render keep the guard capture context active during downstream geometry work.
- Every refused response contains one failed call, `mask_match.ok=False`, and the unchanged `P.classify` decision: `label='fallback', reason='runtime_failure', value=None`. The renderer receives no visual fallback evidence for that capture and emits an excluded row without a target. Every row remains in `K1_ANALYSIS_INPUT.jsonl`.
- `k1_report.py` needs no edit. Its expected-ID check preserves the full selected row denominator; its held-out distance count includes refusals. Answered-only MRA and trust/fallback-share rules remain unchanged, including the failure classifier's fallback label.
- Convert emits `GUARD_REPORT.json` beside `BINDING.json`, including when a later capture halts. Tables and render also emit the reviewed recorder's report.

**Receipt-bound source paths**

`B.source_identity()` includes absolute filenames. Relocating the private native kit changes its identity keys even when its bytes match. Both guarded launchers therefore export:

```bash
export K1_NATIVE_KIT={BASE}/k1_build/work/kit_k1a/native_kit
```

The patched pipeline supports that import path. K1 work-stage code runs from `{W}`; frozen native code loads read-only from its original receipt-bound location. Neither the identity function nor its results are rewritten. All 303 upstream receipts pass exact source-map equality. Every bound file in the private native copy also matches the baseline bytes.

Use the guarded launchers, or set this environment variable for direct Python commands. Guardless legacy convert receipts fail the new guard-binding check and require a fresh convert root. Both launcher copies point to the private K1 work tree. The downstream copy uses the supplied scipy interpreter and writes under `kc_guard/guard_downstream`. The original scripts remain untouched.

**Real canary evidence**

The test used the unchanged 300-capture manifest, the real tower root, and three real own captures. No three-capture production manifest was created.

| Capture | Sealed refused | Reviewed refused | Geometry |
|---|---|---|---|
''']
for r in proof['canary']:
 v=r['gravity_verdict'];parts.append(f"| {r['canonical']} | {str(v['sealed_refused']).lower()} | {str(v['reviewed_refused']).lower()} | Loaded; depth scale count {r['geometry']['depth_scale_count']} |\n")
parts.append(f'''
Capture 4 is `arkitscenes/41069181` (`927c65c6781ef0c8`). Its own `PHASE_COMPLETE.json` is absent. The CLI exits 1 and writes `HALTED.json`, as expected. The progress journal records all three commits before capture 4 starts; the log names its missing receipt.

Canary root: [{T}/canary]({T}/canary). Guard report:

```json
{json.dumps(proof['guard_report'],indent=2)}
```

**Tests and commands**

Tests ran on `trinity-1-18` without SSH, Git, network, GPU, process termination, or file deletion. The existing supervisor tests mock signals and subprocesses. The canary invoked the CLI directly without its terminating watchdog. All test roots are under `{T}`.

Common environment:

```bash
cd {PRIVATE}
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export K1_NATIVE_KIT={BASE}/k1_build/work/kit_k1a/native_kit
PY=/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python
```

Real canary command (expected exit 1):

```bash
"$PY" -I -s -B k1_build/work/kit_k1a/work/k1_pipeline.py cache \\
  --manifest {T.parent}/manifest_v2/a40fbc19.json \\
  --out {T}/canary --phase convert --max-seconds 14400 \\
  --tower-cache /scratch/jjyeung/k1/run_tower_sam_2 \\
  --own-cache {T.parent}/own7/canary/native/probe > {T}/canary.log 2>&1
```

Guard regression command (exit 0):

```bash
K1_GUARD_TEST_RUN=unit_v3 "$PY" -I -s -B k1_build/work/kit_k1a/work/test_k1_guard.py > {T}/unit_v3.log 2>&1
```

The planted refusal uses synthetic tower/own arrays and proper synthetic rotations with reference plane 1 and margin -1. The real validators, converter, phase checks, receipt writer, cache loader, tables writer, classifier, and renderer execute. Proposal content and fit metadata are fixtures. One refused row carries verified visual fallback evidence; the test proves that it produces no target. Resume runs with an empty recorder and restores the receipt verdicts. Passing downstream tests load real canary geometry but use fixture candidate extraction, GT reads, fit metadata, and backend calls. They test context and row retention, not fitted-model accuracy.

```text
{log.rstrip()}
```

Byte identity, 300 tower checks, 3 own checks, and canary verification (exit 0):

```bash
"$PY" -I -s -B {T}/verify_identity.py > {T}/identity.log 2>&1
```

```text
{(T/'identity.log').read_text().rstrip()}
```

Existing kit checks (exit 0 each):

```bash
"$PY" -I -s -B {T}/run_existing.py test_kit > {T}/test_kit.log 2>&1
"$PY" -I -s -B {T}/run_existing.py test_guards > {T}/test_guards.log 2>&1
"$PY" -I -s -B k1_build/work/kit_k1a/work/verify_sources.py > {T}/verify_sources.log 2>&1
```

`run_existing.py` executes the existing test sources and changes only output-root expressions in memory. Fixtures and coverage outputs stay under the permitted test root. The native test files remain byte-identical to the baseline. These suites test their original sealed control path; the new regression suite tests the installed reviewed guard.

```text
{(T/'test_kit.log').read_text().rstrip()}

{(T/'test_guards.log').read_text().rstrip()}

{(T/'verify_sources.log').read_text().rstrip()}
```

Launcher syntax checks (exit 0):

```bash
bash -n {BRIEF}/convert7.guard.sh
bash -n {BRIEF}/k1_downstream.guard.sh
```

A bounded Python check recomputed all `$KC`/`$KIT` file hashes in the launchers: 4 convert pins and 10 downstream pins match. The report generator repeats those checks and verifies the final protected source hashes:

```bash
"$PY" -I -s -B {T}/build_report.py
```

**Byte-identity table**

Each row shows the pre-edit private-tree hash and final hash. Runtime imports use `BASE` for private native-kit rows; those files have the same before/after hashes. Both absolute-path source maps are recorded in [identity_proof.json]({T}/identity_proof.json). The private `k1_phases.py` exactly matches the producer hash in all 303 upstream receipts.

Aliases: `PRIVATE={PRIVATE}`; `BASE={BASE}`. External paths are shown in full.

| Protected path | Before SHA-256 | After SHA-256 |
|---|---|---|
''')
for p,before in proof['private_before'].items():
 label=p.replace(str(PRIVATE),'PRIVATE')
 parts.append(f"| `{label}` | `{before}` | `{proof['private_after'][p]}` |\n")
parts.append('\nAdditional unchanged native tests:\n\n| File | Baseline and private SHA-256 |\n|---|---|\n')
for path,digest in extra:parts.append(f'| `{path}` | `{digest}` |\n')
parts.append('''
Manifest v2 SHA-256: `e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146` (unchanged).

**New and changed file hashes**

Paths are relative to `kc_guard`, except the named launcher copies.

| File | SHA-256 |
|---|---|
''')
for path,digest in hashes:parts.append(f'| `{path}` | `{digest}` |\n')
parts.append(f'| `kc_guard_brief/PATCH.diff` | `{sha(BRIEF/"PATCH.diff")}` |\n')
parts.append('''
**Lines without test coverage and validation limits**

The table lists executable lines without recorded coverage in the final ten-test regression trace. It is a conservative list of unobserved lines: the real canary was not traced, and a child process tests the sealed-hash mismatch refusal. Thus the pipeline entry point and the hash-mismatch branch appear unobserved despite those separate tests. The stdlib trace pseudo-line 0 is omitted. Full hit/missing sets are in `kc_guard_tests/guard_coverage.json`.

| File | Traced executable lines | Lines without recorded coverage |
|---|---|---|
''')
for name,v in coverage.items():
 hit=set(v['hit'])-{0};all_lines=set(v['executable'])-{0}
 parts.append(f"| `{name}` | {len(hit)}/{len(all_lines)} | {ranges(v['missing'])} |\n")
parts.append(f'''
The native suites have separate line reports in [TEST_COVERAGE.json]({T}/TEST_COVERAGE.json) and [GUARD_COVERAGE.json]({T}/GUARD_COVERAGE.json). No GPU coverage is claimed. The shell launchers were syntax-checked and hash-checked; their operational command lines were not executed. Full production tables/refit/render and neural inference were not run. Passing downstream fixtures do not measure learned selection or accuracy.

**Open questions**

No implementation question blocks review. A full production run requires the remaining own outputs and a fresh guarded convert root. Preserving refused geometry under a non-loadable name follows the no-deletion rule. Existing scoring still calls runtime failures `fallback`; refused geometry supplies no fallback prediction or training target.

The report applies the no-archaeology skill. No borderline historical prose was retained; baseline differences are included because unified diffs are explicitly required.

**Unified diffs**

These are all runtime and test changes against `{BASE}`. New files use `/dev/null`. Launcher diffs compare the untouched originals in `work/` with their new `.guard.sh` copies. The combined patch is [PATCH.diff]({BRIEF}/PATCH.diff). Test logs and evidence are linked above and are not deployment changes.

''')
for name,diff in diffs:parts.append(f'`{name}`\n\n```diff\n{diff}```\n\n')
parts.append('READY\n')
(BRIEF/'REPORT.md').write_text(''.join(parts))
print(json.dumps(dict(report=str(BRIEF/'REPORT.md'),patch=str(BRIEF/'PATCH.diff'),runtime_modified=2,runtime_added=2,test_added=1,launchers_added=2,tests=36,verdict='READY')))
