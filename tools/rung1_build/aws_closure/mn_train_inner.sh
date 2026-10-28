#!/usr/bin/env bash
# Multi-node native training on code-aws (lane rung1_build), one copy per node inside the image: the awstrain lane's
# train_inner.sh environment and lease path, with node-scoped leases (trainer b4b2979 orchard_admission multi-node
# allocation, bind-lease-ddp --node-rank/--nnodes, merge-lease-ddp on node 0) and the trainer's own multi-node torchrun
# launcher (scripts/diagnostic_ddp_gpu_batch.sh with NNODES/NODE_RANK/MASTER_ADDR/MASTER_PORT). An optional N-step smoke
# stop records per-step seconds from the trainer's metrics.
# usage: mn_train_inner.sh FROZEN_NAME RUN_NAME [SMOKE_STEPS]   (FROZEN_NAME: a directory under the run root's frozen/)
set -euo pipefail
frozen_name="${1:?frozen preparation name}"
run="${2:?unique run name}"
smoke="${3:-0}"
: "${R1_MOUNT:?}" "${R1_TRAINER:?}" "${ANYHOST_JOBS:?}" "${SLURM_JOB_ID:?}" "${SLURM_NODEID:?}" "${SLURM_JOB_NODELIST:?}"
base="$R1_MOUNT/runs/aws128p_20261025"
[[ "$frozen_name" =~ ^[A-Za-z0-9_]+$ && "$run" =~ ^[A-Za-z0-9_]+$ && "$smoke" =~ ^[0-9]+$ ]]
frozen="$base/frozen/$frozen_name"
export TRAINER="$R1_TRAINER" PILOT_VENV="$R1_MOUNT/venvs/rwtrain_torch211_cu129"
export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/cm/shared/apps/slurm/current/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
export ANYHOST_NEUTRAL_RUNTIME="${R1_RUNTIME_RECORD:-$R1_MOUNT/anyhost/NEUTRAL_RUNTIME.json}"  # spec may name its tree's record
export STUDENT_ORCHARD=1 STUDENT_SLURM_SITE=code-aws
export SLURM_CONF=/cm/shared/apps/slurm/var/etc/aws-iad-cs-002/slurm.conf
export STUDENT_MODEL_ROOT="$base/models"
export STUDENT_FRAME_ROOT_MAP="{\"/data2\": \"$R1_MOUNT/data2root\"}"
export HF_HOME="$base/cache/huggingface" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false WANDB_DISABLED=true STUDENT_IO_THREADS=4
export STUDENT=$(python -c 'print(bytes.fromhex("7177656e3335").decode())') PARALLEL=fsdp
export PROVISIONAL_DIAGNOSTIC=ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW
export TRAINING_MANIFEST="$frozen/training.json" PROTOCOL="$frozen/protocol.json" TRAINING_CONFIG="$frozen/config.json"
export NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,NET
if [[ "${R1_EFA:-0}" == 1 ]]; then
    # libfabric's CUDA memory support (FI_HMEM, which the plugin's RDMA protocol requires) dlopens the unversioned CUDA
    # runtime and driver libraries; the image has them only inside the venv's wheels and as libcuda.so.1.
    cudalib="$TMPDIR/r1_cudalib"
    mkdir -p "$cudalib"
    ln -sfn "$(ls "$PILOT_VENV"/lib/python3.12/site-packages/nvidia/cuda_runtime/lib/libcudart.so.1* | head -1)" "$cudalib/libcudart.so"
    for candidate in /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/lib64/libcuda.so.1; do
        if [[ -e "$candidate" ]]; then ln -sfn "$candidate" "$cudalib/libcuda.so"; break; fi
    done
    export LD_LIBRARY_PATH="/opt/aws-ofi-nccl/lib:/opt/amazon/efa/lib:/opt/efa_hostlib:$cudalib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export FI_PROVIDER=efa FI_EFA_USE_DEVICE_RDMA=1 FI_EFA_FORK_SAFE=1 FI_LOG_LEVEL=warn
    export NCCL_IB_DISABLE=1  # never fall back to NCCL's own verbs transport on EFA devices (it crashed with SIGSEGV)
    ls -la "$cudalib"
    timeout 60 /opt/amazon/efa/bin/fi_info -p efa -t FI_EP_RDM -c FI_HMEM 2>&1 | head -8 || true
