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
