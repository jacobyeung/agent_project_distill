#!/usr/bin/env bash
# Opaque code-aws job entry (lane rung1_build; adapted from the awstrain lane entry). Verifies the pinned job closure
# and job spec, then runs the spec's phase: prep (frame plans on the host, then prep_inner.sh in the trainer image),
# prestage (prestage_inner.sh, CPU), mntrain (mn_train_inner.sh per node), fetch or efaprobe.
# Slurm sees only the opaque name a15_cot_ap<8 hex>, this script's opaque path and two hex arguments.
# usage: entry.sh CLOSURE_SHA256 SPEC_SHA256
set -euo pipefail
: "${SLURM_JOB_ID:?Run through the assigned Slurm allocation}"
[[ "$SLURM_JOB_ID" =~ ^[0-9]+$ && "${SLURM_JOB_NAME:-}" =~ ^a15_cot_ap[0-9a-f]{8}$ ]]
closure_sha="${1:?closure manifest sha256}"
spec_sha="${2:?spec sha256}"
[[ "$closure_sha" =~ ^[0-9a-f]{64}$ && "$spec_sha" =~ ^[0-9a-f]{64}$ ]]
base=/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9
wheels=/lustre/fsw/portfolios/av/users/jyeung/ap/5f67d1f3/w
jobs="$base/j/${closure_sha:0:12}"
spec="$base/s/$spec_sha.json"
data="$base/d"
commit=b4b2979d59b19bfc613fdf38b4fa1c6949b69ae3  # default trainer tree; a spec may name another installed neutral tree
host_python=/cm/local/apps/python3/bin/python3
$host_python -I -B - "$jobs" "$closure_sha" "$spec" "$spec_sha" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
raw = (root / "JOBS.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == sys.argv[2], "The job manifest differs from its pinned hash"
expected = json.loads(raw)["files"]
actual = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in expected}
assert actual == expected, "The code-aws job closure changed"
assert hashlib.sha256(Path(sys.argv[3]).read_bytes()).hexdigest() == sys.argv[4], "The job spec differs from its pinned hash"
PY
phase=$($host_python -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["phase"])' "$spec")
R1_EFA=$($host_python -I -c 'import json, sys; print(1 if json.load(open(sys.argv[1])).get("efa") else 0)' "$spec")
spec_commit=$($host_python -I -c 'import json, sys; print(json.load(open(sys.argv[1])).get("trainer_commit", ""))' "$spec")
R1_RUNTIME_RECORD=$($host_python -I -c 'import json, sys; print(json.load(open(sys.argv[1])).get("runtime_record", ""))' "$spec")
if [[ -n "$spec_commit" ]]; then
    [[ "$spec_commit" =~ ^[0-9a-f]{40}$ && -d "$data/trainer/$spec_commit" && -n "$R1_RUNTIME_RECORD" ]]
    commit="$spec_commit"
