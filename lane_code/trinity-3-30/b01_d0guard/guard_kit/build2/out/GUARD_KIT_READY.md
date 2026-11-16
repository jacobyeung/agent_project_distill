# Guard-read kit: NOT READY

The package contains candidate closure admission, production packet and worker code, and an operator rehearsal command. It is not ready to submit. Runtime naming remains incomplete, and the whole-worker path has not run (`RELEASE_BLOCKERS.json`). The delivered family rejects production packet emission; unit tests use explicitly fabricated authority (`FAMILY.json`, `PACKET_TEST.json`).

The real candidate metadata passes config-identity, preparation, source-seal, initialization-chain and unchanged restoration checks (`CLOSURE_ADMISSION.json`, `RESTORATION_TEST.json`). The export must match the selected closure artifact byte-for-byte before candidate execution (`guard_kit/staging.py`, `guard_kit/closure.py`). The actual candidate tensors were not supplied or loaded.

The coordinator stages both exports, launches fresh checkpoint processes, publishes proof and canary receipts before continuing, and returns a merged native-only bundle with in-job admission (`guard_kit/worker.py`, `guard_kit/checkpoint.py`, `guard_kit/admission.py`). Component tests verify authority refusals, milestone packet emission, subprocess isolation, receipt ordering and failure returns. They do not establish a production run.

The executed suites pass 124 checks (`TESTS.json`), and all 25 report mutants are detected (`MUTANTS.json`). The inherited backend and reviewed stager remain byte-identical (`SOURCE_IDENTITY.json`). The report remains unchanged (`FINAL_AUDIT.json`).

Run the operator rehearsal with `out/rehearsal/run_whole_worker.sh`, from this build directory, outside the sandbox. The sandbox attempt stopped at the namespace netlink refusal (`rehearsal/whole/sandbox/RESULT.json`). The command shares the production phase coordinator but retains fixture staging and allocation boundaries; it does not yet constitute a transport-only full-packet rehearsal (`rehearsal/RUNBOOK.md`).

Runtime naming is still blocked. The neutral outer metadata archive round-trips to identical file bytes, but the runtime does not consume the proposed config/item projections (`NAME_ROUNDTRIP.json`, `NAMING.json`). Renaming the prohibited trainer members changes the required source-tree digest even when every content hash stays equal (`NAMING_CONFLICT.json`). A canonical-name adapter remains unimplemented and unreviewed.

| Artifact | SHA256 | Evidence |
|---|---|---|
| `code_g2.tar` | `15d144c077cee098a7b016126d449705a4722677513f23070f85b8e3cc5a6551` | `CODE_MANIFEST.json` |
| `inputs_g2.tar` | `3be24165b9856024dc5359b1760a8a1ad88f11022972fb3d075edb70c02aff72` | `INPUT_MANIFEST.json` |
| `FAMILY.json` | `6a1d5c22ad16d66b2ae4b26539d3e302dcc402ff4d270e44ebac2122ba395825` | `FINAL_AUDIT.json` |
| `candidate_m50/metadata.tar` | `d04e294d2cf2908fef45208280f9bc7313b0a54ae0b71d0be1403358a9cde443` | `candidate_m50/CLOSURE.json` |
| Unchanged report | `6fead56128b2081314e52aa0ca6a7ab2f077aac72078554f2d1d7b61067aacc6` | `FINAL_AUDIT.json` |

`DIFF.md` records changed source blocks; `DIFF.patch` gives exact lines. `PIN_CLASSIFICATION.md` covers rows 1–46 with accepted values and implementation references (`PIN_CLASSIFICATION.json`). `RUN.md` gives closure fetch, preparation, packet, submission, return fetch and ledger commands. `SIZING.md` records provisional time and storage estimates. All remote commands remain unexecuted.

Not checked: real tensor restoration, GPU parity and token identity, complete worker execution, Orchard allocation, live GCS generations or credentials, result-pool state, installed operator/governor commands, and complete runtime naming. Independent review and the milestone-specific closure, export and ORCH GO records remain required (`RELEASE_BLOCKERS.json`).
