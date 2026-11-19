from pathlib import Path
import json
import re
ROOT=Path(__file__).resolve().parents[1]
old=(ROOT/'out_round3/REPORT.md').read_text()
note=(ROOT/'out/NOTE_FOR_TREE_REBUILD.md').read_text()
checks=json.loads((ROOT/'out/evidence/round3_checks.json').read_text())
manifest=json.loads((ROOT/'out/patches_b21/manifest.json').read_text())
assert all(c['accepted'] for c in checks) and len(checks)==9
analysis=old[old.index('## Numbers:'):old.index('## Review round 2:')]
analysis=analysis.replace('**approximately 0 for low reuse**','**≤0 at low reuse**')
analysis=analysis.replace('**0–3**, likely modest','**≈0 (≤0.1)**')
analysis=analysis.replace('Same device math and Python float accumulation order. Keep finite-loss checks, final synchronization and collectives. Internal model metrics still synchronize.', 'Same device math and Python float accumulation order. Finite-loss, grid and carrier-count reads still synchronize each microstep; about seven redundant scalar reads are removed. This estimate is below the timing kit’s ≈3-s resolution at three repeats and assumed 1-s repeat SD.')
analysis=analysis.replace('rejects prepared groups exceeding **1 GiB of encoded tensor storage** through the original admission boundary.', 'rejects prepared groups exceeding **1 GiB of encoded tensor storage** through the original admission boundary unless the separate default-OFF synchronous fallback is enabled.')
analysis=analysis.replace('A budget error remains a row failure at that group\'s admission, and all ranks must refuse it.', 'With fallback OFF, a budget error remains a row failure at that group\'s admission, and all ranks must refuse it. With `C1_CPU_PREFETCH_FALLBACK=1`, the worker releases the prepared group and the main thread performs the original synchronous fetch/admission; the synchronous group is not capped, and total RSS must still be monitored.')
analysis=analysis.replace('Before any prefetch ON run, `data_only.py --full-plan` must audit a complete epoch plan on every rank, including targets and auxiliary tensors, and record its peak below the unchanged guard.', 'Before production prefetch ON, `write_plan.py` and `data_only.py --steps 10 --require-coverage` audit the first 10 continuation updates on four rank projections and two arms, including augmented pose rows, targets and auxiliary tensors. Every emitted grid must fit `[32,20,26]`, and the group peak must fit the unchanged guard. The estimated audit runtime is 42 minutes from the supplied timer, or roughly 45–60 minutes with startup and hashing.')
analysis=analysis.replace('The build-20 series is in `patches/`; the build-21 series is in `patches_b21/`. Their tested trees are `work/tree/` and `work/b21_final/work/tree_r1/` under this workspace.', 'The build-21 series is in `patches_b21/`, with identical copies in `patches/`. Its tested tree is `work/b21_final/work/tree_r1/`. `out_round3/` preserves the complete input delivery; its build-20 series is archival and is not the current deployment target.')
analysis=analysis.replace('It also refuses admission groups above eight rows', 'Clip-mix refusal occurs at the first group’s factory setup, after model load. It also refuses admission groups above eight rows')
analysis=analysis.replace('production expectation remains approximately zero until counters show reuse.', 'production gain is expected to be **≤0 at low reuse**: each miss adds a second encoded-file read and SHA-256 after the caller’s pin check. Counters and whole-step timing must show reuse and benefit.')
analysis+='''
Every non-OFF step includes `performance`, mapping switch names to their frozen string values. All-OFF steps omit it. r1_ops must require `ranks[r].performance.C1_CPU_PREFETCH == "1"` in the ON arm, rather than accepting a silent OFF run. The fallback switch joins the existing startup agreement only when enabled; the ordinary three-value `_frozen` tuple remains unchanged when fallback is OFF. Enabled fallback also writes cumulative `cpu_prefetch.budget_fallback_groups`.

03 can retain about 0.2 MB of CUDA scalar blocks per rank (estimate). Exclude `memory.microbatches[*].after_forward.allocated_bytes`, `after_backward.allocated_bytes`, and allocator `peak_*` fields, including `peak_allocated_bytes` and `peak_reserved_bytes`, from numerical parity. Monitor them separately for headroom.

'''
round2=old[old.index('## Review round 2:'):old.index('## Existing-suite failures:')]
round2=round2.replace('The corresponding final tests pass on both builds.', 'The corresponding regressions are included in the current build-21 gates.')
round2=round2.replace('Updated two-rank controls are packaged but await the lane command.', 'The supplied build-21 coordinator and review logs pass these controls; the changed series has a new lane command below.')
round2=round2.replace('Require a complete epoch plan on every rank before production ON.', 'Require the bounded 10-update continuation audit on every rank and both arms before production ON.')
round2=round2.replace('Cite the supplied 16-test coordinator pass with its actual source scope.', 'Cite the supplied build-21 coordinator pass (23 tests) and independent review rerun with their source scope.')
round2=round2.replace('Exact supplied lines below; the modified build-21 suite is separately marked pending.', 'Exact supplied lines below; the current series has a distinct lane gate, including GX and asymmetric fallback tests.')
failures=old[old.index('## Existing-suite failures:'):old.index('## Patch delivery and build-21 pin')]
failures=failures.replace('[patched build-20 output](evidence/round2_patched_existing.txt), and [patched build-21 output](evidence/round2_final_b21_existing.txt)', '[current build-21 output](evidence/round3_existing.txt)')
failures=failures.replace('and both patched outputs show', 'and [current build-21 output](evidence/round3_related.txt) show')
round3=note[note.index('## Review round 3:'):]
round3 += '''
All requested findings 1–12, 14 and 15 are fixed. Finding 13 is covered by the mandatory production-host augmentation gate; its real torchvision operations cannot run in this CPU environment. No requested code fix is deferred for size. The existing unrelated baseline failures and real CUDA measurements remain outside this dispatch.

The [trainer before](evidence/round3_trainer_before.txt) run executes the five new local regressions against the reconstructed round-2 build-21 source: `Ran 5 tests in 11.418s`, `FAILED (failures=1, errors=4)`. The failures are the over-budget row refusal, absent fallback switch, absent performance fields in both direct and real-train paths, and absent class docstring. The [trainer after](evidence/round3_trainer_after.txt) run reports `Ran 5 tests in 10.573s`, `OK`.

The six initial kit cases fail before the changes ([output](evidence/round3_kits_before.txt)); the seven final kit cases pass, including the complete four-rank artifact comparator ([output](evidence/round3_round3_kits.txt)). The plan writer also has a real pinned-checkpoint CLI test: it verifies the continuation step and preserves the existing output-filter contract ([before](evidence/round3_plan_cli_before.txt), [after](evidence/round3_plan_cli_after.txt)). Coverage observation uses a controlled augmentation function locally; this does not claim real torchvision execution.

'''
command=note[note.index('```bash\ncd /scratch'):note.index('\n## Review round 3:')]
coordinator='''## Coordinator command

The supplied coordinator log [round2_b21_gloo_by_coordinator.txt](../work/round2_b21_gloo_by_coordinator.txt) reports these exact lines:

```text
Ran 23 tests in 1016.666s
OK
EXIT=0
```

The independent round-3 review reports `Ran 23 tests in 871.372s OK` and `Ran 2 tests in 12.606s OK` for the two GX cases. Those results cover the source reviewed before these fixes. They establish the 03 numerical condition for the first launch; they do not certify this modified series.

**The lane must run the following 31-test gate on the delivered tree.** It includes the two-rank asymmetric fallback proof and both GX tests. Sockets are unavailable in this sandbox, so this command was not attempted here.

'''+command+'\n'
patches=f'''## Patch delivery and build-21 pin

The base seal is `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`, with **936 verified input files**. READY supplies package SHA-256 `fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59`; the untarred input files were verified, while the archive itself was not rehashed.

Apply **01, 02, 03, 04 in order**, using `patch --batch --fuzz=0 -p1 -i <absolute-diff-path>`. Patch 01 carries the worker, startup agreement, fallback and relevant fixture/docstring changes; 02 carries the decoded cache; 03 carries metrics and conditional performance records; 04 carries scalar hashing and round-2/round-3 regressions. Tests run after the complete series. [manifest.json](patches_b21/manifest.json) records input/output SHA-256s, per-patch hashes, defaults and the base pin.

[Exact replay output](evidence/round3_patch_replay.txt): `ROUND3_REPLAY_PASS: 4 patches, 22 touched files, 927 untouched files; zero fuzz and offsets`. Every touched replay file matches the tested tree. Both `patches/` and `patches_b21/` target build 21 and are byte-identical. No input source or fixture was edited.

The candidate source has **{manifest['_application']['candidate_source_files']} files**, digest `{manifest['_application']['candidate_source_tree_sha256']}`. This is the candidate identity, not a production admission. READY fixture links remain beside the source, outside its sealed tree. The orchestrator must issue the final seal/admission.

'''
kits='''## Kits and continuation acceptance

[NOTE_FOR_TREE_REBUILD.md](NOTE_FOR_TREE_REBUILD.md) contains the exact commands and r1_ops fields. The CPU plan writer starts from the pinned continuation checkpoint; the audit covers the first 10 updates × 4 ranks × 2 arms, with actual augmented pose rows and an emitted-grid cap. It records each process's peak RSS, including the worker's private receipt/processor. Expected runtime is about 42 minutes from the supplied data timer, or 45–60 minutes including startup/hash overhead (**estimates**).

`kit_profile/replay.sh` uses **mode `replay`, one update, no warmup**, in **OFF, OFF, ON** order. Each leg restores the same explicit `RESUME_PIN` and uses the CPU-audited plan. Expected total wall time is **30–60 minutes (estimate)**, with a 3,600-second cap per leg and no retry. The output is disposable. When OFF repeats agree bitwise, ON must match bitwise. Otherwise, CPU hashes/draws must match and each ON scalar's deviation from either OFF scalar must not exceed the OFF-to-OFF spread. NaNs, changed plans/state and missing ON provenance fail acceptance. Historical launch step 1 is not a continuation baseline.

Compare `ranks[r].data_seconds` and `ranks[r].wall_seconds` on matched replay steps. For ordinary continuation monitoring, compare per-rank and slowest-rank medians/IQR over at least 20 updates per arm. Read logged losses from `ranks[r].components[key]` and `ranks[r].stream_means[stream]`; the disposable total losses are `rank<r>/steps.json[0].first_step_micro_losses`. Require `ranks[r].performance.C1_CPU_PREFETCH == "1"` in ON. 02 and fallback remain OFF; hold 03 fixed.

The separate instrumented profile retains its 895-second bound, heartbeat, partial tables and source-only checkpoint bridge. The precision timing kit retains 20 discarded + 20 measured updates per arm and three repeat blocks: **840 updates, about 31 hours at 133 s/update (estimate)**, plus startup. It uses a stricter bitwise timing-parity gate; the short acceptance replay has the OFF-spread policy above.

For approximate 80% power and two-sided alpha 0.05, `MDD = (t(.975,n−1) + t(.80,n−1)) × s_repeat / sqrt(n)`. At three repeats this is **3.0969 × s_repeat**. An assumed 1-s repeat SD gives approximately 3.10-s resolution, which cannot resolve 03's estimated ≤0.1-s gain. These are planning calculations, not measured production variance or speedups.

'''
local='''## Exact local commands and outputs

All local gates run serially at nice 10 on CPUs 0–7, with `torch.set_num_threads(8)`, the requested thread environment, bytecode disabled and no GPUs. The exact per-suite commands, stdout/stderr and exit statuses appear in the linked logs. The driver command is:

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \\
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \\
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_round3_checks.py \\
  > out/evidence/round3_check_driver.txt 2>&1
```

Exact driver result: `ROUND3_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES`.
[Machine-readable results](evidence/round3_checks.json) distinguish passing gates from accepted baseline-only failures.

| Suite | Exact unittest output | Complete command/output |
|---|---|---|
'''
for c in checks:
    local+='| '+c['kind']+' | `'+ '; '.join(c['summary'])+'; EXIT='+str(c['exit'])+'` | ['+c['log']+'](evidence/'+c['log']+') |\n'
