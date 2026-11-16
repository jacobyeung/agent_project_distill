# Fix the own-grounding head kit per an independent review (GO AFTER FIXES)

Code: /scratch/jjyeung/orch_n30/b05_owngrd/code (package owngrd; you wrote vit/head/losses/data/train/export earlier;
the lane then changed head.PresenceHead and train.py presence size to 320x416 — keep those). Rules: CPU only, no git,
no ssh, no network, no GPU, no file removal of any kind (rename to move aside), write only under code/ and
/scratch/jjyeung/orch_n30/b05_owngrd/tmp_codex, no recursive search outside the named directories, torch threads <= 16.
Python: /scratch/jjyeung/envs/allospatial_1111_v1/bin/python.

Read the verdict first: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_owngrd/REVIEW_VERDICT_OWNGRD.md
(8 numbered fixes + "Recommended"). The reviewer's failing tests are in
/scratch/jjyeung/orch_n30/review_owngrd/work/code2/tests/test_review_refute.py and test_review_resume.py: copy both into
code/tests/ unchanged except where stated below. They are the gate (with the existing suite).

## Fix all eight
1. CUDA autocast: no banned op under autocast. Replace F.binary_cross_entropy on probabilities (losses.py ~173) with a
   logits/log-sigmoid form (log of a product of sigmoids = sum of logsigmoids; log(1-p) via log1p(-p) clamped), and run
   compute_losses with autocast disabled and fp32 inputs. Test F1 must pass.
2. Distillation only where the design allows: presence/decoder-presence score distillation only on rows whose `why` is
   `uncertain_absent` or `not_annotatable`, plus rows of role confuser/absent whose why is `absent`. No presence loss of
   any kind on `disputed_absent`, `miss`, `sliver`, `invalid_frame` rows. Keep DISPUTED proposals in the data (data.py
   currently drops them) and give queries that overlap a DISPUTED proposal (mask IoU > 0.5) zero match weight. Tests F2.
3. Metrics: a false presence on an ABSENT pair counts only when the selector's chosen logit beats "none"; on-target
   share is computed over present, unambiguous (single GT instance) pairs only. Tests F3a/F3b.
4. Recall@5: primary metric = recall over unambiguous names (exactly one GT instance in the clip): covered when a top-5
   candidate overlaps that instance at mask IoU >= 0.5 in some decoded frame. Log the all-instance recall as a diagnostic.
   Also compute and log once, at the start of training from the labels alone, the ceiling of both metrics (share of
   eligible names/instances that have at least one GT-visible frame — an oracle shortlist of 4 frames and 5 candidates),
   and make the fail-fast bar at step 600 = 0.70 x the unambiguous ceiling (bar recorded in RUN.json before step 1).
5. Selector source fingerprint: teacher candidates must not carry a constant feature. For feature 4 give each teacher
   candidate a value with the decoder candidates' distribution: the decoder's IoU estimate of the query that best overlaps
   the teacher member in that frame (fill it inside the forward, where the decoder outputs exist). teacher_candidates()
   called on a target alone (test F4) must return a non-constant, non-zero placeholder that the forward overwrites — or
   change test F4 minimally so it checks the features the selector actually sees in a forward; state which.
6. Confuser rows (selection_only HARDNEG) train selection only: queries overlapping them get zero match weight. Test F5.
7. Train-only manifests: add `--split train|heldout|all` to build_manifest.py (default all, current behaviour) and a
   small tool `python -m owngrd.split_manifest --in M --split train --out M2` that filters captures by k1_split, reruns
   Gate.admit on the result and writes the new receipt (counts, source manifest sha). GroundingDataset('train') keeps
   refusing a manifest with heldout captures. Replace test F6 with: split_manifest on
   /scratch/jjyeung/orch_n30/b05_owngrd/work/manifests/TEACHER_K1.json -> train manifest -> GroundingDataset(train) and
   (train_val) construct on the real labels /scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1 and teacher root
   /scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full/teacher_k1, with non-empty train and train_val and no
   heldout capture; the original TEACHER_K1.json is still refused for train.
8. README: pilot template uses --hours 4 (the cap is 4 A6000-hours) and the real defaults (presence 320x416).
## Recommended (do these too)
- Seeded per-epoch item permutation stored in the resume cursor (exact resume must still hold: test_review_resume.py).
- train.jsonl: on resume, do not duplicate lines already logged after the last checkpoint (truncate-by-rewrite to the
  checkpoint step, or tag lines with a run segment id); RUN.json records a hash of the owngrd source files.
- A `--val-items N` option (deterministic subset of train_val items) so validation does not dominate pilot wall time;
  default all.

## Deliver
All tests pass (existing + reviewer's, F6 replaced as above): paste the pytest summary. Then run the real-label CPU
smoke: `python -m owngrd.train --manifest <train-only manifest from split_manifest restricted to these 4 captures:
arkitscenes/41048124, 41069076, 41098061, 42444814, with frame paths rewritten to
/scratch/jjyeung/orch_n30/b05_owngrd/work/frames/<sha[:2]>/<sha>.png> --labels .../work/labels_k1 --teacher-root
.../work/teacher_k1_full/teacher_k1 --out tmp_codex/smoke_fix --hours 0.4 --steps 3 --validate-every 3
--checkpoint-every 3` and report losses, metrics and the logged ceilings/bar. Update code/HEAD_README.md and
tmp_codex/BUILD_REPORT.json (new file hashes, every choice you made). One line per fix in tmp_codex/FIXES_DONE.md
with file:line.
