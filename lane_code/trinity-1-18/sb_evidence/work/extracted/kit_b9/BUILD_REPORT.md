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

## Build 6

**Validation: 100 passed, 1 skipped, 0 failed.** All 91 existing tests pass;
nine Build-6 tests pass. The skipped test needs the missing real JSON inputs.

The CPU fixture diagnostic implements the native S1 readout, faithful rendering,
tokenisation, forward and backward path, plus one native pose microstep per rank.
The tiny proof passes with and without forced pose-own. The real-weight run and
the supplied-real-JSON loading proof remain unverified: the entire directory
`/dev/shm/jjyeung/h1tmp/from118` is absent on trinity-3-30. No 9B weights were loaded.

### Files and behavior

- `first_batch/real_fixture_batch.py` accepts the requested CLI and exposes
  `run(args, loader=...)` for the tiny proof. The production loader calls
  `processor_for_receipt`, `load_model(evaluation=True)` and `load_artifact`.
  It removes lineage warm-start/depth-init fields before loading the explicit
  step-544 export. The artifact must match the config's full SHA256,
  `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef`.
  Missing declared files produce a clear `Missing node-local` error.
- `first_batch/real_fixture_batch.sh` derives K from its own location, accepts
  `PY` and `PY_OVERLAY`, forces CPU/offline operation, limits threads to 16,
  and puts caches and temporary files under the output directory. It imposes
  no address-space cap. `PYTHONHASHSEED=17` fixes the native set-derived stream
  ordering used by `mixed_indices`.
- `rows/ground_fixtures.jsonl` retains the two a0 rows used by `tests/first_step.py`,
  repacked with `ground_rows.pack`. Both fail the native `routing.c1_row` check
  with `Absolute label mismatch`. The diagnostic records their qids and reasons
  in `SUMMARY.json` and omits them. It does not change either answer.
- `tests/test_build6.py` exercises actual PNG loading, native `Rows.get`, carrier
  insertion, routing labels, own-head readout, faithful answers, pose supervision,
  loss and gradients. Its loader uses `tests.fixtures.tiny`; its pixel processor
  extends `tests.fixtures.Processor` for 4x4 synthetic RGB frames. It never uses
  the tiny fixture's prebuilt batch or `tests.fixtures.routing_batch`. Tests also
  check unchanged parameters, NaN-gradient failure, artifact-pin rejection,
  native-loader wiring, forbidden paths, and the wrapper's nonzero failure exit.
- `cpu.sh`, `tests/build4_plugin.py`, `tests/reader_plugin.py`, `tests/fixtures.py`,
  `tests/test_cli.py` and `tests/test_eval.py` honor `LANE_TEST_OUTPUT` for test
  scratch files and outputs. The regression reader reuses the existing tiny
  checkpoint without copying its payload or rewriting its metadata.

### Conservative fixture choices

The tool accepts the existing clip-manifest schema instead of adding a parity-kit
binding. A clip contains exactly 32 frame records with `path`, `sha256` and
`source_index`, plus positive `fps` and `total_num_frames`. Relative frame paths
resolve under `--frames-root`, or under the manifest's directory when omitted.
Absolute paths stay unchanged. The native pixel loader checks frame hashes.

The 12 camera programs keep their fixture poses, questions, targets and answers.
Their 1–32 slots bind to the clip's ordered source indices before `routing.c1_row`
packs them. This deliberately combines fixture labels with real pixels to test
the code path; it measures no accuracy or correspondence between RGB and GT pose.

An in-memory subclass overrides only `Rows.row`; the trainer's `Rows.get` and all
batch builders remain unchanged. A pose record uses the first camera fixture's
32 GT poses and gravity. It supplies masked depth placeholders because the fixture
has no GT depths. Thus every rank also executes a native pose forward/backward.

The step-2 plan uses `mixed_indices(counts, 2, start_step=1, seed=17,
training_mode='final', mix=recipe_for(cfg)['mix'], world=4)`. Fixture counts are
12 for routing and 16 for the other streams, matching the tiny first-step
convention; the lineage receipt supplies no training data. Routing indices map
modulo the admitted fixture count. The default selects routing microsteps 24 and
25 and pose microstep 0 on each rank. Gates use `decide(2, micro//factor)`;
`--force-pose-own` changes only the pose decision to True.

Each routing step calls the trainer's `own_values`, clears gradients, runs forward
and backward, and checks every non-None gradient. The tool allocates no optimizer
and updates no weights. Ranks execute sequentially in one CPU process; this does
not test distributed collectives. Forced runs fail if any selected rank has no
successful own camera row. Unforced runs require finite losses and gradients but
do not require an own draw from the selected prefix.

`real_fixture_batch.jsonl` records the original microstep, planned/fixture index,
gate decision, H1 audit, loss components, trained tokens, encode/readout/forward/
backward/gradient-check times and peak RSS. `SUMMARY.json` records the full plan,
per-rank own/GT/refused counts and refusal histograms, non-finite findings,
errors, elapsed time and pass flag. Outputs require a fresh directory. The audit
hook rejects `/home`, `/data*`, `/lustre`, symlink aliases to those roots, network,
subprocesses and deletions; file writes must stay under `--output`.

### Validation

All test commands use `/scratch/jjyeung/envs/p1cpu/bin/python -B` through `cpu.sh`,
with CUDA hidden, a 32 GiB address-space cap, at most 16 threads, and all current
test scratch paths under `tmp/b6`. The real-host wrapper does not apply that cap.

```bash
LANE_TEST_OUTPUT="$PWD/tmp/b6" PYTHONHASHSEED=17 bash cpu.sh -m pytest \
  tests/test_build6.py tests/test_build4.py tests/test_review.py \
  tests/test_reader_build4.py tests/test_build3_items.py tests/test_h10.py \
  tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py \
  tests/test_stop.py tests/test_rows.py tests/test_own_forward.py \
  -q -rs -p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin \
  --basetemp="$PWD/tmp/b6/suite2" > tmp/b6/suite2.log 2>&1
bash -n first_batch/real_fixture_batch.sh cpu.sh
```