fi
R1_STUDENT_HEX=$($host_python -I -c 'import json, re, sys; v = json.load(open(sys.argv[1])).get("student_hex", ""); assert re.fullmatch(r"[0-9a-f]*", v); print(v)' "$spec")
export R1_EFA R1_RUNTIME_RECORD R1_STUDENT_HEX
mapfile -d '' argv < <($host_python -I -c '
import json, sys
for item in json.load(open(sys.argv[1])).get("argv", []):
    sys.stdout.write(str(item) + "\0")' "$spec")
export ANYHOST_JOBS=/opt/anyhost_jobs ANYHOST_SPEC="/opt/anyhost_specs/$spec_sha.json"
printf '%s | phase %s on %s job=%s cpus=%s\n' "$(date -u +%FT%TZ)" "$phase" "$(hostname)" "$SLURM_JOB_ID" \
    "${SLURM_CPUS_ON_NODE:-}"

container() {
    local inner="$1"
    shift
    local step="${SLURM_STEP_ID:-batch}"
    # CPU nodes can have a nearly full /tmp; the container root then goes to the node's memory-backed /dev/shm.
    local scratch=/tmp
    if (( $(df -Pk /tmp | awk 'NR==2 {print $4}') < 12000000 )); then scratch=/dev/shm; fi
    printf '%s | container scratch %s (/tmp free %s kB)\n' "$(date -u +%FT%TZ)" "$scratch" "$(df -Pk /tmp | awk 'NR==2 {print $4}')"
    export TMPDIR="$scratch/jjyeung_tmp/$SLURM_JOB_ID.$step" HOME="$scratch/jjyeung/home-$SLURM_JOB_ID"
    export ENROOT_CACHE_PATH="$data/cache/enroot" ENROOT_DATA_PATH="$scratch/jjyeung_enroot_data_$SLURM_JOB_ID.$step"
    export ENROOT_RUNTIME_PATH="$scratch/enroot-jyeung-$SLURM_JOB_ID.$step" ENROOT_MOUNT_HOME=no ENROOT_REMAP_ROOT=no
    NVIDIA_VISIBLE_DEVICES=void
    if [[ "$inner" == mn_train_inner.sh || "$inner" == efa_probe_inner.sh ]]; then
        NVIDIA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Slurm must supply driver-local CUDA device IDs}"
    fi
    export NVIDIA_VISIBLE_DEVICES NVIDIA_DRIVER_CAPABILITIES=compute,utility
    export CAWS_IN_CONTAINER=1 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 TZ=America/Los_Angeles
    printf '%s | %s on %s step %s\n' "$(date -u +%FT%TZ)" "$inner" "$(hostname)" "$step"
    mkdir -p "$TMPDIR" "$HOME" "$ENROOT_DATA_PATH" "$ENROOT_RUNTIME_PATH" "$data/cache/enroot"
    local passwd
    passwd=$($host_python -I -B "$jobs/host_identity.py" "$TMPDIR")
    local name="c_${SLURM_JOB_ID}_${step}_${inner%%.*}_$$"
    local image word
    image=$(ls "$data"/images/u2404_py312_*.sqsh)
    word=$(basename "$(readlink "$data")")  # the fixed mount names of the frozen trainer environment
    export R1_MOUNT="/project/community/jjyeung/$word" R1_TRAINER="/home/jjyeung/agent_project_${word}_epochs/$commit"
    local efa=()
    if [[ ( "$inner" == mn_train_inner.sh || "$inner" == efa_probe_inner.sh ) && "$R1_EFA" == 1 ]]; then
        # EFA for NCCL: the host's aws-ofi-nccl plugin and EFA libfabric, the verbs devices and provider, and the
        # handful of host libraries they link against, copied per node (never the whole host library directory).
        mkdir -p "$TMPDIR/efa_hostlib"
        for lib in libibverbs.so.1 libefa.so.1 librdmacm.so.1 libnl-3.so.200 libnl-route-3.so.200 libhwloc.so.15 \
                   libltdl.so.7 libnuma.so.1; do
            cp -L "/usr/lib/x86_64-linux-gnu/$lib" "$TMPDIR/efa_hostlib/" 2>/dev/null || cp -L "/lib/x86_64-linux-gnu/$lib" "$TMPDIR/efa_hostlib/"
        done
        efa=(--mount /dev/infiniband:/dev/infiniband:none:rbind,rw,x-create=dir
             --mount /opt/amazon/efa:/opt/amazon/efa:none:rbind,ro,x-create=dir
             --mount /opt/aws-ofi-nccl:/opt/aws-ofi-nccl:none:rbind,ro,x-create=dir
             --mount "$TMPDIR/efa_hostlib:/opt/efa_hostlib:none:rbind,ro,x-create=dir"
             --mount /usr/lib/x86_64-linux-gnu/libibverbs:/usr/lib/x86_64-linux-gnu/libibverbs:none:rbind,ro,x-create=dir
             --mount /etc/libibverbs.d:/etc/libibverbs.d:none:rbind,ro,x-create=dir)
    fi
    local selfsrc=()
    local source_dir
    source_dir=$($host_python -I -c 'import json, sys; print(json.load(open(sys.argv[1])).get("self_source", ""))' "$spec")
    if [[ -n "$source_dir" ]]; then
        [[ -f "$source_dir/MANIFEST.json" ]]
        selfsrc=(--mount "$source_dir:/opt/r1_selfsrc:none:rbind,ro,x-create=dir")
    fi
    local args=(--rw "${efa[@]}" "${selfsrc[@]}"
        --mount "$HOME:$HOME:none:rbind,rw,x-create=dir"
        --mount "$TMPDIR:$TMPDIR:none:rbind,rw,x-create=dir"
        --mount "$data/orch:$R1_MOUNT:none:rbind,rw,x-create=dir"
        --mount "$data/trainer/$commit:$R1_TRAINER:none:rbind,ro,x-create=dir"
        --mount "$wheels:/opt/aws_wheels:none:rbind,ro,x-create=dir"
        --mount "$base/x:/opt/aws_incoming:none:rbind,ro,x-create=dir"
        --mount "$jobs:/opt/anyhost_jobs:none:rbind,ro,x-create=dir"
        --mount "$base/s:/opt/anyhost_specs:none:rbind,ro,x-create=dir"
        --mount /cm/shared/apps/slurm:/cm/shared/apps/slurm:none:rbind,ro,x-create=dir
        --mount /cm/local/apps/slurm/var/spool:/cm/local/apps/slurm/var/spool:none:rbind,ro,x-create=dir
        --mount /etc/slurm:/etc/slurm:none:rbind,ro,x-create=dir
        --mount /run/munge:/run/munge:none:rbind,ro,x-create=dir
        --mount "$passwd:/etc/passwd:none:bind,ro"
        --mount /etc/group:/etc/group:none:bind,ro)
    local variable
    for variable in R1_EFA R1_RUNTIME_RECORD R1_STUDENT_HEX R1_MOUNT R1_TRAINER ANYHOST_JOBS ANYHOST_SPEC CAWS_IN_CONTAINER HOME TMPDIR TZ PYTHONDONTWRITEBYTECODE PYTHONNOUSERSITE \
        NVIDIA_VISIBLE_DEVICES NVIDIA_DRIVER_CAPABILITIES SLURM_JOB_ID SLURM_JOB_NAME SLURM_CPUS_ON_NODE \
        SLURM_STEP_ID SLURM_JOB_NODELIST SLURM_NODELIST SLURM_RESTART_COUNT SLURM_CPUS_PER_TASK SLURM_MEM_PER_NODE \
        SLURM_NODEID SLURM_NNODES SLURM_JOB_NUM_NODES SLURM_PROCID SLURM_LOCALID SLURM_JOB_GPUS SLURM_STEP_GPUS \
        SLURM_GPUS_ON_NODE CUDA_VISIBLE_DEVICES; do
        if [[ -v "$variable" ]]; then args+=(--env "$variable=${!variable}"); fi
    done
    enroot create --name "$name" "$image"
    enroot start "${args[@]}" "$name" bash "$ANYHOST_JOBS/$inner" "$@"
}

