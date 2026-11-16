# H1-1 packet for cont_ops (from h1_headsft, 2026-11-16)

H1-1 is D0's job-B leg (init step 544 `1d6eeb28...`, D0's rows, seed 17, D0's 1,000-step LR horizon, world 4 on
Orchard advanced, 4 H100) with two switches on, S1 (faithful own camera rows) and S2 (pose targets on camera
routing rows), stopped after step 200. Package it from `D0_JOB_B_PACKET.md` as you packaged D0.

## Files (this folder; sha256 in SHA256SUMS)
- `h1_1_code.tar` (10.2 MB): `tree/` (sealed b01ce449 + `patches/h1_trainer.patch`, `h1_rest.patch`,
  `faithful_own_rows.patch`), `rows/faithful_gate.py`, `configs/h1_1.json` (S1+S2, the leg),
  `configs/h1_1a.json` (S1 only, not submitted), `configs/diff_against_d0.json`, `configs/d0.json`,
  `auth/R0_ROOMS.txt` (bdb5d402, 372 rooms; resolved relative to the package root, so keep `tree/` and
  `auth/` side by side), `auth/d0_base.json`, `auth/d0_override.txt` (the D0 inputs the diff was taken from).
- Kit snapshot: trinity-3-30 `/scratch/jjyeung/orch_n30/h1_headsft/snap/kit_b5.tar` (sha256 00b3aac9...,
  report `kit/BUILD_REPORT.md` section "Build 5").

## Config: what differs from D0 (`diff_against_d0.json`, 7 fields)
`h1` block added (S1 on, S2 on, camera types displacement / movement direction / rotation, `stop_after_step`
200, metrics on, R0 pin); `milestones` and `recipe.milestones` = [100, 200]; `scheduled_sampling` and
`recipe.scheduled_sampling`: `force_from_step` 1, `max_own_probability` 0.5. Everything else is D0's.

## Packaging steps that must differ from D0
1. **New output paths.** `output` and `preparation_output` still carry D0's AWS-layout paths (`runs/469ddece`,
   `f/469ddece`). Give H1-1 its own run directory and preparation directory; it must never write into D0's
   run directory or touch D0's end slot.
2. **Code pin and admission.** The tree differs from D0's sealed tree, so rebuild `code` (D0: `k/7.json`
   c82c2da1...) and the `admission` record for this tree the way D0_JOB_B_PACKET does; do not reuse D0's.
3. Map the AWS-layout stream paths (routing `5e1d07a4/f/h/r16/receipt.json` 9a7f3310..., pose, VQA, pointing)
   to their Orchard copies as for D0; the sha256 pins stay.

## Gate before submission (Orchard login node, CPU, nice 19, a few minutes)
`cd <extracted package> && nice -19 python -B rows/faithful_gate.py <Orchard path of the routing receipt> --out gate.json`
Exit 0: S1 identity >= 95%, submit. Exit 1: below 95%: do not submit H1-1; submit D0's second allocation as
ordered (ORCH 1342Z) and write a RESULT. Exit 2: input refused (missing or unreadable receipt): BLOCKER.
Preparation repeats the check on the bound receipt and refuses S1 below 95%, so the in-job gate holds too.
Record `gate.json` (identity rate, per-type counts, refusal histogram) in your RESULT; h1_headsft copies it
into the H1 design record.

## Run behaviour to babysit
- Expected: ~140 s/step (D0 132-140 s plus the S1 readout), 200 steps ~7.8 h plus admission and 2 exports.
- Stop rule (registered): over steps 1-50, if the all-reduced share of own camera rows whose faithful answer
  differs from GT exceeds 35% (difference = option change, displacement > 10% of GT, rotation > 10 deg), the
  leg exports m100 and stops; the report names `h1_own_camera_answer_differs_gt_35pct_steps1_50`, `H1_STOP`.
  Otherwise it exports m100 and m200 and stops at 200 (`stopped_for_resume=false`; nothing to requeue).
- Per-step metrics carry `h1_answer_counts` (own, answer_differs, share) and per-type
  own/gt/refused counts with a refusal histogram; S1 refusals train the GT row and never stop the job.
- Losses must stay finite as in D0. After the leg, D0 resumes from its end slot.

## Gate evidence (all CPU, trinity-3-30)
- Review: `events/h1_headsft/REVIEW_VERDICT_H1KIT.md` GO AFTER FIXES; all 7 fixes landed (Build 4);
  ORCH RULING 1535Z settled F1 (faithful training stands; usage is measured against the same model's
  unperturbed answer) and F2 (step 2 stands, plus one forced pose-own run). Suite 91 passed, 0 failed
  (`kit/logs/b5/suite.log`), reviewer tests included (`tests/test_review.py` 89d6b051...).
- First batch, every rank, step 2, native trainer on the tiny model: own rows 4/4/6/5
  (`kit/logs/b5/first_batch_step2.json`); forced pose-own: 8/8/11/11, every camera routing row own or a
  counted refusal (`kit/logs/b5/first_batch_step2_forced.json`); OFF identity 4/4 exact against the sealed tree.
- Not yet run: the real 9B step-544 first batch on CPU (owed by 05:30Z 11-17; result goes to events/cont_ops
  as a RESULT). The job's own `first_step_admission: all_rank_native_v1` still runs every rank's first step.