The full suite completed in **65.08 seconds** (`tmp/b6/suite2.log`); both shell
files pass syntax checking. The retained development logs are `proof1.log`,
`proof2.log`, `proof3.log` and `suite1.log`, all under `tmp/b6`.

The tiny end-to-end runs each execute 12 microsteps: four pose and eight routing.
Forced own-camera counts are **1/2/1/2**; GT counts are **1/0/1/0**. The two GT rows
are counted refusals, `near_tie` and `movement_no_positive_option`. Unforced own
counts are **0/0/0/0**, because the first two pose-gate draws are closed. Both
summaries pass; losses and gradients are finite, and every parameter remains
unchanged. Forced rows keep the exact own answer in the trained suffix.
The final tiny forced run took **6.51 seconds**, with median routing/pose
microsteps of **0.575/0.409 seconds** and peak process RSS **533,516 KiB**.
The unforced run took **10.47 seconds**, including initial loader warm-up.

Storage added is **below 10.4 MB of allocated space** and **below 4.4 MB of
logical content**, including all retained test scratch directories. These are
conservative upper bounds: `tmp/b6/SIZE.json` counts every touched source/report
file in full, plus directory allocation and the five legacy output files. Both
bounds remain below the requested 20 MB. No tree, kit or model payload was copied.

The real-file test reads `B6_REAL_JSON_DIR`, defaulting to the requested
`/dev/shm/jjyeung/h1tmp/from118`. It explicitly skips when any of `model.json`,
`receipt.json`, `artifact.json` or `RESTORE.json` is missing. Once they are staged,
it checks the real artifact pin and expects file opening to fail on absent model
assets. The synthetic missing-file and native-loader-wiring tests do pass; they
do not substitute for that real-JSON proof.

The initial regression invocation rewrote existing `tmp/b4/artifact/h1eval.json`
metadata and four `logs/tiny_*` result files inside K. These legacy test writes
violated the requested b6 scratch boundary. The current helpers keep those inputs
read-only and redirect the result files under b6. No model payload was copied or
rewritten. No Git, network, SSH, GPU, process termination, deletion or write
outside K was used. This paragraph records a required boundary exception.

### Real-host command and timing estimate

Use a CPU host with the model, processor and export assets already staged at the
node-local paths named by their JSON files. The lineage receipt is used only for
loading; D0 row databases and its production identity gate are not needed for
this fixture diagnostic. This diagnostic does not replace that launch gate.

```bash
KIT=/path/to/extracted/kit
MODEL_JSON=/path/to/model.json
RECEIPT_JSON=/path/to/receipt.json
ARTIFACT_JSON=/path/to/step544/artifact.json
FRAMES_JSON=/path/to/clip.json
FRAMES_ROOT=/path/to/frames
PY=/path/to/python PY_OVERLAY=/path/to/optional/overlay \
  bash "$KIT/first_batch/real_fixture_batch.sh" \
  --config "$KIT/configs/h1_1.json" --model-manifest "$MODEL_JSON" \
  --receipt "$RECEIPT_JSON" --artifact "$ARTIFACT_JSON" \
  --frames "$FRAMES_JSON" --frames-root "$FRAMES_ROOT" \
  --ranks 0,1,2,3 --routing-per-rank 2 --force-pose-own --threads 16 \
  --output "$KIT/tmp/b6/real_forced"
```

Omit `PY_OVERLAY` when no overlay is needed. To test the registered unforced
draws, omit `--force-pose-own` and use a different output directory. The wrapper
inherits any limit imposed by its caller, so invoke it without `cpu.sh` or a
32 GiB caller limit on the real host.

**Guess, not a measurement:** allow 5–30 minutes per forced routing microstep
and 2–20 minutes per pose microstep for the 9B model on 16 CPU threads, plus model
loading and hash checks. CPU instruction support and processed token count can
move this estimate substantially. The JSONL timings provide the actual result;
the tiny model's sub-second microsteps do not predict 9B performance.

### Build 6 lane follow-up (h1_headsft, after the Codex build)
- Plan fidelity: the trainer seeds each stream's shuffle by `receipt['streams']` order (pointing, pose, routing, vqa,
  equal to `cfg['streams']` order), not by `set()` order. `real_fixture_batch.py` and `real_first_batch.py` now build
  `counts` in that order, so their step-2 plans match production regardless of PYTHONHASHSEED.
- Restored artifact: b04's `stage_restore` rewrites `full_weights.path` and `heads.path`, so the local artifact.json
  digest (2e9df594...) differs from the D0 pin. `--restore RESTORE.json` binds it: the record's original artifact must
  carry the pin 1d6eeb28..., must exist locally with that digest, and must equal the local artifact except those two
  paths. `test_real_json_loading_until_missing_weights` runs against the real JSON copies and checks both branches.
- `--threads` accepts 1..64 (run host 1-18 has 96 cores).
- Suite: 101 passed, 0 failed, 0 skipped (`logs/b5/suite_b6_lane.log`, basetemp `tmp/b6x/`).

## Build 7

The H1-0 launcher targets b04's reviewed `e2e_reader.parity:make_real` interface.
The full CPU kit suite has **109 passed, 1 skipped, 0 failed**. The skipped
Build-6 test requires `model.json`, `receipt.json`, `artifact.json` and
`RESTORE.json` under `/dev/shm/jjyeung/h1tmp/from118`; all four are absent here.
Thus this build cannot claim the requested no-skip validation or a real-weight
CPU first batch. No weights, RGB dataset or GPU were loaded on trinity-3-30.

### Files and behavior

- `h1eval/h10/launch.py` passes the artifact binding object, native items and
  settings to the reviewed factory. Both arms use b04's required `own_depth`
  setting. One model loads per decoded arm; each item gets a fresh perception.
  The launcher preserves fsynced records, immutable resume bindings, read plans,
  first-ten-read projections and the M1–M4 evaluator. It never rewrites text.
