# H1-kit-2

**Status: CPU implementation validated; two item sets remain unavailable.**
The evaluator CLI, R0 trainer filter and separate S1 patch are implemented.
The available RevSI set is pinned and clean. A production SFT/RL comparison
still requires missing task payloads and a validated native export/media binding.

## Delivered behavior

- `h1eval/cli.py` provides `items build`, `run`, `pair` and `curve`.
  `README_EVAL.md` gives the RL commands; `NATIVE_EXPORT_CONTRACT.md` defines
  the native loader's pinned inputs. The loader uses the reader's `E2EGenerator`.
- `h1eval/reader_core/` contains 15 copied reader/head source files.
  `READER_BUILD2_INPUT_SHA256.json` records their sources and hashes.
  The evaluator does not follow mutable reader source files during production runs.
- M1 reports every type's call rate and observed openers. It checks exact sequences
  for the three camera types and object distance. Direct types receive no
  false-call or route-correctness penalty. The question parser matches the
  operands of all 150 available native distance tasks and parses all 283 RevSI distances.
- M2 retains printed head errors and available per-frame pose/FoV/gravity/depth
  metrics. M3 compares answers with each intervention's own printed decision.
  Numeric eligibility requires at least 20% movement; options must change.
  Follow and stick use 5% tolerance; stick refers to the baseline answer.
  Direction options compare exactly. Bars are follow >= 0.80 and stick <= 0.10.
- `box_grid_5cm` is unchanged. On the fixture, scene scaling by two moves the
  printed gap from 0.11 m to 0.15 m, a 36.36% change. The printed-value copier
  scores follow 1.0, stick 0.0. No scorer converts or rewrites the model's text.
- Each run writes per-item JSONL, a readable report and `curve.json` with lineage,
  step, export/item/evaluator hashes, GT pins, frames, arms, modes and per-type
  M1/M2/M3/M4. Room bootstrap uses 10,000 draws, seed 20261115 and percentile 95% intervals.
  Means weight items; bootstrap samples whole rooms with replacement.
- Pair reports B minus A on shared item/arm/mode records. M3 differences use
  items eligible in both runs. Pair refuses different item sets, evaluator code,
  frames, loader/dependency/GT bindings, fixture status or intervention parameters.
  Curve prints metrics and hashes in SFT-step order followed by RL-step order.
- `h1.r0_rooms` binds the reserve text file by path and SHA256. Both supplied H1
  configs enable it. Preparation and admission filter pose, VQA, routing and
  pointing selections, with per-stream seen/removed/retained counts. Composite
  pose selections and MDG partitions use the same selection machinery.
  ScanNet rescans collapse to physical rooms; ScanNet++ aliases normalize;
  ARKitScenes IDs cannot match ScanNet or ScanNet++ rooms. Unknown room identity
  refuses. R0 rows bypass frame-layout and pointing-mask checks before selection.
- The R0 filter reuses `s1_exclusions.selection`/identifier handling and
  `carrier_c1_routing.excluded`. Admission authenticates the pin and prepared
  accounting again. A legacy unfiltered receipt receives an admission selection;
  tampered prepared selections refuse. Without the switch, these hooks do nothing.
- `faithful_own_rows.patch` contains S1 alone. `h1_rest.patch` contains S2,
  stopping, R0 and the remaining integration. Applying either order, or applying
  `h1_trainer.patch` directly, produces six byte-identical files matching `tree/`.
  The proof uses plain `patch`, zero fuzz, and retained copies under K/tmp.

## Item sets and unavailable inputs

| Set | State | Evidence |
|---|---|---|
| `revsi999` | Ready | 999 items; 283 distance questions all in meters; 37 room; 999 R0 checks, 0 overlaps |
| `devs1_routed` | Refuses | Native inventory has 636 IDs: 150 per camera type, 150 distance, 36 room; 450 camera task payloads are absent |
| `devs1_direct` | Refuses | e193 non-camera families contain 1,825 IDs; 1,525 main tasks are present, 300 forward/away payloads are absent |
| `r0dev` | Refuses without input | Supplied items must belong to the pinned R0-dev room list; development reads only |

RevSI source: `/scratch/jjyeung/orch_n30/b07_offread/in/kit_revsi/inputs/i1.json`.
Its canonical item-set SHA256 is
`7cc88e80aec9a495b4ebcd7fd62b763a03dfd9c464ae2b4918c7e870f06af368`.
The reserve pin matches `bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3`
and contains 372 rooms; R0-dev contains 100.

