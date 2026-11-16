# Warm-start contingency for run 469ddece

**Configuration alone is insufficient. Build a private source delta; do not reseal, assemble, submit, or change the running leg.**
This is a new weight-warm-start experiment, not exact checkpoint continuation.

## Evidence key
All source references below are relative to `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872`, the inherited b01ce449 source.
`C` = `student_pilot/carrier_c1_run.py`; `D` = `student_pilot/carrier_c1_data.py`; `S` = `student_pilot/carrier_c1_sweep.py`.
`F` = `student_pilot/full_ft.py`; `R` = `student_pilot/carrier_c1_routing.py`; `L` = `launch_s1/build.py`; `G` = `launch_s1/b/d.py`.
The retained production template is `work/fourstream_template_inputs/k/28429cf9.json`; its identity and run are bound in `out/FOURSTREAM_TEMPLATE_PLAN.json`.

## What configuration already supports
- A distinct run key, output directory, and persistent root are builder inputs (`L:44–47,87–89,220–222`).
- Final mode accepts a pinned C1 milestone, full base weights, and selected pose/depth/frame-embedding heads (`C:129–142,828–839,851–871,894–938`).
- The milestone schema is `artifact.json`, `heads.pt`, and `full_weights/` with a pinned manifest, index, and shards (`C:1977–2013`; `F:660–692`).
- The existing node-local init mirror stages and hashes these payloads; it is not a remote download mechanism (`launch_s1/b/c.sh:216–262`).
- A fresh train constructs AdamW before optional checkpoint restoration (`C:2770–2782`).
- Final-mode configuration sets the total horizon, milestones, mix, world, and warm-up ratio (`S:60–113`); retain the donor's 1,000-step horizon, not 1,000 additional updates.
- Four-stream final mode and the no-MDG parent branch already exist (`C:85–95`; `G:120–135`). Keep their policy, exclusions, routing table, and stream order unchanged.

## What requires a source change
- A fresh train hardcodes `start_step=0`; only exact checkpoint restoration changes it (`C:2781–2784`). Add an authenticated export-derived starting step.
- `row_start_step` rejects final mode (`C:131–133`). Do not relax it or double-offset the sampler: use the absolute starting step with zero row offset.
- The loop already passes its absolute step to optimization and skips that many sampler plans (`C:2191–2200,2243–2246`); learning rate uses that step (`C:1563–1564`; `student_pilot/decoupled_v.py:195–199`).
- The sampler rebuilds independent shuffles from ordered counts and seed, then skips integer plans without decoding rows (`D:449–484`). Require identical ordered admitted row identities, counts, seed, mix, and world; counts alone do not prove continuity.
- Model loading currently overwrites routing-token input/output rows after loading the donor LM (`C:769–779`; `R:668–678`). Preserve those trained rows only for the authenticated same-leg contingency.
- Selected-head loading can leave unselected modules initialized, and inherited-head metadata controls parameter grouping (`C:908–950`; `student_pilot/carrier_c1.py:621–651`). Require complete live-head coverage and verify donor-equivalent optimizer groups/rates.
- The CPU first-batch helper currently builds step-zero plans (`C:2924–2926`). Make its contingency branch inspect the first post-export batch instead.

## Private implementation and review contract
1. Add a narrowly scoped, fail-closed warm-start block that binds the donor export, donor run, effective donor configuration, and prepared-row identity evidence.
2. Read the completed step from the pinned artifact; require integer `0 < step < 1000`, the expected donor/source/base/layout, and a distinct destination run/root. Reject an independent step override and simultaneous exact resume on the initial warm-start invocation.
3. Preserve the sealed initialization path for all other configurations. For this branch, restore all exported model/head tensors, preserve opener rows, start with an empty optimizer, and start training at `export_step + 1`.
4. Keep the donor schedule and sampler policy; authenticate the rebuilt admitted row order before training. Reject any mismatch rather than silently replaying or substituting a different population.
5. Emit explicit lineage and fresh-optimizer/BF16/RNG-reset labels. Subsequent checkpoints belong to the new run and must retain absolute steps.
6. Build tiny CPU fixtures with the native export schema. Test payload pins, full head/base restoration, first post-export plan on every rank, LR continuity, fresh optimizer state, absolute checkpoint/metric steps, and fail-closed identity/step/row mismatches.
7. Review default-path noninterference, routing-row preservation, head grouping, no double offset, and checkpoint continuation after the new run has saved its own state.
8. Rebind admission to the new source/configuration/run directories without weakening its policy. The existing gate binds the exact directory, configuration, frame evidence, and parent artifact (`G:16–33,111–135`).
9. Supply the private patch, tests, and a configuration/binding template. Choosing the export also needs its mirrored effective configuration and prepared-row evidence; an artifact hash alone cannot establish sampler identity.
10. Keep release status BLOCKED pending independent review, authorized reseal, full binding/content scan, and the operator gate. No release assembly is authorized.

## Scientific claims and monitoring
The export saves BF16-rounded base tensors and heads, not the exact optimizer/RNG/master state (`C:1977–2013` versus `C:1854–1897,1947–1956`; `F:687–691`).
Fresh training reseeds rather than restoring donor rank RNG (`C:2747`); AdamW moments and bias-correction age restart even while the global LR schedule continues (`C:2770–2782`).
Call the result “donor prefix through step s, then weight warm start through step 1000.” Do not pool it with an uninterrupted or exact-resumed 1,000-step leg as the same treatment.
Same held-out evaluation protocol and a clearly labeled recovery-treatment comparison remain valid; equal absolute step is not equal optimizer history or equal consumed compute.
Compare each stream's first post-export losses and subsequent fixed windows against mirrored run-469ddece metrics at matching absolute steps where those exist; otherwise use its pre-export windows and label the unmatched comparison.
Track nonfinite losses, clipping/gradient norms, per-stream loss jumps, and sustained divergence; fresh moments and BF16 rounding can alter the first updates. A smooth trace does not prove exact equivalence.
This design uses local source inspection only. It makes no live-health, GPU, actual-export-load, or full-population re-admission claim.