- `h1eval/h10/parity_adapter.py` maps and checks native task/frame metadata,
  converts b04 partition journals, selects the sealed native tree and pins only
  the parity runner's Python source. Restores, caches and growing journals under
  `parity_kit` are excluded from that code digest. `h1eval/__init__.py` selects
  the settings' native tree before the reserve checker imports trainer modules.
  The active host overlay is included in the effective settings' `env_roots`;
  both benchmark and diagnostic receipts record those effective settings.
- `h1eval/h10/perception_own.py` accepts b04's five keyword arguments. It supplies
  capture identity and image dimensions to the existing own adapter. Own pose,
  gravity and depth come from that read's prefill; scale stays one. Ground/gap
  use b04's StageOne socket, artifact-checked SAM 3 and selector head. Components
  are shared across items, while sessions and geometry are fresh. Perturbations
  go through `h1eval.perception.perturb` and refuse a mismatched target type.
- `h1eval/h10/cpu_first_batch.py` selects displacement, movement direction,
  rotation and absolute distance. Each gets baseline plus one registered mode:
  translation ×2, translation rotation 180 degrees, turn negation and scene ×2,
  respectively. `FIRST_BATCH.json` records exact texts, served/unserved calls,
  timings, intervention metadata and finite pose/gravity/depth checks. Partial
  read failures retain their receipt. The tiny reviewed-interface proof completes
  eight reads with one model construction; it does not measure model accuracy.
- `h1eval/h10/gpu_113.sh`, `host_run.sh` and `host_entry.py` use b04's bwrap view,
  vllm environment and overlay, with existing staged settings/restores. Updated
  `run_card.sh` and `card_entry.sh` keep the >1024 MiB refusal, vnice and nice 10.
  OUT contains all caches and temporaries. No wrapper restores inputs, copies
  data, retries jobs or kills processes. `RUN_H10.md` gives the input contract
  and commands. `merge.py`, the registered mode definitions and scorers are
  unchanged.
- `tests/build7_probe.py` imports the actual reviewed reader in an isolated
  interpreter. `tests/test_build7.py` covers its signature, keyword factory,
  native mapping, missing/staged ReVSI metadata, StageOne component reuse,
  eight tiny CPU reads, model reuse, resume, journal conversion/refusals, counts,
  native-tree bootstrap and the host busy-card guard. The legacy-entry test in
  `tests/test_h10.py` names its draft entry explicitly.

### Mapping, provenance and conservative choices

All **636/636** dev-S1 items map to `parity.key(task)` and pass real
`bind_item(..., verify=False)` metadata checks. Their questions, native answers,
options, types, source indices and physical-room identities agree. The kit's
released `ground_truth` labels remain unchanged; they differ from native `answer`
labels on some items and still drive the existing evaluator.

The mapping is `tmp/b7/devs1_mapping.json`. Its canonical mapping-list SHA256 is
`3dcf08279401b7d8c41a43acb7bd6d9f452173dffe98752d38f69b9e46aed881`;
the file SHA256 is
`ec0a05e1bf42ba8515ca55fdc2157ba0207f8dc13ba31783844a858fb11455bc`.
Every carrier layout has count 32. The mapping preserves b04's dense counts:
567 items have 64 dense frames, 69 have 32, and all have 32 pinned anchors.
It neither fabricates frames nor collapses b04's dense inputs.

Neither `B/parity_kit/settings_bw.json` nor its requested fallback
`B/parity_kit/settings.json` exists on 3-30. Metadata validation therefore uses
b04's published TASKS/FRAMES/DENSE defaults and a metadata-only frame root; it
makes no claim about run-host file availability. The production default is the
1-13 bwrap `settings_bw.json` path. The 1-18 commands explicitly select that
host's `settings.json` and `host_restore`.

ReVSI official999 has no staged native frame binding here. It refuses with
`frames not staged`. Stage a native task JSONL for all 999 exact official IDs,
with their unchanged question/type/options/dataset/scene/answer plus `native`
and `room`; stage the corresponding FRAMES and dense manifests and hashed RGB
files. Supply `item_sets.revsi999.{tasks,frames_json,dense_manifest,frames_root}`
in settings. Captures need 32 anchors, source indices, timestamps, fps and total
frame counts; dense entries need matching slots, indexed paths and hashes. The
synthetic staged-ReVSI test proves the adapter path only. It does not establish
coverage of official pixels.

Tower reuse accepts `<run>/gpu_results/own_depth_p*/items.jsonl`, with a sibling
`LOAD_RECEIPT.json` for every partition. It checks the `parity-load-v2` receipt
byte digest; each row's arm/settings/load/runtime digests; complete partition
coverage; cross-partition identity; export RESTORE content and pin; artifact
binding; task/config/request/frame/dense pins; perception settings; reader and
runner code inventories and hashes; decode-policy hash; and item key/type/room.
Duplicates, missing items, torn tails and altered provenance refuse. The full
registered set must be present even when importing into one H1 shard.

b04 rows carry model text, calls, finish, timings, scores, head outputs and layout,
plus the provenance digests above. They do not carry the kit's item-set digest;
native task-file pins and keys provide that check. Conversion verifies recorded
model identity without rehashing model payloads. Tower partitions must share a
runtime, but the converter does not require that runtime to equal the own run.
The launcher still authenticates its actual export/artifact before decoding.

Dev-S1 remains **636 + 900 own reads**, and ReVSI remains **999 + 566**. Each tower
item has one baseline; complete journal reuse adds zero tower decodes. No M1–M4
threshold, bootstrap seed, label, denominator or answer formatter changed.
The GPU wrapper omits an address-space cap because CUDA reserves large virtual
ranges. All Python validation here uses cpu.sh's 32 GiB cap and at most 16 threads.
No permission to exceed physical host capacity is implied by the wrapper.

### Validation commands and evidence

The full suite command is:

```bash
LANE_TEST_OUTPUT="$PWD/tmp/b7" PYTHONHASHSEED=17 bash cpu.sh -m pytest \
  tests/test_build7.py tests/test_build6.py tests/test_build4.py tests/test_review.py \
  tests/test_reader_build4.py tests/test_build3_items.py tests/test_h10.py \
  tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py \
  tests/test_stop.py tests/test_rows.py tests/test_own_forward.py \
  -q -rs -p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin \
  --basetemp="$PWD/tmp/b7/full2" > tmp/b7/full2.log 2>&1
```

It completed in **99.60 seconds**, with 109 passed, one missing-input skip and
one existing tensor-to-scalar warning. `cpu.sh` executes
`/scratch/jjyeung/envs/p1cpu/bin/python -B`, with CUDA hidden and
`PYTHONPATH=$PWD/tree:$PWD`. All test scratch files stay under `tmp/b7`.

The focused command uses the same environment, plugins and flags, replacing the
test list with `tests/test_build7.py` and using a fresh basetemp. `adapter3.log`
records nine passing adapter tests. `adapter2.log` records seven passing probes;
`adapter1.log` records seven old H1-0 passes and a test-fixture socket-signature
failure. `full1.log` records 107 passed and the same missing-input skip.
The final bootstrap/overlay check uses
`tests/test_build7.py::test_native_tree_bootstrap`, basetemp
`tmp/b7/bootstrap_final`, and log `tmp/b7/bootstrap_final.log`: **1 passed in
2.17 seconds**. The final CPU receipt and resume checks use
`tests/test_build7.py::test_reviewed_cpu_first_batch` and
`tests/test_build7.py::test_reviewed_resume`, with the same flags and environment,
basetemp `tmp/b7/receipt_final`, and log `tmp/b7/receipt_final.log`: **2 passed
in 33.35 seconds**. These checks cover the final effective-settings receipt fields.

The reviewed-interface CPU receipt is
`tmp/b7/receipt_final/reviewed0/cpu/FIRST_BATCH.json`. Its loader and decode step are tiny
stand-ins; the actual reviewed `make_real`, native binding and own perception
execute. The full suite separately retains the existing real tiny decode tests.
No result here proves step-544 real-weight compatibility or real-host throughput.

```bash
bash -n h1eval/h10/run_card.sh h1eval/h10/card_entry.sh \
  h1eval/h10/gpu_113.sh h1eval/h10/host_run.sh
```

### Exact run-host commands

These commands assume the complete kit is already staged at K on each host.
They make no SSH connection. Check the current allocation, RAM and card before
launch; run long commands in compute-node tmux. A killed run requires the user's
answer before any rerun. The builder did not launch these commands remotely.

On **trinity-1-13**, run the CPU diagnostic inside b04's existing bwrap view:

```bash
K=/scratch/jjyeung/orch_n30/h1_headsft/kit
bwrap --dev-bind / / --bind /dev/shm/jjyeung /scratch/jjyeung/b04shm \
  bash "$K/h1eval/h10/host_run.sh" cpu devs1_routed own 0/1 "$K/tmp/b7/cpu113"
```

The wrapper uses reader
`/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook`, its
`parity_kit/settings_bw.json` and `parity_kit/restore_bw`, Python
`/scratch/jjyeung/envs/vllm/bin/python -B`, and overlay
`/scratch/jjyeung/b04shm/b04/pyoverlay`. All caches live under `cpu113`.

After that CPU receipt passes, launch each GPU partition separately on an
assigned card. Set tower reuse before the first launch only when all b04
partitions are complete; omit it for an own-only journal.

```bash
export H10_TOWER_FROM=/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit
CARD=${ORCH_CARD:?Set the assigned card index}
bash "$K/h1eval/h10/gpu_113.sh" "$CARD" devs1_routed own 0/3 "$K/tmp/b7/devs1_p0"
bash "$K/h1eval/h10/gpu_113.sh" "$CARD" devs1_routed own 1/3 "$K/tmp/b7/devs1_p1"
bash "$K/h1eval/h10/gpu_113.sh" "$CARD" devs1_routed own 2/3 "$K/tmp/b7/devs1_p2"
```

These commands are not a retry loop. `ARMS=own` specifies new decodes;
`H10_TOWER_FROM` adds reused tower records. The binding cannot change on resume.
For ReVSI, use `revsi999` and separate output directories after staging its
native tasks/frames. Paired ReVSI also needs complete ReVSI tower journals;
the dev-S1 journals cannot supply them.

On **trinity-1-18**, use the specified local restore and scipy overlay:

```bash
K=/scratch/jjyeung/orch_n30/h1_headsft/kit
export H10_READER_ROOT=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
export H10_SETTINGS=$H10_READER_ROOT/parity_kit/settings.json
export H10_EXPORT=$H10_READER_ROOT/parity_kit/host_restore
export H10_PY=/scratch/jjyeung/envs/vllm/bin/python
export H10_OVERLAY=/scratch/jjyeung/orch_n30/h1_headsft_w/pyoverlay
bash "$K/h1eval/h10/host_run.sh" cpu devs1_routed own 0/1 "$K/tmp/b7/cpu118"
CARD=${ORCH_CARD:?Set the assigned card index}
bash "$K/h1eval/h10/host_run.sh" "$CARD" devs1_routed own 0/3 "$K/tmp/b7/devs1_118_p0"
bash "$K/h1eval/h10/host_run.sh" "$CARD" devs1_routed own 1/3 "$K/tmp/b7/devs1_118_p1"
bash "$K/h1eval/h10/host_run.sh" "$CARD" devs1_routed own 2/3 "$K/tmp/b7/devs1_118_p2"
```

b04's status describes 1-18 settings with `sam3: null`. Such settings refuse
before loading. That host must stage SAM 3 source/checkpoint/receipt, selector
and their artifact pins, then supply the local SAM/selector settings through
`H10_SETTINGS`. This build cannot confirm those assets on another host.

**GUESS:** 25–100 seconds/decode on an A6000-class card with SAM 3, based on b04's
reported smoke range. Dev-S1 own reads cost about **10.7–42.7 card-hours**;
ReVSI own reads cost **10.9–43.5 card-hours**, excluding loading. b04 also records
call-heavy items up to 430 seconds, so the range is not a deadline guarantee.
Use the first-ten-read projection to assess the ~13:00Z target.

