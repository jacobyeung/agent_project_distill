export PYTHONDONTWRITEBYTECODE=1
set -euo pipefail
tk_evidence_exit() {
    local status="$1"
    trap - EXIT TERM USR1
    /usr/bin/python3 -B -I -s "$Q_KIT/b/ep.py" "$Q_KIT" "$Q_ROOT" "${SLURM_JOB_ID:?}" "$status" || true
    exit "$status"
}
trap 'tk_evidence_exit $?' EXIT
trap 'exit 143' TERM
trap 'exit 138' USR1
export TMPDIR="$Q_ROOT/tmp" XDG_CACHE_HOME="$Q_ROOT/cache"
export HF_HOME="$Q_ROOT/cache/hf" TORCH_HOME="$Q_ROOT/cache/torch" TRITON_CACHE_DIR="$Q_ROOT/cache/triton"
export CUDA_CACHE_PATH="$Q_ROOT/cache/cu" MPLCONFIGDIR="$Q_ROOT/cache/plot"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$Q_ROOT"
export PATH=/usr/local/bin:/usr/bin:/bin
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
K=8865619b
X=$AS/ap/$K
R=/project/community/jjyeung/okh7/l_94a76bda
HX="${TK_KIT_HOME:?}"
IN=$R/in
REV=c202236235762e1c871ad0ccb60c8ee5ba337b9a
P=/project/community/jjyeung/c7d31ddd
RR=runs/aws128p_20261025
EPOCHS=/home/jjyeung/6d00e578
S="$Q_ROOT/s"
U=$S/aws/u
HM=$HX
NX="$Q_ROOT/x"
NR="$Q_ROOT/rp"
CUR=$HX/k/0.json
COMMIT=$(/usr/bin/python3 -B -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' "$CUR")
tk_step() {
    local line
    line="$(date -u +%FT%TZ) | $*"
    printf '%s\n' "$line"
    if [[ -n "${SLURM_JOB_ID:-}" ]]; then printf '%s\n' "$line" >> "$Q_ROOT/$SLURM_JOB_ID.steps"; fi
}
hp() {
    case "$1" in
        "$X"/*) printf '%s\n' "$NX/${1#"$X"/}" ;;
        "$AS"/*) printf '%s\n' "$U/${1#"$AS"/}" ;;
        "$AL"/*) printf '%s\n' "$U/${1#"$AL"/}" ;;
        *) printf '%s\n' "$1" ;;
    esac
}
tk_current() { /usr/bin/python3 -B -I -c 'import json, sys; e = json.load(open(sys.argv[1]))[sys.argv[2]]; print(e["file"], e["sha256"])' "$CUR" "$1"; }
tk_has() { /usr/bin/python3 -B -I -c 'import json,sys; sys.exit(0 if sys.argv[2] in json.load(open(sys.argv[1])) else 1)' "$CUR" "$1"; }
CLOSURE_DIR="_jobs/cp4tk_$(tk_current closure | cut -d' ' -f2 | cut -c1-12)"
tk_kitx() {
    local key="$1" dest="$2" file sha
    read -r file sha < <(tk_current "$key")
    file=$(hp "$file")
    if [[ -f "$S/.stamp/$key.$sha" && -d "$dest" ]]; then return 0; fi
    if [[ -e "$dest" ]]; then mv "$dest" "$dest.old.$(date +%s)"; fi
    mkdir -p "$(dirname "$dest")" "$S/.stamp"
    /usr/bin/python3 -B -I "$HX/b/kitx.py" "$file" "$sha" "$dest"
    touch "$S/.stamp/$key.$sha"
}
sha_is() { [[ "$(sha256sum < "$1" | cut -d' ' -f1)" == "$2" ]] || { tk_step "sha differs: $1"; return 3; }; }

tk_venv_shebangs() {
    local v="$S/c7d31ddd/venvs/rwtrain_torch211_cu129" stamp
    stamp="$S/.stamp/shebang.$(tk_current venv | cut -d' ' -f2)"
    [[ ! -f "$stamp" ]] || return 0
    /usr/bin/python3 -B -I - "$v/bin" "$P/venvs/rwtrain_torch211_cu129/bin/python" <<'PYSHEBANG'
import os, re, sys
bindir, target = sys.argv[1], sys.argv[2].encode()
pattern = re.compile(rb'#!/project/community/jjyeung/[^/\s]+/venvs/rwtrain_torch211_cu129/bin/python[0-9.]*')
changed = 0
for name in sorted(os.listdir(bindir)):
    path = os.path.join(bindir, name)
    if os.path.islink(path) or not os.path.isfile(path):
        continue
    with open(path, 'rb') as stream:
        data = stream.read()
    first, sep, rest = data.partition(b'\n')
    if pattern.fullmatch(first.rstrip()) and first != b'#!' + target:
        with open(path + '.part', 'wb') as stream:
            stream.write(b'#!' + target + sep + rest)
        os.chmod(path + '.part', os.stat(path).st_mode)
        os.replace(path + '.part', path)
        changed += 1
assert os.path.isfile(os.path.join(bindir, 'torchrun'))
print('venv console scripts repointed:', changed, flush=True)
PYSHEBANG
    touch "$stamp"
}

tk_join() {
    local dest="$1" sha="$2"; shift 2
    [[ ! -f "$S/.stamp/join.$sha" || ! -f "$dest" ]] || return 0
    mkdir -p "$(dirname "$dest")" "$S/.stamp"
    cat "$@" > "$dest.part"
    sha_is "$dest.part" "$sha"
    mv "$dest.part" "$dest"; chmod a-w "$dest"
    touch "$S/.stamp/join.$sha"
    tk_step "joined $(basename "$dest") $(stat -c %s "$dest") B"
}

tk_readonly_files() {
    find "$1" -type f -exec chmod a-w {} +
    find "$1" -type d -exec chmod 700 {} +
}

tk_stage_model() {
    local snap="$S/c7d31ddd/$RR/models/a32330d0/snapshots/$REV" file sha
    read -r file sha < <(tk_current model)
    [[ ! -f "$S/.stamp/model.$sha" || ! -d "$snap" ]] || return 0
    /usr/bin/python3 -B -I "$Q_KIT/b/m.py" "$file" "$sha" "$snap" "$REV"
    tk_readonly_files "$snap"
    touch "$S/.stamp/model.$sha"
    tk_step "model staged: $(du -sk "$snap" | cut -f1) KiB"
}

tk_stage_small() {
    local sha stamp
    read -r _ sha < <(tk_current small)
    stamp="$S/.stamp/small.$sha.$( { if [[ -d "$HX/in_small" ]]; then (cd "$HX" && find in_small -type f -printf '%P %s %T@\n'); fi; } 2>/dev/null | sort | sha256sum | cut -c1-16)"
    [[ ! -f "$stamp" ]] || return 0
    sha_is "$IN/e00" "$sha"
    mkdir -p "$U" "$S/aws/raw.$sha"
    [[ -f "$S/.stamp/e00.$sha" ]] || { tar -x -f "$IN/e00" -C "$S/aws/raw.$sha" --no-same-owner; touch "$S/.stamp/e00.$sha"; }
    cp -a "$S/aws/raw.$sha/${AS#/}/." "$U/"
    cp -a "$S/aws/raw.$sha/${AL#/}/." "$U/"
    mkdir -p "$U/ap/f1a2c7e9/k"
    cp "$U/ap/244cdf20/k/932c0c4e.json" "$U/ap/244cdf20/k/99e6eed6.json" "$U/ap/f1a2c7e9/k/"
    if [[ -d "$HX/in_small" ]]; then rsync -rt "$HX/in_small/" "$U/"; fi
    touch "$stamp"
    tk_step "small inputs staged"
}

tk_stage_extra() {
    local dest sha parts
    while IFS=$'\t' read -r dest sha parts; do
        [[ -n "$dest" ]] || continue
        tk_join "$(hp "$dest")" "$sha" $parts
    done < <(/usr/bin/python3 -B -I -c 'import json,sys
d=json.load(open(sys.argv[1]))
for e in d.get("extra", []) + [d["a1rows"]]: print(e["dest"], e["sha256"], " ".join(e["parts"]), sep="\t")' "$CUR")
}

tk_stage_tars() {
    local i n
    n=$(/usr/bin/python3 -B -I -c 'import json,sys; print(len(json.load(open(sys.argv[1])).get("tars", [])))' "$CUR")
    for ((i = 0; i < n; i++)); do
        local id parts
        id=$(/usr/bin/python3 -B -I -c 'import json,sys,hashlib; e=json.load(open(sys.argv[1]))["tars"][int(sys.argv[2])]; print(hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()[:16])' "$CUR" "$i")
        [[ ! -f "$S/.stamp/tar.$id" ]] || continue
        parts=$(/usr/bin/python3 -B -I -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["tars"][int(sys.argv[2])]["parts"]))' "$CUR" "$i")
        mkdir -p "$U"
        cat $parts | tar -x -C "$U" --no-same-owner --no-same-permissions
        /usr/bin/python3 -B -I - "$CUR" "$i" "$U" <<'PYTARS'
import hashlib, json, sys
from pathlib import Path
entry = json.load(open(sys.argv[1]))['tars'][int(sys.argv[2])]; root = Path(sys.argv[3])
for rel, want in sorted(entry['files'].items()):
    h = hashlib.sha256()
    with open(root / rel, 'rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    if h.hexdigest() != want:
        raise SystemExit('archive member differs: ' + rel)
print('archive members verified:', len(entry['files']), flush=True)
PYTARS
        touch "$S/.stamp/tar.$id"
        tk_step "archive $id staged"
    done
}

tk_stage_fla() {
    [[ ! -f "$S/.stamp/fla.d00" ]] || return 0
    local file sha
    mkdir -p "$U/ap/7b30c1e4/u"
    tar -x -f "$IN/d00" -C "$U/ap/7b30c1e4/u" --no-same-owner
    read -r file sha < <(tk_current fla)
    sha_is "$(hp "$file")" "$sha"
    (cd "$U/ap/7b30c1e4/u/ebe69df8/p" && sha256sum -c --quiet ../m.sha)
    touch "$S/.stamp/fla.d00"
    tk_step "fla overlay staged"
}

tk_stage_bundle() {
    local key="$1" file sha manifest manifest_sha stamp dest="$S/c7d31ddd/data2root" store parts got
    tk_has "$key" || return 0
    read -r file sha < <(tk_current "$key")
    read -r manifest manifest_sha < <(tk_current "${key}_manifest")
    manifest=$(hp "$manifest")
    sha_is "$manifest" "$manifest_sha"
    if /usr/bin/python3 -B -I -c 'import json,sys; p=json.load(open(sys.argv[1])).get("staged_inputs", {}); sys.exit(0 if sys.argv[2] in p.get("covered_bundles", []) else 1)' "$CUR" "$key"; then
        store=$(/usr/bin/python3 -B -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["stores"].get(sys.argv[2], ""))' "$CUR" "$key")
        /usr/bin/python3 -B -I "$HX/b/f2.py" "$manifest" "$dest" "$manifest_sha" "$store"
        tk_step "frames $key verified through pinned shards"
        return 0
    fi
    stamp="$S/.stamp/$key.$sha.$manifest_sha"
    mkdir -p "$dest"
    if [[ ! -f "$stamp" ]]; then
        parts=$(/usr/bin/python3 -B -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(" ".join(d.get("bundle_parts", {}).get(sys.argv[2], d.get("f3_parts") if sys.argv[2] == "f3" else [])))' "$CUR" "$key")
        [[ -n "$parts" ]] || parts=$(hp "$file")
        : > "$S/.$key.sha"
        cat $parts | tee >(sha256sum | cut -d' ' -f1 > "$S/.$key.sha.part" && mv "$S/.$key.sha.part" "$S/.$key.sha") \
            | tar --extract --directory="$dest" --skip-old-files --no-same-owner --no-same-permissions
        for _ in $(seq 300); do [[ -s "$S/.$key.sha" ]] && break; sleep 1; done
        got=$(cat "$S/.$key.sha")
        [[ "$got" == "$sha" ]] || { tk_step "frame tar $key sha differs: $got"; return 3; }
        store=$(/usr/bin/python3 -B -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["stores"].get(sys.argv[2], ""))' "$CUR" "$key")
        /usr/bin/python3 -B -I "$HX/b/f2.py" "$manifest" "$dest" "$manifest_sha" $store
        touch "$stamp"
    fi
    tk_step "frames $key verified: ${manifest_sha:0:12}"
}

tk_stage_init() {
    local file sha dest
    tk_has init || return 0
    read -r file sha < <(tk_current init)
    dest="$S/c7d31ddd/init/${sha:0:16}"
    if [[ -f "$dest/.verified" ]]; then tk_step "init mirror present: ${sha:0:16}"; return 0; fi
    [[ ! -e "$dest" ]] || mv "$dest" "$dest.old.$(date +%s)"
    [[ ! -e "$dest.part" ]] || mv "$dest.part" "$dest.part.prev.$(date +%s).$$"
    mkdir -p "$dest.part/full_weights"
    cp "$(hp "$file")" "$dest.part/artifact.json"
    /usr/bin/python3 -B -I - "$dest.part" "$sha" "$U" "$AS" "$AL" <<'PYINIT'
import hashlib, json, os, sys
from pathlib import Path
dest, sha, union, aws, awl = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()
def host(p):
    for prefix in (aws, awl):
        if p.startswith(prefix + '/'):
            return Path(union + p[len(prefix):])
    raise SystemExit('init path outside the code-aws prefixes: ' + p)
if digest(dest/'artifact.json') != sha:
    raise SystemExit('init artifact differs from its pin')
artifact = json.loads((dest/'artifact.json').read_text())
heads, manifest = host(artifact['heads']['path']), host(artifact['full_weights']['path'])
os.link(heads, dest/'heads.pt')
if digest(dest/'heads.pt') != artifact['heads']['sha256']:
    raise SystemExit('init heads differ')
os.link(manifest, dest/'full_weights'/manifest.name)
if digest(dest/'full_weights'/manifest.name) != artifact['full_weights']['sha256']:
    raise SystemExit('init manifest differs')
spec = json.loads(manifest.read_text())
pins = {spec['index']['name']: spec['index']['sha256'], **{f['name']: f['sha256'] for f in spec['files']}}
for name, expected in pins.items():
    os.link(manifest.parent/name, dest/'full_weights'/name)
    if digest(dest/'full_weights'/name) != expected:
        raise SystemExit('init weights differ: ' + name)
PYINIT
    touch "$dest.part/.verified"
    mv "$dest.part" "$dest"
    tk_step "init mirror verified: ${sha:0:16}"
}

tk_stage() {
    local mode="$1"
    mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung
    mkdir -p "$S" "$TK_JOBDIR"
    tk_nx
    exec 8>"$S/../stage.lock"
    flock 8
    tk_step "stage $mode on $(hostname): /tmp free $(df -Pk /tmp | awk 'NR==2 {print int($4 / 1048576)}') GiB; mem $(free -g | awk 'NR==2 {print $2}') GiB"
    mkdir -p "$S/c7d31ddd/$RR" "$S/epochs" "$S/c7d31ddd/anyhost" "$S/c7d31ddd/coord" "$S/c7d31ddd/stop" "$S/c7d31ddd/data2root"
    tk_kitx venv "$S/c7d31ddd/venvs"
    tk_venv_shebangs
    tk_kitx closure "$S/c7d31ddd/$CLOSURE_DIR"
    local sa_stamp
    sa_stamp="$S/.stamp/sitealias.${CLOSURE_DIR##*/}.$(cat "$HX/b/sa/sitecustomize.py" "$HX/b/sa/prestage_hooks.py" | sha256sum | cut -c1-16)"
    if [[ ! -f "$sa_stamp" ]]; then
        [[ ! -d "$S/c7d31ddd/$CLOSURE_DIR/site_alias" ]] || mv "$S/c7d31ddd/$CLOSURE_DIR/site_alias" "$S/c7d31ddd/$CLOSURE_DIR/site_alias.closure.$(date +%s)"
        mkdir -p "$S/c7d31ddd/$CLOSURE_DIR/site_alias"
        cp "$HX/b/sa/prestage_hooks.py" "$HX/b/sa/sitecustomize.py" "$S/c7d31ddd/$CLOSURE_DIR/site_alias/"
        touch "$sa_stamp"
    fi
    if [[ ! -d "$S/epochs/$COMMIT" ]]; then
        tk_kitx trainer "$S/epochs/$COMMIT"
        tk_readonly_files "$S/epochs/$COMMIT"
    fi
    if [[ "$mode" != preflight ]] && tk_has trainer_old; then
        local old_commit
        old_commit=$(/usr/bin/python3 -B -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["trainer_old_commit"])' "$CUR")
        if [[ ! -d "$S/epochs/$old_commit" ]]; then
            tk_kitx trainer_old "$S/epochs/$old_commit"
            tk_readonly_files "$S/epochs/$old_commit"
        fi
    fi
    local rfile rsha
    read -r rfile rsha < <(tk_current record)
    cp "$(hp "$rfile")" "$S/c7d31ddd/anyhost/$rsha.json.part" && mv "$S/c7d31ddd/anyhost/$rsha.json.part" "$S/c7d31ddd/anyhost/$rsha.json"
    sha_is "$S/c7d31ddd/anyhost/$rsha.json" "$rsha"
    R1_RUNTIME_RECORD="$P/anyhost/$rsha.json"
    if [[ "$mode" == preflight ]]; then
        tk_stage_fla
        if tk_has np; then tk_kitx np "$S/np226"; fi
        mkdir -p "$U/ap/$K/u" "$NX/u" "$S/c7d31ddd/$RR/models"
        flock -u 8
        tk_step "stage preflight done"
        return
    fi
    tk_stage_model
    tk_kitx art "$S/c7d31ddd/art"
    mkdir -p "$S/c7d31ddd/lb"
    cp -f "$S/c7d31ddd/art/lb/51f013139e77.npz" "$S/c7d31ddd/lb/51f013139e77.npz"
    mkdir -p "$S/c7d31ddd/$RR/frozen" "$S/c7d31ddd/$RR/prestage" "$S/c7d31ddd/$RR/incoming_r1" "$S/c7d31ddd/data2root/t6tk"
    tk_stage_small
    tk_stage_extra
    tk_stage_tars
    tk_stage_fla
    if tk_has np; then tk_kitx np "$S/np226"; fi
    local import_mode=metadata
    if [[ "$mode" != reuse && -z "${TK_LIGHT:-}" ]]; then import_mode=full; fi
    /usr/bin/python3 -B -I "$Q_KIT/b/s.py" "$Q_KIT" "$CUR" "$HX" "$S" "$import_mode"
    if [[ "$mode" != reuse && -z "${TK_LIGHT:-}" ]]; then
        local key
        for key in f3 f4 f5 f6 f7 f8 f9 f10 f11 f12 f13 f14; do tk_stage_bundle "$key"; done
        tk_stage_init
    fi
    mkdir -p "$U/ap/$K"
    mkdir -p "$U/ap/$K/u" "$NX/u"
    flock -u 8
    tk_step "stage $mode done"
}

