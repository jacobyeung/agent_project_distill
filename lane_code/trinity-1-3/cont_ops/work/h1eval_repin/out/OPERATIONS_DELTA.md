# Operations status: no package to submit

`REPORT.md` explains why the build stopped. `TOKEN` is reserved only. Do not install the extracted audit sources as a replacement package or submit that token.

The intended export receipt is `/project/community/jjyeung/okh7/x_3fdda0fb/o/gcs_17c4ffa4_m100.done`. Its object must be exactly `q8/8865619b/17c4ffa4_m100.tar`. Its positive byte count and full SHA256 describe the whole archive formed by ordered parts `00`, `01`, `02`, `03` from bucket `cmu-gpucloud-jjyeung`, with suffixes `.partNN-of-04`.

The reviewed stager accumulates those four streams into one job-local archive, checks the total byte count and SHA256, and only then admits extraction. The current H1-0 job instead copies pinned project-disk parts. No integration between those paths was implemented in this stopped build.

The artifact’s `heads` and `full_weights` records provide their hashes; the full-weights record pins `full_weights/full_weights.json`, whose entries pin the tensor files and index. The artifact’s own hash and each exact byte count should be computed from the authenticated archive. The enclosing member directory must be observed, not inferred from `m100` in the GCS object name. The m100 artifact bytes are unavailable here. Its `config_sha256` must be compared with `84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb` before claiming compatibility with the frozen restore.

The existing camera selection is:

```json
"types": ["camera_displacement", "camera_rotation", "camera_movement_direction"]
```

Run 170631 used one NVIDIA H100 80GB HBM3 on `general`. Its first three phases completed 1,050 reads: 450 displacement, 300 rotation, and 300 movement-direction reads. The timestamps in its returned `STEPS.jsonl` give 7,321.985 seconds from the first camera phase start to the last camera phase exit, approximately 2 hours 2 minutes. The read-only samples total approximately 7,039.222 seconds; the phase timing includes worker/model startup. The full run subsequently failed in the distance phase, so its overall completion status is not evidence of a complete five-type run.

A provisional camera allocation would be **04:00:00 on one H100**: approximately 2:02 measured camera work, the unchanged 30-minute stop margin, and approximately 88 minutes for staging, CPU preparation, and variation. This fits the unchanged five GPU-hour cap. A slower m100 checkpoint or cloud transfer may still produce a partial run; no automatic retry should follow. The production submission helper requests `--gres=gpu:1` without an H100-specific constraint, so the operator must verify the assigned card type rather than assume that flag selects H100.

The H1-0 camera analysis script is `in/h10_operator_from118/work/proof/submerge.py`. It requires all planned records for the three-type prefix and calls the package’s `measure`, `write_curve`, and table functions. `submerge3.py` is a partial-read analysis variant and is not interchangeable with that complete-camera check. Bootstrap settings are fixed in production `h1eval/statistics.py`: room units, 10,000 draws, seed 20261115.

The complete-camera script also checks the evaluator hash against returned journals. Camera run 170631’s evaluator hash differs from the supplied authoritative production archive, so scoring its old return with this archive will fail that check. A new read and its scorer must use the same sealed package. No check was weakened to reuse the old camera return.

The unchanged fetch convention is the package token followed by the numeric allocation ID formatted as eight hexadecimal digits. The helper verifies the returned archive hash and uses the existing framed transfer. Exact package placement, a replacement CPU check, submit, fetch, and scoring commands are intentionally not presented as runnable instructions: no replacement package passed this build. The existing `3.py check` produces only a metadata `scope:0` receipt; it does not satisfy the requested empty-root check in the real node environment.