### Storage and boundaries

Storage added is at most **19,070,976 bytes of allocated space (19.1 MB)**
and **14,680,064 logical bytes (14.7 MB)**, below the 20 MB limit. These
conservative bounds include directory allocation and edited files counted in full.
The final storage receipt is `tmp/b7/SIZE.json`; its totals include all retained
Build-7 scratch files and count every edited source/report file in full as a
conservative upper bound. No kit, code tree or model payload was copied. All
writes were inside K. No Git, network, SSH, GPU, process termination or file
deletion command ran. No source under B was modified.

The requested numbered Build section and validation ledger are retained as
build evidence; no superseded behavior is presented as the active contract.

### Build 7 lane follow-up (h1_headsft)
- `launch.py --types` / `H10_TYPES` (host_entry): decode one question type at a time, baseline and its registered modes
  together (ORCH 1739Z order: displacement, rotation, movement direction, absolute distance, then room). The shard
  binding carries the selected ids, so each type runs in its own output directory. `tests/test_build7_types.py` checks
  that the four types partition 600 items across shards with 1,500 own reads (600 baselines + 900 perturbed).
- My rerun of the Build-7 suite with the real JSON copies present: 110 passed, 0 skipped (`logs/b5/suite_b7_lane.log`).

## Build 8

The Orchard package is built at `orchard_h10/package`. It has **911 pinned source
and metadata files**, a 4,647,986-byte code archive, and an opaque Slurm job name:
`a15_cot_apb01ec87a6f29b`. The plan SHA256 is
`dfcfffe43e5783e6fe55df76e2b4f7034fa631eac9844c3bc28a8b8780ed3e61`.
Nothing was submitted, uploaded, downloaded, or run on a GPU.

The full CPU suite completed with **117 passed, 1 skipped, 0 failed** in
179.95 seconds. The skip is `test_real_json_loading_until_missing_weights`:
`model.json`, `receipt.json`, `artifact.json`, and `RESTORE.json` are absent from
`/dev/shm/jjyeung/h1tmp/from118`. No replacement metadata was fabricated. The
requested all-pass, no-skip result therefore remains unproved on this node.
Production submission also remains blocked on the concrete inputs listed in
`orchard_h10/OPEN_INPUTS.md`.

### Files and execution contract

- `orchard_h10/build.py` creates the code tar, embedded bootstrap, `BATCH.sh`,
  `CONFIG.json`, `SUBMIT.cmd`, package pins, and an unresolved input example.
  The tar contains K's tree, h1eval, auth, rows, dev-S1 items, b04's reviewed
  e2e_reader and head source, parity_kit dependencies, C8r policy, and native
  metadata. It contains no weight payload or RGB. b04's files remain read-only.
  `TOKENS.json` maps the opaque token and stays on Trinity.
- The package pins unmodified copies of the template launcher, stage, export,
  return, trace, stdout-transfer, and ledger helpers. It calls the template's
  `copy_parts`, `extract_stream`, bwrap `namespace`, `publish`, and `return_io`.
  It does not call the template's D0 export fetch, which selects another run.
  Large input archives and the code tar stage once to the job-private disk;
  no transport implementation was substituted.
- `job.py` checks the allocation's storage, code/input hashes, CPU receipt,
  policy scripts, and assigned card count. `prepare.py` imports torch,
  torchvision, transformers >=5.12 and scipy, checks their recorded versions,
  then uses b04's reviewed `stage_restore` and artifact-manifest builder in the
  stable bwrap view. The manifest pins evaluator/runner code as well as the
  reader, tree, head and SAM source. No installation runs inside the job.
- `runner.py` launches one `h1eval.h10.launch` process per GPU per type. It
  waits for every shard before advancing through displacement, rotation,
  movement direction, absolute distance, then room. Each process receives
  `--arms own`, its `--types` value, the registered mode default, and
  `--shard i/n`. This preserves 636 baselines plus 900 perturbations; room
  receives baseline only. No answer, unit conversion, score or numeric format
  is rewritten.
- `h1eval/h10/launch.py` accepts a read-admission cutoff, completion deadline,
  and shared stop marker. Complete records are fsynced. The Python deadline
  signal is deferred during a journal commit; an unfinished decode is not
  recorded. Workers exit 75 at the deadline. A failure prevents the next type
  from starting; siblings drain under their own guards. No process is killed
  or automatically relaunched by the new runner.
- The default admission cutoff is 1,800 seconds before allocation end, with
  a completion deadline 1,200 seconds before the end. The template's return
  timeout chain can consume about 1,020 seconds, so the conservative reserve
  leaves time for that chain and archive creation. The helper enforces one
  general node, 1–4 GPUs, at least 40 minutes and at most five allocated
  GPU-hours. Indefinitely blocked native calls or filesystems remain outside
  the guarantee of a Python timer.
- Returns contain `metadata/journals/<type>/<gpu>/`, their environment/mapping
  receipts, shard projections after ten reads, aggregate
  `metadata/projection.json`, `SUMMARY.json`, `STEPS.jsonl`, and logs. The
  template excludes caches, weights and RGB and enforces its 90 MB archive
  and 100 MB shared pool limits. A partial archive remains incomplete in the
  template receipt; its summary identifies a clean deadline stop.
- Resume imports only durable journals and stable identity. It retains the
  logical input paths, package, GPU shard count, and archive/receipt identity;
  changing input bytes refuses. Allocation stop and terminal markers are not
  imported. A killed run still needs the user's answer before resubmission.

`STAGING.md` lists expected hashes, byte counts and registry evidence;
`INPUT_CATALOG.json` adds each source and transfer requirement. Full pins are
available for the step-544 archive, artifact, heads, full-weights manifest,
FRAMES/DENSE metadata, SAM checkpoint, selector, code and template assets.
The registry does not prove Orchard residency of the H1-0-specific inputs.
Unknown G3T full pins, SAM source/receipt sizes and hashes, compatible environment
closure, policy locations and frame-archive hash remain explicit OPEN entries.
The RGB producer receipt reports **1,773,951,824 bytes**. No bulk model or RGB
payload was opened to improve this inventory.

