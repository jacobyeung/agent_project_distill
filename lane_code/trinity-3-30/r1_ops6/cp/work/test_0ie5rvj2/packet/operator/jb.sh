#!/bin/bash
# Conditional four-rank entry; a separate submission approval is required.
#SBATCH -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00
#SBATCH --no-requeue --signal=B:USR1@3600
set -uo pipefail
umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"

export PATH=/usr/local/bin:/usr/bin:/bin
export TK_JOB_START="$(date +%s)"   # one wall clock for restore, staging, admission and training (job.sh must keep it)
KH=/project/community/jjyeung/okh7/x_fa541ab9 RUN=/tmp/jjyeung/a_d478a970/runs/d478a970
RS=/project/community/jjyeung/okh7/r/d478a970 LOG=$KH/o/${SLURM_JOB_ID}.w.steps
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
newest() {  # newest verified slot: prints "slot step" (empty if none)
    for s in A B; do [[ -f $RS/$s.json ]] && /usr/bin/python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["slot"], d["step"]) if d.get("verified") is True else None' "$RS/$s.json"; done | sort -k2,2n | tail -1
}
# BEGIN directory preflight
NL=/tmp/jjyeung/a_d478a970
private_dir "$KH"
for p in /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS"; do
    [[ ! -e "$p" && ! -L "$p" ]] || private_dir "$p"
done
for p in "$NL/runs"/* "$NL/runs"/.[!.]* "$NL/runs"/..?*; do
    [[ ! -e "$p" && ! -L "$p" ]] && continue
    [[ "${p##*/}" == d478a970 && -d "$p" && ! -L "$p" ]] || { echo 'foreign run directory; refusing' >&2; exit 3; }
done
mkdir -p -m 700 /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS" "$KH/o" || exit 3
for p in "$NL" "$NL/runs" "$RUN" "$RS"; do private_dir "$p"; done
# END directory preflight
free_kib=$(df -Pk /tmp | awk 'NR==2 {print $4}')
step "wrapper start on $(hostname -s); /tmp free $(( free_kib / 1048576 )) GiB; TK_JOB_START=$TK_JOB_START ($(date -u -d @"$TK_JOB_START" +%FT%TZ))"
# Final review F4: a leg needs about 3.6 TB free at its first save; refuse below 3.8 TB (decimal) in the first minute.
(( free_kib * 1024 >= 3800000000000 )) || { step "refused: /tmp free $(( free_kib * 1024 )) B is below 3.8 TB"; exit 5; }
# Export sessions: every milestone of the plan has its four part sessions for this run, in a file only the account reads.
/usr/bin/python3 -I -c '
import json, os, stat, sys
p, run = sys.argv[1], sys.argv[2]
if stat.S_IMODE(os.stat(p).st_mode) != 0o600: sys.exit("sess.json mode is not 600")
d = json.load(open(p)); ms = ["m100", "m200", "mstop", "mstopB", "mstopC"]
want = {"q8/8865619b/%s_%s.tar.part%02d-of-04" % (run, m, i) for m in ms for i in range(4)}
miss = sorted(want - set(d))
sys.exit("sess.json lacks %d sessions, first %s" % (len(miss), miss[:1]) if miss else 0)' "$KH/sess.json" "${RUN##*/}" 2>> "$LOG" \
    || { step "refused: export sessions incomplete for run ${RUN##*/}"; exit 5; }
step "export sessions present for run ${RUN##*/}"
# Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
/usr/bin/python3 -I /project/community/jjyeung/okh7/i_fa541ab9/v.py "$KH" /project/community/jjyeung/okh7/i_fa541ab9/b0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
    || { step "refused: staging entry check: $(tail -c 300 "$KH/o/${SLURM_JOB_ID}.vt.json")"; exit 5; }
