# build_rv differences

The active payload is `rv_payload/`. Its 84 production payload files match every SHA256 in job 170037's CONFIG. The source package hash is `ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b`. `RV_SOURCE_EVIDENCE.json`, `RV_PAYLOAD_PINS.json`, and `PACKAGE_MEMBER_CHECK.json` record the checks. No reader, scorer, prompt builder, sampler, budget code, or proof file was edited.

## Compared with kit_revsi

| File or boundary | Class | Difference |
|---|---|---|
| `rv_payload/reader/`, `cohort/`, `inputs/`, `parity/`, selected `proof/`, `launcher/MODELS.json`, `TRANSPORT.json`, `vllm_isolated.sh` | PATH/ENV | Byte-identical production payload, relocated under a read-only namespace bind. |
| `rv_payload/launcher/{trace_runtime.py,ORCHARD_ASSETS.json}`, `media/NEED_261.json` | PATH/ENV | Byte-identical support files from the reviewed source, pinned locally. |
| `rv_read.py:make_config`, `namespace`; `rv_entry.py` | PATH/ENV | Local run/output paths, explicit video-root bind, unchanged staged interpreters; invoke the original chain without Orchard bootstrap, cloud publishing, or scheduler submission. The absent optional supplied plan lets the kit compute and verify its decoded plan. |
| `rv_read.py:extract_media`, `media_check`, `runtime_check`, `pins_check` | BEYOND | Local exact-manifest tar admission, successful receipt, pre-use rehashing, runtime descriptor equality, and payload verification. No shared media path is opened. |
| `rv_read.py:card_admission`, `launch` | BEYOND | Two empty card readings, local single-use tokens, proof prerequisite, space reserve, vnice, sandbox/probe receipts, stub audit, sampler audit, and terminal packet hashes. |
| `rv_read.py:select_artifact` | BEYOND | Apply build_t6 lineage admission and explicitly refuse any identity the unchanged kit rejects, including D0. Refuse 64 anchors before GPU admission. |
| `rv_read.py:compare`, packet verification | BEYOND | Read-only per-item token/score comparison across all three arms; validate membership and stored scorer means. No answer rewriting or new score extraction. |
| Proof configuration | PATH/ENV | Run kit phase A with real processor checks and its original synthetic engine; `phase_b=false`, as documented for proof 170035. Production still uses the original real-engine path. |
| `rv-stage`, `rv-proof`, `rv-read`, `rv-compare` | PATH/ENV | Local system-Python CLI entry points. |

Engine settings, cohort membership, model identity, prompt bytes, frame plans, max_seqs 32, and inflight 16 retain the kit contract. The output report paths are unchanged. Wrapper evidence adds files around that packet.

## Compared with build_t6

| File or boundary | Class | Difference |
|---|---|---|
| `trinity_read.py:probe` | PATH/ENV | Add optional `namespace_factory`; default behavior is unchanged. ReVSI supplies the same namespace with the local wrapper and payload binds. |
| `rv_read.py`, `rv_entry.py`, `rv-*`, `rv_payload/` | BEYOND | Add a separate ReVSI command family using its reviewed chain and scorer. The inherited dev-S1 command family remains available. |
| GPU admission | BEYOND | Build_t6's `check_card` takes one reading. ReVSI calls it twice, 60 seconds apart, records both, and checks UUID stability. |
| Model/frame handling | BEYOND | ReVSI checks the 261-video manifest and invokes the kit's original model copies. It does not use dev-S1 PNG shards or the optional model hard-link path. |
| `tests/test_rv.py` | BEYOND | Add CPU fixtures for staging attacks, hash failures, runtime mismatch, model/frame refusal, card admission, packet execution/failure, real-scorer comparison, and corrupted inputs. |
| `README.md`, `DIFF.md`, `REPORT_RV.md`, `RUNTIME_FIT.json`, evidence JSON and test logs | BEYOND | ReVSI operation, limitations, source authentication, runtime/frame accounting, and validation evidence. |
| `revsi_kit/`, `RV_KIT_PINS.json` | PATH/ENV | Inactive source snapshot retained as evidence; it is neither mounted as the active payload nor imported by the ReVSI runner. |

All other inherited Python modules retain their build_t6 bytes. `BASELINE_FILE_CHECK.json` records the bounded top-level source comparison. The active reader and scorer were authenticated against the production payload, not inferred from filename similarity.