### CPU evidence and commands

`tests/test_build8.py` and `tests/build8_worker.py` run the reviewed parity
factory with tiny loader/decode stand-ins in retained production-style roots
under `tmp/b8/rehearsal/`, outside `/dev/shm` and pytest basetemps. Each rehearsal
uses ten items of each type across two shards, yielding **110 completed tuples**.
They check type barriers, disjoint sharding, registered modes, exact model text,
byte-preserving resume, time-guard admission, an interrupted in-flight decode,
template result-tar layout, code/bootstrap pins, Slurm opacity, input-change
refusal and failure handling. These are control-flow proofs, not step-544
real-weight compatibility or timing measurements.

The full suite command was:

```bash
LANE_TEST_OUTPUT="$PWD/tmp/b8" PYTHONHASHSEED=17 bash cpu.sh -m pytest \
  tests/test_build8.py tests/test_build7.py tests/test_build7_types.py \
  tests/test_build6.py tests/test_build4.py tests/test_review.py \
  tests/test_reader_build4.py tests/test_build3_items.py tests/test_h10.py \
  tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py \
  tests/test_stop.py tests/test_rows.py tests/test_own_forward.py \
  -q -rs -p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin \
  --basetemp="$PWD/tmp/b8/full1" > tmp/b8/full1.log 2>&1
```

The final package/rehearsal check uses the same flags with only
`tests/test_build8.py`, basetemp `tmp/b8/final`, and log `tmp/b8/final.log`.
Its final result is recorded below. `bash -n` passed for the generated batch
and submission shell scripts. The standalone operator helper loaded the pinned
package in memory and refused the local Trinity package path before any remote
or Slurm action.

Package commands, run only through the requested CPU environment, are:

```bash
LANE_TEST_OUTPUT="$PWD/tmp/b8" bash cpu.sh -m orchard_h10.build \
  --out "$PWD/orchard_h10/package"
LANE_TEST_OUTPUT="$PWD/tmp/b8" bash cpu.sh -m orchard_h10.inventory \
  "$PWD/orchard_h10/package"
```

`build.py --refresh` can replace an unsubmitted package in place while retaining
its token; it refuses a package with a submission ledger. Changing a package
invalidates its plan and any resume binding. All Python commands use
`/scratch/jjyeung/envs/p1cpu/bin/python -B`, hidden CUDA, at most 16 threads, and
the CPU wrapper's 32 GiB address-space cap. All new test scratch files live
under `tmp/b8`.

### Operator steps and conservative choices

`orchard_h10/OPERATIONS.md` contains the complete archive schema and commands.
The operator must resolve OPEN inputs, stage one archive through the existing
governed bridge, extract the small package to
`/project/community/jjyeung/b01ec87a6f29b`, and fill its `1.json`. The bridge
connection is not available here; no new SSH transport or upload was invented.
The optional outer transport tar was not created on this disk-constrained node.

On the Orchard login node, the exact CPU admission and later explicit submit
commands are:

```bash
cd /project/community/jjyeung/b01ec87a6f29b
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 4 --time 01:15:00
# Only after ORCH releases GPUs and the CPU receipt passes:
A_N=4 A_T=01:15:00 bash SUBMIT.cmd --test-only
A_N=4 A_T=01:15:00 bash SUBMIT.cmd
```

The login check reads package/contract metadata and archive sizes, not tensors.
The allocated node performs full admission and the CPU restore. The example
uses four GPUs for 75 minutes; the operator chooses the actual `--time` and
reruns admission for it. Slurm receives only opaque paths/tokens and four
explicitly supplied environment values. It receives no inherited lane paths,
comments, dataset names or model names. Shipped source and item contents use
the stated ORCH exemption.

To fetch, set the real job ID, derive its return token, and use the pinned
template framed transport through the package helper:

```bash
J=170999  # Replace with the actual returned job ID.
R=$(/usr/bin/python3 -I -s -B -c \
  'import sys; print("b01ec87a6f29b"+format(int(sys.argv[1]),"08x"))' "$J")
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$R" --out "/tmp/$R"
```

The operator returns that single archive and its receipts through the governed
bridge at <=8 MB/s. Resume pins the returned archive in `1.json`, retains the
same shard count and inputs, repeats the CPU check, and explicitly resubmits.

Conservative choices: missing remote proof means OPEN; full G3T/SAM receipt pins
are never inferred from hash prefixes. The stable data root is opaque and bound
under `/scratch` because the reviewed reader rejects physical `/tmp` paths.
The package includes parity_kit and native metadata because e2e_reader imports
them. It reads only the own arm and does not import b04's partial baseline rows:
the requested kit's complete paired-journal contract cannot authenticate that
partial set as a reusable tower run. The 20-minute return reserve prioritizes
durable results over maximizing allocated decode time. No historical prose was
kept except the numbered build and validation ledger explicitly requested here.

**GUESS:** an H100 may take **10–60 seconds per decode**, compared with b04's
reported **25–120 seconds on an A6000 with SAM 3 in the call**. This is an
unmeasured estimate, not a claimed speedup. All 1,536 own decodes would consume
about **4.3–25.6 H100-hours**, excluding loading, staging and return. Five
H100-hours should therefore be treated as a budget for an ordered partial read;
the returned projection determines how much remains.

### Final checks and storage

The final rehearsal suite has **10 passed in 73.58 seconds** (`tmp/b8/final.log`).
The final package-pin and deadline-handler checks have **2 passed in 0.38
seconds** (`tmp/b8/deadline.log`). The deadline check proves that an allocation
stop crosses an ordinary reader `except Exception` handler; it cannot be
converted into an answer record. That check and the package test ran with the
same CPU/pytest flags, selecting
`test_package_pins_and_embedded_bootstrap` and
`test_deadline_crosses_reader_exception_handlers`, under basetemp
`tmp/b8/deadline`.