Bounded searches covered the supplied C8r copy and reader n13 tree. The native
inventory comes from `native/paired/request.json` in
`/scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/full_c8r/result.tar.gz`.
Its source/member hashes and type counts are retained in `items_sources/`.
The referenced camera task pin is `f59090ffc8fd0f4d80a2b049e2624660c0f46dbc1d26016145f4747850a432ac`;
its referenced path is absent on this node. The C8r mask-kit archive contains
186 matching routed IDs and no camera tasks. It cannot supply the missing set.

The direct inventory is the requested `e193_items.json`. Available task payloads
come from its staged `reader/work/vendor/r3/TASKS.jsonl`. The r4/r5 copies contain
adapter code but no forward/away task files. `BUILD2_INPUT_SHA256.json` records
these inputs. No unavailable set receives invented questions, room keys or labels.

Conservative choices: direct means the e193 main, forward and away families;
camera belongs to routed. Supplied routed tasks must match the native 636 IDs,
not merely its type counts. Ready manifests refuse replacement with changed
content. Unavailable manifests can become ready when complete inputs are supplied.
The builder never silently removes R0 items from a fixed evaluation denominator.

## Validation ledger

Run from K. Every Python command below starts with `bash cpu.sh`.
The wrapper uses the requested interpreter, CUDA hidden, offline loading,
K-local caches/temporaries, at most 16 threads and a 32 GiB address-space cap.
Pytest commands also use `-p no:cacheprovider`; evaluator tests use
`-p tests.reader_plugin`. Each `--basetemp` below is under `$PWD/tmp/`.

| Command after `bash cpu.sh` | Result | Log |
|---|---|---|
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/eval_build2" tests/test_eval.py -q` | 5 passed | `logs/eval_build2.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/build2_cli_r0" tests/test_cli.py tests/test_r0.py tests/test_eval.py -q` | 17 passed | `logs/cli_r0_build2.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/build2_cli_v2" tests/test_cli.py -q` | 7 passed, 1 failed: fixture opener metadata absent | `logs/cli_build2_v2.log` |
| Same CLI suite with `--basetemp "$PWD/tmp/build2_cli_v3"` | 7 passed, 1 failed: fixture attempted to reinstall existing opener tokens | `logs/cli_build2_v3.log` |
| Same CLI suite with `--basetemp "$PWD/tmp/build2_cli_v4"` | 8 passed | `logs/cli_build2_v4.log` |
| `-m unittest tests.test_trainer tests.test_stop tests.test_rows tests.test_own_forward tests.test_r0 -v` | 16 passed | `logs/trainer_build2.log` |
| `tests/patch_composition.py` | 3 compositions passed, 6 files each; both executions passed | `logs/patch_composition.log`, `logs/patch_composition_final.log` |
| `tests/first_step.py --tree "$PWD/tree" --out logs/off_h1_build2.json` | 4 complete rank plans, 288 microsteps | `logs/off_h1_build2.log` |
| `tests/compare_off.py --b logs/off_h1_build2.json --out logs/off_identity_build2.json` | 4/4 exact comparisons | `logs/off_compare_build2.log` |
| `tests/first_step.py --tree <faithful_only path from logs/patch_composition.json> --out logs/off_faithful.json` | 4 complete rank plans, 288 microsteps | `logs/off_faithful.log` |
| `tests/compare_off.py --b logs/off_faithful.json --out logs/off_faithful_identity.json` | 4/4 exact comparisons | `logs/off_faithful_compare.log` |
| `tests/faithful_patch_proof.py` | 13 checks passed; both executions passed | `logs/faithful_standalone.log`, `logs/faithful_standalone_final.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/build2_final" tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py tests/test_stop.py tests/test_rows.py tests/test_own_forward.py -q` | 29 passed; one tensor-to-scalar warning in a test assertion | `logs/build2_final.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --import-mode=importlib --basetemp "$PWD/tmp/reader_build2" /scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py -q` | 5 passed | `logs/reader_build2.log` |
| CLI suite with `--basetemp "$PWD/tmp/build2_cli_final"` | 9 passed, 1 failed: exact float assertion for GT interpolation | `logs/cli_final.log` |
| CLI suite with `--basetemp "$PWD/tmp/build2_cli_final_v2"` | 10 passed | `logs/cli_final_v2.log` |
| `-m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/r0dev_exit_final" tests/test_cli.py -k reserve_refusal -q` | 1 passed, 9 deselected | `logs/r0dev_exit_final.log` |
| `-m h1eval.cli run --export tmp/build2_cli_final_v2/artifact0 --items tmp/build2_cli_final_v2/test_tiny_cli_curve0/items.json --arms own --modes scale_translation:2 --out logs/tiny_final_run` | Tiny checkpoint run; baseline and intervention records | `logs/tiny_final_run.log`, `logs/tiny_final_run/curve.json` |
| `tests/build2_audit.py` | 49 syntax checks; 15 copy hashes; 150 exact operand-call matches; 283 RevSI parses; printed-gap acceptance | `logs/build2_audit.log` |
| `rows/mix_h1.py` | 2 configs rendered with the R0 pin | `logs/config_build2.log` |
| `-m h1eval.cli items build` | RevSI ready; two unavailable sets and R0-dev stub; expected nonzero exit | `logs/items_build2.log` |