local+='''
The additional plan CLI regression runs as `nice -n 10 taskset -c 0-7 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_round3_plan_cli.py` under the same environment; [its exact output](evidence/round3_plan_cli_after.txt) records one passing case. The main passing gates total 65 test cases, 64 passes and one skip; the additional CLI case brings that to **65 passes and one skip**. The broader 91- and 55-case suites are baseline comparisons, not clean passes.

Patch generation/replay uses the same interpreter/environment with `work/package_round3.py`; it serializes all four zero-fuzz applications. The installed-source audit is retained in [framework_source_audit.txt](evidence/framework_source_audit.txt), [review1_framework_sources.txt](evidence/review1_framework_sources.txt) and [round2_framework_sources.txt](evidence/round2_framework_sources.txt). [SOURCE_NOTES.md](SOURCE_NOTES.md) cites installed torch 2.11 file:line locations and official library documentation for storage accounting, byte comparisons, thread behavior, object collectives and FSDP stream ordering. `resource.RUSAGE_SELF` records process lifetime RSS; it does not isolate the worker.

'''
round1=old[old.index('## Review round 1:'):old.index('## What could go wrong')]
limitations='''## What could go wrong, detection, and work not done

- The bounded audit can miss a larger future group. The default guard fails through original admission; optional fallback preserves synchronous outputs but adds duplicate CPU work and permits an uncapped synchronous group. Watch group/RSS peaks and fallback counter deltas.
- A producer can reduce data wait while slowing training through GIL or CPU-thread contention. Check wall time and per-microstep host timing as well as data wait.
- A missing environment variable can leave prefetch OFF. Require ON `performance` records on every rank; equality alone is insufficient.
- OFF replays can differ across GPU processes. Use the measured per-scalar OFF spread with exact CPU inputs; do not invent a tolerance or compare different checkpoint/row states.
- Clip mixes refuse at first-group factory setup after model load; geometry/MDG/gf1 remain refused. The kit fails absent augmented-pose coverage and out-of-cap emitted grids.
- Peak RSS includes startup and every thread; it is not a 2-GiB total-RAM bound. CUDA allocator diagnostics can change with 03 while losses remain equal.

The eight baseline failure entries are not fixed. The updated 31-test gloo gate, actual production torchvision/processor audit, real CUDA attribution, production numerical acceptance and speed measurements remain host work. No GPU or socket run was attempted here, and no speedup is claimed.

No Git, SSH, GPU query/work, deletion, production write, external job launch or paid API was used. The requested review mappings and supplied-run comparisons are retained because they identify evidence scope. `out_round3/` is the preserved input bundle. [ARTIFACTS.json](ARTIFACTS.json) inventories the final delivery.
'''
report='''VERDICT: DONE All requested round-3 fixes and regressions are delivered against build 21; updated lane gloo and production acceptance remain required.

The dedicated CPU gates pass, including bitwise synchronous-fallback outputs, real `train()` startup and ON provenance. The broad suites reproduce eight documented baseline failure entries without additional failures. Four ordered patches replay with zero fuzz and zero offsets. No production performance gain is claimed.

'''+round3+analysis+patches+kits+coordinator+local+failures+round2+round1+limitations
(ROOT/'out/REPORT.md').write_text(report)
print('ROUND3_REPORT_WRITTEN: outcome, findings, corrected estimates, exact gates and pending host checks')