fi
world=$(python -c 'import json, sys; print(json.load(open(sys.argv[1]))["world_size"])' "$TRAINING_CONFIG")
mapfile -t nodes < <(scontrol show hostnames "$SLURM_JOB_NODELIST")
export NNODES="${#nodes[@]}" NODE_RANK="${SLURM_NODEID:-0}" MASTER_ADDR="${nodes[0]}" MASTER_PORT=$(( 29000 + SLURM_JOB_ID % 900 ))
export NPROC_PER_NODE=$(( world / NNODES ))
(( NPROC_PER_NODE * NNODES == world ))
root="$base/$run"
attempt="$root/attempt-$SLURM_JOB_ID-${SLURM_RESTART_COUNT:-0}"
export SCRATCH_ROOT="/tmp/jjyeung/$run" RUN_OUTPUT="/tmp/jjyeung/$run/attempt-$SLURM_JOB_ID/train"
export ORCHARD_CHECKPOINT_ROOT="$root/checkpoints"
export AGENT_COORD_DIR="$R1_MOUNT/coord/r1mn_${SLURM_JOB_ID}.$run"
mkdir -p "$attempt" "$SCRATCH_ROOT" "$AGENT_COORD_DIR"
step() { printf '%s | node %s/%s %s\n' "$(date -u +%FT%TZ)" "$NODE_RANK" "$NNODES" "$*"; }
step "world $world: $NNODES nodes x $NPROC_PER_NODE ranks, master $MASTER_ADDR:$MASTER_PORT"
cd "$TRAINER"
# Rank admission requires lease evidence younger than 300 s. Containers start minutes apart across 4 nodes and cold
# imports from the shared venv are slow, so warm the imports first, then create the leases only once every node is
# ready (a barrier on the shared attempt directory), keeping lease creation close to rank admission.
python -B -c "import torch, transformers, peft, student_pilot.ddp_training" > /dev/null 2>&1 || true
# One controller reply per node for the job's read-only allocation queries (see site_alias/sitecustomize.py), fetched
# now so lease binding and rank admission read it locally.
export AWS_SCONTROL_CACHE_DIR="$TMPDIR/scontrol_cache_$SLURM_JOB_ID"
python -B -c "import student_pilot.orchard_admission as o; o.allocation()" > /dev/null
step "allocation reply cached in $AWS_SCONTROL_CACHE_DIR ($(ls "$AWS_SCONTROL_CACHE_DIR" | wc -l) files)"
touch "$attempt/ready_$NODE_RANK"
for i in $(seq 1 900); do
    (( $(ls "$attempt" | grep -c '^ready_') >= NNODES )) && break
    sleep 1
done
step "all $NNODES nodes ready; creating leases"
python -B -m student_pilot.orchard_admission "$frozen/request.json" "$attempt/supervisor_$NODE_RANK" \
    "$PROVISIONAL_DIAGNOSTIC" > "$attempt/supervisor_paths_$NODE_RANK.txt"
