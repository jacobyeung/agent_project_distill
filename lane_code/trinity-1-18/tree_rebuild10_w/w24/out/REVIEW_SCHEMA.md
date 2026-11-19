The independent reviewer writes `<n_root>/n_r/review.json` after reading the job’s `live/v.json`, `identity.txt`, and `e0.json` through `e5.json`. The job polls every 30 seconds for at most 7,200 seconds from `WAITING_REVIEW.json`.

The `n_r` directory must belong to the job user and have mode 0700. The receipt must be a regular, non-symlink file owned by the job user with mode 0600. The job opens both without following symlinks. A missing directory or file remains pending; an unusable existing directory or file refuses.

The receipt has exactly these top-level fields:

- `verdict`: `PASS`.
- `config_identity`: `student_pilot.carrier_c1_run.identity(v.json)`, computed in the job view.
- `evidence`: an optional object containing every additional check, evidence hash, and reviewer-session identifier.

```json
{"verdict":"PASS","config_identity":"<prepared identity>","evidence":{"reviewer_session":"n_review1/<session>","checks":{},"hashes":{}}}
```

`launch_r1.entry.admit()` reads verdict and config_identity. It ignores evidence. Independent authorship remains the reviewer’s and orchestrator’s responsibility; no production review is supplied by this builder.

The job copies accepted bytes to `Q_NS/p/rv.json`, attaches their sha256 as `r1_training.review`, synchronizes the preparation receipt’s receipt pins, and writes `REVIEW_ACCEPTED.json` before calling t.py. Host and review pins do not change identity. The live v.json remains the exact snapshot the reviewer saw; the private v.json gains the accepted pin.

`out/arm_go.py` takes no review argument. It copies the GO template to a separate armed directory, verifies/scans it, and emits a three-file GO delta. The review is never staged in k/a.json or the upload set. Arming performs no upload or launch. GO=false jobs publish and wait too; t.py retains its GO check.

`N_IDENTITY.txt` describes the localised input, not the prepared production identity. Use only the identity published by the launch job for the receipt. A valid host receipt is still required before publication; see PRODUCTION_BLOCKERS.md.
