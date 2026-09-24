# Qwen3.6-27B answer-only Orchard stage

This stage trains vision, merger, and language LoRA adapters with the pinned arm C trainer. It selects an answer-only dataset and epoch count without changing the evaluation harness, trainer source, model-staging key, or publication path. The corrected set H is the primary variant; its one-epoch option is a deadline fallback.

## Recipes and dataset identities

| Variant | Config | Epochs | Candidate rows | Train rows | Heldout rows | Estimated wall time |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `setH` | `qwen36_27b_ao_setH.json` | 3 | 9,232 | 7,684 | 1,548 | ≈9.3h, from 23,136 realized rows including padding / 0.694 rows/s |
| `setH_e1` | `qwen36_27b_ao_setH_e1.json` | 1 | 9,232 | 7,684 | 1,548 | ≈3.1h, from ≈7,712 realized rows / 0.694 rows/s |
| `fullpool` | `qwen36_27b_ao_fullpool.json` | 1 | 29,399 | 25,164 | 4,235 | ≈10h upper bound, from 25,164+ rows / 0.694 rows/s |

These are the brief's rate-based planning estimates, not measured answer-only runtimes or guaranteed deadlines. Queueing, staging, initialization, and requeues add time. The set H and full-pool epoch counts match their respective 9B recipes; the fallback does not match the three-epoch set H comparison.

All configs retain world size 4, effective batch 32, FSDP, bf16 (`bfloat16` in JSON), LoRA rank 32 / alpha 64 / dropout 0.05, learning rate 1e-4, cosine scheduling, warmup 0.03, sequence limit 16,384, target limit 8,192, and `targets=exact_text_attention_mlp_vision_attention_mlp_mergers`. The included `configs/qwen36_27b.json` is the unchanged deployment template used as the derivation reference. Only `epochs` may differ. Dataset and split paths belong to launch arguments and environment variables, never to the training JSON.

The microbatch policy stays `microbatch_size="auto"`, `max_microbatch_size=8`. Answer-only targets do not remove prompt frames or images, which dominate memory. The arm C probe measured microbatch 4, 59.6–62.3 GB reserved per rank on 80 GB GPUs, 96 steps, 5,206.02 seconds total wall time, and 0.6941 rows/s. Its frozen run config has a cap of 4, while the supplied deployment template has a cap of 8. This stage deliberately derives from the requested deployment template; it does not claim that the probe measured cap 8 or that larger microbatches are safe. The unchanged automatic memory-fit logic must resolve the new run.

`manifest.json` stores the candidate/split names, row counts, canonical Orchard paths, and these SHA256 pins. These metadata are fixtures, not copies of the datasets.

| Dataset | File | SHA256 |
| --- | --- | --- |
| Set H | `candidate_index.jsonl` | `5797eac24b659eb9c5ac7f41242f842a345e231b5cd7ed7135758cc85de97cca` |
| Set H | `split_trainer.json` | `eec29d981c5c30b6217c72938bfbb1c0cbd13842ff651767a2c657125092cb27` |
| Full pool | `candidate_index.jsonl` | `b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446` |
| Full pool | `split_trainer.json` | `46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70` |

## Freeze configs locally and transfer them

The builder runs only the CPU checks. The separate ssh-capable Orchard lane runs the transfer and submission commands below; they are not authorization for the builder to contact Orchard.

On Trinity, retain the three selected configs under their real model-staging filename:

```bash
L=/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/qwen27b_answeronly_stage_20260924
STAGE=$L/work/repo/orchard/stages/qwen36_27b_answeronly
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=""
export TMPDIR=/scratch/jjyeung/qwen27b_ao_stage_tests
mkdir -p "$TMPDIR"
python -B "$STAGE/scripts/dry_run_check.py" --frozen-root "$L/out/frozen_configs"
AO_REFERENCE_DEPLOYMENT="$L/inputs/deployment_433d8a1" \
  python -B -m unittest discover -s "$STAGE/tests" -v
```

The reference path enables integration tests against the actual staged submitter. Those tests replace Slurm and Git with local CPU fixtures; without that path, only the integration class is skipped.

