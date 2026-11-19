VERDICT: PARTIAL The A10b step-400 kit passes all CPU checks, but target preparation and the Ada run require 13 missing runtime parts and an idle card.

The delivery targets Orchard job **173060**, read A, package `a15_cot_apdc76460c3a164`, run `6ed2c7aa`, step **400**, artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. A10b is the default and the main test fixture. [README.md](README.md) describes the kit; [MISSING.json](MISSING.json) lists every additional byte the coordinator must supply. The kit fetches nothing.

The original delivery is preserved in `../out_round0/`. The integrity check verified all 999 preserved files against the untouched original before publication. No original input tree was edited. This build ran on trinity-1-18 with CUDA hidden, no SSH, no Git, no scheduler operation, no paid API, and no deletion. Network use was limited to the cited official PyTorch documentation.

## Numbers: measured, pinned, and estimated

| Quantity | Result | Evidence/basis |
|---|---:|---|
| Direct revised CPU suite | 71 tests passed | Measured across 39 base, 18 review, 7 preparation, and 7 bootstrap tests. |
| Same finding suite on preserved code | 16 failures, 1 error, 1 positive control passed | Measured; the error is the rejected scratch runtime prefix. All 18 pass on revised code. |
| Applied-patch CPU suite | 71 tests passed | Measured after fresh application and A10b bootstrap. |
| Maximum test-process RSS | 238392 kB | Measured by `/usr/bin/time -v`; eight-thread limits, far below the 30 GB ceiling. |
| Sealed source | 927 files; 24,684,350 bytes | Measured from authenticated A10b payload; every source byte matches the supplied tree. |
| Base files preserved by patch | 944 files | Measured source/package/operator hash comparison. |
| Orchard reference | 77 archive members; 636 rows; first 50 authenticated | Measured against archive SHA256 `c038467436ef0c6e87cb9cace5f472ac5e9b40cb4863f295b748ccbcd5ee8ae3`; [REFERENCE_PROOF.json](REFERENCE_PROOF.json). |
| Missing runtime | 13 parts; 10,497,433,600 bytes | Read from A10b ORCHARD_ASSETS pins, observed host `orchard-login-001`; MISSING.json has each source and target path. |
| Model/input archives | 32613048320 bytes packed; 32606120583 bytes expanded | Read from A10b a/1.json pins. |
| Planned target disk peak | 124,166,664,744 bytes | Estimate including pinned inputs, retained archives, existing SAM3, 40 GB runtime allowance and 5 GB operating allowance; cap 150 GB. |
| Free scratch floor | 214,748,364,800 bytes | Configured 200 GiB requirement, not a measurement of current target free space. |
| Actual target runtime imports / full preparation / GPU runs | 0 / 0 / 0 | Not performed; no target-host access was permitted. |

The disk estimate conservatively counts existing SAM3 separately from input expansion; extraction reuses that archive member when its bytes agree. The supplied member lists resolve a2/a3/a4/G3T contents. The pinned environment receipt requires **torch 2.13.0+cu130, torchvision 0.28.0+cu130, transformers 5.19.0, scipy 1.14.1**. These are receipt values, not measurements on 2-28. The listed a4.tar supplies the wrapper and overlay, not the base Python/torch runtime. [ENVIRONMENT.md](ENVIRONMENT.md) records the namespace mapping and the remaining target import requirement.

The bootstrap uses `/usr/bin/python3` **3.6.8** for stdlib extraction and relocation; seven tests ran on the actual system 3.6.8 interpreter here. Control and worker execution use `/scratch/jjyeung/b01ec87a6f29b/d/v/py`, with the sealed wrapper's `-B -I` arguments. The base environment moves to local scratch; the kit imposes no `/scratch/jjyeung/envs` prefix requirement. The real staged control Python cannot be tested here because its pinned runtime parts are absent. The import probe must pass before preparation or the card gate.

## Review round 1: finding -> fix -> test