step "staging entries verified"
read -r slot sstep < <(newest || true)
if [[ -n "${slot:-}" ]] && ! ls "$RUN"/checkpoint_*/complete.json > /dev/null 2>&1; then   # restores checkpoint, inputs/, binding.json
    t0=$(date +%s)
    # The slot record must carry the content check written by the copy below; nothing is extracted without it.
    rec=$(/usr/bin/python3 -I -c '
import json, re, sys
d = json.load(open(sys.argv[1])); h = re.compile("[0-9a-f]{64}")
ok = (d.get("verified") is True and d.get("content_check") == "c1-slot-check-v1" and type(d.get("step")) is int and d["step"] > 0
      and h.fullmatch(str(d.get("archive_sha256"))) and h.fullmatch(str(d.get("manifest_sha256")))
      and re.fullmatch(r"checkpoint_\d{6}(?:_[0-9a-f]{32})?", str(d.get("checkpoint"))))
print(d["archive_sha256"], d["manifest_sha256"], d["checkpoint"], d["step"]) if ok else sys.exit(1)' "$RS/$slot.json") \
        || { step "restore: slot $slot record has no valid content check; stop before extracting (no retry)"; exit 3; }
    read -r rarch rman rck rstep <<< "$rec"
    want=$(cut -c1-64 "$RS/$slot.sha256") || { step "restore: slot $slot sha file unreadable; stop (no retry)"; exit 3; }
    [[ "$want" == "$rarch" && "$rstep" == "$sstep" ]] || { step "restore: slot $slot sha file or step disagrees with its record; stop (no retry)"; exit 3; }
    : > "$RUN/.restore.sha"
    tee >(sha256sum | cut -d' ' -f1 > "$RUN/.restore.sha.part" && mv "$RUN/.restore.sha.part" "$RUN/.restore.sha") < "$RS/$slot.tar" \
        | tar -x -C "$RUN" --no-same-owner
    ps=("${PIPESTATUS[@]}")
    [[ "${ps[*]}" == "0 0" ]] || { step "restore: slot $slot read/extract failed (tee tar = ${ps[*]}); stop (no retry)"; exit 3; }
    for _ in $(seq 300); do [[ -s "$RUN/.restore.sha" ]] && break; sleep 1; done
    [[ "$(cat "$RUN/.restore.sha")" == "$want" ]] || { step "restore: slot $slot sha differs or its hash failed; stop (no retry)"; exit 3; }
    mh=$(sha256sum < "$RUN/$rck/complete.json" | cut -d' ' -f1) || { step "restore: hashing the restored manifest failed; stop (no retry)"; exit 3; }
    [[ "$mh" == "$rman" ]] || { step "restore: restored manifest digest differs from slot $slot record; stop (no retry)"; exit 3; }
    /usr/bin/python3 -I -c '
import json, sys
m = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
sys.exit(0 if m.get("schema") == "c1-checkpoint-v1" and m.get("step") == int(sys.argv[3]) and m.get("binding") == b else 1)' \
        "$RUN/$rck/complete.json" "$RUN/binding.json" "$sstep" && [[ -d "$RUN/inputs" ]] \
        || { step "restore: slot $slot manifest step, schema or binding disagrees with the record, or inputs are absent; stop (no retry)"; exit 3; }
    step "restore: slot $slot step $sstep into $RUN in $(( $(date +%s) - t0 )) s"
fi
( [[ -f $RS/binding.json ]] && exit 0
  for _ in $(seq 2880); do [[ -s $RUN/binding.json ]] && break; sleep 30; done
  [[ -s $RUN/binding.json ]] || exit 0
  cp "$RUN/binding.json" "$RS/binding.json.part" && sha256sum < "$RS/binding.json.part" | cut -d' ' -f1 > "$RS/binding.json.sha256" \
      && mv "$RS/binding.json.part" "$RS/binding.json" && step "binding mirror written: $(cut -c1-12 "$RS/binding.json.sha256")" ) &
/bin/bash "$KH/job.sh" &
child=$!
trap 'step "USR1: relayed to job.sh"; kill -USR1 $child 2>/dev/null' USR1
while true; do wait "$child"; rc=$?; kill -0 "$child" 2>/dev/null || break; done
step "job.sh exit rc=$rc"
ck=$(ls -d "$RUN"/checkpoint_* 2>/dev/null | while read -r d; do [[ -f $d/complete.json ]] && echo "$d"; done | sort -V | tail -1)
if [[ -z "$ck" ]]; then
    step "copy: no complete checkpoint to copy; slot not written, previous slots untouched"
    printf '{"job": "%s", "reason": "no complete checkpoint", "trainer_rc": %s}\n' "$SLURM_JOB_ID" "$rc" > "$KH/o/${SLURM_JOB_ID}.SLOT_MISSING"
    (( rc != 0 )) && exit "$rc"; exit 4
fi
cstep=$(/usr/bin/python3 -I -c 'import json,sys; print(int(json.load(open(sys.argv[1]))["step"]))' "$ck/complete.json") && [[ "$cstep" =~ ^[1-9][0-9]*$ ]] \
    || { step "copy: unreadable or non-positive step in $ck/complete.json; slot not written"; exit 4; }
read -r slot sstep < <(newest || true)
[[ "${sstep:-}" == "$cstep" ]] && { step "checkpoint $cstep already in slot $slot"; exit "$rc"; }
[[ -d "$RUN/inputs" && -f "$RUN/binding.json" ]] || { step "copy: $RUN/inputs or binding.json absent; slot not written"; exit 4; }
dst=A; [[ "${slot:-}" == A ]] && dst=B
# The persistent root lives on the shared project filesystem: copy only with the whole slot plus 20 GB to spare.
need=$(du -sb --count-links "$ck" "$RUN/inputs" "$RUN/binding.json" | awk '{s += $1} END {print s}') && [[ "$need" =~ ^[0-9]+$ ]] \
    || { step "copy: measuring the slot size failed; slot $dst not written"; exit 4; }
avail=$(df -PB1 "$RS" | awk 'NR==2 {print $4}') && [[ "$avail" =~ ^[0-9]+$ ]] \
    || { step "copy: measuring free space on $RS failed; slot $dst not written"; exit 4; }
if (( avail < need + 20000000000 )); then
    # Fallback when project lacks room: stream the slot from node /tmp to one GCS object (the Orchard gcloud configuration,
    # as the step-544 repack used it), check size and md5 against the stream, record it, exit 6. SLOT_SKIPPED otherwise.
    step "slot copy to project impossible: checkpoint $cstep needs $need B, $RS has $avail B free; streaming the slot to GCS"
    ckn=$(basename "$ck"); obj="q8/d2d30e36/${RUN##*/}_s${cstep}.tar"; gs="gs://cmu-gpucloud-jjyeung/$obj"; sum="$RUN/.gslot.$SLURM_JOB_ID.json"
    left=$(( TK_JOB_START + 46800 - $(date +%s) - 300 )); t0=$(date +%s); gok=0
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
t0=$(date +%s); ckn=$(basename "$ck")
cj0=$(sha256sum < "$ck/complete.json" | cut -d' ' -f1) && [[ "$cj0" =~ ^[0-9a-f]{64}$ ]] \
    || { step "copy: slot $dst write failed before archiving (complete.json hash failed); slot $dst unchanged"; exit 4; }
# The new slot is written to .part files; the previous contents of slot $dst stay in place until the archive verifies,
# and the other (newest verified) slot is never touched.
tar --hard-dereference -cf - -C "$RUN" "$ckn" inputs binding.json | tee "$RS/$dst.tar.part" | sha256sum | cut -d' ' -f1 > "$RS/$dst.sha256.part"
ps=("${PIPESTATUS[@]}")
t1=$(date +%s)
[[ "${ps[*]}" == "0 0 0 0" ]] || { step "copy: slot $dst write failed (tar tee sha256sum cut = ${ps[*]}); slot $dst unchanged, nothing marked verified"; exit 4; }
cj1=$(sha256sum < "$ck/complete.json" | cut -d' ' -f1) && [[ "$cj1" == "$cj0" ]] \
    || { step "copy: checkpoint $ckn moved, changed or unhashable after the copy; slot $dst unchanged"; exit 4; }
# One re-read of the written archive checks its sha against the write-time sha and its contents against the
# checkpoint's own complete.json and binding.json: schema, step, binding, world, every rank's shard and RNG, the
# replicated file, and every listed payload at its declared size and sha256.
/usr/bin/python3 -I -c '
import hashlib, sys, tarfile
import json, re
path, want, ckn, cstep, cj0 = sys.argv[1:6]
class R:
    def __init__(s, f): s.f, s.h = f, hashlib.sha256()
    def read(s, n=-1):
        b = s.f.read(n); s.h.update(b); return b
def fail(why): print("BAD " + why); sys.exit(1)
pay, marker, bind, ninputs = {}, None, None, 0
with open(path, "rb") as f:
    r = R(f)
    with tarfile.open(fileobj=r, mode="r|") as t:
        for m in t:
            top = m.name.split("/")[0]
            if top not in (ckn, "inputs", "binding.json") or m.name.startswith("/") or ".." in m.name.split("/"):
                fail("unexpected member " + m.name)
            if m.isdir():
                if top == ckn and m.name not in (ckn, ckn + "/shards"): fail("unexpected folder " + m.name)
                continue
            if not m.isfile(): fail("non-regular member " + m.name)
            h, size, src = hashlib.sha256(), 0, t.extractfile(m)
            keep = m.name in (ckn + "/complete.json", "binding.json")
            body = bytearray()
            while True:
                b = src.read(1 << 24)
                if not b: break
                h.update(b); size += len(b)
                if keep: body += b
            if m.name == ckn + "/complete.json": marker = bytes(body)
            elif m.name == "binding.json": bind = bytes(body)
            elif top == ckn: pay[m.name[len(ckn) + 1:]] = (size, h.hexdigest())
            else: ninputs += 1
    while r.read(1 << 24): pass
if r.h.hexdigest() != want: fail("archive sha differs from the write-time sha")
if marker is None or bind is None: fail("complete.json or binding.json missing from the archive")
if hashlib.sha256(marker).hexdigest() != cj0: fail("archived complete.json differs from the source marker")
man, binding = json.loads(marker.decode()), json.loads(bind.decode())
step = int(cstep)
if (man.get("schema") != "c1-checkpoint-v1" or type(man.get("step")) is not int or man["step"] != step
        or step < 1 or int(ckn.split("_")[1]) != step):
    fail("schema or step")
if man.get("binding") != binding: fail("manifest binding differs from binding.json")
world = binding.get("world_size")
if type(world) is not int or world < 1: fail("binding world_size")
if "layouts" in man and len(man["layouts"]) != world: fail("layouts do not cover the world")
files = man.get("files")
if not isinstance(files, dict): fail("manifest files")
required = {"shards/rank%03d.pt" % k for k in range(world)} | {"rng%03d.pt" % k for k in range(world)} | {"replicated.pt"}
if set(files) != required: fail("manifest files differ from every rank shard and RNG plus replicated.pt")
if set(pay) != required: fail("archived payloads differ from the manifest")
for name, pin in files.items():
    size, digest = pay[name]
    if type(pin.get("bytes")) is not int or pin["bytes"] < 1 or size != pin["bytes"]: fail("size of " + name)
    if not re.fullmatch("[0-9a-f]{64}", str(pin.get("sha256"))) or digest != pin["sha256"]: fail("sha256 of " + name)
if ninputs < 1: fail("inputs/ is empty")
print(json.dumps({"archive_sha256": want, "manifest_sha256": cj0, "checkpoint": ckn, "world": world, "payloads": len(pay)}))
' "$RS/$dst.tar.part" "$(cat "$RS/$dst.sha256.part")" "$ckn" "$cstep" "$cj0" > "$RS/$dst.verify.part" 2>&1 \
    || { step "copy: slot $dst re-read failed: $(head -c 300 "$RS/$dst.verify.part"); slot $dst unchanged"; exit 4; }
t2=$(date +%s)
# Publication: every value is read and checked first, and each record goes to a unique temporary file that is renamed
# into place only after a successful write, so a live record is never emptied or overwritten in place.
slot_failed() {
    step "copy: slot $dst publication failed: $1; slot $dst not verified"
    builtin printf '{"job": "%s", "slot": "%s", "step": %s, "reason": "%s"}\n' "$SLURM_JOB_ID" "$dst" "$cstep" "$1" > "$KH/o/${SLURM_JOB_ID}.SLOT_FAILED"
    exit 4
}
put_record() {  # put_record VERIFIED: write $RS/$dst.json atomically
    local tmp="$RS/.$dst.json.$SLURM_JOB_ID.$$.tmp"
    if [[ "$1" == true ]]; then
        printf '{"slot": "%s", "step": %s, "verified": true, "job": "%s", "bytes": %s, "content_check": "c1-slot-check-v1", "archive_sha256": "%s", "manifest_sha256": "%s", "checkpoint": "%s"}\n' \
            "$dst" "$cstep" "$SLURM_JOB_ID" "$bytes" "$asha" "$cj0" "$ckn" > "$tmp"
    else
        printf '{"slot": "%s", "step": %s, "verified": false, "job": "%s"}\n' "$dst" "$cstep" "$SLURM_JOB_ID" > "$tmp"
    fi || return 1
    [[ -s "$tmp" ]] && mv -f "$tmp" "$RS/$dst.json"
}
bytes=$(stat -c %s "$RS/$dst.tar.part") && [[ "$bytes" =~ ^[1-9][0-9]*$ ]] || slot_failed "archive size unreadable"
asha=$(cat "$RS/$dst.sha256.part") && [[ "$asha" =~ ^[0-9a-f]{64}$ ]] || slot_failed "archive sha unreadable"
put_record false || slot_failed "unverified record write"
mv "$RS/$dst.tar.part" "$RS/$dst.tar" && mv "$RS/$dst.sha256.part" "$RS/$dst.sha256" || slot_failed "rename of the archive or its sha"
put_record true || slot_failed "verified record write"
step "copy: checkpoint $cstep to slot $dst, $bytes B, write $((t1 - t0)) s, verify $((t2 - t1)) s"
exit "$rc"