On the ssh-capable transfer host, use the established Orchard connection. These commands copy the stage and frozen aliases without deleting destination-only files or modifying a trainer or run deployment:

```bash
L=/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/qwen27b_answeronly_stage_20260924
STAGE=$L/work/repo/orchard/stages/qwen36_27b_answeronly
R=/project/community/jjyeung/distill
export PATH=/home/jjyeung/google-cloud-sdk/bin:$PATH
export CLOUDSDK_CONFIG=/tmp/jjyeung_gcloud_config
RSH="ssh -F /tmp/jjyeung_ssh_orchard_config"
rsync -a --checksum -e "$RSH" --rsync-path="mkdir -p $R/stages/qwen36_27b_answeronly && rsync" \
  "$STAGE/" "orchard:$R/stages/qwen36_27b_answeronly/"
rsync -a --checksum -e "$RSH" \
  "$L/out/frozen_configs/" "orchard:$R/stages/qwen36_27b_answeronly/frozen_configs/"
```

The second command lands `frozen_configs/setH/configs/qwen36_27b.json`, `frozen_configs/setH_e1/configs/qwen36_27b.json`, and `frozen_configs/fullpool/configs/qwen36_27b.json`. The launcher checks each transferred selection against its named variant before copying it into its own deployment. If the alias bundle is absent, the launcher freezes the identical bundled variant directly.

## Check the actual Orchard model stager

The source deployment must already exist at `$ORCH/code/deployment_433d8a1`, with `scripts/orchard/{common.sh,submit_train.sh,run_train.sh,train_job.py,stage_model.py,configs/qwen36_27b.json}` and `slurm/train_qwen36_27b.slurm`. The clean trainer must remain at commit `433d8a117bf94bcd8214de9a6d6e149ff6f5f74f`.

The actual `stage_model.py` was not available to the builder. Before submitting, the Orchard lane must inspect that exact file and its model-manifest lookup. Confirm that its first positional argument accepts `qwen36_27b` and stages `Qwen/Qwen3.6-27B` at revision `6a9e13bd6fc8f0983b9b99948120bc37f49c13e9`. Do not execute the model stager merely to inspect it. After that review, bind the reviewed bytes with this hash:

```bash
export ORCH=/project/community/jjyeung/distill
export ORCH_BASE_DEPLOY=$ORCH/code/deployment_433d8a1
sed -n '1,240p' "$ORCH_BASE_DEPLOY/scripts/orchard/stage_model.py"
export STAGE_MODEL_REVIEWED_SHA256=$(sha256sum "$ORCH_BASE_DEPLOY/scripts/orchard/stage_model.py" | cut -d ' ' -f 1)
: "${ROOMFIX_GATE:?Set the existing dataset review verdict path; do not invent a verdict}"
```

Export `STAGE_MODEL_REVIEWED_SHA256` only after confirming the mapping. The launcher requires it, checks it against the actual source file, and records it in the frozen deployment receipt. It never treats a differently named config as a new student/model token. The model manifest remains `$ORCH/incoming/model_sha256_meta.json`, and the default frame map remains `/data2=$ORCH/data2root`.

## Submit one selected variant on Orchard

Set the shared environment on the Orchard login node. Keep `ROOMFIX_GATE` bound to the applicable dataset review and keep the reviewed model-stager hash from the preceding step.

```bash
export ORCH=/project/community/jjyeung/distill
export PARTITION=advanced QOS=adv_4gpu_qos WORLD_SIZE=4
export TRAINER=$ORCH/code/orchard_trainer_433d8a1
export TRAINER_COMMIT=433d8a117bf94bcd8214de9a6d6e149ff6f5f74f
export MODEL_MANIFEST=$ORCH/incoming/model_sha256_meta.json
export STUDENT_FRAME_ROOT_MAP=/data2=$ORCH/data2root
STAGE=$ORCH/stages/qwen36_27b_answeronly
B=$ORCH/data2root/jjyeung/agent_project_data/student_diagnostic_pilot_20260918
```

For the primary three-epoch set H run:

```bash
SPLIT_RECORD="$B/mix_v25_roomfix_answeronly_20260923/split_trainer.json" \
  bash "$STAGE/submit_train_ao.sh" setH \
  "$B/mix_v25_roomfix_answeronly_20260923_trainer" qwen36_27b_ao_setH_20260924
```