The ten CLI tests cover real RevSI membership/R0 checks, unavailable-set refusal,
M3 thresholds and stick tolerance, room bootstrap, shared-eligibility pairing,
set-hash refusal, SFT/RL ordering, scorer hashing, a tiny checkpoint curve,
native inventory counts and GT-array provenance. The R0 suite uses real SQLite
selections for all four streams, composite pose order, both filtering phases,
pin/tamper refusal, rescan aliases, ARKit nonmatches and OFF identity.

The OFF comparisons reuse the retained sealed golden result and compare input
tensors, labels/masks, every microstep loss and post-update parameters. They
execute rank plans sequentially on CPU; they do not exercise collectives.
`BUILD_REPORT_BUILD1.md` preserves the complete retained command ledger and
passing evidence for the supplied kit. Those artifacts remain present.

## Unverified work

The native loader is implemented, but no real 9B export, staged RGB binding,
SAM 3/selector integration, production donor prefill, production GT run or RL
checkpoint was loaded. The tiny fixture uses a real small LM with scripted
sampled tokens; its curves are marked `fixture=true`. It does not establish
model accuracy or production loader compatibility. The selector socket refuses
SAM-text name embeddings; it accepts the reader's none/trigram modes.

No real training database, real first-batch 9B forward/backward, GPU, distributed
collective, long training run or benchmark accuracy was validated. The unrun
first-batch launcher still needs local artifacts and may exceed 32 GiB at 9B.
The sealed routing suite's external policy/pool fixtures remain absent; its
recorded 12 passes, 6 skips, 1 failure and 17 setup errors are not promoted to a pass.
The 64-frame path still refuses and lists its required compatibility work.

The kit is approximately 1.39 GB before the final checksum index, below 1.5 GB.
`SHA256SUMS` covers every retained regular file except itself. All writes stay
inside K. No Git, SSH, network, GPU, deletion or job relaunch was used.
The validation ledger retains failed test attempts because the user requires
all command outcomes; no superseded behavior is presented as current behavior.

## Build 3

**Status: CPU build validated. The real H1-0 read awaits b04's published `make_real` and staged weights/media.**

### Ready item sets and reserve pins

| Set | Items / R0 checked | R0 overlaps | State |
|---|---:|---:|---|
| `devs1_routed` | 636 | 0 | Ready; exact native inventory membership |
| `devs1_direct_main` | 1,525 | 0 | Ready; exact e193 main membership |
| `revsi999` | 999 | 0 | Ready; canonical item hash unchanged |
| `devs1_direct` | — | — | Refuses without the 300 facing-twin payloads |
| `r0dev` | — | — | Refuses without explicit development items |

Routed counts are 150 each for displacement, movement direction, rotation and
object distance, plus 36 room questions. All **450/450 camera questions (100%)**
parse to the move/turn call and `display_frame_pair` supplied by the native task.
The camera file matches `f59090ffc8fd0f4d80a2b049e2624660c0f46dbc1d26016145f4747850a432ac`.
The main file matches `a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e`.
The distance/room tasks come from that same main file. `BUILD3_INPUT_SHA256.json`
records all eight source copies, their paths, hashes and byte sizes.

`devs1_direct` accepts separate `--forward-tasks` and `--away-tasks` only after
checking the full native pins `4d6c3a9411d091d1f583a9e308525ca08dec55df05fe7c0a1c7c39e8043239af`
and `730ed5363f91a19c99de6f903b947066f5da3b19c42e70f095fa518ac54c5f15`.
A combined unpinned replacement cannot bypass the missing-twin refusal.

