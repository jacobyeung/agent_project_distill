# H1-kit-1

**Status: blocked at evaluator acceptance.** The trainer patch and row tools pass their local acceptance checks. The evaluator has a reproducible failure of the requested exact `scale_scene` behavior. This kit is not ready for a real training or evaluation launch.

## Blocking result

Scaling own depth and translation by 2 changes a fixture's printed box gap from **0.11 m to 0.15 m**, rather than 0.22 m. The shared `trace_format/box_v313.py::grid_points` chooses sample counts with `ceil(extent / 0.05)`. Scaling the scene changes the sampling lattice, so `box_grid_5cm` is not scale equivariant. The acceptance test fails even with a 0.03 m rounding allowance.

The own adapter scales head outputs before formatting and retains the reader's gap implementation. It does not multiply a computed gap or repair the model's answer. Meeting exact gap scaling requires a decision about the measurement rule or the acceptance criterion. The failing test remains enabled in `tests/test_eval.py`; see `logs/eval_final.log`.

## Built artifacts

- `tree/` contains all 792 sealed source files and the H1 implementation. `patches/h1_trainer.patch` is a plain unified diff against the supplied tree. `COPY_MANIFEST.json` records every source copy and its SHA-256.
- S1 uses the existing gates and prefix readout, `row_geometry`, `rerender`, and the existing faithful materializer. It parses the **printed** camera responses, re-derives the target and answer, and retains all non-tool suffix tokens. Materializer refusals retain the GT batch and count the reason. Ground/gap rows remain GT-valued.
- S2 builds 32-frame camera/gravity targets from the routing row and calls the same `pose.loss` method with the same camera settings and `recipe.weights.pose`. Missing GT fields and non-camera rows receive masked targets and zero camera loss.
- Per-rank, per-step metrics group own/GT/refusal counts, refusal reasons, answer-change rates, camera supervision counts, and existing segment CE by type. Refused rows also count as GT because they train the GT batch.
- The stop path exports the milestone, checkpoints, writes `h1_stop_000200.json`, and returns `h1_stop_after_step`. It leaves the 1,000-step LR schedule intact.
- `rows/expected_calls.py`, `rows/faithful_check.py`, and `rows/mix_h1.py` provide call expectations, materializer identity auditing, and config rendering. `configs/h1_1.json` enables S1+S2; `configs/h1_1a.json` enables S1 alone. Both stop at 200 and export milestones 100 and 200. `configs/diff_against_d0.json` lists every change from the merged D0 config.
- `h1eval/` configures the reader's `E2EGenerator`; it does not implement a second decode loop. Its own adapter reads prefill head outputs, uses `OwnGeometry` for camera calls, and lifts stage-1 ground/gap masks with own depth, FoV, pose, gravity and scale 1. The tower arm calls the existing reader factory unchanged. The adapter supports translation scaling/rotation, turn negation, scene scaling, donor heads and supplied GT heads.
- The evaluator supplies pure M1 placement, M2 accuracy, M3 usage and M4 benchmark scorers, JSONL output and a type/arm/mode report table. M4 calls `evalpath.run.score_item`. Scoring converts expected values into question units; it never converts or rewrites the model's answer.
- `first_batch/run_first_batch.py --world 4` runs the native tiny-model first-step diagnostic. `first_batch/real_first_batch.sh` takes config, local model manifest, local preparation receipt, step-544 artifact and output paths. The real script is **unrun** and checks the initialization digest. It performs forwards without an optimizer update.

## Acceptance evidence