| Finding | Fix and remaining limit | Regression evidence |
|---|---|---|
| HIGH 1: unresolved environment | STAGE_PLAN records q/env.json versions and archive destinations. Python 3.6 staging maps the package runtime namespaces onto scratch; explicit relocation preserves originals and changes only recognized absolute prefixes. The import probe verifies local interpreter/module paths and coverage by sysconfig audit roots plus unchanged env_roots. `stage228.py --prepare` and `stage_check(prepare=True)` precede the gate. A valid READY receipt is checked without relaunching preparation. **Deployment remains blocked until MISSING.json is supplied.** | `test_high1_environment_versions_are_resolved`, `test_high1_scratch_runtime_prefix_is_accepted`, and `test_high1_prepare_precedes_gpu_gate` fail on preserved code and pass now. Preparation idempotence, incomplete extraction refusal, audit coverage, and Python 3.6 extraction have additional passing tests. |
| HIGH 2: IO plan | All transfer/governor actions are absent. Existing staged model parts map to reads228/dl; package a/6 travels with the kit. The coordinator owns missing-byte delivery. | `test_finding2_stage_plan_has_no_download_or_governor_actions` fails before and passes after. |
| HIGH 3: placement includes stage-1 floats | Placement contains only `(index, family, call, served, at_token)`. Stage-1 values remain in trace diffs. | `test_high3_one_ulp_stage1_drift_preserves_instrument` fails before and passes after: 50 answers, 50 placements, 49 traces match; SAME_INSTRUMENT. |
| HIGH 4: optional provenance | LOCAL_RUN backend/host/OFF, Ada CARDS snapshot, every journal host, and a non-173060 RETURN_ID are mandatory. Orchard-vs-Orchard is ineligible. | Five refusal regressions fail before and pass after: Orchard-vs-Orchard, wrong local host, wrong GPU, another journal's Orchard host, reused Orchard job. The positive LOCAL_RUN fixture passes both versions. |
| MEDIUM 5: missing return metadata | The adapter calls sealed `runner.run(..., launcher=...)`; the sealed runner writes IDENTITY, projection and a/30.json. Allocation/storage metadata and root logs are included. | `test_medium5_orchard_metadata_members_are_present` fails before and passes after against ORCHARD_MEMBERS and authenticated identity/projection schemas. The original unpacker accepts the 50/636 return. |
| LOW 6: worker environment | USER/LOGNAME are jjyeung. HOME, CUDA_CACHE_PATH and MPLCONFIGDIR are local; cache directories fall within audited write roots. The sealed runner receives a fixed system PATH and no inherited library injection. | `test_low6_worker_identity_and_all_caches_are_local` fails before and passes after. The sealed-runner integration also passes with the normal inherited agent environment. |
| LOW 7: OFF checks wrong object | `rows()` retains complete environment records; OFF validation reads `settings`. | `test_low7_off_is_checked_in_settings` fails before and passes after. |
| LOW 8: unpinned vnice | A10b_PINS records both vnice and terminator SHA256 values; deployment and stage checks verify both. | `test_low8_deployment_verifies_both_policy_scripts` fails before and passes after. Additional tests corrupt each script at unchanged size and verify refusal. |
| LOW 9: writes outside work/local output | Unpacker fixtures copy only their operator wrapper into work; comparator `--out` passes through `local()` before comparison. | Both LOW 9 regressions fail before and pass after. The before test intercepts the forbidden destination before any write occurs. |
| INFO 10: launch differs from Orchard | The worker uses the package's native `--settings` hook, imports the reader/framework before runpy, and wraps load_native to record framework details while returning its original result. The duplicate parity import is removed. These launch/observation differences do not constitute numerical parity evidence. | Existing observer identity and sealed resolver tests pass. The Ada comparison remains required. |
| INFO 11: retained safeguards and receipt | The two-read >=300 s/<100 MiB/no-process Ada gate, UUID lock, per-item peaks, one-second telemetry and first-OOM exit 42 remain. The worker gets `start_new_session=True`, separating it from the control process. `read228.sh --items` defaults to 50. | The process-group regression fails before and passes after. Busy-card, UUID, OOM, partial-return, malformed-journal and argument-forwarding tests pass. No live terminator kill or GPU behavior was tested. |

The before/after comparisons above are retained as the explicitly requested regression evidence. The patch does not certify hardware provenance against forged metadata; it checks the required provenance fields for consistency.

## Exact test outputs and patch

| Run | Exact unittest footer | Measured MaxRSS | Full output |
|---|---|---:|---|
| Direct review_before | Ran 18 tests in 2.559s; FAILED (failures=16, errors=1) | 237300 kB | [exact output](checks/final_review_before.txt) |
| Direct base | Ran 39 tests in 6.401s; OK | 238000 kB | [exact output](checks/final_base.txt) |
| Direct review_after | Ran 18 tests in 2.415s; OK | 238012 kB | [exact output](checks/final_review_after.txt) |
| Direct prepare | Ran 7 tests in 0.125s; OK | 224032 kB | [exact output](checks/final_prepare.txt) |
| Direct bootstrap36 | Ran 7 tests in 0.013s; OK | 18388 kB | [exact output](checks/final_bootstrap36.txt) |
| Applied patch base | Ran 39 tests in 5.030s; OK | 238392 kB | [exact output](checks/patch_base.txt) |
| Applied patch review_after | Ran 18 tests in 2.095s; OK | 238208 kB | [exact output](checks/patch_review_after.txt) |
| Applied patch prepare | Ran 7 tests in 0.123s; OK | 224676 kB | [exact output](checks/patch_prepare.txt) |
| Applied patch bootstrap36 | Ran 7 tests in 0.013s; OK | 18428 kB | [exact output](checks/patch_bootstrap36.txt) |