`auth/R0_ROOMS.txt` contains 372 rooms and retains the required `bdb5d402...` pin.
`auth/R0_DEV_ROOMS.txt` contains 100 rooms and matches `855ef477...`.
Configs, item manifests and the CLI use kit-relative pins; the trainer resolves
relative R0 paths against its kit location and verifies SHA256. Config rendering
also reads copied D0 inputs from `auth/`, so it needs no original staging paths.
The relocated config test and all three ready manifests pass from
`tmp/b3/relocated/`. That one 14.8 MB source/data copy excludes models and logs.

Conservative identity rule: when every identifier is ARKit and exactly one is a
physical venue, that venue identifies the room; native capture IDs identify its
recordings. Cross-dataset and other ambiguous identities still refuse. Manifest
rewrites may relocate pin paths only; pinned digests and item payloads must match.

### H1-0 behavior

`h1eval/h10/launch.py` imports `e2e_reader.real:make_real` from `--reader-root`
(or an explicit `--reader-entry`). It refuses a missing entry or a reader already
imported from another root. b04 owns loading, prefill and decoding. Own perception
uses the existing adapter with scale one, own pose/gravity/depth, no G3T and no
gravity guard. Tower calls pass `perception_factory=None` for every requested mode.
The launcher never changes the model's text, numeric formatting or units.

Shards use zero-based `i/n` over canonical IDs. Each arm/mode includes every shard
item; baseline `none` is always included. The launcher flushes and fsyncs each
complete JSONL record, locks the output, checks immutable resume bindings, and
skips completed tuples. Resume after a simulated reader failure preserves the
first completed record and runs only the seven remaining tuples. A torn JSONL
line refuses and requires a fresh directory; the launcher does not delete or
truncate it. Environment bindings pin items, export, artifact, reader, evaluator,
question parser and R0 code. Timings include model setup and each read.

`merge.py` requires complete, disjoint shard coverage and matching hashes. It
uses the existing evaluator's M1/M2/M3/M4 functions and `h1eval.cli.write_curve`,
then writes scored JSONL, `report.md` and `curve.json`. `run_card.sh` uses the read
vnice usage (`vnice.sh command args`), nice 10, a 32 GiB address-space cap and at
most 16 threads. It refuses a failed GPU query or memory usage above 1024 MiB.
Only a mocked `nvidia-smi` ran in this build. Operator notes contain 40 lines.

### Build 3 validation ledger

All Python commands use `bash cpu.sh` (Python `-B`, CUDA hidden, offline, 16 threads,
32 GiB). Pytest uses `-p no:cacheprovider`; commands with reader fixtures also use
`-p tests.reader_plugin`. All `--basetemp` paths below are under `$PWD/tmp/b3/`.
The retained tiny checkpoint is reused via
`H1_TINY_FIXTURE="$PWD/tmp/b3/h10_tests/artifact0"` for the final, pin and resume suites.

| Command / basetemp | Result | Log under `logs/b3/` |
|---|---|---|
| `-m h1eval.cli items build --sets revsi999,devs1_routed,devs1_direct_main` | First attempt: 1 ready, 2 refused for ARKit capture/venue ambiguity; exit 1 | `items.log` |
| Same item command after venue normalization | 3 ready, 3,160 R0 checks, 0 overlaps; exit 0 | `items_v2.log` |
| `rows/mix_h1.py` | 2 configs rendered; exit 0 | `configs.log` |
| `-m pytest tests/test_cli.py tests/test_r0.py tests/test_rows.py -q`; `items_tests` | 18 passed | `items_tests.log` |
| `-m pytest tests/test_build3_items.py tests/test_r0.py tests/test_rows.py -q`; `membership_tests` | 11 passed | `membership_tests.log` |
| `bash tmp/b3/relocated/cpu.sh -m pytest -p no:cacheprovider --basetemp "$PWD/tmp/b3/relocated/pytest_rows" tests/test_rows.py::Rows::test_configs_keep_d0 -q` | 1 passed from relocated code | `relocated.log` |
| `bash -n h1eval/h10/run_card.sh h1eval/h10/card_entry.sh` | First attempt failed on an apostrophe in parameter-expansion error text; corrected command passed | Tool output |
| `-m pytest tests/test_h10.py -q`; `h10_tests` | 6 passed, including real tiny decode | `h10_tests.log` |
| `tests/patch_composition.py` | 3 patch compositions passed; 6 byte-identical files each, zero fuzz | `patch_composition.log` |
| `-m pytest tests/test_build3_items.py tests/test_h10.py tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py tests/test_stop.py tests/test_rows.py tests/test_own_forward.py -q`; `final_tests` | 40 passed; one existing tensor-to-scalar test warning | `final_tests.log` |
| `-m h1eval.cli items build` | 3 ready; direct twins and unspecified R0-dev refuse as intended; exit 1 | `items_all.log` |
| `tests/build3_audit.py` | 8 copy pins, 30 syntax files, 450 camera parses, 3 relocated manifests, 2 missing-reader refusals; passed | `audit.log` |
| `-m pytest tests/test_build3_items.py tests/test_cli.py tests/test_h10.py -q`; `pin_tests` | 20 passed, including invalid twin-pin refusal | `pin_tests.log` |
| `-m pytest tests/test_h10.py -q`; `resume_tests` | 7 passed, including partial-run resume | `resume_tests.log` |
| `tests/build3_audit.py` | Final bounded audit passed | `audit_final.log`, `audit.json` |
| `tests/build3_seal.py` | Complete checksum membership, added bytes below 300 MB and free space above 200 GiB; passed | `seal.json`, `BUILD3_SIZE.json` |

