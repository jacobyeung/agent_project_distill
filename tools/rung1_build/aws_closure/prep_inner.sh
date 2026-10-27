#!/usr/bin/env bash
# CPU preparation inside the image (lane rung1_build). Installs the rung-1 row archives and frozen inputs (write-once),
# then for each chain in the spec: prepare-protocol, sharded encode (parallel processes), merge into the native
# training.json, seal-source, DDP lease request and the CPU admission train_inner.sh applies.
# Spec fields: "row_archives": [PATH...], "frozen_archives": [{"path": PATH, "sha256": HEX}],
#              "chains": [{"frozen": NAME, "shards": N, "records_from": NAME|null}], "parallel": P
set -euo pipefail
: "${ANYHOST_JOBS:?}" "${ANYHOST_SPEC:?}" "${R1_MOUNT:?}" "${R1_TRAINER:?}"
bash "$ANYHOST_JOBS/venv_build.sh"  # prints the receipt when the environment already exists
root="$R1_MOUNT/runs/aws128p_20261025"
export TRAINER="$R1_TRAINER"
export PILOT_VENV="$R1_MOUNT/venvs/rwtrain_torch211_cu129"
export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
export STUDENT_ORCHARD=1 STUDENT_SLURM_SITE=code-aws CUDA_VISIBLE_DEVICES=
export STUDENT_MODEL_ROOT="$root/models"
export STUDENT_FRAME_ROOT_MAP="{\"/data2\": \"$R1_MOUNT/data2root\"}"
export HF_HOME="$root/cache/huggingface" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false STUDENT_IO_THREADS=8
export ANYHOST_NEUTRAL_RUNTIME="${R1_RUNTIME_RECORD:-$R1_MOUNT/anyhost/NEUTRAL_RUNTIME.json}"  # spec may name its tree's record
test "$(command -v git)" = "$ANYHOST_JOBS/provenance_bin/git"
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*"; }
spec() { python -I -c "import json, sys; v = json.load(open(sys.argv[1])); $1" "$ANYHOST_SPEC"; }
prep="python -B $ANYHOST_JOBS/prep_rung1.py"
cd "$TRAINER"

# Optional trainer unit tests (CPU) named by the spec, run in the trainer tree with the venv.
mapfile -t tests < <(spec 'print("\n".join(v.get("trainer_tests", [])))' | sed '/^$/d')
if (( ${#tests[@]} )); then
    step "trainer tests ${tests[*]}"
    mkdir -p "$TMPDIR/lane_tests"
    { LANE_TEST_OUTPUT="$TMPDIR/lane_tests" CUDA_VISIBLE_DEVICES= python -B -m unittest "${tests[@]}" 2>&1 || echo TRAINER_TESTS_FAILED; } | tail -n 25
fi

mapfile -t rows < <(spec 'print("\n".join(v.get("row_archives", [])))' | sed '/^$/d')
if (( ${#rows[@]} )); then step "install ${#rows[@]} row archives"; $prep install "${rows[@]}"; fi

mapfile -t frozen < <(spec 'print("\n".join(a["path"] + " " + a["sha256"] for a in v.get("frozen_archives", [])))')
for entry in "${frozen[@]}"; do
    [[ -n "$entry" ]] || continue
    path="${entry% *}" digest="${entry#* }"
    test "$(sha256sum < "$path" | cut -d' ' -f1)" = "$digest"
    incoming="$root/incoming_r1/${digest:0:16}"
    if [[ ! -e "$incoming/UNPACKED" ]]; then
        mkdir -p "$incoming.part.$$"
        tar -C "$incoming.part.$$" -xf "$path"
        touch "$incoming.part.$$/UNPACKED"
        mkdir -p "$root/incoming_r1"
        mv -T "$incoming.part.$$" "$incoming" 2>/dev/null || test -e "$incoming/UNPACKED"  # a concurrent job won the race
    fi
    for item in "$incoming"/frozen/*; do
        name="$(basename "$item")"
        if [[ ! -e "$root/frozen/$name" ]]; then
            cp -a "$item" "$root/frozen/$name.part.$$"
            mv -T "$root/frozen/$name.part.$$" "$root/frozen/$name" 2>/dev/null || true  # a concurrent job may have won
        fi
        for f in "$item"/*; do cmp -s "$f" "$root/frozen/$name/$(basename "$f")" || { echo "INSTALL_CONFLICT $name" >&2; exit 3; }; done
        step "frozen inputs $name"
    done
done

# Optional self-trace shard: rows built here from the student's verified samples (mounted at /opt/r1_selfsrc) and an
# installed base arm; it creates the S arm and the base+S mix arm frozen dirs that the chains below prepare.
mapfile -t self_args < <(spec 'a = v.get("selfshard"); print("\n".join(map(str, [a["manifest_sha256"], a["base_arm"], a["s_arm"], a["mix_arm"], a["per_question"], a["commit"]])) if a else "")' | sed '/^$/d')
if (( ${#self_args[@]} )); then
    if [[ ! -f "$root/frozen/${self_args[2]}/SELF_SHARD_REPORT.json" ]]; then
        step "self shard ${self_args[2]} and mix ${self_args[3]} from ${self_args[1]}"
        python -I -B "$ANYHOST_JOBS/selfshard.py" /opt/r1_selfsrc "${self_args[0]}" "$root/frozen" "${self_args[1]}" \
            "${self_args[2]}" "${self_args[3]}" "$R1_MOUNT/data2root" "${self_args[4]}" "${self_args[5]}"
    fi
    cat "$root/frozen/${self_args[2]}/SELF_SHARD_REPORT.json"
fi

parallel=$(spec 'print(v.get("parallel", 8))')
mapfile -t chains < <(spec 'print("\n".join("%s %d %s" % (c["frozen"], c["shards"], c.get("records_from") or "-") for c in v.get("chains", [])))')
for chain in "${chains[@]}"; do
    [[ -n "$chain" ]] || continue
    read -r name shards from <<< "$chain"
    dir="$root/frozen/$name"
    if [[ ! -f "$dir/protocol.json" ]]; then step "protocol $name"; $prep protocol "$dir"; fi
    if [[ "$from" == "-" ]]; then
        records="$dir/shards"
        step "encode $name in $shards shards, $parallel at a time"
        for ((k = 0; k < shards; k++)); do
            while (( $(jobs -rp | wc -l) >= parallel )); do sleep 5; done
            $prep shard "$dir" "$k" "$shards" > "$dir/shard_$k.log" 2>&1 &
        done
        wait
        for ((k = 0; k < shards; k++)); do
            test -f "$records/$(printf '%03d_of_%03d.jsonl' "$k" "$shards")" || { tail -n 20 "$dir/shard_$k.log"; exit 4; }
        done
    elif [[ "$from" == *:* ]]; then
        # Several record sets, ARM:N[,ARM:N...]: each arm's encode shards (e.g. a base export plus the self shard).
        records=""
        IFS=, read -r -a sets <<< "$from"
        for item in "${sets[@]}"; do records+="${records:+,}$root/frozen/${item%%:*}/shards:${item##*:}"; done
    else
        records="$root/frozen/$from/shards"
    fi
    if [[ ! -f "$dir/training.json" ]]; then step "merge $name"; $prep merge "$dir" "$shards" "$records"; fi
    if [[ ! -f "$dir/training.json.source_receipt.json" ]]; then step "seal $name"; $prep seal "$dir"; fi
    if [[ ! -f "$dir/request.json" ]]; then step "request $name"; $prep request "$dir"; fi
    step "admit $name"; $prep admit "$dir"
    cat "$dir/ADMISSION.json"
done
step "prep complete"
