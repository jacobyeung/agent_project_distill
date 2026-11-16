# ScanNet v2 batch-2 rematerialization refusals — REQ-20260917-232

Read-only diagnostic. Lane: `distillation_orchestrator_20260918/codex_materialize_batch2`;
run log: `rematerialization_req232_scannet_v2_batch2_20260918`. Host trinity-3-18, 79 attempted,
0 completed, 79 failed. All 79 scenes were "eligible" on prerequisite check (`PREREQS.md`: no
missing inputs) before the sealed v2 preparer ran and refused every one of them.

## 1. Refused scenes: id, class, message, question count

79 scenes / 4,006 questions total. 57 scenes / 3,064 questions refused for camera-transform
("finite proper rigid transform"); 22 scenes / 942 questions refused for raw/VSI ordinal
correlation. Question counts from `SCENES.md`. Correlation messages with more than one failing
slot are shown as the first slot plus a count of additional failing slots (full per-slot values
are in `PREP_scannet.md` and the per-scene log named there).

| Scene | Class | Message | Questions |
|---|---|---|---:|
| scene0001_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 7 |
| scene0008_00 | correlation | slot 1: 0.9862423645742693 | 41 |
| scene0012_02 | correlation | slot 1: 0.9839185333083966 (+4 more slots < 0.99) | 4 |
| scene0013_00 | correlation | slot 1: 0.9802598895490291 (+22 more slots < 0.99) | 3 |
| scene0020_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 31 |
| scene0026_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 6 |
| scene0034_00 | correlation | slot 1: 0.9875372761954456 | 8 |
| scene0034_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 8 |
| scene0035_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 62 |
| scene0037_00 | correlation | slot 1: 0.9897471447176496 | 4 |
| scene0038_02 | correlation | slot 1: 0.9803049639236117 (+7 more slots < 0.99) | 4 |
| scene0041_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 19 |
| scene0045_00 | correlation | slot 1: 0.9782130934705086 (+22 more slots < 0.99) | 6 |
| scene0051_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 208 |
| scene0055_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 95 |
| scene0067_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 14 |
| scene0073_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 54 |
| scene0078_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 206 |
| scene0080_01 | correlation | slot 1: 0.9889395909085594 (+3 more slots < 0.99) | 16 |
| scene0080_02 | correlation | slot 1: 0.9875858837654256 (+3 more slots < 0.99) | 47 |
| scene0112_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 9 |
| scene0126_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 57 |
| scene0127_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 14 |
| scene0132_01 | correlation | slot 1: 0.9891382328933586 (+9 more slots < 0.99) | 6 |
| scene0132_02 | correlation | slot 1: 0.9820784417386946 (+4 more slots < 0.99) | 6 |
| scene0143_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 206 |
| scene0147_00 | correlation | slot 11: 0.9857092731992313 | 52 |
| scene0157_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 71 |
| scene0165_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 6 |
| scene0181_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 86 |
| scene0181_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 88 |
| scene0200_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 51 |
| scene0205_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 4 |
| scene0205_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 16 |
| scene0241_02 | correlation | slot 19: 0.9899365569997 | 110 |
| scene0270_01 | correlation | slot 9: 0.9896498067963915 (+2 more slots < 0.99) | 292 |
| scene0274_01 | correlation | slot 24: 0.9888654036437342 | 100 |
| scene0276_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 233 |
| scene0289_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 28 |
| scene0295_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 81 |
| scene0331_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 219 |
| scene0337_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 1 |
| scene0346_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 3 |
| scene0349_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 4 |
| scene0375_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 7 |
| scene0387_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 6 |
| scene0416_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 217 |
| scene0431_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 4 |
| scene0442_00 | correlation | slot 10: 0.9872877839593809 (+4 more slots < 0.99) | 4 |
| scene0444_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 2 |
| scene0446_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 7 |
| scene0451_00 | correlation | slot 1: 0.9826199496028257 (+7 more slots < 0.99) | 11 |
| scene0451_01 | correlation | slot 1: 0.9895691197534403 (+11 more slots < 0.99) | 11 |
| scene0455_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 20 |
| scene0459_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 5 |
| scene0469_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 66 |
| scene0481_00 | correlation | slot 20: 0.9879096768180871 | 4 |
| scene0485_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 2 |
| scene0491_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 2 |
| scene0523_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 17 |
| scene0524_01 | correlation | slot 1: 0.953258144711294 (+1 more slots < 0.99) | 3 |
| scene0526_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 3 |
| scene0533_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 6 |
| scene0543_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 3 |
| scene0545_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 140 |
| scene0545_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 140 |
| scene0600_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 152 |
| scene0601_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 6 |
| scene0610_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 18 |
| scene0619_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 15 |
| scene0620_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 79 |
| scene0625_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 8 |
| scene0635_00 | correlation | slot 1: 0.9791494694565714 (+4 more slots < 0.99) | 2 |
| scene0639_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 4 |
| scene0656_01 | correlation | slot 14: 0.9895325465500047 | 208 |
| scene0672_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 125 |
| scene0674_01 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 4 |
| scene0705_02 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 86 |
| scene0706_00 | camera-transform | sensor camera_to_world must be a finite proper rigid transform | 33 |