| Check | Result |
|---|---|
| OFF first step against sealed TREE | **4/4 rank plans identical**, 72 microsteps each, 288 total |
| OFF compared values | Input tensor, label and mask hashes; exact losses; post-update parameter hashes |
| Faithful camera identity | **12/12 raw and 12/12 packed rows**, 100%, no refusals |
| Expected calls | **14/14 fixtures**, 100%, all four routed types |
| Trainer focused suite | **6 passed**; final stop/resume suite **2 passed** |
| Native forced-own readout, faithful labels, S1+S2 forward/backward | **1 passed** |
| Row/config suite | **3 passed** |
| Sealed routing suite on patched tree | **12 passed, 6 skipped, 1 failed, 17 setup errors**; external fixtures missing |
| Unchanged reader `test_tiny_e2e.py` | **5 passed** |
| H1 evaluator suite | **4 passed, 1 failed**; scene-scale gap failure described above |
| Scripted usage | Copier follow **1.0**; ignorer stick **1.0** |
| H1 native first step | Four ranks, 72 microsteps each; all losses finite |

The OFF and H1 tests execute each rank plan sequentially on CPU with native `optimize_step`, including backward and an optimizer update. They do **not** run distributed collectives. The tiny model is the tree's native Qwen3.5 fixture with a character tokenizer for trainer traces. The reader tests use a tiny Qwen3 LM with the real local Qwen3.5 tokenizer and a script processor.

The H1 first step supervises 14, 13, 15 and 13 camera routing rows on ranks 0–3. Peak RSS is 473072, 477824, 478080 and 478340 KiB. Each rank trains 16 GT-valued routing rows. The exact seed-17 schedule draws no pose-own values in either routing reference group at step 1; the second group draws depth only. These draws are retained. A separate forced-own test exercises native own-head readout, faithful labels, both losses and backward.

The sealed routing failures all require absent files under `/scratch/jjyeung/orch_cd/leg_s1_tree`: the standalone policy test needs `out/ROUTING_POLICY_FROZEN_NO_FLAG.json`; 17 setup errors need `inputs/pool_s1_samples.json`. Six other tests skip absent review-pool/tokenizer fixtures. Their code remains unchanged. These are environment failures, not claimed passes.

## Test commands and logs

Run commands from K. `bash cpu.sh` uses `/scratch/jjyeung/envs/p1cpu/bin/python -B`, hides CUDA, disables network-dependent model loading, places caches and temporaries in K, caps address space at 32 GiB and threads at 16. The full-step and reader fixtures use two torch threads.

| Command after `bash cpu.sh` | Result / log |
|---|---|
| `-m unittest tests.test_trainer -v` | 5 passed; `logs/trainer.log` |
| `-m unittest tests.test_stop -v` | Initial stop check: 1 passed, `logs/stop.log`; final stop/resume checks: 2 passed, `logs/stop_final.log` |
| `-m unittest tests.test_trainer tests.test_stop -v` | 6 passed; `logs/trainer_final.log` |
| `tests/first_step.py --tree /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449 --out logs/off_sealed.json` | Four complete rank plans; `logs/off_sealed_v2.log` |
| `tests/first_step.py --tree "$PWD/tree" --out logs/off_h1.json` | Four complete rank plans; `logs/off_h1.log` |
| `tests/compare_off.py` | 4 rank comparisons passed; `logs/off_identity.json` |
| `-m pytest -p no:cacheprovider --import-mode=importlib tree/tests/test_carrier_c1_routing.py tree/tests/test_s1_routing.py tree/tests/test_e2e_routing_rows.py -q` | 12 passed, 6 skipped, 1 failed, 17 errors; `logs/sealed_routing_tests.log` |
| `rows/mix_h1.py` | Configs rendered; `logs/config_build.log` |
| `rows/mix_h1.py --frames 64` | Expected refusal, exit 2; seven required changes in `logs/frames64.log` |
| `rows/faithful_check.py rows/camera_fixtures.jsonl` | 12/12 identical; `logs/faithful_identity.json` |
| `-m unittest tests.test_rows -v` | 3 passed; `logs/rows.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --import-mode=importlib --basetemp "$PWD/tmp/reader_tests2" /scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py -q` | 5 passed; `logs/reader_unchanged_v2.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/eval_tests3" tests/test_eval.py -q` | 4 passed, 1 failed; `logs/eval_final.log` |
| `tests/first_step.py --tree "$PWD/tree" --out logs/h1_first_step.json --h1` | Four complete rank plans; `logs/h1_first_step.log` |
| `-m unittest tests.test_own_forward -v` | 1 passed; `logs/own_forward.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/eval_output_test" tests/test_eval.py -k tiny -q` | 1 passed, 4 deselected; `logs/eval_output.log`; emits `logs/tiny_eval_items.jsonl` and `logs/tiny_eval_report.md` |