The conservative storage upper bound is **18,550,784 allocated bytes (18.56 MB)**
and **13,950,768 logical bytes (13.96 MB)**, below the 20 MB cap. The receipt is
`tmp/b8/SIZE.json`. It excludes the supplied template, counts new files and
positive file growth, counts the edited launcher/report in full, includes all
Build-8 directory allocation, and reserves 256 KiB for final metadata and report
edits. No extra outer transport archive or expanded code tree was written.
No Git, network, SSH/SCP/rsync, GPU use, process termination, input modification,
or file-deletion command ran. All writes were inside K.


## Build 9

F1–F3 are implemented. The final full CPU suite passed **142 tests**, with one
permitted skip and no failures, in **197.72 seconds**. Nothing was submitted,
staged remotely, uploaded, run on a GPU, or repinned to the deferred reader.

### Delivered behavior and files

- `h1eval/h10/merge.py` adds `merge_types()` and `--type-layout`. The entry
  requires every type/GPU shard, the registered own-arm mode plan, equal
  bindings and allocation identity, exact shard membership and exact union
  coverage. It refuses missing shards, duplicate/foreign tuples and changed
  bindings. The existing single-type entry remains available. Both reviewer
  and Build-9 tests merge the read-only Build-8 rehearsal into 110 records.
- `h1eval/scorers.py`, `statistics.py`, `runner.py` and `cli.py` preserve b04's
  journaled `scores.answer` for M2. Without that field, they use the unchanged
  benchmark answer scorer. Unserved/error calls never overwrite accuracy.
  Tables and curves report their separate per-type rates, with total calls as
  denominator; zero calls produce an undefined rate. No answer is rewritten.
- `orchard_h10/entry.py`, `runner.py`, `job.py`, `prepare.py`, `operator.py`,
  `common.py` and `build.py` dispatch through numeric entries/configs. Worker
  argv is `<python> -B -I 5.py <numeric>.json`; types are indices. Items get
  numeric private copies. A lock protects shared copies; completed copies and
  entry files are not rewritten while other workers read them. Public package
  config contains only opaque identifiers, sizes and hashes. Descriptive pins
  live in `0.tgz`; input/dispatch data lives in 0700 directories. The extended
  forbidden list scans all controlled process argv, environments and public
  package plaintext, including template subprocesses. The template return
  helper runs from a numeric copy without changing its source bytes.
- `h1eval/items.py` replaces `items/r0dev.json` with the pinned `r0dev_f32` set:
  2,169 items, 98 rooms, nine types, 32 frames, development only. Every room is
  in R0_DEV_ROOMS and covered by the existing training exclusion. Item-source,
  frames-manifest, room-list and summary hashes are fixed. Counts are 385
  counting, 293 size, 290 absolute distance, 279 relative distance, 246
  appearance, 192/194/192 direction, and 98 room size.
- `h1eval/h10/reserve_frames.py`, `parity_adapter.py` and `launch.py` bind the
  f32 layout to the reviewed reader and require own baseline reads of all
  types. The optional sixth package phase requires an authenticated frames
  archive, verified per-scene manifests/RGB and the time guard. Missing input
  skips it. Its journals merge separately with `items/r0dev.json`. Reports and
  curves print b10's pinned f32 constants beside accuracy/MRA on a 0–1 scale.
- `cli.py` caches the original full export hash under a lock for one allocation.
  The receipt binds the export path, resolved file paths, device/inode, size,
  mtime, ctime and allocation ID. Any change forces a full rehash. Private
  receipts and an export that remains read-only during decoding make reuse
  safe; archive and artifact checks still run. Tests verify both file-change
  and allocation-change invalidation. No bulk export was read here.
- `h1eval/h10/RUN_H10.md` registers separate R0-dev baseline reads beside
  dev-S1 at H1-1 m100/m200. `OPERATIONS.md`, `STAGING.md`, `OPEN_INPUTS.md`,
  `INPUT_CATALOG.json`, `inventory.py`, token metadata and the package describe
  the operator contract and open optional archive. `tests/test_build9.py`
  covers the new contracts. All six copied reviewer probes live under
  `tests/review_h10/`, with assertions and a fresh-interpreter pytest gate.

### Conservative choices and test updates

Two source qids each occur twice, but all 2,169 source rows differ. Canonical IDs
append a source-row digest and retain the original qid; no row is dropped or
combined. The source registration note says 100 rooms; the supplied f32 rows
cover 98 admitted rooms, which determine this set's count.

The supplied frame inventory pins per-scene manifest hashes but does not include
those files. The adapter requires the producer's original `manifest.json`
bytes and a `frames` list with index, relative path and SHA256. Archive layout
and that schema remain OPEN for confirmation; incompatible input refuses.
The CPU optional-phase proof uses stand-in outputs, not missing RGB or weights.

`tests/test_build4.py::test_unserved_call_stays_zero_in_task_accuracy` becomes
`test_unserved_call_preserves_answer_accuracy`; both correct-answer assertions
now expect 1.0. `test_cli.py` expects the supplied R0 set to build successfully.
Build-8 tests and their worker now exercise numeric dispatch, numeric event
indices, in-tar config and scratch under `LANE_TEST_OUTPUT`. The six reviewer
scripts retain their substantive checks and run against K; their temporary
outputs no longer target /dev/shm. The merge probe selects the new type entry.

`tests/build4_plugin.py` optionally compresses completed function-scoped test
payloads losslessly. Original hashes and paths are recorded in
`logs/b9/TEMP_COMPRESSION.json` and `test_compression.jsonl`. A `.gz` suffix
identifies retained compressed output. Shared fixtures are compressed only
after their module finishes. No file-deletion command ran; the old Build-8
rehearsal and all outside inputs remain untouched.

### Validation commands and results

All Python commands use `bash cpu.sh`: the requested p1cpu interpreter with
`-B`, CUDA hidden, a 32 GiB cap, and 16-thread environment limits. Pytest keeps
its existing reader/build4 plugins, disables its cache and uses new basetemps
under `tmp/b9`. The final complete command is:

```bash
LANE_COMPRESS_TEST_OUTPUT=1 LANE_TEST_OUTPUT="$PWD/tmp/b9" PYTHONHASHSEED=17 \
  bash cpu.sh -m pytest \
  tests/test_build8.py tests/test_build7.py tests/test_build7_types.py \
  tests/test_build6.py tests/test_build4.py tests/test_review.py \
  tests/test_reader_build4.py tests/test_build3_items.py tests/test_h10.py \
  tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py \
  tests/test_stop.py tests/test_rows.py tests/test_own_forward.py \
  tests/test_build9.py tests/review_h10/ \
  -q -rs -p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin \
  --basetemp="$PWD/tmp/b9/full2" > logs/b9/full2.log 2>&1
```

| Gate | Result | Retained log |
|---|---|---|
| Reviewer probes plus Build 8 | 17 passed | `logs/b9/gate1.log` |
| Initial Build 9 unit gate | 12 passed, 1 fixture failure: missing commit marker | `logs/b9/b9first.log` |
| First full suite | 139 passed, 1 skipped, 1 fixture failure: one item/type across two shards | `logs/b9/full1.log` |
| Corrected optional phase, package/opacity and reviewer gates | 9 passed | `logs/b9/final_gate.log` |
| Final full suite above | **142 passed, 1 skipped, 0 failed** | `logs/b9/full2.log` |

The permitted skip is `test_build6::test_real_json_loading_until_missing_weights`:
model.json, receipt.json, artifact.json and RESTORE.json are absent from the
specified /dev/shm fixture. No replacement was fabricated. One existing
trainer-test tensor-to-scalar warning remains. The final suite includes missing,
duplicate, foreign-key, binding and identity refusals; unchanged single-type
callers; reviewed M2 agreement at 1.0; all six reviewer probes; opaque package
and process checks; optional skip/run/time-guard proofs; R0 pins/counts/guards;
constant display; cache invalidation; and strict repin validation.

Package commands used `LANE_TEST_OUTPUT="$PWD/tmp/b9" bash cpu.sh` with:

```text
-m h1eval.cli items build --sets r0dev
-m orchard_h10.build --out "$PWD/orchard_h10/package" --refresh
-m orchard_h10.inventory "$PWD/orchard_h10/package"
```

`bash -n` passed for cpu.sh, first_batch/real_fixture_batch.sh, BATCH.sh and
SUBMIT.cmd. Package checks read compressed code in memory; no tree was copied
or expanded. The code tar expands to 24,618,426 bytes, below its 32 MiB runtime
admission bound, but no expanded tree was written by this build.

### Package pins and deferred F4

Token: `b01ec87a6f29b`. Code tar: **5,292,320 bytes**.

- Code tar SHA256: `9db85a6b21e0b0c167fe48d2700db9d434a537501fcbefd6a9ff7d9fe52e952c`.
- Plan SHA256: `a75a22a8c0a6c7809a5366c2f548c27530ca4dd44f44eb7814b3104a452f1ee5`.
- `orchard_h10/package/PACKAGE.json` SHA256: `76ea96b610fcdc0a3b7f5ca5be99ee09b5c2b4f50a4db77de01971b7b2ff59e4`.
- Grounding SHA256: `47ab8435f45023a83175d3b580b8d530a8398ed6959694d48807df41742be92d`.

F4 is deferred as instructed. Refresh preserves the reader bytes already in the
tar and does not import b04's live grounding. After review, create one JSON spec
with `source` pointing to a directory containing only `e2e_reader/*.py` and
`sha256` mapping its complete relative inventory to expected full hashes. Run:

```bash
LANE_TEST_OUTPUT="$PWD/tmp/b9" bash cpu.sh -m orchard_h10.build \
  --out "$PWD/orchard_h10/package" --refresh --reader-repin "$PWD/<spec>.json"
```

The option refuses unlisted, missing, symlinked or hash-mismatched files and
requires the complete pinned reader inventory. A successful repin records every
old/new hash in BUILD_REPORT and changes the package plan. Rerun the CPU suite,
inventory and operator admission afterward. No repin was performed here.

### Open inputs and storage

The R0 frames archive hash/size, actual per-scene metadata layout, and every
unresolved production dependency in OPEN_INPUTS remain open. F4 still needs
ORCH's reader review and an explicit repin. Real-weight/RGB compatibility and
GPU timing are unproved. Nothing in this build authorizes submission.

Temporary payloads remained below 20 MB, but the observed allocated-size upper
bound briefly reached **24,457,216 bytes**, including directory/symlink
accounting, before lossless compression. This exceeded a 20 MB physical-space
interpretation of the cap. The final allocation is recorded below; finished
payloads remain recoverable, and no deletion was used to reduce the footprint.
The numbered build/test ledger is retained because the user explicitly requested
it; operator documentation describes only the current contract.

Final measured sizes (`logs/b9/SIZE.json`):

- Code, tests, item files and positive package growth: **2,639,367 bytes**.
- All kept positive file growth before the size receipt: **2,759,462 bytes**; an additional 8,192-byte metadata reserve covers this receipt and paragraph.
- `tmp/b9` regular-file payload: **6,133,058 bytes**.
- `tmp/b9` unique allocated blocks, including directories: **18,018,304 bytes**.

All final measured footprints meet the 3 MB kept-code and 20 MB temporary caps.
No Git, network, SSH/SCP/rsync, GPU, process termination, outside-K write, or file
deletion ran. Raw Build-8 inputs and the supplied R0 sources remain unchanged.

The final opaque operator entry loaded the pinned package and refused the local
Trinity path before staging or Slurm (`logs/b9/operator_local.log`). The CPU
command was `bash cpu.sh orchard_h10/package/3.py check --gpus 4 --time 01:15:00`
with `LANE_TEST_OUTPUT="$PWD/tmp/b9"`; its exit 1 is the expected location refusal.