mapfile -t leases < "$attempt/supervisor_paths_$NODE_RANK.txt"
(( ${#leases[@]} == NPROC_PER_NODE ))
export LEASE_BUNDLE="$attempt/leases.json"
if (( NNODES == 1 )); then
    python -B -m student_pilot.cli diagnostic bind-lease-ddp --leases "${leases[@]}" --request "$frozen/request.json" \
        --output "$LEASE_BUNDLE" --provisional-diagnostic "$PROVISIONAL_DIAGNOSTIC" > /dev/null
else
    python -B -m student_pilot.cli diagnostic bind-lease-ddp --leases "${leases[@]}" --request "$frozen/request.json" \
        --node-rank "$NODE_RANK" --nnodes "$NNODES" --output "$attempt/partial_$NODE_RANK.json" \
        --provisional-diagnostic "$PROVISIONAL_DIAGNOSTIC" > /dev/null
fi
if (( NNODES == 1 )); then
    :
elif (( NODE_RANK == 0 )); then
    partials=()
    for ((r = 0; r < NNODES; r++)); do
        for i in $(seq 1 300); do [[ -s "$attempt/partial_$r.json" ]] && break; sleep 2; done
        partials+=("$attempt/partial_$r.json")
    done
    python -B -m student_pilot.cli diagnostic merge-lease-ddp --partials "${partials[@]}" --request "$frozen/request.json" \
        --output "$LEASE_BUNDLE" --provisional-diagnostic "$PROVISIONAL_DIAGNOSTIC" > /dev/null
else
    for i in $(seq 1 300); do [[ -s "$LEASE_BUNDLE" ]] && break; sleep 2; done
fi
[[ -s "$LEASE_BUNDLE" ]]
host=$(hostname -s)
CUDA_VISIBLE_DEVICES="$(python -B -c '
import json, os, sys
ranks = json.load(open(os.environ["LEASE_BUNDLE"]))["ranks"]
mine = sorted((r for r in ranks if r["host"] == sys.argv[1]), key=lambda r: r["rank"])
print(",".join(r["gpu_uuid"] for r in mine))' "$host")"
export CUDA_VISIBLE_DEVICES
step "leases bound; local GPUs $CUDA_VISIBLE_DEVICES"
if (( smoke == 0 )); then
    # Full run: every node runs the trainer's launcher to the end; node 0 holds rank 0's output and publishes it.
    rc=0
    bash "$TRAINER/scripts/diagnostic_ddp_gpu_batch.sh" || rc=$?
    step "trainer exit $rc"
    if (( NODE_RANK == 0 && rc == 0 )); then
        test -f "$RUN_OUTPUT/training_result.json"
        python -B -m student_pilot.cli diagnostic finalize \
            --training-run "$RUN_OUTPUT" --scratch-root "$SCRATCH_ROOT" \
            --publish-root "$attempt/publication" \
            --provisional-diagnostic "$PROVISIONAL_DIAGNOSTIC"
        test -f "$RUN_OUTPUT/PUBLISHED.json"
        cp -a "$RUN_OUTPUT" "$attempt/train"
        ln -sfn "$attempt/train" "$root/train"
        step "published $attempt/publication"
    fi
    step "done"
    exit "$rc"
fi
started=$(date +%s)
setsid bash "$TRAINER/scripts/diagnostic_ddp_gpu_batch.sh" &
pid=$!
deadline=$(( started + 3000 ))
while kill -0 "$pid" 2>/dev/null; do
    if (( smoke > 0 && NODE_RANK == 0 )) && [[ -f "$RUN_OUTPUT/metrics.jsonl" ]] && (( $(wc -l < "$RUN_OUTPUT/metrics.jsonl") >= smoke )); then break; fi
    if (( smoke > 0 && NODE_RANK != 0 )) && [[ -f "$attempt/SMOKE_DONE" ]]; then break; fi
    (( $(date +%s) < deadline )) || { step "SMOKE_TIMEOUT"; break; }
    sleep 10
done
if (( NODE_RANK == 0 && smoke > 0 )) && [[ -f "$RUN_OUTPUT/metrics.jsonl" ]]; then
    cp "$RUN_OUTPUT/metrics.jsonl" "$attempt/smoke_metrics.jsonl"
    for f in memory_probe.json batch_plan.json run.json; do [[ -f "$RUN_OUTPUT/$f" ]] && cp "$RUN_OUTPUT/$f" "$attempt/smoke_$f"; done
    python -B - "$attempt/smoke_metrics.jsonl" "$started" > "$attempt/SMOKE_RESULT.json" <<'PY'
import json, sys, time
rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
seconds = [row.get("seconds") for row in rows if isinstance(row.get("seconds"), (int, float))]
print(json.dumps({"logged_steps": len(rows), "step_seconds": seconds,
                  "mean_after_first_two": (sum(seconds[2:]) / len(seconds[2:])) if len(seconds) > 2 else None,
                  "losses": [row.get("loss") for row in rows], "startup_to_stop_seconds": time.time() - float(sys.argv[2])},
                 indent=1))
PY
    cat "$attempt/SMOKE_RESULT.json"
    touch "$attempt/SMOKE_DONE"
fi
if kill -0 "$pid" 2>/dev/null; then
    kill -TERM -- "-$pid" 2>/dev/null || true
    sleep 30
    kill -KILL -- "-$pid" 2>/dev/null || true
fi
wait "$pid" || true
step "done"
