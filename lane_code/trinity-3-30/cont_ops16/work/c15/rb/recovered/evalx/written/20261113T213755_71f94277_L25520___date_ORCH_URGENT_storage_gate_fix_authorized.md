<!-- recovered by seal_plan: transcript=71f94277 line=25520 utc=2026-11-13T21:37:55.780Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_URGENT_storage_gate_fix_authorized.md heredoc_quoted -->
# ORCH, urgent: fix the storage gate as you propose; I confirm the diff; then one corrected step-50 attempt

Your 2136Z BLOCKER. The diagnosis is right: Orchard stacks two mounts on `/tmp` (a tmpfs, then the job's ext4 mount from `/dev/md127` under `job_tmp/<job>`), and the validator's tie on the longest prefix picked the hidden tmpfs. The rehearsal did its job: it found this before the decision read.

**Authorized:**
1. The targeted fix: select the mount by the existing work directory's kernel mount id (from `/proc/self/fdinfo` of an open handle on it), then apply the same physical-filesystem and job-private checks to that entry, unchanged. Record the selected mount entry and the full list of `/tmp` entries in the evidence on success and on refusal. Nothing else changes.
2. Tests: your regression with the real stacked lines must pass; the NFS-refusal control must still refuse; add one where the stacked order is reversed.
3. Post the diff file, the new seven-file digest and the test log as a RESULT. I read the diff myself and answer within minutes.
4. **One corrected step-50 attempt is pre-authorized** the moment I confirm, with a new token and intent (the first intent is spent correctly; job 169274 is kept as evidence).

Also, from this first job: it ran on orchard-community-2, the node that hosts the production job. That is allowed, but record in the rehearsal's RESULT the node, and whether the production job's step times moved while your read ran (the operator's snapshots have them).

Step 100 has completed or is completing now; the decision read follows the rehearsal as planned.