The shell and item-build failures remain in this required command ledger.
The S1 patch is unchanged; the combined and remaining patches include the
relocatable reserve logic and pass composition checks. No training behavior,
answer post-processing or gap measurement rule was added.

### Size and unverified work

Build 3 adds approximately **198 MB**, below the 300 MB cap; `BUILD3_SIZE.json`
records the final byte counts. The deployable code/data selection is about
21.7 MB. Temporary files, test databases and retained tiny checkpoints all stay
under `tmp/b3/`; no tree or model is copied per test. The two created tiny fixture
artifacts are shared within their suites; subsequent suites reuse one artifact.
The checksum index hashes all code/data/docs and all new files; it retains prior hashes
only for unchanged temporary artifacts from the supplied builds. All writes remain
inside K. No Git, SSH, network, GPU, deletion or killed-job
relaunch ran. The node retains more than 200 GiB free.

No real step-544 weights, heads, media, SAM 3, selector, CUDA decode, card launch,
CPU real-weight first batch or benchmark accuracy was validated. Their remote
sizes are unavailable here; the operator note marks them unverified instead of
inventing measurements. Its 106 card-hour example assumes 60 seconds per read;
actual card-hours require a measured read time and model setup overhead.

The published reader must bind `model.h10_stage1_socket` or `model.sam3_tower`
and `model.selector_head` for own grounding. This binding is unverified; absent
components raise a clear error. Donor and GT perturbations retain the existing
adapter API and require explicit supplied Heads/GT through Python
`factory_options`; the CLI refuses those modes without inputs. The CLI-supported
numeric interventions and tower passthrough are tested. Real export/head lineage,
frame binding, production loader compatibility and 32 GiB fit remain unverified.

## Build 4

**Status: CPU fixes and the registered read plan are implemented. Review acceptance
remains blocked by two contradictory assertions in the unchanged reviewer file.**
The current evidence covers **88 passing tests and two failing reviewer tests**:
42 existing kit tests, five reader tests, 36 Build-4 tests and five reviewer tests
pass. The reviewer file is byte-identical to the supplied source; its SHA256 is
`eed915be8bf3c08de67045ff7adbfc3ab899d244da0d942be03e5a28f8657239`.

### Implemented behavior

- The stop metric counts direction-option changes, displacement differences
  strictly greater than 10% of GT, and wrapped rotation differences strictly
  greater than 10 degrees. It leaves faithful target text unchanged. Each S1
  optimizer step all-reduces successful own-camera counts and differing-answer
  counts, and logs their global share. Counts over steps 1–50 determine whether
  the run exports m100 and stops. The stop record names
  `h1_own_camera_answer_differs_gt_35pct_steps1_50` and includes the definition,
  counts and share. The report uses `H1_STOP` and `stopped_for_resume=false`.
  Resume reconstructs the window from consistent global counts in the metrics;
  missing or conflicting history refuses. Resume at the terminal milestone
  performs no updates. The LR horizon remains 1,000 steps.
- S1 catches MaterializeRefusal, RenderError, ValueError, KeyError, StopIteration
  and IndexError, records each refused row, and trains its GT batch. Every rank
  joins the readout when requested and the MAX failure-flag reduction. A remote
  refusal is visible to all ranks; each rank continues to backward.
