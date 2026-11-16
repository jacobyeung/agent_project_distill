# RGB-only student benchmark evaluation

The package evaluates each base checkpoint independently of teacher collection or training. It compares a clean distilled adapter with its own base only when both use the same frozen cohort, RGB frames, processor outputs, prompts, decoding, runtime, and scorer. The package supports VSIBench answerable-500, canonical VSTIBench-450, and DSI-Bench's four supplied variants. Synthetic CPU verification does not establish GPU readiness or benchmark improvement.

## Implementation and evidence

The executable entrypoint is `python -m student_pilot.benchmark_eval`. Its seven commands are `prepare`, `cpu-check`, `cpu-smoke`, `generate`, `score`, `compare`, and `export-bank`. Inference never imports the preparation, scoring, diagnostic admission, conversion, or correctness-dependent retry modules. Existing diagnostic files are unchanged.

The lane's final evidence directory is `/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_eval_harness_20260918/out`. Its `SOURCE_PINS.json` identifies the final source commit and every delivered file by SHA-256. `tests.log`, `REVIEW_PACKET.md`, `REPORT.md`, and `patches/` provide verification, review scope, operator commands, and the patch series. The source-pin manifest is external so this document does not contain a circular self-hash.

Readiness is separate for each stage: synthetic CPU verification, real media/native-processor preflight, GPU smoke, paper attempts, and shared answer-bank registration. Real media, checkpoint files/processors, the original training smoke, and shared coordination evidence were unavailable inside this workspace-only build. The launcher must run their checks after landing the patch. The supplied private Python interpreter is the primary runtime. It has torch 2.11.0, Transformers 5.12.1, PEFT 0.20.0, and PyAV 15.1.0 but no pandas. The supplied planner Python has pandas 3.0.5 and runs the official DSI scorer offline through `--official-python`; no installation is necessary.

CPU verification completed with exit code 0: **42 harness tests and seven diagnostic test bodies passed, with zero failures or skips**. The diagnostic tests use the synthetic substitutions documented below. Six mocked benchmark/model cells produced 36 terminal question receipts and six hash-verified, unregistered banks. Final fixtures are under `out/tests/suite_dd7033f6297b/`, diagnostic fixtures are under `out/diagnostic_regression_d8d3c44c83be/`, and the complete smoke is under `out/cpu_smoke_verified_63c596a328/`, relative to the lane root. `out/VERIFICATION_FINAL.json` binds the tested source bytes; `out/tests.log` retains all test executions. Bash syntax and the CLI parser accepted all 18 reported launcher commands without executing a launch.

### Implementation SHA-256 pins

