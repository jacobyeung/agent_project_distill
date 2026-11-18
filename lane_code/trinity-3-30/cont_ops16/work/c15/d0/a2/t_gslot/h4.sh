set -uo pipefail
B=/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/t_gslot
export PATH=$B/bin:/usr/local/bin:/usr/bin:/bin
SLURM_JOB_ID=99 RUN=$B/run KH=$B/kh4 RS=$B/rs TK_JOB_START=$(date +%s) ck=$B/run/checkpoint_000010_x cstep=10 need=999 avail=1 rc=0
step() { echo "STEP $*"; }
if (( avail < need + 20000000000 )); then
    # Fallback when project lacks room: stream the slot from node /tmp to one GCS object (the Orchard gcloud configuration,
    # as the step-544 repack used it), check size and md5 against the stream, record it, exit 6. SLOT_SKIPPED otherwise.
    step "slot copy to project impossible: checkpoint $cstep needs $need B, $RS has $avail B free; streaming the slot to GCS"
    ckn=$(basename "$ck"); obj="q8/d2d30e36/${RUN##*/}_s${cstep}.tar"; gs="gs://cmu-gpucloud-jjyeung/$obj"; sum="$RUN/.gslot.$SLURM_JOB_ID.json"
    left=$(( TK_JOB_START + 86400 - $(date +%s) - 300 )); t0=$(date +%s); gok=0
    if (( left > 600 )); then
        tar --hard-dereference -cf - -C "$RUN" "$ckn" inputs binding.json \
            | /usr/bin/python3 -I -c '
import base64, hashlib, json, sys
s, m, n = hashlib.sha256(), hashlib.md5(), 0
i, o = sys.stdin.buffer, sys.stdout.buffer
while True:
    b = i.read(1 << 24)
    if not b: break
    s.update(b); m.update(b); n += len(b); o.write(b)
o.flush()
open(sys.argv[1], "w").write(json.dumps(dict(bytes=n, sha256=s.hexdigest(), md5=base64.b64encode(m.digest()).decode())))' "$sum" \
            | env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_FILE_LOGGING=1 CLOUDSDK_CORE_DISABLE_PROMPTS=1 \
                CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=1 CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=1 \
                CLOUDSDK_STORAGE_PARALLEL_COMPOSITE_UPLOAD_ENABLED=False \
                timeout -s KILL "$left" gcloud storage cp - "$gs" > "$KH/o/${SLURM_JOB_ID}.gslot.log" 2>&1
        ps=("${PIPESTATUS[@]}")
        if [[ "${ps[*]}" == "0 0 0" && -s "$sum" ]]; then
            env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_FILE_LOGGING=1 CLOUDSDK_CORE_DISABLE_PROMPTS=1 \
                timeout 300 gcloud storage objects describe "$gs" --format=json > "$RUN/.gslot.meta.json" 2>> "$KH/o/${SLURM_JOB_ID}.gslot.log" \
            && /usr/bin/python3 -I -c '
import json, sys
s, m = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
ok = int(m.get("size", -1)) == s["bytes"] and m.get("md5_hash", m.get("md5Hash")) == s["md5"]
sys.exit(0 if ok else 1)' "$sum" "$RUN/.gslot.meta.json" && gok=1
        fi
        step "slot to GCS: pipeline ${ps[*]}, verified $gok, $(( $(date +%s) - t0 )) s"
    fi
    if (( gok == 1 )); then
        mh=$(sha256sum < "$ck/complete.json" | cut -d' ' -f1) && [[ "$mh" =~ ^[0-9a-f]{64}$ ]] || gok=0
    fi
    if (( gok == 1 )) && /usr/bin/python3 -I -c '
import json, sys
s = json.load(open(sys.argv[1]))
print(json.dumps(dict(job=sys.argv[2], step=int(sys.argv[3]), checkpoint=sys.argv[4], manifest_sha256=sys.argv[5], object=sys.argv[6], **s)))' \
            "$sum" "$SLURM_JOB_ID" "$cstep" "$ckn" "$mh" "$obj" > "$KH/o/${SLURM_JOB_ID}.SLOT_TO_GCS.part" \
        && [[ -s "$KH/o/${SLURM_JOB_ID}.SLOT_TO_GCS.part" ]] && mv "$KH/o/${SLURM_JOB_ID}.SLOT_TO_GCS.part" "$KH/o/${SLURM_JOB_ID}.SLOT_TO_GCS"; then
        step "SLOT TO GCS: checkpoint $cstep as $obj (project lacked room); exports are kept"
        exit 6
    fi
    (( gok == 1 )) && step "slot to GCS: object verified but its record could not be published"
    step "SLOT COPY SKIPPED: checkpoint $cstep needs $need B, $RS has $avail B free, and the GCS fallback failed; the continuation is lost, exports are kept"
    printf '{"job": "%s", "step": %s, "need": %s, "free": %s}\n' "$SLURM_JOB_ID" "$cstep" "$need" "$avail" > "$KH/o/${SLURM_JOB_ID}.SLOT_SKIPPED"
    (( rc != 0 )) && exit "$rc"; exit 5
fi
echo "fell through"
