#!/usr/bin/env bash
# Opaque code-aws CPU job entry (lane rung1_build; adapted from the awstrain lane entry). Verifies the pinned job closure
# and job spec, installs the spec's frame plans on the host, then runs prep_inner.sh inside the trainer image.
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
commit=b4b2979d59b19bfc613fdf38b4fa1c6949b69ae3
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
    export NVIDIA_VISIBLE_DEVICES=void NVIDIA_DRIVER_CAPABILITIES=compute,utility
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
    local args=(--rw
        --mount "$HOME:$HOME:none:rbind,rw,x-create=dir"
        --mount "$TMPDIR:$TMPDIR:none:rbind,rw,x-create=dir"
        --mount "$data/orch:$R1_MOUNT:none:rbind,rw,x-create=dir"
        --mount "$data/trainer/$commit:$R1_TRAINER:none:rbind,ro,x-create=dir"
        --mount "$wheels:/opt/aws_wheels:none:rbind,ro,x-create=dir"
        --mount "$base/x:/opt/aws_incoming:none:rbind,ro,x-create=dir"
        --mount "$jobs:/opt/anyhost_jobs:none:rbind,ro,x-create=dir"
        --mount "$base/s:/opt/anyhost_specs:none:rbind,ro,x-create=dir"
        --mount "$passwd:/etc/passwd:none:bind,ro"
        --mount /etc/group:/etc/group:none:bind,ro)
    local variable
    for variable in R1_MOUNT R1_TRAINER ANYHOST_JOBS ANYHOST_SPEC CAWS_IN_CONTAINER HOME TMPDIR TZ PYTHONDONTWRITEBYTECODE PYTHONNOUSERSITE \
        NVIDIA_VISIBLE_DEVICES NVIDIA_DRIVER_CAPABILITIES SLURM_JOB_ID SLURM_JOB_NAME SLURM_CPUS_ON_NODE \
        SLURM_STEP_ID SLURM_JOB_NODELIST SLURM_NODELIST SLURM_RESTART_COUNT SLURM_CPUS_PER_TASK SLURM_MEM_PER_NODE; do
        if [[ -v "$variable" ]]; then args+=(--env "$variable=${!variable}"); fi
    done
    enroot create --name "$name" "$image"
    enroot start "${args[@]}" "$name" bash "$ANYHOST_JOBS/$inner" "$@"
}

case "$phase" in
    prep)
        $host_python -I -B "$jobs/frames_install.py" "$spec"
        container prep_inner.sh  # one container: prep_inner.sh runs venv_build.sh first
        ;;
    *)
        exit 2
        ;;
esac
printf '%s | phase finished\n' "$(date -u +%FT%TZ)"
