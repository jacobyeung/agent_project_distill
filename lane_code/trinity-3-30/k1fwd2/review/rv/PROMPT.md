# Read-only review: one boundaries.py patch that adds frozen-FoV depth variants to a GPU own-depth forward

Work only inside this folder. Do not run ssh, git, network, GPU, kill or delete commands. You may run `python3`
and the CPU test below. Write your verdict as your final message (first line `GO` or `NO-GO`), listing only
verified problems with file:line evidence. Do not design fixes beyond one line each.

## Context
`k1fwd1_boundaries.py` is the reviewed, GPU-parity-verified model boundary (review GO: `K1FWD1_REVIEW.md`; a run
with it reproduced a reference job's depth grids bit for bit on 64 of 64 captures). `new_boundaries.py` adds one
thing (`diff_boundaries_vs_k1fwd1.txt`): when `settings['fov_variants']` is set, `GPU.own` wraps the point-depth
head's `encode` to observe the served pose-head FoV, and after the served grid is computed, `fov_variants()` writes
`fov.npz` + `FOV_RECEIPT.json` into the capture's output directory with two extra depth grids:
- V1: private `depth.fov` (Linear) on the states of a separate private feature pass, `1e-4+(pi-2e-4)*sigmoid(.)`.
- V2: frozen G3T intrinsics `raw_pose9[anchor_slots,7:9]` read from a pinned cached file (authenticated by capture
  digest and anchor indices; covers 242 of the 300 captures, the rest record V2 MISSING).
Both must match `scale_donor_PATCH_DONOR3.py` `ScaleDonor.forward` (V1/V2 definitions) as evaluated at the donor's
own checkpoint, where the donor's tensors equal the live ones. A control grid (served pose FoV through the second
feature pass) is compared with the served grid and recorded.
`build2.py` builds the batch: it reuses `k1fwd1_build.py` (unchanged), applies the patch, pins the G3T file and the
settings into the manifest's `gpu` block, and keeps every other pin (export, tree, env, captures). Build output:
`BUILD_OUTPUT.txt`. The model code the boundary runs against is tree 168872: `tree168872_*.py` (HeadState in
`tree168872_carrier_c1_decode.py:140-170`, PointDepthHead encode/query in `tree168872_point_depth_head.py:175-226`,
PrivateDepth in `tree168872_carrier_c1.py:39-75`). `k1_phases.py` (pinned, unchanged) writes `own.npz` after
`boundary.own` returns; `new_phase_worker.py` runs it and binds kit identity (`same_kit`).

## Check
1. The served `own.npz` grid and gravity are computed exactly as before (no numerical or state change from the
   wrapper, the extra feature pass, or the extra encodes), for this capture and later captures.
2. V1 and V2 equal scale_donor's definitions at the donor checkpoint (dtype, slicing, sigmoid parameterisation,
   FoV clamp path, uv grid, frame queries), and nothing in V1/V2 reads the live pose-head FoV or the LM.
3. The writes cannot break the pinned phase (file-set checks, resume, canary, output cap, return), and a failure in
   `fov_variants` cannot silently produce a served capture without its variants.
4. `build2.py` changes nothing else in the batch relative to k1fwd1's step-544 variant except: new token/pool/cloud
   names, allocation 7140 s, capture_reserve 600 s, the boundaries/DEPENDENCIES pins and the two manifest additions.
5. Run the CPU test: `cd stub/.. && python3 -B t_fov.py new_boundaries.py` needs torch; if torch is unavailable,
   say so and review the test statically (it uses the real tree-168872 PointDepthHead with stubbed features).
