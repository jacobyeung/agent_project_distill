# LEG-S1 continuation (steps 545-1000): launch readiness (2026-11-15)

**Question.** Can the step-544 slot be resumed to 1,000 on Orchard today, and what does the run write where?
**Answer.** Yes, pending user and ORCH GO. Card: `distillation_orchestrator_20260918/orch_n30/events/cont_ops/PRELAUNCH_CARD_CONTINUATION.md`. Command: `cd /home/jjyeung/okit && env -u TK_JOB_START sbatch -J a15_cot_ap0b0c99e1 -o /dev/null -e /project/community/jjyeung/okh7/x_07ca49df/o/%j.err /home/jjyeung/okit/j/07ca49df.sh`.
**Evidence.** Slot A step 544 is verified (sha 22249bc7), and B is absent. The wrapper and job.sh hashes are unchanged. The numbered sessions m600, m800 and m1000 and the stop generations mstopB and mstopC exist. 169097 ran at 131.1 s/step, which projects to about 20 h. Every okit path resolves to /project/community, and the trainer sees /home read-only, so the over-quota Orchard /home does not block. The early-loss baseline for steps 530-544 was read from `metrics_169097.jsonl`. The tool is `events/cont_ops/cont_tools/early_loss_check.py`.
**Options rejected.**
- Separate CPU restore proof on general: it competes with evalx27 for the one job per user, delays the launch by 1.5-5 h, and the job's steps 545-547 already test the same thing.
- Default stdout on project: the unguarded rank-0 print can crash a rank on a full filesystem.
**What might not work.**
- The project filesystem is 99% full. If it fills, uploads wait, an export can be lost at job end, and slot B is skipped.
- A semantically bad resume is caught only at step 547, about 3 h into the job.
- The 4-GPU per-user QOS blocks main's and native_r2's advanced jobs for about 20 h.
- The GCS session lifetime is assumed to be 7 days and is unverified.
**Tests that settle it.** Rule E verdict at step 547; m600/m800/m1000 done markers.
**Status.** Packet ready; not submitted.