- Both first-batch tools select the step-2 sampler plan and seed-17 gate draws.
  The tiny native optimizer proof completed 72 microsteps on each of four rank
  plans, with **4, 4, 6 and 5 successful faithful own rows**, respectively.
  The real-weight diagnostic executes backward, checks positive own-row counts
  per rank, and requires the preparation identity gate. It has not run here.
- Preparation checks all packed camera rows from the authenticated routing
  receipt bound by `cfg.streams.routing`. The preparation record contains the
  identity rate, per-type counts and refusal histogram. S1 admission requires
  at least 95% identity and a matching receipt pin. A failed preparation retains
  its report and refuses launch. `rows/faithful_gate.py ROWS` provides the same
  check for JSONL rows, JSON receipts and read-only SQLite rows on a CPU host.
- Registered modes are translation scales 0.5/2 for displacement, translation
  rotation 180 degrees for movement direction, turn negation for rotation,
  and scene scales 0.5/2 for object absolute distance. Names and parameters form
  distinct record, statistic, pair and curve keys. Direct items receive only
  baseline reads. The tower receives only one baseline read per item.
- M1 emits threshold values and explicit pass flags: routed call rate >=98%,
  exact sequence >=95%, answer-before-call <=1%; direct false calls <=2%
  overall and <=5% per type; ReVSI distance call rate >=95%. M2 pairs own and
  tower task accuracy by item and type, bootstraps physical rooms 10,000 times
  with seed 20261115, and reports percentage-point differences. Adequacy requires
  the lower 95% bound to be strictly above -5. Unserved routed calls score zero.
- H1-0 prints its read count before decoding. Dev-S1 requires 636 + 900 own
  reads and 636 tower reads; ReVSI requires 999 + 566 own reads and 999 tower
  reads. `--tower-from DIR` reuses complete baseline records only when export,
  item-set, item-file, reader and artifact hashes match. The directory contract
  is documented in `h1eval/h10/RUN_H10.md`. Resume skips completed records,
  including reused tower records. After ten actual decodes, the launcher writes
  measured seconds/read and projected card-hours to `projection.json` and its
  log; model-loading time is separate. No answer text is rewritten.
- Reserve compares the supplied digest with the registered `R0_SHA256` before
  loading the list. The combined patch and both patch orders produce six
  byte-identical implementation files, with zero fuzz. The standalone S1 patch
  includes its preparation gate and has no dependency on the rest of H1.

### Items and unresolved inputs

`devs1_direct` is ready with exactly **1,825 e193 IDs**: 1,525 main, 150 away and
150 forward. All 1,825 pass the R0 check; none overlaps. Its item-set SHA256 is
`b7b5c01ea9c2b176a10bfc9cb1442308666b75c17e03a194c8d9e63c418b7c53`.
`BUILD4_INPUT_SHA256.json` records the supplied twin paths, byte sizes and verified
hashes. The audit also rechecks the 636 routed, 1,525 direct-main and 999 ReVSI
items against their R0 pins. All four manifests have zero overlaps.

The real config-bound routing receipt is absent:
`/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/5e1d07a4/f/h/r16/receipt.json`.
The operator gate therefore refuses that input. The 12-row fixture and synthetic
packed-row SQLite gate tests pass; they do not establish the real identity rate.

Conservative resolution of the reviewer contradictions:

1. `test_F1_answer_differs_is_not_wrong_answer` compares exact answer strings,
   demanding that an own answer of 1.44 become GT 1.43. Faithful training requires
   the answer derived from the own printed value. The registered metric correctly
   counts this difference as false without changing the answer. The test remains
   failing; `test_faithful_training_keeps_own_printed_answer` verifies both facts.
2. `test_F2_step1_draws_own_camera_rows` demands an own draw at step 1. This build
   explicitly permits step 2. The tools use step 2 and prove positive own counts
   on every rank. The training sampler remains registered, and the test remains
   failing. Neither reviewer assertion was weakened or marked as an expected failure.

These conflicts prevent a claim that all seven reviewer tests pass. The reviewer's
file has no identity-gate test; the Build-4 suite supplies that coverage.

### Build 4 validation ledger

All Python commands below run through `bash cpu.sh`, which uses the requested
Python `-B`, hides CUDA, limits address space to 32 GiB and threads to 16, and
puts caches and temporary paths under `tmp/b4/`. Pytest adds
`-p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin`.
Each basetemp is a fresh directory under `$PWD/tmp/b4/`.