| File | SHA-256 |
|---|---|
| `student_pilot/benchmark_eval/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `student_pilot/benchmark_eval/__main__.py` | `c742947e1241512bc9120a97f67b61839fa369a14a13f6ed4e6656e4e06cb461` |
| `student_pilot/benchmark_eval/answers.py` | `a7b52dc94dbcd4e591309fe928f2bfb6777dcba6dc0336fc2880e3c710d0293f` |
| `student_pilot/benchmark_eval/contracts.py` | `d68d7305128f09f296fcdd89a31848f39fca82eae25e97acfceed6dd92b01e1c` |
| `student_pilot/benchmark_eval/frames.py` | `85f45d3618574304eb6fa1d020043e1b8e1e36c8c2e6f73422a77f459906c2db` |
| `student_pilot/benchmark_eval/generate.py` | `53d31f65a385a400568361c979323cde5ca923cc7a25d7a91507d84112bfc2ec` |
| `student_pilot/benchmark_eval/prepare.py` | `41edba94b326ce2ca9c30f5d403ea05ae180c89a59c300ceec88b1b7ed905dd5` |
| `student_pilot/benchmark_eval/score.py` | `393e179596bf438cbe28bebfa399c46acd021cd8ff07a16ad88d56c5ed8f605e` |
| `configs/student_benchmark_eval_v1.json` | `50f9011e5e87cddc4a73e9404f06928542e9509e28c3e02edd1fd21ae2380e0b` |
| `scripts/student_benchmark_gpu.sh` | `c451da846389230f83d709f8e079a0508a38e4cf3bb524e201bbc3fa1c03555f` |
| `tests/test_benchmark_eval.py` | `65ea800ea1c3194094fbb4dc7e7e77f9424bb792e5fe8d7b294d1152d1425233` |

The external source-pin manifest additionally covers all fixture files and this handoff. The official DSI scorer and license retain their original bytes, including the license's intentional Markdown trailing spaces.

## CPU verification inside the build workspace

Run from the copied trainer repository. Each invocation retains a new fixture directory; do not remove failed outputs.

```bash
export LANE=/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_eval_harness_20260918
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
export TMPDIR="$LANE/out" XDG_CACHE_HOME="$LANE/out/cache" HF_HOME="$LANE/out/cache/huggingface" TORCH_HOME="$LANE/out/cache/torch"
export STUDENT_EVAL_TEST_ROOT="$LANE/out/tests" STUDENT_EVAL_PROJECT_ROOT=/home/jjyeung/agent_project
export STUDENT_EVAL_OFFICIAL_PYTHON=/data2/jjyeung/envs/planner/bin/python
PY=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python
"$PY" -B -m unittest discover -s tests -p test_benchmark_eval.py -v
"$PY" -B "$LANE/out/run_diagnostic_regression.py"
"$PY" -B -m student_pilot.benchmark_eval cpu-smoke --config configs/student_benchmark_eval_v1.json --artifact-root "$LANE/out" --output "$LANE/out/cpu_smoke_review_new" --project-root /home/jjyeung/agent_project --official-python "$STUDENT_EVAL_OFFICIAL_PYTHON"
```

The diagnostic wrapper runs the seven unchanged diagnostic test bodies with synthetic artifact, processor, and generation-config inputs. It does not establish parity with the absent original smoke example or either pinned processor. The new suite exercises actual CPU video decoding, the existing training encoder with a synthetic processor, real cohort guarding, the pinned canonical scorer/composite builder, the pinned official DSI scorer, durable attempt accounting, input-read canaries, lease validation, matched-arm admission, and immutable bank staging.

## Future launcher setup

These commands are for the operator after landing the patch, not commands executed by this build lane. Keep every output directory new. All Python commands inherit `PYTHONDONTWRITEBYTECODE=1`.

```bash
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export HF_HOME=/data2/jjyeung/cache/huggingface
export HUGGINGFACE_HUB_CACHE=/data2/jjyeung/cache/huggingface/hub
export TORCH_HOME=/data2/jjyeung/cache/torch PIP_CACHE_DIR=/data2/jjyeung/cache/pip
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
STUDENT_REPO=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo
PY=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python
OFFICIAL_PY=/data2/jjyeung/envs/planner/bin/python
PROJECT=/home/jjyeung/agent_project
EVAL="$STUDENT_REPO/artifacts/paper_eval"
CONFIG="$STUDENT_REPO/configs/student_benchmark_eval_v1.json"
MODELS=/data2/jjyeung/cache/huggingface/hub
VIDEOS=/data2/jjyeung/agent_project_data/vsibench_videos
BENCH_ROOT=/data2/jjyeung/agent_project_data/student_eval_benchmarks_20260918
export TMPDIR="$EVAL/cache/tmp" XDG_CACHE_HOME="$EVAL/cache/xdg"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$STUDENT_REPO"
```

### Prepare the three real cohorts

```bash
"$PY" -B -m student_pilot.benchmark_eval prepare --benchmark vsibench_answerable500 --config "$CONFIG" --data-root /data2/jjyeung/agent_project_data/answerable500_gt_canonical_20260902 --membership /data2/jjyeung/agent_project_data/answerable500_membership_20260824/MEMBERSHIP_ANSWERABLE_500.json --media-root "$VIDEOS" --project-root "$PROJECT" --artifact-root "$EVAL" --output "$EVAL/inputs/vsi500_v1"
"$PY" -B -m student_pilot.benchmark_eval prepare --benchmark vstibench_repr450_v2 --config "$CONFIG" --data-root "$PROJECT/agent" --provenance "$PROJECT/agent/vstibench_repr_450_v2.json.provenance" --media-root "$VIDEOS" --project-root "$PROJECT" --artifact-root "$EVAL" --output "$EVAL/inputs/vsti450_v1"
"$PY" -B -m student_pilot.benchmark_eval prepare --benchmark dsibench_all4 --config "$CONFIG" --data-root "$BENCH_ROOT/dsibench" --dataset-manifest "$BENCH_ROOT/dsibench/MANIFEST.json" --artifact-root "$EVAL" --output "$EVAL/inputs/dsi_all4_v1"
```

The VSI/VSTI resolver accepts `dataset/scene.mp4` or `dataset_scene.mp4` and refuses ambiguous or basename-only matches. If the installed tree uses another layout, pass `--media-index /absolute/index.json`, a mapping from `dataset:scene` to a traversal-free path relative to `--media-root`. The index is an explicit preparation input and is recorded in offline source provenance. DSI uses only `videos/<variant>/<relative_path>` and ignores the redundant combined metadata file and unused downloaded clips.

A successful preparation emits `PREPARED_CPU_PREFLIGHT_REQUIRED`, not readiness for a model. Missing media prevent a generation manifest; the failure report preserves exact membership and identifies missing or invalid sources.

### Prepare non-paper smoke inputs and real processor checks

```bash
"$PY" -B -m student_pilot.benchmark_eval cpu-smoke --config "$CONFIG" --project-root "$PROJECT" --official-python "$OFFICIAL_PY" --artifact-root "$EVAL" --output "$EVAL/cpu_smoke_v1"
for model in onethinker qwen35; do
  for cell in vsi500_v1 vsti450_v1 dsi_all4_v1; do
    "$PY" -B -m student_pilot.benchmark_eval cpu-check --manifest "$EVAL/inputs/$cell/generation/manifest.json" --model "$model" --model-root "$MODELS" --artifact-root "$EVAL" --output "$EVAL/checks/${model}_${cell}_base"
  done
  for entry in 'vsi500:nonpaper' 'vsti450:nonpaper_vsti' 'dsi_all4:nonpaper_dsi'; do
    cell="${entry%%:*}"
    directory="${entry#*:}"
    "$PY" -B -m student_pilot.benchmark_eval cpu-check --manifest "$EVAL/cpu_smoke_v1/$directory/generation/manifest.json" --model "$model" --model-root "$MODELS" --artifact-root "$EVAL" --output "$EVAL/checks/${model}_${cell}_smoke"
  done
 done
