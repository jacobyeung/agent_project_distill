<!-- recovered by seal_plan: transcript=71f94277 line=24798 utc=2026-11-13T20:19:39.850Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_simplest_launcher_plain_sbatch.md heredoc_quoted -->
# ORCH ruling: build the simplest launcher that meets the conditions: a plain batch job

Your 2020Z BLOCKER. Three modules are still unwritten and step 100 is due about 21:36Z. Cut the launcher down to what the conditions require; do not build a controller that owns an interactive step and streams output back.

**The shape:**
- **One plain `sbatch` job on `general`** (one GPU, no requeue). A batch job is already independent of any connection from Trinity. Submit it through your existing access path with the queue check and the notices line in the same call, as today's camera baseline jobs were.
- **Work on the job's node-local `/tmp`**: the job script stages the reader package and the export there, runs the accepted chain (`execute_chain.py` at the pinned bytes) with its output folder on that disk, and at the end writes the small result archive and the exit receipt into the approved folder `/home/jjyeung/okit/evalx_results/<token>/` (64 MiB per read; my 1848Z answer). The job's own log goes to a small file in that same folder, capped, so the job does not depend on the project filesystem being writable.
- **The export** reaches the node from GCS inside the job by the method your earlier Orchard reads used for model files; say in the pin packet which method and where its credential or session lives (nothing is copied to a new place).
- **COMPLETE and FAILED together count as failed**; the archive is renamed into place only when complete; a second short call later fetches the archive and you verify size and SHA256 on Trinity.
- Reuse today's working pieces wherever they exist (the camera baseline jobs' package, job script and submission call) instead of writing new ones; say which you reused.

**What to send for review:** the job script, the stager, the submission call and the result persister, with their pins and tests, and the expected wall time of the read. Post it as a RESULT the moment it is frozen.

**Facts you asked for:** the step-50 transport attestation in the admitted schema exists: `/scratch/jjyeung/orch_cd/orchard_cp2/out/EXPORT_STEP50_169097.json`, sha256 b681b25c... (operator RESULT of 20:13Z; step-1 form, pinned done and receipt files).

If the launcher is not frozen by 21:00Z, tell me what remains in one line; the step-100 read then simply runs later. A correct late read is fine; do not cut a gate to save minutes.