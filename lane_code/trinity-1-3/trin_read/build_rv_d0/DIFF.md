# build_rv_d0 differences

The active payload is `rv_payload/`. Its 84 production payload files match every SHA256 in job 170037's CONFIG. The source package hash is `ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b`. `RV_SOURCE_EVIDENCE.json`, `RV_PAYLOAD_PINS.json`, and `PACKAGE_MEMBER_CHECK.json` record the checks. The staged payload files are unchanged. D0 applies the identity-only adapter overlay described below; no scorer, prompt builder, sampler, budget code or proof file is patched.

## Compared with kit_revsi

| File or boundary | Class | Difference |
|---|---|---|
| `rv_payload/reader/`, `cohort/`, `inputs/`, `parity/`, selected `proof/`, `launcher/MODELS.json`, `TRANSPORT.json`, `vllm_isolated.sh` | PATH/ENV | Byte-identical production payload, relocated under a read-only namespace bind. |
| `rv_payload/launcher/{trace_runtime.py,ORCHARD_ASSETS.json}`, `media/NEED_261.json` | PATH/ENV | Byte-identical support files from the reviewed source, pinned locally. |
| `rv_read.py:make_config`, `namespace`; `rv_entry.py` | PATH/ENV | Local run/output paths, explicit video-root bind, unchanged staged interpreters; invoke the original chain without Orchard bootstrap, cloud publishing, or scheduler submission. The absent optional supplied plan lets the kit compute and verify its decoded plan. |
| `rv_read.py:extract_media`, `media_check`, `runtime_check`, `pins_check` | BEYOND | Local exact-manifest tar admission, successful receipt, pre-use rehashing, runtime descriptor equality, and payload verification. No shared media path is opened. |
| `rv_read.py:card_admission`, `launch` | BEYOND | Two empty card readings, local single-use tokens, proof prerequisite, space reserve, vnice, sandbox/probe receipts, stub audit, sampler audit, and terminal packet hashes. |
| `rv_read.py:select_artifact`, `rv_d0.py` | BEYOND | Admit pinned step 544 or a complete stage-export receipt for lineage `8865619b`, run `359fcc3c`, positive step. Apply the identity overlay below for D0. Refuse 64 anchors before GPU admission. |
| `rv_read.py:compare`, packet verification | BEYOND | Read-only per-item token/score comparison across all three arms; validate membership and stored scorer means. No answer rewriting or new score extraction. |
| Proof configuration | PATH/ENV | Run kit phase A with real processor checks and its original synthetic engine; `phase_b=false`, as documented for proof 170035. Production still uses the original real-engine path. |
| `rv-stage`, `rv-proof`, `rv-read`, `rv-compare` | PATH/ENV | Local system-Python CLI entry points. |

Engine settings, cohort membership, prompt bytes, frame plans, max_seqs 32, and inflight 16 retain the kit contract. Only D0 model identity changes through the recorded overlay. The output report paths are unchanged. Wrapper evidence adds files around that packet.

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


## Compared with build_rv

The adapter overlay is **BEYOND**. Its source SHA256 is `a10f34f4b6d240e0e366e56c9928f1c7d9cd080a91886d6a3a1d6c1381b35109`. The wrapper requires that exact source before making these four substitutions. Here `H` is the stage-export receipt's artifact SHA256, checked against the artifact and checker evidence; `S` is the receipt's positive optimizer step, checked against its allowlisted path, artifact and checker result.

| Site | Exact original source | Replacement source |
|---|---|---|
| Module constant used by `model_specs`, bind and launch | `EXPORT_SHA='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'` | `EXPORT_SHA='H'` |
| `bind` full-checker argument | `models['base']['path'],544)` | `models['base']['path'],S)` |
| `bind` reader identity | `reader=dict(step=544,` | `reader=dict(step=S,` |
| `launch` full-checker argument | `cfg['models']['base']['path'],544)` | `cfg['models']['base']['path'],S)` |

The wrapper substitutes actual values for `H` and `S`, requires each old snippet to occur exactly once, and records all four literal replacements and the resulting SHA256 in each packet. No broad string replacement or checker bypass occurs. Step 544 uses the original adapter file directly.

| File or boundary | Class | Difference |
|---|---|---|
| `rv_d0.py` | BEYOND | Admit complete D0 staging/checker evidence; reject links and special files; render, pin and audit the four-substitution overlay; describe model dependencies of proof. |
| `rv_read.py:select_artifact`, `make_config` | BEYOND | Cross-check D0 receipt identity and populate `spec.step`, `spec.artifact`, `spec.models.cp1m200`; add `spec.adapter_overlay` evidence. All other model and protocol pins retain their values. |
| `rv_read.py:namespace`, `launch` | BEYOND | Bind the verified overlay file read-only in the probe and reader sandboxes; audit effective adapter/model identity and full-checker success; pin D0 evidence in EXIT. |
| `rv_read.py:proof_check`, `output_pins` | BEYOND | Require the same D0 artifact, staging evidence, overlay and proof scope; authenticate the adapter, receipts and bound request/code pins. Step-544 output pins retain the original set. |
| `rv_entry.py` | BEYOND | For D0 only, check the mounted adapter SHA before entering the unchanged chain. |
| `tests/test_rv.py`, `tests/test_rv_d0.py` | BEYOND | Update the missing-receipt refusal expectation; add receipt/checker/identity/link attacks, real-checker tiny exports, real adapter bind/launch checks, overlay tampering, packet receipts and step-544 equivalence. |
| `README.md`, `DIFF.md`, `REPORT_RV_D0.md`, new validation evidence/logs | BEYOND | D0 operation, exact contract changes, tests and limitations. |
| Build location | PATH/ENV | `build_rv_d0` is the bound wrapper path; staged runtime and logical kit paths retain their values. |

The payload, payload pin manifest, inherited runtime/staging modules, engine options, llguidance stub, cohort, media, scorer and comparison implementation retain their build_rv bytes or behavior. The unchanged chain's `AUTHORIZATION.json.step` remains the literal protocol label `544`; selected identity is recorded separately and this limitation appears in `PROOF_SCOPE.json`. The unchanged adapter error message still names step 544. No production result or GPU fit is claimed by these CPU fixtures.
