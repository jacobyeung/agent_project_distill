# Codex build 5: apply review fixes F1-F4 to the job, rebuild the packets, rehearse on a read-only PROJECT layout. No GPU, no submission.

Model gpt-6-astra, effort high. BRIEF.md's rules still hold: write only in this workspace (/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build), no Git, ssh, network, GPU, kill or deletion; bounded reads; nice 19, one thread.
First read the review whole: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_k1b2/REVIEW_VERDICT_K1_PART_B.md (reviewer's test: /scratch/jjyeung/orch_n30/review_k1b2/bwt2/BWRAP_TEST.txt). Then read the orchestrator's order /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/20261116T0729Z_ORCH_NOTE_cap_first_job.md. Then REPORT4.txt.

## Fixes, smallest change each
- F1: in stage_job.namespace(), create NS.physical(root, pool_root) and NS.physical(root, gcloud_config) as mount points (mkdir parents, exist_ok) before the argv binds them. Every other bind that targets a path inside a read-only bind needs the same treatment; audit them all and list them.
- F2: bind gcloud_config read-write (--bind), as C8r used it from the outer process.
- F3: the a7e31d84.sh bootstrap execs /usr/bin/python3 (C8r native_launcher.py:72,198 parity). Operator check at 07:46Z: Orchard login node /usr/bin/python3 is 3.12.3, and gcloud is /usr/bin/gcloud. The compute nodes are not confirmed. Replace job_support.sha's hashlib.file_digest with the chunked loop of orchard_results.sha, so the outer path also runs on 3.6-3.10.
- F4: add deadline_unix to a.json (CONFIG). Set it as a submit-time parameter equal to 2026-11-16T12:30:00Z minus return_margin_seconds. Use allocation = min(43200, deadline_unix - started_unix) in phase_support.budget and in phase_worker's literal 43200 check, so the job ends cleanly with its return written by 12:30Z whatever its start time. Later resume jobs get a fresh a.json/batch with their own deadline (or none). Document how the operator sets it for a later job.
- Minor: phase_worker.py:173 must not write FAILED.json on a clean code-4 boundary. Leave the other minor points and list them.
- Do not touch the kit, the source_identity members, manifest v2 or the six C8r helper files.
## Rebuild and rehearse
- Rebuild the source bundle and the batch with build_package.py. Print the new bytes and sha256 for d6e92a81.tar (keep the name only if bytes are unchanged; otherwise choose a new opaque name under q8/b7e31d84a90c62f5/) and for the batch. Update UPLOAD.json, submit_command.txt and the ledger proposal.
- Extend rh_batch so the success case runs with the pool and the gcloud stand-in under a read-only PROJECT-like bind: /project/community/jjyeung ro-bound from <root>/project, as in production. Show that without the F1 fix this layout reproduces the reviewer's error, and that with it the case passes. Add a deadline case: a deadline_unix a few fixture-seconds out stops cleanly with BUDGET->RESUME, publishes, and advances the pointer.
- Bare `python3` must no longer be shimmed for the bootstrap. The rehearsal must exec /usr/bin/python3 as the job will. Trinity's /usr/bin/python3 is 3.6.8, so the outer path must run on it. If that is impossible, say exactly which line needs 3.7 or later.
- Rebuild rh/RH_1_3.tar (`build_rh.py --pack-env`, authorized). Run locally as far as bwrap allows.
## Deliver
REPORT5.txt (short, no-archaeology): each fix with its unified diff (job files only, also as evidence/REPORT5_JOB.diff), the new packet names, bytes and sha256, the new submit command with how deadline_unix is set, the local output, and the operator command for 1-3 (extract into a fresh /scratch/jjyeung/orch_n30/k1_partb_rh/r4, cd there, `bash run_rh.sh`).
