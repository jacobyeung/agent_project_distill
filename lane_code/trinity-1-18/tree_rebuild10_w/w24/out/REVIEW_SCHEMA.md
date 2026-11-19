`launch_r1.entry.admit()` reads exactly two review fields:

- `verdict`: the string `PASS`.
- `config_identity`: the exact value of `student_pilot.carrier_c1_run.identity(cfg)` for the final training configuration.

The review must be a JSON object. The independent lane `n_review1` writes it after its checklist passes. The builder supplies no production review. The orchestrator's launch GO is a separate decision.

The additional field `evidence` contains `checks` (named checklist results), `hashes` (SHA-256 pins for the checked artifacts), and `reviewer_session` (the independent reviewer session). `admit()` ignores this entire field; it does not authenticate a reviewer's identity. The reviewer and orchestrator must enforce independent authorship.

```json
{
  "verdict": "PASS",
  "config_identity": "<64 lowercase hexadecimal characters>",
  "evidence": {
    "checks": {"<check name>": "PASS"},
    "hashes": {"<artifact name>": "<sha256>"},
    "reviewer_session": "n_review1/<session identifier>"
  }
}
```

The kit stores the review pin in decoded `k/a.json` as `review = {path: "u/<sha256>", sha256: "<sha256>"}`. The resolver authenticates its bytes, stages it under the job namespace, and adds it to the staged-pin set. `h.py` verifies its digest, verdict and final config identity before writing `v.json`. It attaches a job-private snapshot through `r1_training.review`; the host result is attached through `r1_training.host_receipt`. Both pins are excluded from the identity function.

Run `out/identity.py`, then run `out/arm_go.py <review.json>` after the independent review exists. Arming writes a separate kit and a four-file upload delta: `n/k/a.json`, `n/SHA256SUMS.txt`, `n/BUILD.json`, and `u/<review sha256>`. It performs no upload or launch. An existing arming output refuses instead of overwriting it.

Production admission is BLOCKED. `N_IDENTITY.txt` identifies the decoded, localised input config, not an authenticated final production canary config. The hidden-view canary refuses at the production-store boundary before producing `RESULT.json.config`. Native preparation creates identity-bearing fields, so equality cannot be asserted safely. `PRODUCTION_BLOCKERS.md` and `work/build24h/IDENTITY_COMPARISON.json` state the exact evidence. A PASS review of only this input identity cannot replace review of the final identity that `h.py` checks.