Every test argv, environment override, UTC start, exit code and output path is recorded in [final_RUNS.json](checks/final_RUNS.json) and [patch_RUNS.json](checks/patch_RUNS.json). CPU tests use the requested `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`; torch tests call `torch.set_num_threads(8)`. All test artifacts and cache overrides stay under `work/`. The complete outputs are linked above; no timing or RSS value is estimated.

To repeat the revised suite from the delivered kit:

```bash
date -u
bash tests/run_tests.sh
```

The measured validation commands were serialized by `work/round1/validate.py`; each child command has this exact form, with the specific script path recorded in RUNS.json:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_kit.py
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_review.py
nice -n 10 /usr/bin/time -v /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_prepare.py
nice -n 10 /usr/bin/time -v /usr/bin/python3 -I -s -B tests/test_bootstrap36.py
```

The before run sets `READ228_REVIEW_KIT=/scratch/jjyeung/orch_n30/so_reads228/out_round0` while executing the same revised `tests/test_review.py` and A10b fixtures. It must exit 1. Direct and applied-patch revised suites must exit 0.

[01_trinity_adapter.diff](patches/01_trinity_adapter.diff) adds **59 files**, **3148814 bytes**, under `read228/` against the supplied A10b tree. It changes no existing source/package/operator file. Its SHA256 is `eb683b133f60b0406d8586be280f569a7c592e3a339648e873988836c8ea6de3`. [patches/MANIFEST.json](patches/MANIFEST.json) pins every added file. New entry points activate the adapter; observation requires `--observe`, relocation requires `--relocate-runtime`, and cache extensions default OFF.

The exact recorded patch check was:

```bash
nice -n 10 patch --batch --fuzz=0 -p1 -d /scratch/jjyeung/orch_n30/so_reads228/work/round1/patch_apply_proof -i /scratch/jjyeung/orch_n30/so_reads228/work/round1/kit/patches/01_trinity_adapter.diff
```

It returned 0 with no fuzz. The fresh patch output, the tested applied tree, and the delivered adapter all match every manifest hash. [INTEGRITY.json](checks/INTEGRITY.json) records this check, the unchanged base files, syntax checks and the measured workspace footprint. A10b bootstrap reported exactly:

```text
{"output": "/scratch/jjyeung/orch_n30/so_reads228/work/round1/applied_base/read228/A10b", "files": 927, "expanded_bytes": 24684350, "step": 400}
```

The CPU comparison cases have these measured outcomes; they are synthetic local-provenance fixtures, not GPU runs:

| Fixture | Answers | Placement | Trace | Verdict |
|---|---:|---:|---:|---|
| local_identical | 50/50 | 50/50 | 50/50 | SAME_INSTRUMENT |
| one_answer_changed | 49/50 | 50/50 | 49/50 | SAME_INSTRUMENT |
| one_call_moved | 50/50 | 49/50 | 49/50 | DIAGNOSTIC_ONLY |
| orchard_vs_orchard | 50/50 | 50/50 | 50/50 | DIAGNOSTIC_ONLY |
| stage1_one_ulp | 50/50 | 50/50 | 49/50 | SAME_INSTRUMENT |

[COMPARE_CASES.json](checks/COMPARE_CASES.json) records the counts and reasons; adjacent `compare_*.json` files contain every per-item diff.

## Exact coordinator sequence on trinity-2-28

Run in an existing tmux session on **trinity-2-28** after the coordinator places the complete kit at `/scratch/jjyeung/orch_n30/reads228/kit` and supplies every missing part at its MISSING.json target. All model/input archives are already staged per the dispatch. The following is the delivered script; invoke it as `bash coordinator228.sh "$CARD" /scratch/jjyeung/orch_n30/reads228/runs/a400check1`, where CARD is the chosen index/UUID and the output directory is fresh. The gate currently has no known idle candidate because all eight cards are occupied per the dispatch.

```bash
#!/usr/bin/env bash
# Run only after the coordinator supplies every MISSING.json target on local scratch.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo 'Usage: bash coordinator228.sh <idle-card-index-or-UUID> <fresh-local-run-directory>' >&2
  exit 2
fi
date -u
if [[ "$(hostname -s)" != trinity-2-28 ]]; then
  echo 'REFUSED: coordinator228.sh is restricted to trinity-2-28' >&2
  exit 2