tk_bwrap() {
    local bw sha
    read -r bw sha < <(tk_current bwrap)
    [[ -x "$bw" ]] && sha_is "$bw" "$sha"
    BW=("$bw")
    local entry
    for entry in /* /.[!.]* /..?*; do
        case "$entry" in /home|/dev|/proc) continue ;; esac
        [[ -e "$entry" || -L "$entry" ]] || continue
        if [[ -L "$entry" ]]; then BW+=(--symlink "$(readlink "$entry")" "$entry"); else BW+=(--ro-bind "$entry" "$entry"); fi
    done
    BW+=(--tmpfs /tmp --bind "$Q_ROOT" "$Q_ROOT" --dev-bind /dev /dev --proc /proc
        --tmpfs /home --dir /home/jjyeung
        --ro-bind "$U" "$AS"
        --ro-bind "$U" "$AL"
        --bind "$NX" "$X"
        --bind "$NR" "$X/runs"
        --ro-bind "$U/ap/$K/u" "$X/u"
        --ro-bind "$S/c7d31ddd/data2root" "$X/data2root"
        --ro-bind "$S/c7d31ddd/$RR/models" "$X/models"
        --ro-bind "$S/c7d31ddd" "$P"
        --ro-bind "$S/epochs" "$EPOCHS"
        --bind "$TK_JOBDIR" "$TK_JOBDIR"
        --remount-ro /home
        --unshare-user --uid "$(id -u)" --gid "$(id -g)")
}

tk_env() {
    export R1_OPAQUE_LOGS=1
    export Q_E5=6d38613965 R1_MODEL_DIR=a32330d0
    export R1_MOUNT="$X" R1_TRAINER="$EPOCHS/$COMMIT" TRAINER="$EPOCHS/$COMMIT" ANYHOST_JOBS="$P/$CLOSURE_DIR"
    export R1_RUNTIME_RECORD ANYHOST_NEUTRAL_RUNTIME="$R1_RUNTIME_RECORD"
    export PILOT_VENV="$P/venvs/rwtrain_torch211_cu129"
    export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/usr/local/bin:/usr/bin:/bin"
    export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
    export Q_E1=1 Q_E2=orchard A_SITE_PROFILE="$X/b/profile.json"
    export Q_E3="$X/models"
    # The job folder is also bound at Q_NJ, under the tree's owned node-local root /tmp/jjyeung, the only
    # place the frame root map may point besides the store. The kit's python steps run under Q_NS, where
    # every reviewed path string was written. Frame reads resolve through Q_NJ to the kit's copy of the
    # frame store inside the job folder (q/f/<sha256 of the frame root>), and the frame audit gets the
    # request's frame roots under that name (b/pf.py audit_roots).
    case "${Q_NS:-}" in /tmp/?*) ;; *) echo E06 >&2; exit 1 ;; esac
    Q_NJ="/tmp/jjyeung/${Q_NS#/tmp/}"
    export Q_E4="{\"/data2\": \"$Q_NJ/p/q/f/$(printf '%s' "$X/data2root" | sha256sum | cut -c1-64)\"}"
    export C1_INIT_LOCAL="$P/init"
    export HF_HOME="$TK_JOBDIR/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
    export OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48 TOKENIZERS_PARALLELISM=false WANDB_DISABLED=true
    export Q_E6=1
    export TMPDIR="$TK_JOBDIR/tmp"
    export XDG_CACHE_HOME="$TK_JOBDIR/cache" TORCH_HOME="$TK_JOBDIR/cache/torch" TRITON_CACHE_DIR="$TK_JOBDIR/cache/triton"
    mkdir -p "$TMPDIR"
}

tk_pythonpath() {
    local mode="${1:?}" fla_file fla_sha
    export PYTHONPATH="$X/b:$ANYHOST_JOBS:$ANYHOST_JOBS/site_alias"
    if tk_has np; then export PYTHONPATH="$S/np226:$PYTHONPATH"; tk_step "numpy 2.2.6 overlay on"; fi
    if [[ "$mode" =~ ^[ctu]$ ]] && read -r fla_file fla_sha < <(tk_current fla 2>/dev/null); then
        sha_is "$(hp "$fla_file")" "$fla_sha"
        export PYTHONPATH="$(dirname "$fla_file")/p:$PYTHONPATH" C1_EXPECT_FLA=1
        tk_step "fla overlay on: ${fla_sha:0:12}"
    fi
}

tk_nx() {
    mkdir -p "$NR" "$NX/o" "$NX/runs" "$NX/arm" "$NX/ck" "$NX/data2root" "$NX/models" "$HM/o" "$HM/arm" "$HM/runs"
    rsync -rt --chmod=D700 "$HX/b" "$HX/k" "$HX/ANON_OK.json" "$HX/SHA256SUMS.txt" "$NX/"
    rsync -rt "$HM/arm/" "$NX/arm/"
}

tk_stage full
tk_env
if [[ "${Q_MODE:-q}" == r ]]; then export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8; fi
tk_pythonpath c
tk_bwrap
export PATH="$(dirname "${BW[0]}"):$PATH"
BW+=(--bind "$Q_ROOT" "$Q_NS" --bind "$Q_ROOT" "$Q_NJ" --setenv TK_JOB_START "${TK_JOB_START:?}")
Q_LIVE=$(/usr/bin/python3 -B -I -s "$Q_KIT/b/rv.py" --live "$Q_ROOT" "${SLURM_JOB_ID:?}")
BW+=(--bind "$Q_LIVE" "$Q_LIVE")
if [[ "${Q_CAPTURE:-0}" == 1 ]]; then
    /usr/bin/python3 -B "$Q_KIT/b/w.py" "$Q_ROOT/args.json" "${BW[@]}"
    exit 0
fi
# Whole-leg disk plan right after staging: the tree's own plan on the kit configuration against the free space of
# the job folder's filesystem (the run output's); free must exceed the plan by 300 GB.
if [[ "${Q_MODE:-q}" != r ]]; then
set +e
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/dp.py" preflight "$Q_KIT" "$Q_NS" 300000000000 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/dp.log"
rc=${PIPESTATUS[0]}
set -e
tk_step "disk plan after staging rc=$rc: $(tail -n 1 "$Q_ROOT/dp.log" | cut -c1-900)"
if [[ "$rc" != 0 ]]; then exit "$rc"; fi
fi
if [[ "${Q_MODE:-q}" != r ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/g.py"
fi
set +e
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/a.py" "${Q_MODE:-q}" "$Q_NS/p" "$Q_NS/r.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/q.log"
rc=${PIPESTATUS[0]}
if [[ "${Q_MODE:-q}" == r ]]; then
    /usr/bin/python3 -B -I -s "$Q_KIT/b/rd.py" "$Q_ROOT" "${SLURM_JOB_ID:?}" "$rc"
    rp=$?
    if [[ "$rc" == 0 ]]; then rc=$rp; fi
    exit "$rc"
fi
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/d.py" "$Q_NS/p/s" "$Q_NS/r.json" "$Q_NS/n.json" "$Q_NS/rooms.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rooms.log"
rr=${PIPESTATUS[0]}
if [[ "$rc" == 0 && "$rr" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/h.log"
rc=${PIPESTATUS[0]}
if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
"${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "${SLURM_JOB_ID:?}" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rv.log"
rc=${PIPESTATUS[0]}
fi
# Ranks 1-3 read the init artifact's own weight and head paths under the mount's runs folder: link them to the
# staged copies named by the persisted-file map (b/il.py), then recheck the disk plan on the job configuration.
if [[ "$rc" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/il.py" "$Q_NS/v.json" "$X" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/il.log"
rc=${PIPESTATUS[0]}
tk_step "init links rc=$rc: $(tail -n 1 "$Q_ROOT/il.log" | cut -c1-900)"
fi
if [[ "$rc" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/dp.py" train "$Q_KIT" - 0 "$Q_NS/v.json" "$Q_NS/p/s" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/dp2.log"
rc=${PIPESTATUS[0]}
tk_step "disk plan at training start rc=$rc: $(tail -n 1 "$Q_ROOT/dp2.log" | cut -c1-900)"
fi
if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/t.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/t.log"
rc=${PIPESTATUS[0]}
fi
fi
/usr/bin/python3 -B "$Q_KIT/b/o.py" "$Q_ROOT" "$rc" "$rr"
exit "$rc"
