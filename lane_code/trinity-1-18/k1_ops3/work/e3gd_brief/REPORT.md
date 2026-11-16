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