fi
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
export HOME=/scratch/jjyeung/orch_n30/reads228/control_home
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/reads228/control_cache
export CUDA_CACHE_PATH="$XDG_CACHE_HOME/nv" MPLCONFIGDIR="$XDG_CACHE_HOME/mpl"
export HF_HOME="$XDG_CACHE_HOME/hf" TRITON_CACHE_DIR="$XDG_CACHE_HOME/triton"
export USER=jjyeung LOGNAME=jjyeung PATH=/usr/local/bin:/usr/bin:/bin
unset LD_LIBRARY_PATH
mkdir -p "$HOME" "$XDG_CACHE_HOME" "$CUDA_CACHE_PATH" "$MPLCONFIGDIR" "$HF_HOME" "$TRITON_CACHE_DIR"
package="$kit_dir/A10b"
# All extraction uses the target system Python 3.6.8; it imports no ML libraries.
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --extract-runtime
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --extract-inputs
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --relocate-runtime
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --install-code
date -u
# Match the wrapper's Orchard invocation flags. No /envs/p1cpu is needed on 2-28.
export READ228_CONTROL_PYTHON=/scratch/jjyeung/b01ec87a6f29b/d/v/py
nice -n 10 "$READ228_CONTROL_PYTHON" -B -I "$kit_dir/stage228.py" "$package" --prepare
date -u
nice -n 10 "$READ228_CONTROL_PYTHON" -B -I "$kit_dir/stage228.py" "$package" --out /scratch/jjyeung/orch_n30/reads228/STAGE_CHECK.json
date -u
# run228 performs stage_check(prepare=True), then the two >=300-second idle readings,
# then exactly the requested first 50 commits. A busy card exits; there is no wait/retry loop.
bash "$kit_dir/run228.sh" "$package" "$1" "$2" --items 50
date -u
bash "$kit_dir/compare228.sh" "$2/ret" --orchard "$kit_dir/reference" --out "$2/COMPARE.json"
date -u
```

The run command performs the stage check, card gate and 50-item run in one process so the gate's UUID lock stays held. It never loops until a card becomes free. A busy card, missing byte, failed import, failed preparation or killed worker exits without automatic retry. The clean prefix has `requested_prefix_complete=true`, remains 50/636, and has no full-read COMPLETE marker. The original return envelope labels incomplete returns `FAILED`; the adapter exits 0 for a successful requested prefix.

## What could go wrong and how we would notice

- **Missing or incompatible runtime:** missing parts stop extraction; unknown members/links stop mapping; wrong versions, ABI imports or audit-root coverage stop the import probe. None triggers a fetch, install, fallback interpreter or retry. Runtime archive lists/binaries and the actual target wrapper have not been inspected here.
- **Partial staging or a killed preparation:** completed extraction receipts are required; original/relocated wrapper hashes must agree. An existing restore without READY refuses preparation. Existing mismatching archive members are preserved and refused.
- **Occupied or newly claimed GPU:** the strict gate refuses current occupancy. The UUID lock coordinates this kit only; another user's allocation can still arrive afterward. One-second telemetry exposes occupancy changes. Do not run a relaunch loop.
- **Memory pressure or kill:** the first OOM writes OOM.json and STOP, exits 42 and packages failure without COMPLETE. A worker-group exit can leave the separate control process alive to write a receipt. Killing the control process or whole user session can still prevent a receipt. A kill before the first journal can make the unchanged unpacker reject the archive.
- **H100/Ada numerical drift:** the comparator reports answer, placement and trace differences. Only >=49 answers and all 50 placements with eligible OFF provenance establish SAME_INSTRUMENT. One-ulp stage-1 drift is diagnostic trace data. Source/weight equality alone proves no device parity.
- **Disk estimate exceeded:** extraction caps runtime expansion at 40 GB; the stage check enforces the 150 GB budget with a 5 GB operating allowance and 200 GiB free floor. Target disk usage and runtime expansion were not measured.

## What is not done

The 13 missing runtime parts were not fetched. No command ran on trinity-2-28. Real runtime relocation/imports, full sealed model preparation, the 300-second live gate, the 50-item Ada run, CUDA peaks, runtime and SAME_INSTRUMENT verdict remain pending. CPU doubles exercise control flow and metadata layout only. Full corpus ingestion and downstream scorers were not executed. ON overlays remain unavailable until their supplied inconsistencies are resolved; OFF does not load them.

Framework API behavior is cited to installed torch 2.11 source by file/line in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md), with fetched official documentation links. A10b's pinned 2.13 reader environment must pass its own import probe. No other agent's work was stopped.
