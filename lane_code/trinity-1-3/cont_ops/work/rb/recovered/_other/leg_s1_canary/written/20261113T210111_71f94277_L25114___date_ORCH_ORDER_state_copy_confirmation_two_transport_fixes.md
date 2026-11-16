<!-- recovered by seal_plan: transcript=71f94277 line=25114 utc=2026-11-13T21:01:11.647Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_ORDER_state_copy_confirmation_two_transport_fixes.md heredoc_quoted -->
# ORCH order: confirmation is RUN for the cheap variant and RUN for the full copy after an accepted cheap run; make two transport fixes now

Result: `/scratch/jjyeung/orch_cd/leg_s1_review/STATE_COPY_CONFIRMATION.md` (24 lines; read it in full). Both HIGH fixes hold; rates, start rule, names, time limit and the byte-identical validator are confirmed; 78 of 78 fixtures pass; with today's facts the full copy would be admitted with at least 2.0 TB of disk headroom. No finding can disturb the trainer; each only loses a result or blocks a run.

Fix these two before the cheap run, as a small diff on the operator-side transport only (the node helper stays byte-identical; say so with hashes), each with a test:

1. **MEDIUM-2 (`operator_transport.py:308`, inherited at `:204`):** the worker's `srun` inherits the 512 MiB address-space limit and Slurm passes it on to the step, so `srun` itself may fail under it. Reset the limit for the `srun` child; the helper applies its own limit inside the step.
2. **MEDIUM-1 (`operator_transport.py:300`, `live_entry.py:188`):** `unpack_fetch` refuses any nonzero exit, so a NOT_ACCEPTED record and the memory discovery report never reach the operator; and with no finite memory limit the cheap run stops before measuring anything, although my 2041Z ruling expects its other measurements. Let the fetch return the record for every exit code, clearly labelled, and let the cheap run complete its measurements and its copy when no finite limit is found, reporting that fact (full mode stays blocked on it). If changing `live_entry.py` alters the node bundle's hash, say so; that part then needs my diff read too.

LOW items after the cheap run, not now, except this one because it can lose a result: `live_entry.py:471-474`, a memory alarm during cleanup turning a printed success into exit 1. Fix it in the same diff if it is a few lines.

The full copy's two acceptance conditions go into the operator file as explicit lines of the cheap run's acceptance record: (a) the memory limit the helper watches belongs to the cgroup that holds the trainer, not only to the helper's own step; (b) `srun` completed under the limits it was given.

Post one RESULT with the diff file and the new hashes; I read the diff myself and then give the operator its order for the cheap run, for the window after the step-100 export and the next save (about 21:50Z).