Totals: camera-transform 57 scenes / 3,064 questions; correlation 22 scenes / 942 questions;
combined 79 scenes / 4,006 questions.

## 2. Refusal logic (quoted, sealed preparer `r1313_vsi_distill_gt_training_scannet_v2`)

**Camera-transform refusal** — `scannet_sens.py` lines 11-18, the `rigid()` helper:

```
def rigid(matrix, name):
    value = np.asarray(matrix, dtype=np.float64)
    if (value.shape != (4, 4) or not np.isfinite(value).all()
            or not np.allclose(value[3], [0, 0, 0, 1], atol=1e-5)
            or not np.allclose(value[:3, :3].T @ value[:3, :3], np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(value[:3, :3]), 1, atol=1e-4)):
        raise ValueError(f'{name} must be a finite proper rigid transform')
    return value
```

It inspects a single 4x4 pose matrix for: correct shape, all-finite entries, a `[0,0,0,1]`
bottom row (atol 1e-5), rotation-block orthonormality `RᵀR ≈ I` (atol 1e-4), and
`det(R) ≈ 1` (atol 1e-4). Called at `scannet_adapter.py` line 129, inside
`selected_camera_alignment()`:

```
source, depth, record = sensor.decode(ordinal)
pose = rigid(record['camera_to_world'], 'sensor camera_to_world')
```

The input is `record['camera_to_world']`, the per-frame pose baked into the raw `.sens` binary
stream (read by `SensReader` in the same file, not a separate pose text file), for whichever
frame `ordinal` is one of the scene's 32 pre-selected slots (`items = frames['frames']`, checked
to be exactly 32 at line 102). The loop iterates `for slot, item in enumerate(items, 1)` and
`rigid()` raises immediately and uncaught on the first non-finite/improper pose it meets — it
does not continue past the first failure the way the correlation check does.

**Correlation refusal** — `scannet_adapter.py` lines 88-95, `correspondence()`:

```
def correspondence(source, vsi, selected):
    if selected is None or not np.array_equal(vsi, selected):
        raise ValueError('authenticated selected PNG differs from its VSI video ordinal')
    vh, vw = vsi.shape[:2]
    resized = cv2.resize(source, (vw, vh), interpolation=cv2.INTER_AREA)
    correlation = float(np.corrcoef(resized.reshape(-1), vsi.reshape(-1))[0, 1])
    mae = float(np.abs(resized.astype(np.float32) - vsi).mean())
    return correlation, mae
```

and the threshold check at lines 130-132, inside the same `selected_camera_alignment()` loop:

```
correlation, mae = correspondence(source, vsi, selected)
if not np.isfinite(correlation) or correlation < .99:
    errors.append(f'raw/VSI ordinal correlation failed at slot {slot}: {correlation}')
```

It compares the raw `.sens` color frame for a selected ordinal, resized to the VSI video's
frame size, against the decoded VSI video frame at that same ordinal, via a flattened Pearson
correlation (`np.corrcoef`) against a fixed 0.99 threshold. Unlike the camera-transform check,
failures are appended to an `errors` list across all 32 slots and raised together
(`'; '.join(errors)`) at line 153 after the full 32-slot loop completes — which is why some
scenes list many failing slots at once.

## 3. Sampled pose statistics and correlation values

**Pose statistics, 5 camera-transform scenes** (all raw frames read from
`/data2/jjyeung/raw_datasets/scannet/scans/<scene>/<scene>.sens` via the preparer's own
`SensReader`; orthonormality error = `max|RᵀR − I|` on the rotation block):