For the one-epoch set H fallback instead:

```bash
SPLIT_RECORD="$B/mix_v25_roomfix_answeronly_20260923/split_trainer.json" \
  bash "$STAGE/submit_train_ao.sh" setH_e1 \
  "$B/mix_v25_roomfix_answeronly_20260923_trainer" qwen36_27b_ao_setH_e1_20260924
```

For the one-epoch full-pool run:

```bash
SPLIT_RECORD="$B/answeronly_fullpool_20260923_trainer/split_trainer.json" \
  bash "$STAGE/submit_train_ao.sh" fullpool \
  "$B/answeronly_fullpool_20260923_trainer" qwen36_27b_ao_fullpool_20260924
```

Each invocation verifies the real Orchard candidate/split hashes and candidate row count, checks the clean trainer pin, and refuses an already published run. It copies the source deployment into `$ORCH/code/deployment_433d8a1_ao27b_<variant>_<run_id>` and places the selection at `scripts/orchard/configs/qwen36_27b.json`. It preserves the copied arm C config and Slurm file under `_quarantine/answeronly_stage/`; it never edits the source deployment. Reusing a deployment requires the same receipt, source bytes, selected config, and Slurm wrapper. A partial or changed deployment fails closed; retain it and use a new run ID.

The launcher exports this new root as `ORCH_DEPLOY` and invokes its existing `submit_train.sh qwen36_27b <dataset_root> <run_id>`. The copied `_ao` Slurm wrapper occupies both Slurm filenames so the existing case statement remains unchanged. The wrapper delegates to `run_train.sh qwen36_27b "$1" "$2"`, and `train_job.py` still loads `HERE/configs/(student+'.json')`. The variant name never becomes the student token.

`PREPARE_ONLY=1` performs the checks and freezes the deployment without contacting Slurm. `DRY=1` additionally runs only `sbatch --test-only`; the normal path runs the existing submitter's test-only check and then its parsable submission. `DEPENDENCY=afterany:<job_id>` passes through unchanged. `ORCH_BASE_DEPLOY` selects the source root; `ORCH_AO_DEPLOY` can select a distinct destination. An inherited `ORCH_DEPLOY` is deliberately replaced, not edited.

The default scheduler allocation is four H100s on `advanced/adv_4gpu_qos`, with 32 CPUs, 384 GB host memory, a one-day limit, and no requeue. The supported override is `PARTITION=preempt QOS=preempt_qos WORLD_SIZE=8`, with 64 CPUs, 512 GB host memory, a two-day limit, and requeue. Other combinations fail as they do in the original submitter. The eight-GPU override changes the runtime world size through the existing trainer; it is not the four-GPU comparison in the recipe table. FSDP, checkpoint interval 25, and the trainer commit remain pinned; smoke mode is refused.

## Publication identity and verification scope

The unchanged trainer finalizer publishes to `$ORCH/runs/<run_id>/publication/`. The publication must carry the following identity fields verbatim; the Orchard lane must verify the actual `PUBLISHED.json` before treating the run as published:

```text
schema=student-publication-v1
protocol_version=vlm-lora-ddp-v2
base.repo_id=Qwen/Qwen3.6-27B
base.revision=6a9e13bd6fc8f0983b9b99948120bc37f49c13e9
student=qwen36_27b
trained_module_families=[vision,merger,language]
result_status="diagnostic, provisional"
provisional_diagnostic=ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW
benchmark_improvement_claim=false
score_nomination_allowed=false
provenance.commit=433d8a117bf94bcd8214de9a6d6e149ff6f5f74f
```

The staging commit is not the trainer provenance commit. `dry_run_check.py` reproduces the config lookup using the literal student token, verifies all three JSON recipes and the literal dataset fixtures, and rejects changed hashes and row counts. It loads no model and reads no real Orchard dataset. Unit tests cover derivation, identity checks, deployment freezing, and scheduler/argument propagation with CPU fixtures. Tests retain their temporary files under `TMPDIR`; they do not delete or clean artifacts. No benchmark score or improvement claim follows from these staging checks.