For compact commands below, `OLD` means `tests/test_build3_items.py`,
`tests/test_h10.py`, `tests/test_cli.py`, `tests/test_r0.py`, `tests/test_eval.py`,
`tests/test_trainer.py`, `tests/test_stop.py`, `tests/test_rows.py` and
`tests/test_own_forward.py`. `ALL` means `tests/test_build4.py tests/test_review.py OLD`.
Every log below is under `logs/b4/` unless another path is given.

| Command after `bash cpu.sh`, or shell check | Result | Log / basetemp |
|---|---|---|
| `-m h1eval.cli items build --sets devs1_direct --away-tasks <DEV_BACKDIR/TASKS.jsonl> --forward-tasks <DEV_FORWARD_TWINS/TASKS.jsonl>` | 1 set ready; 1,825 R0 checks, 0 overlaps | `items.log` |
| `-m pytest tests/test_review.py OLD -q` | 41 passed, 8 failed: two reviewer contradictions, fixture code pins, task-score metadata and stop initializer | `suite1.log` / `suite1` |
| `-m pytest tests/test_build4.py -q` | 31 passed, 2 failed: stop initializer and duplicate preparation receipt write | `build4_tests1.log` / `build4_tests1` |
| `-m pytest ALL -q` | 79 passed, 3 failed: two reviewer contradictions and the new mock's step argument index | `suite2.log` / `suite2` |
| `first_batch/run_first_batch.py --output logs/b4/first_batch_step2.json` | 4 rank plans passed; 288 forward/backward microsteps; own rows 4/4/6/5 | `first_batch_step2.log` |
| `tests/patch_composition.py` | Failed during the first composition: two overlapping preparation hunks; 0 complete compositions | `patch_composition.log` |
| `tests/faithful_patch_proof.py` | 13 checks passed against the retained Build-3 overlay; excluded from current-patch evidence | `faithful_standalone.log` |
| `rows/faithful_gate.py rows/camera_fixtures.jsonl` | 12/12 identical; 0 refusals; exit 0 | `faithful_gate_fixture.log` |
| `rows/faithful_gate.py <config-bound routing receipt>` | Expected refusal for absent file; exit 2; real gate unverified | `faithful_gate_real_refusal.log` |
| `-m pytest ALL -q` | 82 passed, 2 failed: unchanged reviewer contradictions | `suite3.log` / `suite3` |
| `tests/patch_composition.py` | Failed on the same overlapping hunks after the edit helper refused a non-unique anchor; 0 complete compositions | `patch_composition_v2.log` |
| `tests/patch_composition.py` | 3 compositions passed; 6 identical files each; zero fuzz | `patch_composition_v3.log` |
| `tests/faithful_patch_proof.py` | 13 checks passed against the current Build-4 standalone S1 overlay | `faithful_standalone_v2.log` |
| `tests/first_step.py --tree "$PWD/tree" --out logs/b4/off_h1.json` | 4 rank plans passed; 288 microsteps | `off_h1.log` |
| `tests/compare_off.py --b logs/b4/off_h1.json --out logs/b4/off_identity.json` | 4/4 exact OFF comparisons against the sealed golden result | `off_compare.log` |
| `tests/build4_audit.py` | Passed: source pins, four R0 checks, exact e193 membership, read counts, syntax and own-row counts | `audit.log` |
| `-m pytest ALL -q` | 82 passed, 3 failed: two reviewer contradictions and a missing `op` parameter in the new remote-refusal mock | `final_suite.log` / `final_suite` |
| `-m pytest tests/test_build4.py::test_remote_refusal_flag_keeps_local_collective_path tests/test_reader_build4.py -q` | 6 passed: corrected remote-refusal mock and all five reader tests | `targeted_final.log` / `targeted_final` |
| `tests/build4_audit.py` | Final audit passed | `audit_final.log`, `audit.json` |
| `bash -n cpu.sh first_batch/real_first_batch.sh h1eval/h10/run_card.sh h1eval/h10/card_entry.sh` | 4 shell files passed | Tool output |
| `tests/build4_seal.py` | Checksum membership, added-storage limit and free-space floor checked | `seal.json`, `BUILD4_SIZE.json` |

The reader tests reuse one shared tiny artifact. Their copied test source changes
only local bindings, fixture reuse and the tamper setup: one small scale-head file
replaces a whole-kit copy while preserving the checksum-refusal assertions.
`reader_test_source.json` pins that source and records the adaptations. The test
plugin retains temporary directories instead of deleting them. Existing tests
also use the parameter-bearing mode key, type-specific decode counts and a
mocked registered pin for the synthetic two-room R0 fixture.