case "$phase" in
    mntrain)
        if [[ -z "${R1_NODE_STEP:-}" && "${SLURM_NNODES:-1}" != 1 ]]; then
            # Batch step: one task per node, each with all of its node's GPUs; every task re-verifies the closure.
            R1_NODE_STEP=1 srun --nodes="$SLURM_NNODES" --ntasks="$SLURM_NNODES" --ntasks-per-node=1 --gres=gpu:8 \
                --cpus-per-task="$SLURM_CPUS_PER_TASK" --mem=0 --kill-on-bad-exit=1 \
                bash "$jobs/entry.sh" "$closure_sha" "$spec_sha"
        else
            # A one-node job runs in its batch step, as the single-node trainer path expects (no srun GPU step).
            nvidia-smi --query-gpu=index,name,driver_version --format=csv,noheader | head -2 || true
            container mn_train_inner.sh "${argv[@]}"
        fi
        ;;
    fetch)
        # One pinned model snapshot from the public hub into the model root (CPU job; nothing passes through Trinity).
        $host_python -I -B "$jobs/fetch_model.py" "$spec"
        ;;
    efaprobe)
        # Host-side and in-container libfabric checks for EFA (one node, any GPU count).
        set +e
        echo "== host: $(. /etc/os-release; echo "$PRETTY_NAME") memlock $(ulimit -l)"
        ls /opt/aws-ofi-nccl/lib /etc/libibverbs.d; ls /dev/infiniband | head -4; ls /sys/class/infiniband | head -4
        FI_LOG_LEVEL=warn timeout 60 /opt/amazon/efa/bin/fi_info -p efa -t FI_EP_RDM 2>&1 | head -12
        set -e
        container efa_probe_inner.sh
        ;;
    prep)
        $host_python -I -B "$jobs/frames_install.py" "$spec"
        container prep_inner.sh  # one container: prep_inner.sh runs venv_build.sh first
        ;;
    prestage)
        # CPU startup pre-stage of the frozen preparations a chained GPU job will train (prestage.py build).
        container prestage_inner.sh
        ;;
    *)
        exit 2
        ;;
esac
printf '%s | phase finished\n' "$(date -u +%FT%TZ)"
