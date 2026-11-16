The E3 copy provides `GD_sealed` and `GD_reviewed`. Both load the same deployed file. Every other arm retains sealed validation. The three-capture CPU check passed, including byte-identical non-GD diagnostics and all 55 non-GD scored rows. The build is ready for the requested GD evaluation; the full production dataset has not been run.

Runtime files: `e3gd/harness.py`, `e3gd/run.sh`, `e3gd/agg.py`, and `e3gd/gravity_guard.py`. The regression/subset driver is `e3gd/test_gd.py`. [PATCH.diff](PATCH.diff) and the embedded diff below contain every edit and added file. No Git, SSH, network, GPU, process termination, deletion, or write to the original harness was used. All work ran on `trinity-1-18`.

**Guard and refusal behavior**

- The vendored guard is byte-identical to the reviewed K1 guard: SHA-256 `b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79`. Its installer verifies the sealed validator source SHA-256 `05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a`.
- The serial harness installs the guard once, on the first reviewed load. It saves both validators, supplies the guard's capture context, and restores sealed validation in `finally` before returning geometry to the evaluator. The test also verifies restoration after an unrelated exception and rejection of a second install.
- Each present file gets a path and SHA-256 receipt in both `f['GD_sealed']` and `f['GD_reviewed']`. A load-time `GeometryError` adds its exact refusal string. A missing digest-path file uses the convert receipt's refusal code when available; otherwise it records `FileNotFoundError:deployed_geometry_missing`. Neither arm reads `REFUSED_GEOMETRY.npz`.
- Refusals use the existing tuple path. Each distance or room row stays in the denominator and scores zero. Missing-file room tests cover R0, R1, and train-fitted R2. Ambiguous roots with multiple matching files remain configuration errors.
- Scale fitting, scoring arithmetic, GT masks, the 8-thread limit, and non-GD programs are unchanged. `room_rules.py`, `r2fit.py`, both shard scripts, `finalize.py`, and the supplied `out/FITS.json` were checked byte-for-byte against the original copy.

**Fixture and real-capture evidence**

Fixture root: `/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/gd_tests/convert_fixture`.

| Capture | Digest directory | Fixture | GD_sealed | GD_reviewed |
|---|---|---|---|---|
| arkitscenes/41048124 | dfece798227526fb | Byte copy from K1 canary | 0.98 m; MRA 0.9 | 0.98 m; MRA 0.9 |
| arkitscenes/41069076 | 54c1c9d606f2a398 | Missing geometry with synthetic refusal receipt | Refused; MRA 0 | Refused; MRA 0 |
| arkitscenes/41069175 | 48f3924ccb5dd8b6 | Byte copy from K1 canary | All 3 rows refused; MRA 0 | 3.56 / 4.46 / 2.81 m; MRA 0.8 / 1.0 / 0.8 |

The missing fixture is deliberately planted; it does not assert that K1 refused the real `41069076` capture. The copied files come from `/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary/<digest>/geometry.npz`. [FIXTURE.json](../e3gd/out/gd_tests/FIXTURE.json) pins their hashes. The three GT rasters total 4,736,767 compressed bytes and were read from local `/scratch`.

The baseline executes original `harness.py` SHA-256 `a38d1ad20f6c0cd7843320d0ba98dc6f43f16624c715a04a47ee51ef16c9cfa1`. Only its workspace assertion is redirected in memory; its `__file__` and output root keep every write inside e3gd. The changed harness evaluates the same captures with the fixture GD directory. Removing only the two added GD receipts and GD rows gives byte-identical serialized per-capture JSON, including diagnostics, predictions, scores, and refusal strings.

| Capture | Non-GD rows | Serialized bytes | SHA-256, identical for both runs |
|---|---:|---:|---|
| arkitscenes/41048124 | 11 | 5956 | `32c2240e1eb485250739d5b77b70c352962ba4a017087976501317e827771af2` |
| arkitscenes/41069076 | 11 | 5955 | `492d72f98287cd2b88dd471f429531a81ded52713003df2199d93c1b66b75bfe` |
| arkitscenes/41069175 | 33 | 14738 | `ba2dea52464c6ecf8e3c7516f78a53e71a4ebff8b81f71d89bf443f5756dbb88` |

Baseline files: `e3gd/out/gd_tests/changed/baseline/*.json`. Changed files including GD: `e3gd/out/gd_tests/changed/captures/*.json`. Filtered changed files: `e3gd/out/gd_tests/*.non_GD.json`. The supplemental synthetic room check also proves non-GD byte parity.

**Test commands and outputs**

The stock harness CLI offers only `preflight`, `run`, `--approved-heavy-io`, `--so-mask`, and `--gd-dir`; it has no capture selector. The copied shard scripts hardcode the original harness and pass no GD directory. The new subset driver accepts `--gd-dir` and invokes the copy's real capture loading, feature extraction, and evaluation on the three selected captures. It uses the supplied train fits and writes only test outputs.

