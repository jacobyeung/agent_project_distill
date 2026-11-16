# Guard-read kit: G5 sealed; production authority required

The final report pin matches the operator-authorized source. All 158 tests pass (`TESTS.json`), and all 31/31 mutants are detected in a fresh run (`MUTANTS.json`). The report and its test-source hashes are verified before and after validation (`REPORT_PIN_G4.json`).

The production package differs from G4 only in the report pin in `worker.py`. FAMILY differs from `2b5563214dd1c99b49551278fe4ec53c3867d5a746b141e36c543d94f0eec7a5` only in `code_pins.worker.py`; all other fields, including `release_ready: false`, retain their values (`FAMILY_CHANGES_G5.json`). The input archive, production inventory, inherited C8r code and reviewed stager retain their bytes (`G5_SEAL.json`, `SOURCE_IDENTITY.json`, `FINAL_AUDIT.json`).

Every report call binds the candidate artifact. The coordinator retains stage/checker receipts, and return verification rejects missing evidence (`G4_TESTS.json`, `G4_RETURN_EVIDENCE.json`). The C8r diff matches the sealed code (`DIFF_C8R.json`, `DIFF_C8R.patch`). Documented transfers use the registered serial-governor wrapper (`RUN.md`).

The seven trainer-tree names are ACCEPTED by ORCH 1601Z. The CPU-fixture blocker is CLOSED on operator-supplied evidence. Production requires a review bound to the current FAMILY, a completed milestone closure/export and exact ORCH GO (`RELEASE_BLOCKERS.json`).

| Artifact | SHA256 |
|---|---|
| `code_g2.tar` | `6024aa2be082b1881a8e33f52dcaa7d57c209858d6a1adf8d25bbb97516cb54e` |
| `inputs_g2.tar` | `3be24165b9856024dc5359b1760a8a1ad88f11022972fb3d075edb70c02aff72` |
| `FAMILY.json` | `23cadfceac2896ab0f5f0ae7edc05cca64af7925277539beae321b784cf2f302` |
| `candidate_m50/metadata.tar` | `d04e294d2cf2908fef45208280f9bc7313b0a54ae0b71d0be1403358a9cde443` |
| Required and observed report | `5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11` |

Reproduce with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, `nice -n 10` and numerical-library threads set to one: `work/family.py --g5`, `work/seal.py --g5`, `work/g4_diff.py`, `work/run_g4_tests.py --g5`, then `work/finish.py --g5`.

Not checked: real tensors, GPU parity, token identity, the namespace worker, live Orchard/GCS/pool/credentials or governor transfers. G5 did not access `out/rehearsal/whole/`. Size and timing are recorded in `BUILD_SIZE_G5.json` and `../work/TIMING_G5.json`.
