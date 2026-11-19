"""Write the current delivery report from retained measurements and final gate outputs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = json.loads((ROOT/'out/evidence/round2_final_checks.json').read_text())
assert len(checks) == 15 and all(c['accepted'] for c in checks)
analysis = (ROOT/'work/report_analysis_round2.md').read_text()
analysis = analysis.replace('At a representative grid', 'As an illustrative estimate, at a representative grid')
analysis = analysis.replace('A budget error remains a row failure at that group\'s admission, and all ranks must refuse it.',
    'A budget error remains a row failure at that group\'s admission, and all ranks must refuse it. This grid does not establish that the largest production group fits. Before any prefetch ON run, `data_only.py --full-plan` must audit a complete epoch plan on every rank, including targets and auxiliary tensors, and record its peak below the unchanged guard. No production peak group size has been measured here.')
analysis = analysis.replace('The patch series is in `out/patches/`; the combined review tree is `work/tree/`.',
    'The build-20 series is in `patches/`; the build-21 series is in `patches_b21/`. Their tested trees are `work/tree/` and `work/b21_final/work/tree_r1/` under this workspace.')
analysis = analysis.replace('It also refuses admission groups above eight rows.',
    'It also refuses admission groups above eight rows and any mix source without a SQLite `conn`, including unaudited C1-r clip readers.')
analysis = analysis.replace('Cache identity includes mapped path, inode/device, size, mtime and ctime.',
    'Cache identity is the pinned SHA-256. A miss reads the encoded file once, hashes those exact bytes against the pin, and decodes the verified in-memory bytes. A pin/decode rewrite cannot poison a persistent cache entry.')
head = '''VERDICT: DONE All eight review fixes and the build-21 port are delivered with no new local test failures; lane gloo and production acceptance remain pending.

Both builds pass the dedicated 53-case gate: **52 pass and one socket-dependent test is skipped**. Broader gates reproduce the same six reported baseline failures and two additional baseline export-test failures; their causes appear below. The build-21 base has 936 verified files, and the four delivered patches replay with zero fuzz and zero offsets. No production speedup is claimed.

'''
body = '''## Review round 2: finding -> fix -> test

No HIGH finding was reported. Every MEDIUM and LOW finding is addressed; none is deferred as too large. The failing-before logs are [trainer regressions](evidence/round2_before.txt), [kit regressions](evidence/round2_kits_before.txt), and [row-draw comparison](evidence/round2_draws_before.txt). The corresponding final tests pass on both builds.

| Finding | Fix | Regression and evidence |
|---|---|---|
| 1 MEDIUM: extra OFF startup collective | Parse locally; carry ON settings in the existing preparation broadcast and propagate mismatches/errors through existing `agree()`. All-OFF preserves the original two-item broadcast payload and collective sequence. | `Round2.test_startup_has_no_collective_and_agrees_with_root`; the existing GX rebind test fails before and passes after. All six requested existing modules are in the gate; their six baseline failures are diagnosed below. |
| 2 LOW: frozen settings leak between tests | `so_helpers.reset_switches` clears `_frozen` before each relevant case and registers cleanup. All `so_*` classes and existing carrier-train callers use it. | `Round2.test_fixture_resets_frozen_switches_before_and_after_case` fails before and passes after. The combined gate runs the existing train tests before the ON suites without vacuous OFF comparisons. |
| 3 LOW: ON proofs lack positive controls | Joint and local proofs record row-reader thread names, reset/check cache misses, and count `Components.add` calls. They compare every non-timing/non-allocator logged field, in addition to losses/gradients/updates. Scalar floats also compare bytewise. | `Round2.test_joint_positive_controls_refuse_silent_off`; the local five-arm native proof passes with real ON controls. Updated two-rank controls are packaged but await the lane command. |
| 4 LOW: unproven 1-GiB group budget | Keep the bounded guard; add `--full-plan`, every-group byte counts, target/audit inclusion, per-step maxima and a peak/coverage sidecar. Require a complete epoch plan on every rank before production ON. | `KitRound2.test_full_plan_memory_includes_every_group_and_targets` fails before and passes after: 101 synthetic plans, 64 bytes per two-row group including targets. This synthetic measurement is not a production sizing result. |
| 5 LOW: cache key does not bind decoded bytes | Hash one encoded-byte read against the frame pin, decode that buffer, and key the cache by pinned SHA-256. Preserve caller pin checks and copy-on-hit. | `Round2.test_cache_miss_hashes_the_bytes_that_are_decoded` fails before and passes after; `test_pinned_cache_caller_rejects_rewrite_after_verification` plants a rewrite between verification and decode. Existing invalidation, non-RGB and capacity tests pass. |
| 6 LOW: clip readers are unaudited | `rows_factory` refuses any mix source without `conn`, before copying/starting the private reader. Factory failures still reach the original admission boundary. | `Round2.test_prefetch_refuses_clip_mix_before_starting_worker` fails before and passes after; the SQLite composite-reader and factory-error regressions pass. |
| 7 LOW: GPU kits lack a co-location/free-memory guard | Each rank probes its target before `train()` and refuses another compute PID or less than the observed production peak, **76,699 MiB**, free. The timing wrapper also probes all visible targets before each arm. Probe failure refuses. | `KitRound2.test_gpu_guard_refuses_busy_low_memory_and_unreadable_probe` fails before and passes after using mocked probes. No GPU was queried here. Allocation/admission remain prerequisites; a point-in-time check cannot prevent a later tenant race. |
| 8 LOW: MDD and OFF nondeterminism | Use `t(.80,df)` in the power term. Compare OFF brackets first, write `comparison.json` before rejecting loss mismatches, and mark timing gains unresolved when parity is invalid. | `KitRound2.test_t_power_and_off_drift_persist_comparison_before_refusal` fails before and passes after; the existing slowest-rank/statistics regression passes with the corrected coefficient. |
| 9 INFO: eager reads/imports | Use a lazy `getattr` fallback, hoist loader switch reads/imports outside frame loops, and remove unused `os` imports. | `Round2.test_fetch_uses_captured_switch_without_eager_environment_parse`; combined cache/prefetch suites. Cache capacity validation remains defensive inside `read()`. |
| 10 INFO: stale distributed status | Cite the supplied 16-test coordinator pass with its actual source scope. | Exact supplied lines below; the modified build-21 suite is separately marked pending. |
| 11 INFO: model class names in kit source | Retain class names needed for instrumentation; outputs remain scrubbed. They already occur in the input tree. | Existing output-scrubber and opaque-identifier tests pass. No additional source-name rewrite is needed. |
| 12 INFO: real CUDA attribution unrun | Preserve the explicit limitation. GPU use is prohibited in this dispatch. | Mocked-stream attribution and real CPU profile tests pass; no real CUDA elapsed-time claim is made. |

The CPU kit also rejects different `row_draws` even if encoded bytes happen to be identical (`KitRound2.test_row_draw_difference_fails_even_when_encoded_bytes_match`). This makes the hand-over's row-draw kill rule checkable before training.

## Existing-suite failures: causes and scope

[Input existing-suite output](evidence/round2_baseline_existing.txt), [patched build-20 output](evidence/round2_patched_existing.txt), and [patched build-21 output](evidence/round2_final_b21_existing.txt) have the same six failure entries. Each runs 91 local cases; two additional two-rank GX cases are excluded for unavailable sockets. The two skipped local cases need a missing review pool.

| Existing test failure | Cause; why it is not changed here |
|---|---|
| `GXTests.test_native_layout_matches_vendor_on_augmented_viewpoints`, duplicate layout | `pose_samples.augment` imports unavailable `torchvision.transforms.v2`. This environment dependency is absent on the input tree too. |
| Same test, paired layout | Same missing torchvision dependency; this is the second subtest error. |
| `GXTests.test_student_frames_real_processor_and_square_padding` | Transformers' `pil_torch_interpolation_mapping` is `None` without torchvision, so native resize raises `TypeError`. No fallback processor was substituted. |
| `GXTests.test_production_meta_header_and_strict_safetensors` | Hard-coded `/scratch/jjyeung/orch_cd/gx_build/work/aws_probe/g3t_header.json` is absent. |
| `GXTests.test_vendor_bytes_digest_and_import_origin` | Hard-coded `/scratch/jjyeung/orch_cd/c1r/work/D/g3t_src/vggt/__init__.py` is absent. |
| `CachedBank.test_parity_cached_vs_online` | Existing GF1 BF16 feature-cache gradient `norms.2.weight` differs by **1.5396857634186745e-05** absolute, **0.017092852841054485** relative, above its **0.015625** tolerance. The input and patched trees report the same values. This is a different cache from 02; its tolerance was not weakened. |

The expanded caller gate runs another 55 cases. [Input output](evidence/round2_baseline_related.txt) and both patched outputs show two additional pre-existing failures: `ExportLeg.test_export_leg_needs_a_resume_pin_and_no_smoke` supplies an empty config and encounters `trace_program_version_missing` before its expected export-leg refusal; `ExportLeg.test_export_resume_state_reuses_an_existing_export` expects an old call signature without the existing `optimizer=None, disk_guard=None` keywords. Seven other cases skip absent processor/config/bank fixtures. These tests exercise unrelated export/version expectations and remain unchanged apart from switch-state isolation. The broad suites are **not clean passes**; the gate verifies that the performance patches introduce no additional failures.

## Patch delivery and build-21 pin

[patches/manifest.json](patches/manifest.json) pins build 20 to `780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278` (934 input files). [patches_b21/manifest.json](patches_b21/manifest.json) pins build 21 to `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8` (936 input files), plus the supplied package SHA-256 `fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59` from READY. All 936 build-21 file hashes and the canonical source digest were verified locally; the package archive itself was not rehashed because the supplied input is its untarred tree.

Apply **01, 02, 03, then 04** using `patch --batch --fuzz=0 -p1 -i <absolute-diff-path>`. They are an ordered series. 01 includes shared validation and test-state isolation; 02 carries the content-bound RGB cache; 03 carries batching and positive controls; 04 retains the scalar collective-hash repair and round-2 regressions. Each manifest records byte counts, SHA-256s, touched paths and base pins. Tests run after all four patches.

The [build-20 replay](evidence/round2_replay_b20_final.txt) reproduces every touched file. The [build-21 port/replay](evidence/round2_port_b21_final.txt) verifies all **21 touched files**, no fuzz or offsets in the delivered build-21 replay, and unchanged remaining input files. The porting pass from build-20 hunks uses offsets; the delivered build-21 diffs have exact build-21 context. The tested build-21 candidate has **948 files** and canonical source digest `40644d6bdd68912ac23b36d8cb98b83421b11c2e05a5e5e4ff0dd9eb19dc8a7c`. The orchestrator must seal/admit its final rebuilt tree.

READY's `base/tree_b01ce449`, `build15/inputs` and `build_n1/inputs` are linked from `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work` beside the tested tree, outside its sealed source. The input trees and fixtures were not edited.

## Kits and acceptance

The profile kit retains its single-step 895-second limit plus five-second termination grace, heartbeat, partial tables, stream-aware CUDA events and read-only source-only resume bridge. Its CPU/stream tests pass; full GPU execution is unrun. The timing kit uses 20 discarded + 20 measured updates per arm, three OFF/ON/OFF repeat blocks, inherited production thread settings, explicit cache-state records and a three-hour per-arm timeout. Its 840 updates cost an **estimated 31 hours** at 133 s/update, plus startup. No killed job is automatically retried.

For approximate 80% power and two-sided alpha 0.05, `MDD = (t(.975,n-1) + t(.80,n-1)) * s_repeat / sqrt(n)`. At three repeats this is **3.0969 × s_repeat**: an assumed 1.0-s repeat SD resolves about 3.10 s; an assumed 0.323-s SD resolves about 1 s. These are planning calculations, not measured production variability. `comparison.json` retains OFF reproducibility separately from switch parity and invalidates speedup attribution on a parity failure.

[NOTE_FOR_TREE_REBUILD.md](NOTE_FOR_TREE_REBUILD.md) specifies the orchestrator's acceptance plan: N launches with 01 and 02 OFF; 03 may be ON only after review and build-21 tests prove numerical parity. The first continuation tests 01 ON after the complete epoch-plan CPU check. r1_ops compares matched-plan data wait and first-step loss at identical checkpoint/RNG state; any loss or row-draw difference turns 01 OFF. 02 stays OFF until measured. Read `ranks[].data_seconds`, `ranks[].components` and `ranks[].stream_means` in `metrics_<attempt>.jsonl`; exact total microstep losses are the disposable kit's `rank*/steps.json[0].first_step_micro_losses`. The trainer has no invented top-level `loss` metric. The note names the CPU commands and matched-state replay requirement.

## Coordinator command

**Pending lane execution outside the sandbox, on the final build-21 tree.** No socket suite was attempted here. Run:

'''
note = (ROOT/'out/NOTE_FOR_TREE_REBUILD.md').read_text()
command = note[note.index('```bash\ncd /scratch'):]
command = command[:command.index('\n```')+4]
body += command + '''

Require `SO_ADMISSION_PROOF`, `SO_GLOO_PROOF`, `OK` and `EXIT=0`, including positive controls for the ON arms. The admission test covers both ranks at factors 1 and 2 and failures in first/middle/last groups. The joint proof compares every loss/gradient/update, numerical log field, trainable, row draw and collective payload/order.

Supplied evidence for the input reviewed in round 2 is `work/review1_full_suite_by_coordinator.txt`, whose exact lines are:

```text
SO_ADMISSION_PROOF /scratch/jjyeung/orch_n30/so_step/work/test_runs/so_453pbecg factors=1,2; both ranks raise in first/middle/last groups
SO_GLOO_PROOF {"directory": "/scratch/jjyeung/orch_n30/so_step/work/test_runs/so_384pmumf", "ranks": 2, "comparisons": 16, "losses_and_every_gradient": "bitwise", "trainables": "identical", "row_draws": "identical", "collectives": "identical; main thread only", "failure_microstep": 2}
Ran 16 tests in 1027.778s
OK
EXIT=0
```

That supplied pass is not a rerun of the modified build-21 series. The command above is still required.

## Exact local commands and outputs

The serial driver runs on at most eight cores, with torch intra-op threads set to eight in every test entrypoint. It writes complete stdout/stderr and exact per-suite commands to the linked logs, including nonzero exits for declared baseline failures:

```bash
cd /scratch/jjyeung/orch_n30/so_step
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \\
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \\
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_round2_final.py \\
  > out/evidence/round2_final_driver_completed.txt 2>&1
```

Exact driver result: `ALL_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES`.
The [machine-readable gate record](evidence/round2_final_checks.json) preserves each exit status. Its exception list is derived from actual input-tree failures, not from blanket skips.

| Build / suite | Exact unittest output | Complete command/output |
|---|---|---|
'''
for c in checks:
    output = '; '.join(c['summary']) + '; EXIT=' + str(c['exit'])
    body += f"| {c['build']} / {c['kind']} | `{output}` | [{c['log']}](evidence/{c['log']}) |\n"
body += '''
Build-20's separate six-module gate reports `Ran 91 tests in 99.350s`, `FAILED (failures=1, errors=5, skipped=2)`; the input gate reports `Ran 91 tests in 107.410s` with the same failure/skip counts. The specifically regressed GX rebind test passes on both patched builds.

Patch replay commands, run with the same `nice`/CPU-only environment and interpreter, are `work/verify_review_patches.py round2_final_patch_check` and `work/port_b21.py`. Their exact output is linked above. `work/recheck_measurements.py` recomputes the retained production-log arithmetic in [round2_measurements.txt](evidence/round2_measurements.txt). Numbered installed-source excerpts for startup broadcast, storage accounting and FSDP ordering are in [round2_framework_sources.txt](evidence/round2_framework_sources.txt), with source hashes and official documentation links in [SOURCE_NOTES.md](SOURCE_NOTES.md).

## Review round 1: finding -> fix -> test

The delivery retains the required round-1 fixes: stream-aware backward/recompute event attribution; GIL/thread analysis; bounded profile execution with partial output; source-only resume binding; lookahead release/bounds; repeated bracketed timing; complete manifests; cache counters; inherited production threads; scrubbed outputs; encoded-row/RNG checks; unsupported-path refusals; startup validation; lifecycle/boundary failures; and the 323,920-token arithmetic. The current regression gates include `test_review_kits.py`, `test_kit_utilities.py`, `test_local_parity.py`, `test_so_review.py` and the admission/joint tests. CUDA elapsed measurements remain unrun. The round-2 table states the current implementations where those findings overlap.

## What could go wrong, detection, and work not done

Prefetch can lose time through GIL or OpenMP contention: compare both `data_seconds` and `wall_seconds` on matched plans and inspect per-microstep forward/backward host time. Full-plan tensor accounting can reject a large group before ON admission; RSS still includes processor/decoder temporaries and must be observed on the host. Clip/geometry/gf1/MDG paths remain refused for prefetch. Cache reuse may be negligible; 02 stays OFF until its counters and timing establish benefit. An OFF loss mismatch invalidates switch attribution, and any ON loss/draw mismatch invokes the hand-over's OFF kill rule.

The eight pre-existing suite failures above are not fixed. The build-21 gloo run, real production processor/full-epoch byte audit, real CUDA event validation, production numerical acceptance, co-location probe and speed measurements have not run here. They require the lane/production host, not an inferred pass from tiny fixtures. No Git, SSH, GPU work, deletion, production write, external job launch or paid API was used. The required review mappings and named supplied coordinator logs are retained because they define the evidence scope.
'''
report = head + analysis + body
for sentence in (
    'As an illustrative estimate, at a representative grid', 'The implementation releases replay references',
    'Thus accepted library-held', 'This grid does not establish',
    'The timing kit uses 20 discarded', 'Its 840 updates cost',
    'Seven other cases skip absent', 'The broad suites are **not clean passes**',
    'All 936 build-21 file hashes', 'The tested build-21 candidate has',
    'Read `ranks[].data_seconds`', 'The trainer has no invented',
    'The build-21 gloo run, real production', 'No Git, SSH, GPU work',
):
    report = report.replace(' '+sentence, '\n\n'+sentence)
(ROOT/'out/REPORT.md').write_text(report)