Executed with exit 0:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
mkdir -p out/gd_tests
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/planner_local_v1/bin/python -B test_gd.py --gd-dir out/gd_tests/convert_fixture > out/gd_tests/test.log 2>&1
```

The driver requires a fresh fixture directory. For another run, choose a new directory such as `out/gd_tests_next/convert_fixture`; retain the existing evidence.

[test.log](../e3gd/out/gd_tests/test.log), with the complete machine-readable result in [RESULT.json](../e3gd/out/gd_tests/RESULT.json):

```text
PASS real capture byte parity + GD disposition: arkitscenes/41048124 non_GD_rows 11
PASS real capture byte parity + GD disposition: arkitscenes/41069076 non_GD_rows 11
PASS real capture byte parity + GD disposition: arkitscenes/41069175 non_GD_rows 33
PASS original harness unit tests under sealed validator after GD_reviewed loads
PASS edge cases: missing file, reviewed refusal, invalid scale, finally restoration, one install
PASS aggregation: train/heldout, both references, comma list, R0/R1/R2, refusal denominator
{"status": "PASS", "fixture": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/gd_tests/convert_fixture", "captures": [{"capture": "arkitscenes/41048124", "non_GD_rows": 11, "bytes": 5956, "sha256": "32c2240e1eb485250739d5b77b70c352962ba4a017087976501317e827771af2"}, {"capture": "arkitscenes/41069076", "non_GD_rows": 11, "bytes": 5955, "sha256": "492d72f98287cd2b88dd471f429531a81ded52713003df2199d93c1b66b75bfe"}, {"capture": "arkitscenes/41069175", "non_GD_rows": 33, "bytes": 14738, "sha256": "ba2dea52464c6ecf8e3c7516f78a53e71a4ebff8b81f71d89bf443f5756dbb88"}], "elapsed_seconds": 159.7722876300104, "guard_identity": {"evaluation_gravity_guard": {"name": "validate_up_convention", "sha256": "b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79"}, "sealed_gravity_guard": {"name": "GeometryContract.validate", "inspect_sha256": "05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a"}}}

```

Supplemental command, exit 0:

```bash
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/planner_local_v1/bin/python -B - <<'PYTEST' > out/gd_tests/room_and_real_agg.log 2>&1
import json, subprocess, sys
import test_gd as T
H=T.H
root=H.ROOT/'out/gd_tests'
H.OUT=root/'changed'
old=T.baseline()
fits=json.loads((H.ROOT/'out/FITS.json').read_text())
c=next(c for c in json.loads(H.MANIFEST.read_text())['captures'] if c['canonical']==T.NAMES[0])
H.load_reviewed_geometry(root/'convert_fixture'/H.digest(c['canonical'])[:16]/'geometry.npz',c)
T.room_refusals(root,old,fits)
for split in ('train','heldout'):
 for ref in ('GD_reviewed','GD_sealed'):
  result=subprocess.run([sys.executable,'-B','agg.py',str(H.OUT/'captures'),split,'out/FITS.json',ref],text=True,capture_output=True,check=True)
  (root/f'real_agg_{split}_{ref}.txt').write_text(result.stdout)
  assert f'vs {ref}:' in result.stdout
  print('PASS real agg',split,ref,flush=True)
print('PASS supplemental checks',flush=True)
PYTEST
```

[room_and_real_agg.log](../e3gd/out/gd_tests/room_and_real_agg.log):

```text
PASS synthetic room: non-GD byte parity; missing GD scores zero in R0/R1/R2; R2 train denominator
PASS real agg train GD_reviewed
PASS real agg train GD_sealed
PASS real agg heldout GD_reviewed
PASS real agg heldout GD_sealed
PASS supplemental checks

```

`bash -n run.sh` passed. Python AST parsing passed for `harness.py`, `agg.py`, `test_gd.py`, and `gravity_guard.py`. Exact byte equality against the source guard passed. The main suite took 159.8 seconds, including both harness evaluations and aggregation checks. Original harness unit tests also passed after reviewed loads. Synthetic checks cover reviewed refusal, another GeometryError (`invalid_scale`), and missing files without receipts.

**Production and aggregation commands**

After explicit approval for the full raster I/O, substitute the actual K1 convert root for `<convert root>` and run:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
bash /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/run.sh run --approved-heavy-io --gd-dir '<convert root>' > /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/production.log 2>&1
```

`run.sh` uses `/scratch/jjyeung/envs/planner_local_v1/bin/python`, disables CUDA, and sets OMP, MKL, OpenBLAS, and NumExpr threads to 8. Full-run outputs stay under `e3gd/out`; production refits `out/FITS.json` on train captures, including separate GD R2 factors. Plan roughly 3 hours, based on the source E3 record's full-run estimate. This is a planning estimate, not a measured 296-capture runtime for this two-arm build.

The source harness has a known finalization error: `GT_low_z_floor_sanity` indexes `gt_floor_at_low_z` on feature-refused captures. The full runner writes all per-capture JSON, the fitted constants, and both PER_ITEM/PER_CAPTURE files before that check, then is expected to exit nonzero on this dataset. This unrelated check is unchanged under the instruction to change only the GD arms. Use the per-capture aggregation below. The copied `finalize.py` and shard scripts still point at the original workspace and must not be used here.

The fourth `agg.py` argument remains a reference arm name, or a comma-separated list. Both requested names work. For room rows, the original semantics append each challenger's R0/R1/R2 suffix to the reference; they do not force every room comparison to GD+R0. The built-in harness SUMMARY/REPORT still use S1+G1 as their primary reference; the requested GD paired tables come from these explicit commands:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
"$PY" -B agg.py out/captures train out/FITS.json GD_reviewed > out/TRAIN_GD_reviewed.txt
"$PY" -B agg.py out/captures heldout out/FITS.json GD_reviewed > out/HELDOUT_GD_reviewed.txt
"$PY" -B agg.py out/captures train out/FITS.json GD_sealed > out/TRAIN_GD_sealed.txt
"$PY" -B agg.py out/captures heldout out/FITS.json GD_sealed > out/HELDOUT_GD_sealed.txt
```

The primary deployed column is `GD_reviewed`; `GD_sealed` diagnoses the sealed reader's behavior on the same files. The C-rule requires a paired train lower bound above zero and a held-out point difference above zero. The small fixture checks implementation only and supports no adoption decision. Fixed-R0 comparisons for all room challengers would require a separate aggregation change; this patch preserves the requested original call semantics.

The report applies the no-archaeology writing skill. It retains no borderline history-only sentences. The unified diff is included because it is an explicit deliverable.

**Unified diff**

```diff
--- original/harness.py
+++ e3gd/harness.py
@@ -18,7 +18,7 @@
 from collections import defaultdict
 
 ROOT = Path(__file__).resolve().parent
-assert ROOT == Path('/scratch/jjyeung/orch_n30/e3_geom/work/harness')
+assert ROOT == Path('/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd')
 TREE = Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
 MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
 TOWERS = Path('/scratch/jjyeung/k1/run_tower_sam_2')
@@ -52,6 +52,8 @@
 import numpy as np
 from student_pilot import camera_targets, ground_lifting, tower_scale_rule
 from student_pilot.ground_profiles import load_geometry
+from student_pilot import geometry_profiles
+import gravity_guard
 from student_pilot.scene_state import FrameMap
 from trace_format.ground_v313 import Session
 from trace_format import room_v314 as room
@@ -65,6 +67,64 @@
 TIMINGS = defaultdict(float)
 SCALES = ('S1', 'S2', 'S3', 'S4', 'SO')
 GRAVITIES = ('GO', 'G1')
+SEALED_VALIDATE = geometry_profiles.GeometryContract.validate
+REVIEWED_VALIDATE = None
+GRAVITY_RECORDER = gravity_guard.Recorder()
+
+
+def load_reviewed_geometry(path, c):
+    """Use the reviewed validator only for this serial deployed-geometry load."""
+    global REVIEWED_VALIDATE
+    previous = geometry_profiles.GeometryContract.validate
+    assert previous is SEALED_VALIDATE, 'reviewed validator leaked outside GD_reviewed'
+    try:
+        if REVIEWED_VALIDATE is None:
+            gravity_guard.install(geometry_profiles, GRAVITY_RECORDER)
+            REVIEWED_VALIDATE = geometry_profiles.GeometryContract.validate
+        geometry_profiles.GeometryContract.validate = REVIEWED_VALIDATE
+        with gravity_guard.capture('E3_GD_reviewed', c['canonical']):
+            return load_geometry(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
+    finally:
+        geometry_profiles.GeometryContract.validate = previous
+
+
+def deployed_conditions(c, gd_dir, f):
+    options = [gd_dir / c['canonical'] / 'geometry.npz',
+               gd_dir / (c['canonical'].replace('/', '__') + '.npz'),
+               gd_dir / digest(c['canonical'])[:16] / 'geometry.npz']
+    paths = [p for p in options if p.is_file()]
+    if len(paths) > 1:
+        raise ValueError('GD requires exactly one deployed geometry file for ' + c['canonical'])
+    if not paths:
+        reason = 'FileNotFoundError:deployed_geometry_missing'
+        detail = dict(path=str(options[-1]), refusal=reason)
+        receipt_path = options[-1].parent / 'CACHE_COMPLETE.json'
+        if receipt_path.is_file():
+            receipt = json.loads(receipt_path.read_text())
+            refusal = receipt.get('geometry_refusal')
+            if isinstance(refusal, dict) and refusal.get('code'):
+                reason = 'GeometryError:' + refusal['code']
+                detail.update(refusal=reason, geometry_refusal=refusal,
+                              gravity_verdict=receipt.get('gravity_verdict'),
+                              cache_receipt=str(receipt_path))
+        for arm in ('GD_sealed', 'GD_reviewed'):
+            f[arm] = dict(detail)
+            yield arm, (reason, None), 'predicted'
+        return
+    path = paths[0]
+    pin = dict(path=str(path), sha256=sha(path))
+    for arm in ('GD_sealed', 'GD_reviewed'):
+        f[arm] = dict(pin)
+        try:
+            geo = (load_reviewed_geometry(path, c) if arm == 'GD_reviewed' else
+                   load_geometry(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled'))
+            assert geo.depth_scale_count == 1
+        except geometry_profiles.GeometryError as exc:
+            reason = type(exc).__name__ + ':' + str(exc)
+            f[arm]['refusal'] = reason
+            yield arm, (reason, None), 'predicted'
+        else:
+            yield arm, geo, 'predicted'
 
 
 def sha(path):
@@ -391,15 +451,7 @@
                 except ValueError as exc:
                     yield arm, (type(exc).__name__ + ':' + str(exc), None), 'predicted'
         if gd_dir:
-            options = [gd_dir / c['canonical'] / 'geometry.npz', gd_dir / (c['canonical'].replace('/', '__') + '.npz'),
-                       gd_dir / digest(c['canonical'])[:16] / 'geometry.npz']
-            paths = [p for p in options if p.is_file()]
-            if len(paths) != 1:
-                raise ValueError('GD requires exactly one deployed geometry file for ' + c['canonical'])
-            geo = load_geometry(paths[0], FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
-            assert geo.depth_scale_count == 1
-            f['GD'] = dict(path=str(paths[0]), sha256=sha(paths[0]))
-            yield 'GD', geo, 'predicted'
+            yield from deployed_conditions(c, gd_dir, f)
     for arm, geo, mode in conditions():
         start = time.monotonic()
         lifted_cache = {}
--- original/run.sh
+++ e3gd/run.sh
@@ -1,6 +1,6 @@
 #!/usr/bin/env bash
 set -euo pipefail
-cd /scratch/jjyeung/orch_n30/e3_geom/work/harness
+cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
 export CUDA_VISIBLE_DEVICES=''
 export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
 export PYTHONDONTWRITEBYTECODE=1
--- original/agg.py
+++ e3gd/agg.py
@@ -1,4 +1,9 @@
-"""Aggregate per-capture JSON into arm tables: mean MRA x100, room-bootstrap 95% CI, paired diffs."""
+"""Aggregate per-capture JSON into arm tables: mean MRA x100, room-bootstrap 95% CI, paired diffs.
+
+Usage: agg.py out/captures heldout out/FITS.json GD_reviewed
+The fourth argument accepts GD_sealed too, or comma-separated references.
+Room comparisons match each arm's R0/R1/R2 suffix, as for S1+G1.
+"""
 import sys, json, glob, collections, numpy as np
 src, split = sys.argv[1], sys.argv[2]
 fits = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
--- /dev/null
+++ e3gd/gravity_guard.py
@@ -0,0 +1,127 @@
+"""Reader-owned gravity decision, installed only after authenticated restore."""
+import ast
+from contextlib import contextmanager
+from contextvars import ContextVar
+import hashlib
+import inspect
+from pathlib import Path
+import textwrap
+
+import numpy as np
+from student_pilot.geometry_profiles import GeometryError
+
+SEALED_VALIDATE_SHA256 = "05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a"
+UP_PLANE_MIN = .3
+
+
+def validate_up_convention(rotations):
+    """Ignore ill-conditioned roll signs; retain upright-convention refusals."""
+    R = np.asarray(rotations, float)
+    plane = np.linalg.norm(R[:, 2, :2], axis=1)
+    margin = -R[:, 2, 1]
+    if plane[0] >= UP_PLANE_MIN:
+        invalid = margin[0] <= 0
+    else:
+        usable = plane >= UP_PLANE_MIN
+        invalid = usable.any() and np.median(margin[usable] / plane[usable]) <= 0
+    if invalid:
+        raise GeometryError('reference_camera_up_opposes_gravity')
+
+
+_capture = ContextVar('gravity_guard_capture', default=None)
+_installed = False
+_recorder = None
+
+
+def identity():
+    return dict(evaluation_gravity_guard=dict(name='validate_up_convention',
+                    sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
+                sealed_gravity_guard=dict(name='GeometryContract.validate',
+                    inspect_sha256=SEALED_VALIDATE_SHA256))
+
+
+@contextmanager
+def capture(capture_set, native):
+    if not isinstance(capture_set, str) or not capture_set or not isinstance(native, str) or not native:
+        raise RuntimeError('gravity_guard_capture_identity_missing')
+    token = _capture.set((capture_set, native))
+    try:
+        yield
+    finally:
+        _capture.reset(token)
+
+
+class Recorder:
+    def __init__(self):
+        self.records = {}
+        self.contracts = {}
+
+    def record(self, sealed_refused, reviewed_refused, contract=None):
+        key = _capture.get()
+        if key is None and contract is not None:
+            bound = self.contracts.get(id(contract))
+            if bound is not None and bound[0] is contract:
+                key = bound[1]
+        if key is None:
+            raise RuntimeError('gravity_guard_capture_context_missing')
+        verdict = (bool(sealed_refused), bool(reviewed_refused))
+        if key in self.records and self.records[key] != verdict:
+            raise RuntimeError('gravity_guard_capture_verdict_changed')
+        self.records[key] = verdict
+        if contract is not None:
+            self.contracts[id(contract)] = (contract, key)
+
+    def report(self):
+        result = {}
+        for capture_set in sorted({key[0] for key in self.records}):
+            rows = {native: value for (scope, native), value in self.records.items() if scope == capture_set}
+            sealed = sorted(name for name, value in rows.items() if value[0])
+            reviewed = sorted(name for name, value in rows.items() if value[1])
+            added = sorted(set(reviewed) - set(sealed))
+            result[capture_set] = dict(captures=sorted(rows), capture_count=len(rows),
+                sealed_refused=sealed, sealed_refused_count=len(sealed),
+                reviewed_refused=reviewed, reviewed_refused_count=len(reviewed),
+                reviewed_only_refused=added, reviewed_only_refused_count=len(added))
+        return result
+
+
+def report():
+    return {} if _recorder is None else _recorder.report()
+
+
+def install(geometry_profiles_module, recorder):
+    global _installed, _recorder
+    if _installed:
+        raise RuntimeError('gravity_guard_already_installed')
+    if geometry_profiles_module.GeometryError is not GeometryError:
+        raise RuntimeError('gravity_guard_exception_class_mismatch')
+    original = geometry_profiles_module.GeometryContract.validate
+    source = inspect.getsource(original)
+    if hashlib.sha256(source.encode()).hexdigest() != SEALED_VALIDATE_SHA256:
+        raise RuntimeError('sealed_validate_mismatch')
+    body = ast.parse(textwrap.dedent(source)).body[0].body
+    terminal = ast.parse("if -R[0, 2, 1] <= 0:\n    raise GeometryError('reference_camera_up_opposes_gravity')\nreturn self").body
+    if len(body) < 2 or any(ast.dump(a) != ast.dump(b) for a, b in zip(body[-2:], terminal)):
+        raise RuntimeError('sealed_validate_terminal_mismatch')
+
+    def validate(self):
+        sealed_refused = False
+        try:
+            original(self)
+        except geometry_profiles_module.GeometryError as error:
+            if str(error) != 'reference_camera_up_opposes_gravity':
+                raise
+            sealed_refused = True
+        C = np.asarray(self.camera_to_world, float)
+        R = C[:, :3, :3]
+        try:
+            validate_up_convention(R)
+        except GeometryError:
+            recorder.record(sealed_refused, True, self)
+            raise
+        recorder.record(sealed_refused, False, self)
+        return self
+
+    geometry_profiles_module.GeometryContract.validate = validate
+    _recorder = recorder
+    _installed = True
--- /dev/null
+++ e3gd/test_gd.py
@@ -0,0 +1,233 @@
+"""CPU subset driver and regression checks; keep every artifact under e3gd/out.
+
+Run: python -B test_gd.py --gd-dir out/gd_tests/convert_fixture
+The stock harness CLI has no capture subset option. This driver calls its real
+load/features/evaluate functions on three selected captures with frozen fits.
+"""
+import argparse
+import copy
+import hashlib
+import json
+from pathlib import Path
+import subprocess
+import sys
+import time
+import types
+from unittest.mock import patch
+
+import harness as H
+
+ORIGINAL = Path('/scratch/jjyeung/orch_n30/e3_geom/work/harness')
+CANARY = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary')
+NAMES = ('arkitscenes/41048124', 'arkitscenes/41069076', 'arkitscenes/41069175')
+CODE = 'GeometryError:reference_camera_up_opposes_gravity'
+
+
+def encoded(value):
+    return (json.dumps(H.clean(value), indent=2, allow_nan=False) + '\n').encode()
+
+
+def sealed():
+    assert H.geometry_profiles.GeometryContract.validate is H.SEALED_VALIDATE
+
+
+def baseline():
+    source = (ORIGINAL / 'harness.py').read_bytes()
+    assert hashlib.sha256(source).hexdigest() == 'a38d1ad20f6c0cd7843320d0ba98dc6f43f16624c715a04a47ee51ef16c9cfa1'
+    # Redirect only the workspace assertion; __file__ binds all writes to e3gd.
+    source = source.decode().replace(str(ORIGINAL), str(H.ROOT))
+    mod = types.ModuleType('e3_original_test')
+    mod.__file__ = str(H.ROOT / 'harness.py')
+    exec(compile(source, str(ORIGINAL / 'harness.py'), 'exec'), mod.__dict__)
+    mod.OUT = H.OUT / 'baseline'
+    mod.OUT.mkdir(exist_ok=True)
+    return mod
+
+
+def check_aggregation(root):
+    captures = root / 'agg_captures'
+    captures.mkdir()
+    rows = []
+    arms = ('S4+G1', 'GD_sealed', 'GD_reviewed')
+    for split in ('train', 'heldout'):
+        for i in range(3):
+            for typ in ('object_abs_distance', 'room_size_estimation'):
+                for a in arms:
+                    for suffix in (('',) if typ == 'object_abs_distance' else ('+R0', '+R1')):
+                        pred = None if a == 'GD_sealed' and i == 0 else 10.
+                        rows.append(dict(row_id=f'{split}_{typ}_{i}', room=f'room_{i}',
+                            split=split, type=typ, arm=a+suffix, dataset='fixture', gt=10.,
+                            pred=pred, mra=H.mra(pred, 10.), refusal_code=CODE if pred is None else None))
+    H.dump(captures / 'fixture.json', dict(items=rows))
+    fits = dict(R2={a:dict(k=1., split='train') for a in arms})
+    H.dump(root / 'agg_fits.json', fits)
+    for split in ('train', 'heldout'):
+        for ref in ('GD_reviewed', 'GD_sealed', 'GD_reviewed,GD_sealed'):
+            result = subprocess.run([sys.executable, '-B', str(H.ROOT / 'agg.py'), str(captures),
+                split, str(root / 'agg_fits.json'), ref], text=True, capture_output=True, check=True)
+            (root / f'agg_{split}_{ref}.txt').write_text(result.stdout)
+            for reference in ref.split(','):
+                assert f'vs {reference}:' in result.stdout
+                for rule in ('R0', 'R1', 'R2'):
+                    assert f'vs {reference}+{rule}:' in result.stdout
+            assert 'items=3 rooms=3' in result.stdout
+    print('PASS aggregation: train/heldout, both references, comma list, R0/R1/R2, refusal denominator', flush=True)
+
+
+def edge_cases(root, capture, source):
+    empty = root / 'empty_convert'
+    empty.mkdir()
+    diag = {}
+    result = list(H.deployed_conditions(capture, empty, diag))
+    assert all(x[1] == ('FileNotFoundError:deployed_geometry_missing', None) for x in result)
+    sealed()
+    with H.np.load(source, allow_pickle=False) as z:
+        arrays = {k:z[k] for k in z.files}
+    for label, mutation, expected in (
+        ('reviewed_refused', 'rotation', CODE),
+        ('invalid_scale', 'scale', 'GeometryError:invalid_scale')):
+        c = dict(capture, canonical='synthetic/' + label)
+        dest = root / 'edge_convert' / H.digest(c['canonical'])[:16]
+        dest.mkdir(parents=True)
+        values = {k:v.copy() for k,v in arrays.items()}
+        if mutation == 'rotation':
+            values['camera_to_world'][:, :3, :3] = [[1,0,0],[0,0,-1],[0,1,0]]
+        else:
+            values['scale'] = H.np.array(-1.)
+        H.np.savez(dest / 'geometry.npz', **values)
+        diag = {}
+        result = list(H.deployed_conditions(c, dest.parent, diag))
+        assert all(x[1] == (expected, None) for x in result)
+        assert all(d['refusal'] == expected and d['sha256'] == H.sha(dest / 'geometry.npz') for d in diag.values())
+        sealed()
+    with patch.object(H, 'load_geometry', side_effect=RuntimeError('test_non_geometry_failure')):
+        try:
+            H.load_reviewed_geometry(source, capture)
+        except RuntimeError as exc:
+            assert str(exc) == 'test_non_geometry_failure'
+        else:
+            raise AssertionError('non-geometry failure swallowed')
+    sealed()
+    try:
+        H.gravity_guard.install(H.geometry_profiles, H.GRAVITY_RECORDER)
+    except RuntimeError as exc:
+        assert str(exc) == 'gravity_guard_already_installed'
+    else:
+        raise AssertionError('second install succeeded')
+    sealed()
+    print('PASS edge cases: missing file, reviewed refusal, invalid scale, finally restoration, one install', flush=True)
+
+
+def room_refusals(root, old, fits):
+    np = H.np
+    raw = np.zeros((64,9)); raw[:,6] = 1; raw[:,7:] = 1.2
+    c = dict(canonical='synthetic/room', room='synthetic/room', k1_split='train',
+             anchor_indices=list(range(0,64,2)), rows=[dict(id='synthetic_room',
+             type='room_size_estimation', gt_value=1.)])
+    u,v = np.meshgrid(np.linspace(0,1,51), np.linspace(0,1,51))
+    tower = dict(raw_pose=raw, anchor_slots=np.arange(0,64,2), grid_uv=np.linspace(0,1000,51),
+                 depth_grid=np.broadcast_to(2+.2*u+.1*v,(32,51,51)).copy())
+    geo = H.geometry_npz(c,tower,[40,48],[0,-1,0],1,'room_fixture')
+    gt = dict(depth=np.ones((32,40,48))*2, inst=np.zeros((32,40,48),int),
+              K=geo.K[0], K_frames=geo.K, c2w=geo.C, valid=np.ones(32,bool))
+    f = dict(SO=1., h_raw=1., span=1., gravity=dict(GO=[0,-1,0],G1=[0,-1,0]))
+    bf, af = copy.deepcopy(f), copy.deepcopy(f)
+    before = old.evaluate_capture(c,gt,tower,[40,48],bf,fits,None,False)
+    after = H.evaluate_capture(c,gt,tower,[40,48],af,fits,root/'empty_convert',False)
+    assert encoded(before) == encoded([r for r in after if not r['arm'].startswith('GD_')])
+    assert encoded(bf) == encoded({k:v for k,v in af.items() if not k.startswith('GD_')})
+    local_fits = copy.deepcopy(fits)
+    H.fit_r2(after,local_fits)
+    after = H.add_r2(after,local_fits)
+    for arm in ('GD_sealed','GD_reviewed'):
+        selected = [r for r in after if r['arm'].startswith(arm+'+')]
+        assert {r['arm'] for r in selected} == {arm+'+'+rule for rule in ('R0','R1','R2')}
+        assert all(r['pred'] is None and r['mra'] == 0 and
+                   r['refusal_code'] == 'FileNotFoundError:deployed_geometry_missing' for r in selected)
+        assert local_fits['R2'][arm]['n_refused'] == 1
+    H.dump(root/'ROOM_REFUSALS.json',dict(items=after,fits=local_fits))
+    sealed()
+    print('PASS synthetic room: non-GD byte parity; missing GD scores zero in R0/R1/R2; R2 train denominator', flush=True)
+
+
+def main():
+    parser = argparse.ArgumentParser(__doc__)
+    parser.add_argument('--gd-dir', type=Path, required=True)
+    args = parser.parse_args()
+    fixture = args.gd_dir.resolve()
+    assert fixture.is_relative_to(H.ROOT / 'out')
+    fixture.mkdir(parents=True, exist_ok=False)
+    root = fixture.parent
+    H.OUT = root / 'changed'
+    H.OUT.mkdir()
+    captures_out = H.OUT / 'captures'
+    captures_out.mkdir()
+    old = baseline()
+    manifest = json.loads(H.MANIFEST.read_text())
+    cs = {c['canonical']:c for c in manifest['captures'] if c['canonical'] in NAMES}
+    assert len(cs) == 3
+    fits = json.loads((H.ROOT / 'out/FITS.json').read_text())
+    fixtures = []
+    for name in NAMES:
+        c = cs[name]
+        dest = fixture / H.digest(name)[:16]
+        dest.mkdir()
+        if name == NAMES[1]:
+            H.dump(dest / 'CACHE_COMPLETE.json', dict(geometry=None,
+                geometry_refusal=dict(code=CODE.split(':',1)[1], message=CODE.split(':',1)[1]),
+                gravity_verdict=dict(sealed_refused=True, reviewed_refused=True)))
+            fixtures.append(dict(capture=name, kind='synthetic missing/refused disposition'))
+        else:
+            source = CANARY / dest.name / 'geometry.npz'
+            (dest / 'geometry.npz').write_bytes(source.read_bytes())
+            assert H.sha(dest / 'geometry.npz') == H.sha(source)
+            fixtures.append(dict(capture=name, source=str(source), sha256=H.sha(source)))
+    H.dump(root / 'FIXTURE.json', fixtures)
+    parity = []
+    start = time.monotonic()
+    for name in NAMES:
+        c = cs[name]
+        tower_dir = H.TOWERS / H.digest(name)[:16]
+        receipt = json.loads((tower_dir / 'PHASE_COMPLETE.json').read_text())
+        assert receipt['capture_sha256'] == H.digest(c)
+        gt, tower, hw = H.load_capture(c, (tower_dir, receipt), True)
+        sealed()
+        before_f = old.features(c, tower, gt, hw, 'specified')
+        before_rows = old.evaluate_capture(c, gt, tower, hw, before_f, fits, None, False)
+        sealed()
+        after_f = H.features(c, tower, gt, hw, 'specified')
+        after_rows = H.evaluate_capture(c, gt, tower, hw, after_f, fits, fixture, False)
+        sealed()
+        before = dict(diagnostics=before_f, items=before_rows)
+        after = dict(diagnostics={k:v for k,v in after_f.items() if k not in ('GD_sealed','GD_reviewed')},
+            items=[r for r in after_rows if not r['arm'].startswith('GD_')])
+        assert encoded(before) == encoded(after), name
+        H.dump(old.OUT / (name.replace('/','__') + '.json'), before)
+        H.dump(captures_out / (name.replace('/','__') + '.json'), dict(diagnostics=after_f, items=after_rows))
+        H.dump(root / (name.replace('/','__') + '.non_GD.json'), after)
+        for arm in ('GD_sealed','GD_reviewed'):
+            selected = [r for r in after_rows if r['arm'] == arm]
+            assert len(selected) == len(c['rows'])
+            if name == NAMES[1] or (name == NAMES[2] and arm == 'GD_sealed'):
+                assert after_f[arm]['refusal'] == CODE
+                assert all(r['pred'] is None and r['mra'] == 0 and r['refusal_code'] == CODE for r in selected)
+            else:
+                assert 'refusal' not in after_f[arm]
+                assert all(r['pred'] is not None for r in selected)
+        parity.append(dict(capture=name, non_GD_rows=len(before_rows), bytes=len(encoded(before)),
+                           sha256=hashlib.sha256(encoded(before)).hexdigest()))
+        print('PASS real capture byte parity + GD disposition:', name, 'non_GD_rows',len(before_rows), flush=True)
+    H.unit_tests()
+    sealed()
+    print('PASS original harness unit tests under sealed validator after GD_reviewed loads', flush=True)
+    edge_cases(root, cs[NAMES[0]], fixture / H.digest(NAMES[0])[:16] / 'geometry.npz')
+    room_refusals(root,old,fits)
+    check_aggregation(root)
+    result = dict(status='PASS', fixture=str(fixture), captures=parity,
+                  elapsed_seconds=time.monotonic()-start, guard_identity=H.gravity_guard.identity())
+    H.dump(root / 'RESULT.json', result)
+    print(json.dumps(result), flush=True)
+
+
+if __name__ == '__main__':
+    main()
```

READY


## Fixes after e3gd_review

The three requested fixes are implemented and validated. The complete regression suite exited 0 in 162.2 seconds on `trinity-1-18`. All 55 non-GD rows across the three captures remain byte-identical to the original harness. The full 296-capture production evaluation has not been run.

**Diffs and runtime behavior**

[PATCH2.diff](PATCH2.diff) is the unified diff against the reviewed e3gd files. It changes `harness.py` (+106/-34 lines), `run.sh` (+3/-3), and `test_gd.py` (+156/-11). The exact input files are retained in `e3gd2_before/`. The full patch follows the commands below.

- GD resolves only `ROOT/<digest(canonical)[:16]>/CACHE_COMPLETE.json`. Alternate geometry layouts are ignored. The validator checks the manifest capture digest, K1 guard identity, source map, phase, boolean verdicts, disposition, exact file membership, resolved pin paths, and every pinned file's SHA-256. A successful reviewed load also checks the recorded gravity verdict. Missing receipts, missing pinned files, wrong captures, conflicting dispositions, and mismatched pins raise configuration errors.
- A valid refused receipt supplies the refusal code for both arms, even when alternate or unadmitted geometry exists. The refused evidence is hashed but never loaded. This receipt precedence follows the requested behavior; K1's own checker instead rejects a refusal directory containing `geometry.npz`.
- Proposal files remain excluded from scoring. The audit hook permits an opaque, context-scoped SHA-256 pass for receipt validation; ordinary `candidates.json` reads still raise `PermissionError`. The source-map checker reproduces the frozen native kit's `bindings.source_identity()` paths without importing its proposal backend. Its result matches the real canary receipts.
- Reviewed loading binds the unchanged loader functions to a private `GeometryContract` subclass. The byte-identical guard installer authenticates and patches only that subclass. The shared sealed contract is never patched. The two-thread barrier test pauses reviewed validation while another thread calls the plain sealed loader; the latter raises `GeometryError:reference_camera_up_opposes_gravity`, and the reviewed load succeeds. Exception isolation, one-time installation, and reviewed-contract revalidation also pass.
- All configured cache and temporary destinations in `run.sh` resolve under `e3gd/out`. The test executes the launcher's setup and inspects the resulting environment. The interpreter, disabled CUDA, and eight-thread settings remain unchanged.

The fixtures use real canary geometry and complete synthetic receipts with opaque dummy proposal/evidence files. The bypass capture, `arkitscenes/41069076`, has both a valid alternate geometry and an unadmitted digest-path geometry. Its synthetic refused receipt produces these saved scored rows:

```json
[
  {
    "arm": "GD_sealed",
    "pred": null,
    "mra": 0.0,
    "refusal_code": "GeometryError:reference_camera_up_opposes_gravity"
  },
  {
    "arm": "GD_reviewed",
    "pred": null,
    "mra": 0.0,
    "refusal_code": "GeometryError:reference_camera_up_opposes_gravity"
  }
]
```

Pin-mismatch assertions catch `ValueError:Cache file hash mismatch: geometry.npz`, and analogous errors for both proposal files. Additional assertions cover wrong pin paths, capture identity, source and guard identity, receipt disposition, actual gravity verdict, missing receipts, and missing admitted geometry.

**Evidence**

[Test output](../e3gd/out/gd2_tests/test.log), [machine-readable result](../e3gd/out/gd2_tests/RESULT.json), [static checks](../e3gd/out/gd2_tests/STATIC_CHECKS.json), and [fixture metadata](../e3gd/out/gd2_tests/FIXTURE.json) are retained under `e3gd/out/gd2_tests`.

| Capture | Non-GD rows | Serialized bytes | Identical SHA-256 |
|---|---:|---:|---|
| arkitscenes/41048124 | 11 | 5956 | `32c2240e1eb485250739d5b77b70c352962ba4a017087976501317e827771af2` |
| arkitscenes/41069076 | 11 | 5955 | `492d72f98287cd2b88dd471f429531a81ded52713003df2199d93c1b66b75bfe` |
| arkitscenes/41069175 | 33 | 14738 | `ba2dea52464c6ecf8e3c7516f78a53e71a4ebff8b81f71d89bf443f5756dbb88` |

The baseline changes only its workspace binding and suppresses its duplicate audit-hook registration in memory; the current harness audit hook remains active. Its fitting, geometry, scoring, and output functions execute unchanged. The report compares serialized diagnostics and scored rows after removing only the added GD arms.

The original harness unit tests pass after reviewed loads. The synthetic room test preserves non-GD byte parity and verifies zero-scored receipt refusals in R0/R1/R2, including train-fit denominators. Aggregation checks cover train and heldout, both GD references, comma-separated references, matching room suffixes, refusal denominators, and the three real-capture outputs. `agg.py` has the original executable AST. `room_rules.py`, `r2fit.py`, both shard scripts, `finalize.py`, and `out/FITS.json` remain byte-identical to the original copy. The vendored guard remains SHA-256 `b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79`. Shell syntax and Python AST checks pass.

Configured destinations, asserted by the test:

```json
{
  "XDG_CACHE_HOME": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/.cache",
  "HF_HOME": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/.cache/hf",
  "TRITON_CACHE_DIR": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/.cache/triton",
  "MPLCONFIGDIR": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/.cache/matplotlib",
  "TMPDIR": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/tmp"
}
```

Executed command, exit 0:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
mkdir -p out/gd2_tests
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/out/.cache" HF_HOME="$PWD/out/.cache/hf"
export TRITON_CACHE_DIR="$PWD/out/.cache/triton" MPLCONFIGDIR="$PWD/out/.cache/matplotlib" TMPDIR="$PWD/out/tmp"
/scratch/jjyeung/envs/planner_local_v1/bin/python -B test_gd.py --gd-dir out/gd2_tests/convert_fixture > out/gd2_tests/test.log 2>&1
```

A rerun needs a fresh fixture directory; existing evidence is retained. Test output:

```text
PASS real capture byte parity + GD disposition: arkitscenes/41048124 non_GD_rows 11
PASS real capture byte parity + GD disposition: arkitscenes/41069076 non_GD_rows 11
PASS real capture byte parity + GD disposition: arkitscenes/41069175 non_GD_rows 33
PASS original harness unit tests under sealed validator after GD_reviewed loads
PASS edge cases: missing receipt raises; reviewed refusal, invalid scale, exception isolation, one install
PASS receipt binding: bypass refused in both arms; missing receipt/file, capture, all file pins, source, guard, disposition errors raise
PASS two-thread barrier: concurrent plain sealed load raises GeometryError:reference_camera_up_opposes_gravity; reviewed load succeeds
PASS run.sh: every configured cache/temp destination resolves under out; interpreter and eight-thread settings unchanged
PASS synthetic room: non-GD byte parity; receipt refusal scores zero in R0/R1/R2; R2 train denominator
PASS aggregation: train/heldout, both references, comma list, R0/R1/R2, refusal denominator
PASS real-capture aggregation: train/heldout and both GD references
{"status": "PASS", "fixture": "/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/gd2_tests/convert_fixture", "captures": [{"capture": "arkitscenes/41048124", "non_GD_rows": 11, "bytes": 5956, "sha256": "32c2240e1eb485250739d5b77b70c352962ba4a017087976501317e827771af2"}, {"capture": "arkitscenes/41069076", "non_GD_rows": 11, "bytes": 5955, "sha256": "492d72f98287cd2b88dd471f429531a81ded52713003df2199d93c1b66b75bfe"}, {"capture": "arkitscenes/41069175", "non_GD_rows": 33, "bytes": 14738, "sha256": "ba2dea52464c6ecf8e3c7516f78a53e71a4ebff8b81f71d89bf443f5756dbb88"}], "elapsed_seconds": 162.22252272604965, "guard_identity": {"evaluation_gravity_guard": {"name": "validate_up_convention", "sha256": "b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79"}, "sealed_gravity_guard": {"name": "GeometryContract.validate", "inspect_sha256": "05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a"}}}
```

**Production command**

After approval for heavy IO, substitute the completed, receipt-bound K1 convert root for `<convert root>`:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
bash run.sh run --approved-heavy-io --gd-dir '<convert root>' > out/production.log 2>&1
```

The interpreter is `/scratch/jjyeung/envs/planner_local_v1/bin/python`. Plan roughly three hours for the full dataset; this is the source E3 estimate, not a measured full-run time for this build. The command refits train-only constants and writes production outputs under `out`.

Run both reference comparisons on both splits for the C-rule:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/e3gd
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/out/.cache" HF_HOME="$PWD/out/.cache/hf"
export TRITON_CACHE_DIR="$PWD/out/.cache/triton" MPLCONFIGDIR="$PWD/out/.cache/matplotlib" TMPDIR="$PWD/out/tmp"
/scratch/jjyeung/envs/planner_local_v1/bin/python -B agg.py out/captures train out/FITS.json GD_reviewed > out/AGG_train_GD_reviewed.txt
/scratch/jjyeung/envs/planner_local_v1/bin/python -B agg.py out/captures heldout out/FITS.json GD_reviewed > out/AGG_heldout_GD_reviewed.txt
/scratch/jjyeung/envs/planner_local_v1/bin/python -B agg.py out/captures train out/FITS.json GD_sealed > out/AGG_train_GD_sealed.txt
/scratch/jjyeung/envs/planner_local_v1/bin/python -B agg.py out/captures heldout out/FITS.json GD_sealed > out/AGG_heldout_GD_sealed.txt
```

The requested section title and diff comparisons are retained to document the review fixes. This append-only section states the current behavior. No Git, SSH, network, GPU, process termination, deletion, or write to the original harness was used.

**Unified diff against the reviewed files**

```diff
--- e3gd_review/harness.py
+++ e3gd/harness.py
@@ -16,6 +16,9 @@
 import traceback
 import warnings
 from collections import defaultdict
+from contextvars import ContextVar
+from functools import lru_cache
+from types import FunctionType, SimpleNamespace
 
 ROOT = Path(__file__).resolve().parent
 assert ROOT == Path('/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd')
@@ -24,13 +27,15 @@
 TOWERS = Path('/scratch/jjyeung/k1/run_tower_sam_2')
 CONVERTER = Path('/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py')
 IMPORTED = set()
+_PIN_HASH_PATH = ContextVar('gd_pin_hash_path', default=None)
 
 
 def audit(event, args):
     if event != 'open' or not isinstance(args[0], (str, bytes)):
         return
     p = Path(os.fsdecode(args[0])).absolute()
-    if p.name == 'candidates.json':
+    if p.name == 'candidates.json' and not (
+            _PIN_HASH_PATH.get() == p.resolve() and args[1] == 'r'):
         raise PermissionError('Grounding kill-test boundary: candidates.json is forbidden')
     mode, flags = args[1:3]
     writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
@@ -68,51 +73,114 @@
 SCALES = ('S1', 'S2', 'S3', 'S4', 'SO')
 GRAVITIES = ('GO', 'G1')
 SEALED_VALIDATE = geometry_profiles.GeometryContract.validate
-REVIEWED_VALIDATE = None
 GRAVITY_RECORDER = gravity_guard.Recorder()
 
 
+def reviewed_loader():
+    """Bind the unchanged loaders to a private contract; never patch shared classes."""
+    class ReviewedContract(geometry_profiles.GeometryContract):
+        pass
+
+    gravity_guard.install(SimpleNamespace(GeometryContract=ReviewedContract,
+        GeometryError=geometry_profiles.GeometryError), GRAVITY_RECORDER)
+
+    def bind(fn, **replacements):
+        return FunctionType(fn.__code__, dict(fn.__globals__, **replacements),
+                            fn.__name__, fn.__defaults__, fn.__closure__)
+
+    return bind(load_geometry,
+        legacy_from_heads=bind(geometry_profiles.legacy_from_heads, GeometryContract=ReviewedContract),
+        scaled_from_heads=bind(geometry_profiles.scaled_from_heads, GeometryContract=ReviewedContract))
+
+
+REVIEWED_LOAD_GEOMETRY = reviewed_loader()
+
+
 def load_reviewed_geometry(path, c):
-    """Use the reviewed validator only for this serial deployed-geometry load."""
-    global REVIEWED_VALIDATE
-    previous = geometry_profiles.GeometryContract.validate
-    assert previous is SEALED_VALIDATE, 'reviewed validator leaked outside GD_reviewed'
+    with gravity_guard.capture('E3_GD_reviewed', c['canonical']):
+        return REVIEWED_LOAD_GEOMETRY(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
+
+
+@lru_cache(maxsize=1)
+def k1_source_identity():
+    """K1 bindings.source_identity paths, without importing its proposal backend."""
+    native = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit')
+    paths = [CONVERTER, CONVERTER.with_name('perception.py'),
+             native / 'vendor_sam/vendor/sam_backend.py',
+             native / 'vendor_sam/variantlib.py', native / 'vendor_sam/variant_cache.py']
+    paths += [TREE / 'student_pilot' / n for n in (
+        'tower_read.py', 'tower_scale.py', 'candidate_policy.py', 'routed_features.py',
+        'live_instances314.py', 'carrier_c1_decode.py')]
+    paths += [p for p in native.glob('*.py') if not p.name.startswith('test_')]
+    return {str(p): sha(p) for p in paths}
+
+
+def receipt_pin_sha(path):
+    """Hash opaque cache bytes; never expose proposal content to scoring."""
+    token = _PIN_HASH_PATH.set(Path(path).resolve())
     try:
-        if REVIEWED_VALIDATE is None:
-            gravity_guard.install(geometry_profiles, GRAVITY_RECORDER)
-            REVIEWED_VALIDATE = geometry_profiles.GeometryContract.validate
-        geometry_profiles.GeometryContract.validate = REVIEWED_VALIDATE
-        with gravity_guard.capture('E3_GD_reviewed', c['canonical']):
-            return load_geometry(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
+        return sha(path)
     finally:
-        geometry_profiles.GeometryContract.validate = previous
+        _PIN_HASH_PATH.reset(token)
+
+
+def deployed_receipt(c, gd_dir):
+    dest = (gd_dir / digest(c['canonical'])[:16]).resolve()
+    receipt_path = dest / 'CACHE_COMPLETE.json'
+    if not dest.is_relative_to('/scratch'):
+        raise ValueError('Stage GD inputs onto local disk')
+    receipt = json.loads(receipt_path.read_text())
+    if receipt.get('capture_sha256') != digest(c):
+        raise ValueError('Cache capture differs')
+    refusal = receipt.get('geometry_refusal')
+    votes = receipt.get('gravity_verdict', {})
+    if (receipt.get('gravity_guard') != gravity_guard.identity()
+            or set(votes) != {'sealed_refused', 'reviewed_refused'}
+            or any(type(v) is not bool for v in votes.values())
+            or receipt.get('sources') != k1_source_identity()
+            or receipt.get('phase') != 'unselected_cache_no_responses'):
+        raise ValueError('Cache guard/source binding differs')
+    names = {'candidates.json', 'parity_raw.jsonl'}
+    if refusal or receipt.get('geometry') is None:
+        code = 'reference_camera_up_opposes_gravity'
+        if (refusal != dict(code=code, message=code) or receipt.get('geometry') is not None
+                or not votes['reviewed_refused']):
+            raise ValueError('Cache geometry refusal differs')
+        # The receipt remains authoritative even if an unadmitted file exists.
+        names.add('REFUSED_GEOMETRY.npz')
+    else:
+        if votes['reviewed_refused'] or not receipt.get('geometry'):
+            raise ValueError('Cache geometry verdict differs')
+        names.add('geometry.npz')
+    pins = receipt.get('files', {})
+    if set(pins) != names or any(
+            Path(pin['path']).resolve() != (dest / name).resolve()
+            for name, pin in pins.items()):
+        raise ValueError('Cache file binding differs')
+    for name, pin in pins.items():
+        path = Path(pin['path']).resolve()
+        if not path.is_relative_to('/scratch'):
+            raise ValueError('Stage GD inputs onto local disk')
+        if receipt_pin_sha(path) != pin['sha256']:
+            raise ValueError('Cache file hash mismatch: ' + name)
+    return dest, receipt_path, receipt
 
 
 def deployed_conditions(c, gd_dir, f):
-    options = [gd_dir / c['canonical'] / 'geometry.npz',
-               gd_dir / (c['canonical'].replace('/', '__') + '.npz'),
-               gd_dir / digest(c['canonical'])[:16] / 'geometry.npz']
-    paths = [p for p in options if p.is_file()]
-    if len(paths) > 1:
-        raise ValueError('GD requires exactly one deployed geometry file for ' + c['canonical'])
-    if not paths:
-        reason = 'FileNotFoundError:deployed_geometry_missing'
-        detail = dict(path=str(options[-1]), refusal=reason)
-        receipt_path = options[-1].parent / 'CACHE_COMPLETE.json'
-        if receipt_path.is_file():
-            receipt = json.loads(receipt_path.read_text())
-            refusal = receipt.get('geometry_refusal')
-            if isinstance(refusal, dict) and refusal.get('code'):
-                reason = 'GeometryError:' + refusal['code']
-                detail.update(refusal=reason, geometry_refusal=refusal,
-                              gravity_verdict=receipt.get('gravity_verdict'),
-                              cache_receipt=str(receipt_path))
+    dest, receipt_path, receipt = deployed_receipt(c, gd_dir)
+    path = dest / 'geometry.npz'
+    detail = dict(path=str(path), cache_receipt=str(receipt_path),
+                  capture_sha256=receipt['capture_sha256'],
+                  gravity_verdict=receipt['gravity_verdict'])
+    if receipt.get('geometry_refusal'):
+        refusal = receipt['geometry_refusal']
+        reason = 'GeometryError:' + refusal['code']
+        detail.update(refusal=reason, geometry_refusal=refusal)
         for arm in ('GD_sealed', 'GD_reviewed'):
             f[arm] = dict(detail)
             yield arm, (reason, None), 'predicted'
         return
-    path = paths[0]
-    pin = dict(path=str(path), sha256=sha(path))
+    pin = dict(detail, sha256=receipt['files']['geometry.npz']['sha256'])
     for arm in ('GD_sealed', 'GD_reviewed'):
         f[arm] = dict(pin)
         try:
@@ -124,6 +192,10 @@
             f[arm]['refusal'] = reason
             yield arm, (reason, None), 'predicted'
         else:
+            if arm == 'GD_reviewed':
+                sealed, reviewed = GRAVITY_RECORDER.records[('E3_GD_reviewed', c['canonical'])]
+                if dict(sealed_refused=sealed, reviewed_refused=reviewed) != receipt['gravity_verdict']:
+                    raise ValueError('Cache gravity verdict differs')
             yield arm, geo, 'predicted'
 
 
@@ -641,7 +713,7 @@
                 converter=dict(path=str(CONVERTER), sha256=sha(CONVERTER)),
                 harness_sha256={p.name:sha(p) for p in [ROOT / 'harness.py', ROOT / 'room_rules.py', ROOT / 'run.sh']},
                 elapsed_seconds=time.monotonic() - start, timings=dict(TIMINGS),
-                forbidden_data_access='candidates.json blocked by Python audit hook', **(extra or {}))
+                forbidden_data_access='candidates.json blocked except opaque GD receipt pin hashing', **(extra or {}))
 
 
 def unit_tests():
--- e3gd_review/run.sh
+++ e3gd/run.sh
@@ -4,7 +4,7 @@
 export CUDA_VISIBLE_DEVICES=''
 export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
 export PYTHONDONTWRITEBYTECODE=1
-export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton"
-export MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
-mkdir -p "$TMPDIR" out
+export XDG_CACHE_HOME="$PWD/out/.cache" HF_HOME="$PWD/out/.cache/hf" TRITON_CACHE_DIR="$PWD/out/.cache/triton"
+export MPLCONFIGDIR="$PWD/out/.cache/matplotlib" TMPDIR="$PWD/out/tmp"
+mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$HF_HOME" "$TRITON_CACHE_DIR" "$MPLCONFIGDIR"
 exec /scratch/jjyeung/envs/planner_local_v1/bin/python -B harness.py "$@"
--- e3gd_review/test_gd.py
+++ e3gd/test_gd.py
@@ -5,6 +5,7 @@
 load/features/evaluate functions on three selected captures with frozen fits.
 """
 import argparse
+from concurrent.futures import ThreadPoolExecutor
 import copy
 import hashlib
 import json
@@ -13,6 +14,7 @@
 import sys
 import time
 import types
+from threading import Barrier
 from unittest.mock import patch
 
 import harness as H
@@ -34,14 +36,138 @@
 def baseline():
     source = (ORIGINAL / 'harness.py').read_bytes()
     assert hashlib.sha256(source).hexdigest() == 'a38d1ad20f6c0cd7843320d0ba98dc6f43f16624c715a04a47ee51ef16c9cfa1'
-    # Redirect only the workspace assertion; __file__ binds all writes to e3gd.
+    # Redirect writes and retain the active harness audit hook, not a duplicate.
     source = source.decode().replace(str(ORIGINAL), str(H.ROOT))
+    source = source.replace('sys.addaudithook(audit)', '# The current harness audit hook is active.')
     mod = types.ModuleType('e3_original_test')
     mod.__file__ = str(H.ROOT / 'harness.py')
     exec(compile(source, str(ORIGINAL / 'harness.py'), 'exec'), mod.__dict__)
     mod.OUT = H.OUT / 'baseline'
     mod.OUT.mkdir(exist_ok=True)
     return mod
+
+
+def cache_receipt(dest, capture, refused=False):
+    """Build a complete K1-shaped fixture; proposal payloads are opaque dummies."""
+    dest.mkdir(parents=True, exist_ok=True)
+    payload = dest / 'opaque_fixture'
+    payload.write_bytes(b'{}\n')
+    candidate = dest / 'candidates.json'
+    if not candidate.exists():
+        candidate.symlink_to(payload)
+    (dest / 'parity_raw.jsonl').write_bytes(b'{}\n')
+    name = 'REFUSED_GEOMETRY.npz' if refused else 'geometry.npz'
+    if refused:
+        (dest / name).write_bytes(b'opaque refusal evidence; never loaded\n')
+    code = CODE.split(':', 1)[1]
+    receipt = dict(capture_sha256=H.digest(capture),
+        geometry=None if refused else dict(depth_scale_count=1),
+        gravity_guard=H.gravity_guard.identity(), sources=H.k1_source_identity(),
+        phase='unselected_cache_no_responses',
+        gravity_verdict=dict(sealed_refused=refused or capture['canonical'] == NAMES[2],
+                             reviewed_refused=refused),
+        files={n:dict(path=str(dest / n), sha256=H.receipt_pin_sha(dest / n))
+               for n in (name, 'candidates.json', 'parity_raw.jsonl')})
+    if refused:
+        receipt['geometry_refusal'] = dict(code=code, message=code)
+    H.dump(dest / 'CACHE_COMPLETE.json', receipt)
+    return receipt
+
+
+def raises(expected, message, fn):
+    try:
+        fn()
+    except expected as exc:
+        assert message in str(exc), str(exc)
+    else:
+        raise AssertionError('expected ' + expected.__name__ + ': ' + message)
+
+
+def receipt_checks(root, capture, source):
+    c = dict(capture, canonical='synthetic/bypass')
+    gd = root / 'bypass_convert'
+    dest = gd / H.digest(c['canonical'])[:16]
+    cache_receipt(dest, c, refused=True)
+    # Reproduce both alternate layouts and an unadmitted digest-path file.
+    alternate = gd / c['canonical'] / 'geometry.npz'
+    alternate.parent.mkdir(parents=True)
+    alternate.write_bytes(source.read_bytes())
+    (gd / (c['canonical'].replace('/', '__') + '.npz')).write_bytes(source.read_bytes())
+    (dest / 'geometry.npz').write_bytes(source.read_bytes())
+    diag = {}
+    with patch.object(H, 'load_geometry', side_effect=AssertionError('refusal bypass')), \
+         patch.object(H, 'load_reviewed_geometry', side_effect=AssertionError('refusal bypass')):
+        result = list(H.deployed_conditions(c, gd, diag))
+    assert len(result) == 2 and all(v == (CODE, None) for _, v, _ in result)
+    assert all(d['refusal'] == CODE for d in diag.values())
+
+    good = cache_receipt(dest, c)
+    def rejected(edit, message):
+        bad = copy.deepcopy(good)
+        edit(bad)
+        H.dump(dest / 'CACHE_COMPLETE.json', bad)
+        raises(ValueError, message, lambda: list(H.deployed_conditions(c, gd, {})))
+    rejected(lambda r:r.update(capture_sha256='0'*64), 'Cache capture differs')
+    rejected(lambda r:r['files']['geometry.npz'].update(sha256='0'*64), 'Cache file hash mismatch: geometry.npz')
+    rejected(lambda r:r['files']['parity_raw.jsonl'].update(sha256='0'*64), 'Cache file hash mismatch: parity_raw.jsonl')
+    rejected(lambda r:r['files']['candidates.json'].update(sha256='0'*64), 'Cache file hash mismatch: candidates.json')
+    rejected(lambda r:r['files']['geometry.npz'].update(path=str(alternate)), 'Cache file binding differs')
+    rejected(lambda r:r.update(sources={}), 'Cache guard/source binding differs')
+    rejected(lambda r:r.update(gravity_guard={}), 'Cache guard/source binding differs')
+    rejected(lambda r:r['gravity_verdict'].update(reviewed_refused=True), 'Cache geometry verdict differs')
+    rejected(lambda r:r['gravity_verdict'].update(sealed_refused=True), 'Cache gravity verdict differs')
+    rejected(lambda r:r.update(geometry=None), 'Cache geometry refusal differs')
+    H.dump(dest / 'CACHE_COMPLETE.json', good)
+    # The admitted digest path wins even when both alternate forms exist.
+    assert all(not isinstance(v, tuple) for _, v, _ in H.deployed_conditions(c, gd, {}))
+    (dest / 'geometry.npz').rename(dest / 'geometry_missing.npz')
+    raises(FileNotFoundError, 'geometry.npz', lambda:list(H.deployed_conditions(c, gd, {})))
+    # A raw proposal read remains forbidden after hashing or an exception.
+    raises(PermissionError, 'candidates.json', lambda:(dest/'candidates.json').read_text())
+    print('PASS receipt binding: bypass refused in both arms; missing receipt/file, capture, all file pins, source, guard, disposition errors raise', flush=True)
+
+
+def thread_isolation(capture, source):
+    entered, finished = Barrier(2), Barrier(2)
+    validate = H.gravity_guard.validate_up_convention
+    def paused(rotations):
+        entered.wait(timeout=10)
+        finished.wait(timeout=10)
+        return validate(rotations)
+    def sealed_worker():
+        entered.wait(timeout=10)
+        try:
+            raises(H.geometry_profiles.GeometryError, 'reference_camera_up_opposes_gravity',
+                lambda:H.load_geometry(source,H.FrameMap(tuple(capture['anchor_indices'])),'tower_scaled'))
+            sealed()
+        finally:
+            finished.wait(timeout=10)
+    with patch.object(H.gravity_guard, 'validate_up_convention', paused):
+        with ThreadPoolExecutor(max_workers=2) as pool:
+            reviewed = pool.submit(H.load_reviewed_geometry, source, capture)
+            other = pool.submit(sealed_worker)
+            other.result(timeout=20)
+            geo = reviewed.result(timeout=20)
+    geo.contract.validate()
+    sealed()
+    print('PASS two-thread barrier: concurrent plain sealed load raises GeometryError:reference_camera_up_opposes_gravity; reviewed load succeeds', flush=True)
+
+
+def run_destinations(root):
+    source = (H.ROOT / 'run.sh').read_text()
+    prefix, command = source.rsplit('\nexec ', 1)
+    assert command.strip() == '/scratch/jjyeung/envs/planner_local_v1/bin/python -B harness.py "$@"'
+    keys = ('XDG_CACHE_HOME', 'HF_HOME', 'TRITON_CACHE_DIR', 'MPLCONFIGDIR', 'TMPDIR')
+    probe = '\n' + sys.executable + " -B - <<'PY'\nimport os,json\nprint(json.dumps(dict(os.environ)))\nPY\n"
+    env = json.loads(subprocess.run(['bash', '-c', prefix+probe], check=True,
+                                   text=True, capture_output=True).stdout)
+    for key in keys:
+        assert Path(env[key]).resolve().is_relative_to(H.ROOT / 'out'), (key, env[key])
+    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
+        assert env[key] == '8'
+    assert env['CUDA_VISIBLE_DEVICES'] == ''
+    H.dump(root / 'RUN_DESTINATIONS.json', {k:env[k] for k in keys})
+    print('PASS run.sh: every configured cache/temp destination resolves under out; interpreter and eight-thread settings unchanged', flush=True)
 
 
 def check_aggregation(root):
@@ -78,8 +204,7 @@
     empty = root / 'empty_convert'
     empty.mkdir()
     diag = {}
-    result = list(H.deployed_conditions(capture, empty, diag))
-    assert all(x[1] == ('FileNotFoundError:deployed_geometry_missing', None) for x in result)
+    raises(FileNotFoundError, 'CACHE_COMPLETE.json', lambda:list(H.deployed_conditions(capture, empty, diag)))
     sealed()
     with H.np.load(source, allow_pickle=False) as z:
         arrays = {k:z[k] for k in z.files}
@@ -95,12 +220,13 @@
         else:
             values['scale'] = H.np.array(-1.)
         H.np.savez(dest / 'geometry.npz', **values)
+        cache_receipt(dest, c)
         diag = {}
         result = list(H.deployed_conditions(c, dest.parent, diag))
         assert all(x[1] == (expected, None) for x in result)
         assert all(d['refusal'] == expected and d['sha256'] == H.sha(dest / 'geometry.npz') for d in diag.values())
         sealed()
-    with patch.object(H, 'load_geometry', side_effect=RuntimeError('test_non_geometry_failure')):
+    with patch.object(H, 'REVIEWED_LOAD_GEOMETRY', side_effect=RuntimeError('test_non_geometry_failure')):
         try:
             H.load_reviewed_geometry(source, capture)
         except RuntimeError as exc:
@@ -115,7 +241,7 @@
     else:
         raise AssertionError('second install succeeded')
     sealed()
-    print('PASS edge cases: missing file, reviewed refusal, invalid scale, finally restoration, one install', flush=True)
+    print('PASS edge cases: missing receipt raises; reviewed refusal, invalid scale, exception isolation, one install', flush=True)
 
 
 def room_refusals(root, old, fits):
@@ -132,6 +258,7 @@
               K=geo.K[0], K_frames=geo.K, c2w=geo.C, valid=np.ones(32,bool))
     f = dict(SO=1., h_raw=1., span=1., gravity=dict(GO=[0,-1,0],G1=[0,-1,0]))
     bf, af = copy.deepcopy(f), copy.deepcopy(f)
+    cache_receipt(root/'empty_convert'/H.digest(c['canonical'])[:16], c, refused=True)
     before = old.evaluate_capture(c,gt,tower,[40,48],bf,fits,None,False)
     after = H.evaluate_capture(c,gt,tower,[40,48],af,fits,root/'empty_convert',False)
     assert encoded(before) == encoded([r for r in after if not r['arm'].startswith('GD_')])
@@ -143,11 +270,11 @@
         selected = [r for r in after if r['arm'].startswith(arm+'+')]
         assert {r['arm'] for r in selected} == {arm+'+'+rule for rule in ('R0','R1','R2')}
         assert all(r['pred'] is None and r['mra'] == 0 and
-                   r['refusal_code'] == 'FileNotFoundError:deployed_geometry_missing' for r in selected)
+                   r['refusal_code'] == CODE for r in selected)
         assert local_fits['R2'][arm]['n_refused'] == 1
     H.dump(root/'ROOM_REFUSALS.json',dict(items=after,fits=local_fits))
     sealed()
-    print('PASS synthetic room: non-GD byte parity; missing GD scores zero in R0/R1/R2; R2 train denominator', flush=True)
+    print('PASS synthetic room: non-GD byte parity; receipt refusal scores zero in R0/R1/R2; R2 train denominator', flush=True)
 
 
 def main():
@@ -173,14 +300,22 @@
         dest = fixture / H.digest(name)[:16]
         dest.mkdir()
         if name == NAMES[1]:
-            H.dump(dest / 'CACHE_COMPLETE.json', dict(geometry=None,
-                geometry_refusal=dict(code=CODE.split(':',1)[1], message=CODE.split(':',1)[1]),
-                gravity_verdict=dict(sealed_refused=True, reviewed_refused=True)))
-            fixtures.append(dict(capture=name, kind='synthetic missing/refused disposition'))
+            cache_receipt(dest, c, refused=True)
+            # A complete refusal must score zero despite valid bypass geometry.
+            source = CANARY / dest.name / 'geometry.npz'
+            alternate = fixture / name / 'geometry.npz'
+            alternate.parent.mkdir(parents=True)
+            alternate.write_bytes(source.read_bytes())
+            (dest / 'geometry.npz').write_bytes(source.read_bytes())
+            fixtures.append(dict(capture=name, kind='synthetic refusal with alternate and unadmitted geometry'))
         else:
             source = CANARY / dest.name / 'geometry.npz'
             (dest / 'geometry.npz').write_bytes(source.read_bytes())
             assert H.sha(dest / 'geometry.npz') == H.sha(source)
+            original_receipt = json.loads((source.parent/'CACHE_COMPLETE.json').read_text())
+            assert original_receipt['sources'] == H.k1_source_identity()
+            assert original_receipt['capture_sha256'] == H.digest(c)
+            cache_receipt(dest, c)
             fixtures.append(dict(capture=name, source=str(source), sha256=H.sha(source)))
     H.dump(root / 'FIXTURE.json', fixtures)
     parity = []
@@ -221,8 +356,18 @@
     sealed()
     print('PASS original harness unit tests under sealed validator after GD_reviewed loads', flush=True)
     edge_cases(root, cs[NAMES[0]], fixture / H.digest(NAMES[0])[:16] / 'geometry.npz')
+    receipt_checks(root, cs[NAMES[0]], fixture / H.digest(NAMES[0])[:16] / 'geometry.npz')
+    thread_isolation(cs[NAMES[2]], fixture / H.digest(NAMES[2])[:16] / 'geometry.npz')
+    run_destinations(root)
     room_refusals(root,old,fits)
     check_aggregation(root)
+    for split in ('train', 'heldout'):
+        for ref in ('GD_reviewed', 'GD_sealed'):
+            result = subprocess.run([sys.executable, '-B', 'agg.py', str(captures_out),
+                split, str(H.ROOT/'out/FITS.json'), ref], text=True, capture_output=True, check=True)
+            (root/f'real_agg_{split}_{ref}.txt').write_text(result.stdout)
+            assert f'vs {ref}:' in result.stdout
+    print('PASS real-capture aggregation: train/heldout and both GD references', flush=True)
     result = dict(status='PASS', fixture=str(fixture), captures=parity,
                   elapsed_seconds=time.monotonic()-start, guard_identity=H.gravity_guard.identity())
     H.dump(root / 'RESULT.json', result)
```

READY