Retained failed diagnostic attempts: synthetic camera generation initially lacked the external goal-exclusion pin; the synthetic-only fixture now substitutes an empty exclusion set. The first sealed-step attempt failed because the example ground rows store their events in `ground_record`; the fixture uses the existing `ground_rows.pack` to restore them. The first reader and evaluator collection attempts failed during changes to the reader's geometry API (`logs/reader_unchanged.log`, `logs/eval.log`). The evaluator's second complete run also reports the scene-scale failure (`logs/eval_v2.log`: 4 passed, 1 failed). No killed job was relaunched.

## Choices and limits

- The supplied override file is truncated after its complete `config` object. The renderer extracts that object with `JSONDecoder.raw_decode`, merges it recursively, and never opens paths named inside it.
- Sealed C1 packing retains `gt_pose9` and `gt_up`, but omits materializer metadata. For canonical single-call v3.11 camera rows only, the adapter restores the frame-gap declaration and derives missing GT direction-margin metadata from the original printed GT components. The materializer still checks the original prose, target, answer and decision. Other unsupported rows refuse.
- Ground fixtures copy the first two lines of each named example file. The 100% call-agreement denominator uses the 12 camera rows and two unit rows. Recovery rows are retained separately; their retries are not used to redefine the canonical expected sequence.
- The 64-frame path is refused. `rows/mix_h1.py::NEEDS_64` lists the carrier, pose, depth, grammar, grounding and compatibility work required.
- The own grounding geometry uses the existing metric VC `legacy_v3122` profile with scale 1 and the reader's `ReaderContract`. It computes no gravity-guard verdict or output correction. Camera responses use the direct own geometry; ground/gap depth uses the 51-point endpoint canvas grid.
- Turn negation uses a separate perturbed pose readout for turn formatting. Move, pose, depth and grounding calls retain their original heads for this intervention.
- Donor mode requires a different capture id. GT mode substitutes only supplied arrays/callables and records the substituted fields. No response-number table or fitted constant is loaded.
- Reader files are imported read-only. `READER_INPUT_SHA256.json` records their observed source hashes. The reader test plugin redirects its proof output to K and binds the patched tree without editing test source. The reader is an external mutable dependency; the hashes should be checked before reuse.
- `h1eval.runner` requires a caller-supplied factory that binds a real checkpoint, reader artifact, frozen SAM 3 and selector head. A complete real-artifact loading factory is not supplied or validated. The tiny evaluator uses test head parameters attached to its LM, not a 9B checkpoint.
- The real CPU first-batch script requires staged local manifests and receipts. Its 9B memory fit is unverified; the native loader and activations may exceed the mandatory 32 GiB cap. It does not perform a real backward pass or distributed update.
- No real rows database, step-544 weights, SAM 3 weights, selector checkpoint, 9B decode, native production artifact reload, GPU, distributed collective, long training run or benchmark accuracy was validated. The stop tests mock checkpoint/export I/O while executing the native stop loop, including a resume at the stop milestone with no extra update.
- No source outside K was modified. No Git, SSH, transfer command, network request or GPU job was run. All retained artifacts and caches are inside K.

The evaluator's exact scene-scaling acceptance remains open. The build stops with that failure visible; the partial evaluator and unrun real launcher are not production-ready. No borderline revision-history prose was retained outside the test-attempt ledger.

Syntax validation parses 24 implementation and fixture Python files without executing the real launcher (`logs/syntax.json`). The final reader source check matches all recorded hashes (`logs/reader_source_check.json`).

The kit contains approximately 438.5 MB before the checksum manifest, below the 1.5 GB cap. `SHA256SUMS` covers every retained file except itself, including copied sources, fixtures, logs and test artifacts.
