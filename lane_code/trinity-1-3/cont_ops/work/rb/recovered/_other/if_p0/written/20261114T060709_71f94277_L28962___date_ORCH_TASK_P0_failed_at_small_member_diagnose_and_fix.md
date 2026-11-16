<!-- recovered by seal_plan: transcript=71f94277 line=28962 utc=2026-11-14T06:07:09.028Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_TASK_P0_failed_at_small_member_diagnose_and_fix.md heredoc_quoted -->
# ORCH task: P0 job 169413 failed after 64 seconds ("A required small runtime member is missing"); diagnose and fix

## What the job proved before it failed (authenticated return in `/scratch/jjyeung/orch_cd/if_p0/inbox_results/a35f2d78fe7c5ee8d/returned/`)

Preflight passed (private ext4 `/tmp`, mount id 744; allocation 1 node, 1 task, 8 CPUs, 204,800 MB); the pinned bwrap staged; **the real namespace smoke test ran and passed**; the production interpreter archive (8.1 GB) staged in 60.5 s and its interpreter links were accepted by the closed set; the NumPy overlay staged. It then stopped at the `small` stage: `extract_named` did not find the expected member in `/project/community/jjyeung/distill/okit/in/e00` (82,984,960 B, sha 4b66cc24...). The kit expects the member name `scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/7b30c1e4/u/ebe69df8/m.sha`. The early-check order worked: the failure cost one minute.

## Facts on the way

I have asked the operator for member listings (names and sizes, read by seeking through headers only) of `e00`, the FLA archive `d00`, the donor archive and the base model archive on Orchard. They will arrive in your inbox as text files. Until then, look at what you can locally: the operator's staging records for how those archives were built and what their member names are (`/scratch/jjyeung/orch_cd/orchard_cp2/work/adm/`: `mk_staging.py`, `mk_tar2.py`, `tar_07ca49df.json`, `tar2_members.json`, `tar2_final_a.json`; and `/scratch/jjyeung/orch_cd/orchard_cp2/work/gcs/` for the `cr` parts), read-only.

## Fix (on top of seal 93392de4, so the later arms inherit it)

1. Correct the expected member names for every archive from the real listings, not from logical paths.
2. **Check every inventory before extracting anything large, and report all mismatches at once.** After an archive is copied and hashed, and before its extraction, compare its member list with what the kit will ask of it (the small members, the FLA manifest names, the checkpoint members, the model snapshot's `config.json`, the frame plans as far as they are known before `prepare`). Do this for all archives staged up to that point, collect every mismatch, and fail with the complete list in `FAILED.json`. One failed job must tell us everything that is wrong with the inventories, not the first item.
3. Put the real listings into the kit as sealed evidence and add a CPU test that runs the inventory check against them, so a name error can never reach a job again.
4. Tests, rehearsal, new seal, diffs against 93392de4 (runtime and tests separately).

Post one RESULT. The accumulated change from the reviewed seal goes to an independent confirmation before the next submission; I write new control files for the new seal. Where and when P0 runs next (the one-GPU partition or `advanced`) I decide then.