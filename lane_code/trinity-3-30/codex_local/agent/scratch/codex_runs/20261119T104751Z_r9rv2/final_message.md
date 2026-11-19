1. **[pbjob.sh:247](/scratch/jjyeung/orch_n30/r1_ops6/work/pb/pbjob.sh:247): `job_id` differs from `hr2.sh`.** The receipt serializes `SLURM_JOB_ID`; this script supplies the new recompute job, while `hr2.sh:67` supplies `172660`. For exact receipt equality, use the recorded source job:
   ```python
   'SLURM_JOB_ID='+str(a['job'])
   ```
   Keep the recompute job ID in `pb_report.json`.

The applied fixes otherwise check out: mount destinations exist in the required order; `/tmp` preserves `q.zip`; system Python targets remain visible; `/run`, `/sys`, and `/etc` introduce no verified failure. The timing wrappers and phase sum are correct. Shell and Python syntax checks pass.

The job-private `/tmp` evidence resolves former defect 5. The supplied survey does not establish the venv’s exact Python symlink target.

**NO-GO for exact receipt equality; no other verified remaining defect.**