### Size, limits and unverified work

Build 4 adds approximately **14 MB of distinct file storage**, below 100 MB.
`BUILD4_SIZE.json` records exact growth and free bytes; `SHA256SUMS` indexes every
retained regular file except itself. The shared fixture hardlinks 85,257,575 bytes
of unchanged payload already present in the kit; it allocates no model copy.
New temporary artifacts stay under `tmp/b4/`. The initial suite rewrote the
existing `tmp/b3/h10_tests/artifact0/h1eval.json` metadata before fixture reuse was
redirected to b4; its model payload stayed unchanged. The final seal requires at
least 200 GiB free. No Git, network, SSH, GPU, external write or deletion command ran.

No real 9B forward/backward, live distributed collective, training leg, GPU decode,
real tower-parity reuse, benchmark accuracy or real read-time projection ran.
Collective tests simulate remote counts and failure flags; rank plans execute
sequentially on CPU. The real routing-receipt census and b04's production parity
record compatibility remain unverified. Missing stop history refuses resume
rather than inventing the steps 1–50 denominator. The failed-test ledger and the
single temporary-path exception remain here because the user requires complete
validation accounting; these are the report's intentionally retained history.

## Build 5 (h1_headsft lane, 2026-11-16 ~16:00Z; ORCH RULING 1535Z)

**Status: the reviewer gate passes. 91 tests pass, 0 fail** (`logs/b5/suite.log`,
`tests/test_build4.py tests/test_review.py tests/test_reader_build4.py` plus the nine Build-4 `OLD` files).

- **F1 (ruling 1).** Faithful training stands: own-value rows train on the model's own answer even where it
  differs from GT. `test_F1_answer_differs_is_not_wrong_answer` now checks that a 1% own translation error
  keeps the own answer in the target and is not counted by the tolerance-based stop metric, while a 20% error
  is. The new `test_F1_perturbation_moves_answer_vs_unperturbed` applies the evaluator's own `perturb` to the
  own heads and checks the faithful answer against the SAME geometry's unperturbed answer: displacement
  scales by k = 0.5 and 2 (2% tolerance), the 180-degree rotation maps forward/backward and left/right
  options to their opposites, `negate_turn` negates the turn (1 degree tolerance); `scorers.usage` returns
  the same verdict whether or not the item carries a GT answer.
- **F2 (ruling 2).** Step 2 stands. `test_F2_step2_and_forced_pose_own_cover_every_rank` checks that step 2
  draws pose-own on a routing group under `configs/h1_1.json`, that both first-batch tools expose
  `--force-pose-own`, and that the forced schedule draws pose-own on every routing group at steps 1 and 2.
- **Forced pose-own run.** `tests/first_step.py --force-pose-own` sets `max_own_probability=1` and asserts
  that every camera routing row is own or a counted refusal; `first_batch/real_first_batch.py
  --force-pose-own` sets the pose decision to own on every routing microstep and logs any row that stays GT.
  Tiny native run (`logs/b5/first_batch_step2_forced.{json,log}`): 4 ranks x 72 microsteps, own rows
  8/8/11/11; displacement and rotation rows all own; movement-direction rows are counted `near_tie`
  refusals on the random tiny model; object-distance rows stay GT (depth gate, not S1).
- **Regression.** Unforced step-2 first batch: own rows 4/4/6/5 (`logs/b5/first_batch_step2.json`), equal to
  Build 4. OFF identity: 4/4 exact against the sealed golden result (`logs/b5/off_compare.log`).
- **Test environment note.** `test_loader_refuses_file_outside_manifest` needs a basetemp outside `/dev/`
  (the audit exempts `/proc/ /sys/ /dev/`), so the suite runs with basetemp `tmp/b5/`.
- **Portrait frames (ORCH NOTE 1527Z).** H1-owned code keeps aspect: the trainer feeds frames through the
  Qwen processor's `smart_resize`, and `h1eval.perception.own_profile` uses native `source_hw`. The fixed
  480x640 canvas lives in b04's vendored reader (`h1eval/reader_core/e2e_reader/stage1.py:90`, SAM 3 masks
  via `routed_features.SHAPE`) and the sealed tree's `routed_features.py`/`routed_candidates.py`; it affects
  grounding (`<ground>`/`<gap>`) calls only, not camera calls. Known defect, owned by b04. ARKitScenes share
  (upper bound of portrait items): revsi999 415/999, devs1_routed 47/636, devs1_direct 532/1,825.