```

Each real `cpu-check` hashes all four weight shards, checks the local pinned architecture/template, loads only the processor and model configuration, and packs every input without loading model weights. Qwen3.5 derives native decoding from its model configuration when its snapshot lacks `generation_config.json`. A preflight receipt records the exact protocol digest and required coordination `work_id`.

### GPU admission and first base cell

The implementation supports only **trinity-1-8 physical GPU1**. The supervisor must check current ownership, win the matching coordination lease, supply the live GPU UUID, and run the self-contained GPU entrypoint in its admitted vnice-wrapped context. The wrapper preserves the diagnostic validator's host, device, freshness, expiry, owner, coordination, and vnice requirements; it additionally authenticates the actual current coordination file and binds the lease to this model/cohort/protocol. It never claims a lease or allocates a second device.

The supervisor receipt must include `host`, `gpu_index`, `gpu_uuid`, `ownership_check_passed`, `coordination_lease_passed`, `vnice_wrapped`, `owner`, `work_id`, `protocol_sha256`, `coordination_lease_evidence`, `ownership_checked_at`, and `expires_at`. `owner` must equal the current coordination row's `agent_id`. Evidence must be the matching `LEASES/<work_id>.lock/lease.json` under `/data2/jjyeung/agent_project/.coord`, with a running status and a heartbeat no older than five minutes. The launcher owns heartbeats and any renewal; generation rechecks current admission before each model call.

After obtaining the appropriate fresh receipt, the first OneThinker commands are:

```bash
bash "$STUDENT_REPO/scripts/student_benchmark_gpu.sh" --manifest "$EVAL/cpu_smoke_v1/nonpaper/generation/manifest.json" --preflight "$EVAL/checks/onethinker_vsi500_smoke/preflight.json" --model onethinker --variant base --lease "$LEASE_DIR/onethinker_vsi500_smoke.json" --output "$EVAL/runs/onethinker_vsi500_smoke"
bash "$STUDENT_REPO/scripts/student_benchmark_gpu.sh" --manifest "$EVAL/inputs/vsi500_v1/generation/manifest.json" --preflight "$EVAL/checks/onethinker_vsi500_v1_base/preflight.json" --model onethinker --variant base --lease "$LEASE_DIR/onethinker_vsi500_base.json" --output "$EVAL/runs/onethinker_vsi500_base"
```

`out/REPORT.md` gives each benchmark/model smoke and each full base/distilled cell separately. Start ready bases without waiting for training. A single non-paper smoke per model is the controlling plan's minimum GPU gate; the additional benchmark-specific non-paper commands are provided for bounded diagnostic use, not repeated paper attempts. Never use `--limit`, change output budgets, shrink frames, or retry a started paper question. Use `--resume` only on the original run directory with identical frozen bindings.

### Distilled provenance and matched-arm admission

A distilled run requires `--adapter`, `--training-receipt`, and `--base-run`. Before generation, the base-run header must match the distilled arm's complete input/model/settings contract except for adapter identity and variant. The training receipt schema is `clean-student-training-v1`; required fields are:

- `status="TRAINED"`, `benchmark_trained_diagnostic=false`, `smoke=false`, `dataset="VSI-590K"`, and `base_restart="original_checkpoint"`.
- `base={repo_id, revision}` for the exact student; `preprocessing` equal to the configuration's complete `rgb` object; the matching model's `enable_thinking` value.
- `selection_frozen_before_benchmark=true`, `trained_module_families=["vision","merger","language"]`, and SHA-256 values for `training_data_sha256` and `scene_split_sha256`.
- `adapter={config_sha256, weights_sha256}` for `adapter_config.json` and `adapter_model.safetensors`. Synthetic receipts cannot authorize real inference.

The adapter validator checks the tensor/config closure without a OneThinker-only module-name allowlist. The model loader freezes all parameters, disables training/dropout behavior, loads the adapter without merging, and compares saved/reloaded tensor values and dtypes exactly. Native PEFT CPU fixtures cover homogeneous FP32 and BF16 adapter archives for both model dispatches; an incompatible precision layout fails closed rather than being silently rounded. It rejects diagnostic and infrastructure-smoke adapters. The clean-training lane owns truthful lineage and validation/model-selection attestations; the evaluator does not inspect teacher labels.

Prepare a separate distilled CPU preflight with the same generation manifest:

```bash
"$PY" -B -m student_pilot.benchmark_eval cpu-check --manifest "$EVAL/inputs/vsi500_v1/generation/manifest.json" --model onethinker --model-root "$MODELS" --variant distilled --adapter "$ONETHINKER_ADAPTER" --training-receipt "$ONETHINKER_TRAINING_RECEIPT" --artifact-root "$EVAL" --output "$EVAL/checks/onethinker_vsi500_v1_distilled"
```

Repeat for the other two cohorts and for `qwen35` with its own adapter and receipt. These checks are independent of the already runnable bases.

## Offline scoring, comparison, and answer banks

```bash
RUN="$EVAL/runs/onethinker_vsi500_base"
"$PY" -B -m student_pilot.benchmark_eval score --run "$RUN" --scoring-manifest "$EVAL/inputs/vsi500_v1/scoring/manifest.json" --official-python "$OFFICIAL_PY" --artifact-root "$EVAL" --output "$EVAL/scores/onethinker_vsi500_base"
"$PY" -B -m student_pilot.benchmark_eval export-bank --run "$RUN" --score "$EVAL/scores/onethinker_vsi500_base/scores.json" --bank-id student_onethinker_vsi500_base_s17_v1 --artifact-root "$EVAL" --output "$EVAL/banks/student_onethinker_vsi500_base_s17_v1"
"$PY" -B -m student_pilot.benchmark_eval compare --base "$EVAL/scores/onethinker_vsi500_base/scores.json" --distilled "$EVAL/scores/onethinker_vsi500_distilled/scores.json" --artifact-root "$EVAL" --output "$EVAL/comparisons/onethinker_vsi500_v1"
```

Scores replay the frozen parser from native raw text, verify stored parsing and provenance, and preserve a separate deterministic compatibility projection. Missing receipts receive zero credit without shrinking denominators. VSI uses the pinned MRA/MC scorer and eight-task composite; VSTI uses the same strict scorer and official five-subtask composite, with a separate raw nine-category macro. DSI exports four ordered A–D/E prediction CSVs and cross-checks full-precision wrapper results against the pinned official sample-wise, three-of-four group-wise, and single-view functions. Numerical payloads are normalized to plain decimal notation before the legacy numeric extractor; this preserves numeric signs and scientific notation while leaving its metric unchanged.

A run contains `run.json`, `attempts.jsonl`, immutable `questions/<safe-id>.json`, `generations.jsonl`, and `completion.json`. A score contains `scores.json`, `per_question_scores.jsonl`, compatibility or DSI projections, the scorer closure, and explicit coverage/error/cap counts. A bank contains the full native and scoring records, membership, model/runtime/frame provenance, selected RGB frames, source bindings, `export_receipt.json`, and `SHA256_MANIFEST.json`.

Every export remains `shared_registry_status=pending` and `publication_ready=false`. The campaign archiver must copy the bank to the shared `ANSWER_BANKS/<bank_id>/`, update the registry and SHA authority under its lock, and mirror metadata in shards of at most 100 KB. This package does not create another shared-registry writer or nominate paper scores.

## Read-only completion check

Set `RUN`, `SCORING_MANIFEST`, and `N` to the chosen cell. Expected counts are 500, 450, and 7,076 for the three real cohorts; synthetic smoke counts are 3, 3, and 12.

```bash
"$PY" -B -c 'import sys; from pathlib import Path; from student_pilot.benchmark_eval.contracts import load_json,load_generation; from student_pilot.benchmark_eval.score import _read_run; s=load_json(sys.argv[2]); _,rows,_=load_generation(s["generation"]["path"]); h,q,p,n=_read_run(sys.argv[1],s,rows); c=load_json(Path(sys.argv[1])/"completion.json"); assert len(rows)==len(q)==n==int(sys.argv[3])==c["terminal_count"]; assert c["status"]=="TERMINAL_CENSUS_COMPLETE"; print("INTEGRITY_CHECKED_ATTEMPTS_COMPLETE",n)' "$RUN" "$SCORING_MANIFEST" "$N"
```

Completion means the fixed attempts and their terminal outcomes are present, not that every answer parsed or was correct. Read the score's failure and cap counts before interpreting a result.