| Scene | Total frames | Non-finite frames | Non-finite fraction | Frames failing orthonormality > 1e-3 | Max orthonormality error (finite frames) |
|---|---:|---:|---:|---:|---:|
| scene0034_02 | 1,280 | 70 | 5.47% | 0 | 9.5e-7 |
| scene0020_00 | 1,280 | 65 | 5.08% | 0 | 1.3e-6 |
| scene0026_00 | 2,672 | 67 | 2.51% | 0 | 1.0e-6 |
| scene0035_01 | 1,028 | 30 | 2.92% | 0 | 9.7e-7 |
| scene0041_00 | 3,259 | 68 | 2.09% | 0 | 1.0e-6 |

Non-finite fractions run 2.1%-5.5% of all frames per scene. Zero frames in any of the five
scenes fail orthonormality by more than 1e-3 (or even by more than ~1.3e-6) once non-finite
frames are excluded — the finite poses are numerically clean rigid transforms.

**Correlation values, 3 correlation-failure scenes** (raw `.sens` frame resized to VSI frame
size, compared to the decoded VSI video frame at the same ordinal, Pearson correlation vs. 0.99
threshold; values from `PREP_scannet.md` / the named per-scene logs):

| Scene | Failing slots (of 32) | Correlation values at failing slots |
|---|---:|---|
| scene0008_00 | 1 | slot 1: 0.9862 |
| scene0012_02 | 5 | slots 1, 12, 17, 24, 32: 0.9839, 0.9869, 0.9883, 0.9897, 0.9899 |
| scene0013_00 | 23 | slots 1-25 (23 of 25 listed slots fail): range 0.9432-0.9890 |

## 4. Raw source root comparison (admitted vs. refused)

`REGISTRY_155.json` (`codex_scannet_v2_remat/out/wrapper_scannet_v2/`) pins the same preparer
package and `contract_sha256` (`a1b6ce4...eacc8bfd`) as the batch-2 refusals' `START.json`
commands. Its first receipt, for admitted scene `scene0000_02`
(`.../rematerialization_req232_scannet_v2_20260918/jobs_scannet_v2/scene0000_02/assets/scene_receipt.json`),
records raw source path
`/data2/jjyeung/raw_datasets/scannet/scans/scene0000_02/scene0000_02.sens`. The refused
scene `scene0034_02`'s raw directory (confirmed present via `ls`) is
`/data2/jjyeung/raw_datasets/scannet/scans/scene0034_02/scene0034_02.sens` — same
`RAW_ROOT = /data2/jjyeung/raw_datasets/scannet/scans` constant (`scannet_adapter.py` line 13)
for both. Admitted and refused scenes read from the same raw source root.

## 5. Observations

In the five sampled camera-transform scenes, non-finite `camera_to_world` poses affect only
2.1%-5.5% of all frames in each `.sens` stream, and every finite frame's rotation block is
orthonormal to within about 1e-6, well inside the 1e-3 tolerance used here — the refusal is
driven by a small minority of corrupted frames per scene rather than a scene-wide transform or
convention error. The `rigid()` check runs only on the 32 already-selected ordinals named in a
scene's frames receipt, and it raises on the first non-finite pose it meets among those 32, so a
scene fails whenever any one of its fixed 32 slots lands on a bad frame even though the
surrounding hundreds or thousands of frames in the same `.sens` stream are clean. The three
sampled correlation failures sit just under the 0.99 admission line rather than showing the
near-zero or negative correlations a wrong-video or misaligned-frame mismatch would produce:
scene0008_00 fails 1 of 32 slots at 0.986, scene0012_02 fails 5 of 32 slots between 0.984 and
0.990. scene0013_00 fails 23 of 32 slots with values from 0.943 to 0.989, a shortfall across
nearly the whole selection rather than isolated to a few frames, unlike the other two sampled
correlation-failure scenes. The admitted scene0000_02's raw sensor path and the refused scenes'
raw sensor paths both resolve under the same `RAW_ROOT`
(`/data2/jjyeung/raw_datasets/scannet/scans/<scene>/<scene>.sens`), so the two refusal classes
are not explained by batch-2 reading from a different or stale raw source root than the one
behind the 155 already-admitted scenes.
