BOX dev check: frozen `vote_10_3_best` versus served best-frame boxes

Status: **pending the real rank-1 depth dump**. Synthetic results are tests only.
The registered K1 result is +5.65 [2.09, 9.62] MRA points. The dev criterion passes
iff the overall paired room-bootstrap 95% upper bound is >= 0. This criterion
excludes an interval entirely below zero; it does not establish noninferiority.

Run from `/scratch/jjyeung/orch_n30/lever1_c/boxdev`:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B run.py --depth ../r1/returned/0.gz --receipt ../r1/returned/4.json --out out/BOXDEV.json
```

The runner authenticates the dump and T1 capture, restores exact depth with the
float16 residual, and executes rank 1's unchanged parity-gate code on all 150
items before evaluating either scored arm. Rank 1 requires >=95% operand parity,
with each operand inheriting its item's printed-gap match at 0.00 m tolerance.
A gate/input/source-pin failure writes status STOP, empty scores, and a STOP file.
A successful rerun marks an existing STOP file CLEARED without deleting it.
After the gate, every base prediction must equal rank 1 cell (a), including nulls.
The comparison uses all 150 labels, without the GT-raster eligibility exclusions
that rank 1 applies to its other cells. Missing predictions receive official MRA 0.

Fill this table from `BOXDEV.json.statistics`; scores and differences are MRA points.

| Population | Items / rooms | Base | Vote | Vote − base [95% CI] | Upper bound >= 0 |
|---|---|---|---|---|---|
| All | pending | pending | pending | pending | pending |
| ARKit | pending | pending | pending | pending | pending |
| ScanNet | pending | pending | pending | pending | pending |
| ScanNet++ | pending | pending | pending | pending | pending |

The bootstrap imports rank 1's Bootstrap unchanged: 10,000 draws, seed 20261120,
physical rooms, item weighting. Dataset subsets use the same full-room draws;
undefined subset draws are counted. Only the overall result decides the proposal.

The frozen rule uses **10 cm voxels, three-frame support, plus best-frame points**.
Despite the brief's “two-frame” wording, these are the constants in r2/out_box.
With fewer than three valid frames it uses the best frame. Nothing is fitted.
The vote imports the exact frozen `fusion_box` and `lift_frames` declarations.
Both arms use the served Session frame guard/renderer and rank 1's exact gap kernel.

Read-time cost: both readers touch every visible grounded frame. Base lifts each
once and the best frame again; vote lifts each once, filters each frame's median
spread, retains those points, builds voxel support counts and fits the voted box.
No extra image, depth, pose, mask, or selector inference is required. Retained
numeric point payload, frame lists and lift-call counts appear per object.
Per-item CPU seconds and separately measured peak traced bytes appear under
`rows[].measurements`. `cost` reports means, maxima and extra peak traced bytes.
These measurements exclude inference, mask decoding, geometry restoration and IO;
caches may be warm. Traced memory covers Python/NumPy allocations, not process RSS.
Hardware and local test measurements are in `BUILD_RESULTS.md` and the JSON receipts.

The local T1 renderer prints frame IDs and best frame, `f1 centre (x, y, z) m`,
`size l x w x h m`, and integer `yaw ... deg`; metric fields have two decimals.
The gap response prints `distance d.dd m`. Voting preserves the field format and
frame selection but can change centre, size, yaw and gap values. `RENDER_TEST.json`
contains a measured example. The renderer uses provider values when printing.
Its AnnotationBoxProvider explicitly substitutes GT boxes; changing the inference
provider does not change those GT targets. Existing GT-valued supervision therefore
does not mechanically require replacement. To make training response blocks match
the voted reader's observations, re-render affected numeric responses and audit
answer consistency; the GT answers themselves remain labels. The generator can
reject traces when computed responses disagree with independent GT answers.
This build inspected renderer code, not the full distillation-row corpus.

Renderer sources: `/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/trace_format/box_v313.py`
(`serialize`, `ground`, `BoxRegistry.gap`) and that tree's
`generator/derivgen_v7/derivgen/box_v313.py` (`AnnotationBoxProvider`, `render`).
The suggested `gbuild/g3/orchard_t1` path is absent; the deployed payload is present.

Tests: run `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests.py`
and the same command with `test_k1.py`. Test fixtures and outputs stay in boxdev.
`SOURCE_PINS.json` rejects changed external implementations. `SHA256SUMS` seals
this delivery. Real dev scores, real dump parity and dev runtime remain unverified
until the authenticated depth dump arrives.
