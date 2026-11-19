# Orchard staging and namespace for the CP1-Rv kit (sourced by r.sh).
# Pins keep their code-aws paths; a private bwrap namespace mounts one node-local union tree at both code-aws
# prefixes (/scratch/fsw and /lustre/fsw name the same store there), so every pinned receipt resolves unchanged.
# Inputs come from the Orchard cache (fetched from GCS on the login node) and are sha-checked on the node.
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
K=8865619b
X=$AS/ap/$K
R=/project/community/jjyeung/distill/okit
HX="${TK_KIT_HOME:?}"
IN=$R/in
REV=c202236235762e1c871ad0ccb60c8ee5ba337b9a
P=/project/community/jjyeung/c7d31ddd
RR=runs/aws128p_20261025
EPOCHS=/home/jjyeung/6d00e578
S=/scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T094926Z/launch-timing-li_7i792/tmp/okit_$K/root
U=$S/aws/u
HM=$HX
NX=/scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T094926Z/launch-timing-li_7i792/tmp/okit_$K/x_${SLURM_JOB_ID:-local}
NR=${TK_RUNS_DIR:-/scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T094926Z/launch-timing-li_7i792/tmp/okit_$K/runs}
CUR=$HX/k/0.json
COMMIT=$(/usr/bin/python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' "$CUR")
tk_step() {
    local line
    line="$(date -u +%FT%TZ) | $*"
    printf '%s\n' "$line"
    if [[ -n "${SLURM_JOB_ID:-}" && -d "$HM/o" ]]; then printf '%s\n' "$line" >> "$HM/o/$SLURM_JOB_ID.steps" 2>/dev/null || true; fi
}
hp() {
    case "$1" in
        "$X"/*) printf '%s\n' "$NX/${1#"$X"/}" ;;
        "$AS"/*) printf '%s\n' "$U/${1#"$AS"/}" ;;
        "$AL"/*) printf '%s\n' "$U/${1#"$AL"/}" ;;
        *) printf '%s\n' "$1" ;;
    esac
}
tk_current() { /usr/bin/python3 -I -c 'import json, sys; e = json.load(open(sys.argv[1]))[sys.argv[2]]; print(e["file"], e["sha256"])' "$CUR" "$1"; }
tk_has() { /usr/bin/python3 -I -c 'import json,sys; sys.exit(0 if sys.argv[2] in json.load(open(sys.argv[1])) else 1)' "$CUR" "$1"; }
CLOSURE_DIR="_jobs/cp4tk_$(tk_current closure | cut -d' ' -f2 | cut -c1-12)"
tk_kitx() {
    local key="$1" dest="$2" file sha
    read -r file sha < <(tk_current "$key")
    file=$(hp "$file")
    if [[ -f "$S/.stamp/$key.$sha" && -d "$dest" ]]; then return 0; fi
    if [[ -e "$dest" ]]; then mv "$dest" "$dest.old.$(date +%s)"; fi
    mkdir -p "$(dirname "$dest")" "$S/.stamp"
    /usr/bin/python3 -I "$HX/b/kitx.py" "$file" "$sha" "$dest"
    touch "$S/.stamp/$key.$sha"
}
sha_is() { [[ "$(sha256sum < "$1" | cut -d' ' -f1)" == "$2" ]] || { tk_step "sha differs: $1"; return 3; }; }

tk_venv_shebangs() {
    local v="$S/c7d31ddd/venvs/rwtrain_torch211_cu129" stamp
    stamp="$S/.stamp/shebang.$(tk_current venv | cut -d' ' -f2)"
    [[ ! -f "$stamp" ]] || return 0
    /usr/bin/python3 -I - "$v/bin" "$P/venvs/rwtrain_torch211_cu129/bin/python" <<'PYSHEBANG'
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

# Concatenate cache parts into one verified node-local file.
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

tk_stage_model() {
    local snap="$S/c7d31ddd/$RR/models/a32330d0/snapshots/$REV" file sha
    read -r file sha < <(tk_current model)
    [[ ! -f "$S/.stamp/model.$sha" || ! -d "$snap" ]] || return 0
    local tmp="$S/.model.$$"
    mkdir -p "$tmp" "$(dirname "$snap")"
    /usr/bin/python3 -I "$HX/b/kitx.py" "$file" "$sha" "$tmp/x"
    [[ ! -e "$snap" ]] || mv "$snap" "$snap.old.$(date +%s)"
    mv "$tmp/x/models--Qwen--Qwen3.5-9B/snapshots/$REV" "$snap"
    chmod -R a-w "$snap"
    touch "$S/.stamp/model.$sha"
    tk_step "model staged: $(du -sk "$snap" | cut -f1) KiB"
}

# Small pinned inputs at their code-aws paths: the q7 smalls tar plus this kit's in_small tree (ap/... layout).
tk_stage_small() {
    local sha stamp
    read -r _ sha < <(tk_current small)
    # A kit without in_small must not end the job here (set -e with pipefail would fail the substitution).
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

# Large single files named in k/0.json "extra" (and the A1 rows): [{"dest": <code-aws path>, "sha256", "parts": [cache files]}].
tk_stage_extra() {
    local dest sha parts
    while IFS=$'\t' read -r dest sha parts; do
        [[ -n "$dest" ]] || continue
        # shellcheck disable=SC2086
        tk_join "$(hp "$dest")" "$sha" $parts
    done < <(/usr/bin/python3 -I -c 'import json,sys
d=json.load(open(sys.argv[1]))
for e in d.get("extra", []) + [d["a1rows"]]: print(e["dest"], e["sha256"], " ".join(e["parts"]), sep="\t")' "$CUR")
}

# Archives named in k/0.json "tars": [{"parts": [cache files], "files": {"ap/...": sha256}}], extracted into the union
# tree; every listed member is sha-checked.
tk_stage_tars() {
    local i n
    n=$(/usr/bin/python3 -I -c 'import json,sys; print(len(json.load(open(sys.argv[1])).get("tars", [])))' "$CUR")
    for ((i = 0; i < n; i++)); do
        local id parts
        id=$(/usr/bin/python3 -I -c 'import json,sys,hashlib; e=json.load(open(sys.argv[1]))["tars"][int(sys.argv[2])]; print(hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()[:16])' "$CUR" "$i")
        [[ ! -f "$S/.stamp/tar.$id" ]] || continue
        parts=$(/usr/bin/python3 -I -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["tars"][int(sys.argv[2])]["parts"]))' "$CUR" "$i")
        mkdir -p "$U"
        # shellcheck disable=SC2086
        cat $parts | tar -x -C "$U" --no-same-owner --no-same-permissions
        /usr/bin/python3 -I - "$CUR" "$i" "$U" <<'PYTARS'
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

# One frame bundle: KEY's tar (from its cache parts, else its joined node-local file) into data2root, then the
# manifest check for its store (f3 = A1 frames from the q7 cache parts).
tk_stage_bundle() {
    local key="$1" file sha manifest manifest_sha stamp dest="$S/c7d31ddd/data2root" store parts got
    tk_has "$key" || return 0
    read -r file sha < <(tk_current "$key")
    read -r manifest manifest_sha < <(tk_current "${key}_manifest")
    manifest=$(hp "$manifest")
    sha_is "$manifest" "$manifest_sha"
    if /usr/bin/python3 -I -c 'import json,sys; p=json.load(open(sys.argv[1])).get("staged_inputs", {}); sys.exit(0 if sys.argv[2] in p.get("covered_bundles", []) else 1)' "$CUR" "$key"; then
        store=$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["stores"].get(sys.argv[2], ""))' "$CUR" "$key")
        /usr/bin/python3 -I "$HX/b/f2.py" "$manifest" "$dest" "$manifest_sha" "$store"
        tk_step "frames $key verified through pinned shards"
        return 0
    fi
    stamp="$S/.stamp/$key.$sha.$manifest_sha"
    mkdir -p "$dest"
    if [[ ! -f "$stamp" ]]; then
        parts=$(/usr/bin/python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(" ".join(d.get("bundle_parts", {}).get(sys.argv[2], d.get("f3_parts") if sys.argv[2] == "f3" else [])))' "$CUR" "$key")
        [[ -n "$parts" ]] || parts=$(hp "$file")
        : > "$S/.$key.sha"
        # shellcheck disable=SC2086
        cat $parts | tee >(sha256sum | cut -d' ' -f1 > "$S/.$key.sha.part" && mv "$S/.$key.sha.part" "$S/.$key.sha") \
            | tar --extract --directory="$dest" --skip-old-files --no-same-owner --no-same-permissions
        for _ in $(seq 300); do [[ -s "$S/.$key.sha" ]] && break; sleep 1; done
        got=$(cat "$S/.$key.sha")
        [[ "$got" == "$sha" ]] || { tk_step "frame tar $key sha differs: $got"; return 3; }
        store=$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["stores"].get(sys.argv[2], ""))' "$CUR" "$key")
        # shellcheck disable=SC2086
        /usr/bin/python3 -I "$HX/b/f2.py" "$manifest" "$dest" "$manifest_sha" $store
        touch "$stamp"
    fi
    tk_step "frames $key verified: ${manifest_sha:0:12}"
}

tk_stage_init() {
    # Warm-start milestone mirrored once per node; the trainer reads it through C1_INIT_LOCAL/<sha16>/.verified.
    local file sha dest
    tk_has init || return 0
    read -r file sha < <(tk_current init)
    dest="$S/c7d31ddd/init/${sha:0:16}"
    if [[ -f "$dest/.verified" ]]; then tk_step "init mirror present: ${sha:0:16}"; return 0; fi
    [[ ! -e "$dest" ]] || mv "$dest" "$dest.old.$(date +%s)"
    [[ ! -e "$dest.part" ]] || mv "$dest.part" "$dest.part.prev.$(date +%s).$$"
    mkdir -p "$dest.part/full_weights"
    cp "$(hp "$file")" "$dest.part/artifact.json"
    /usr/bin/python3 -I - "$dest.part" "$sha" "$U" "$AS" "$AL" <<'PYINIT'
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
    mkdir -p /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T094926Z/launch-timing-li_7i792/tmp && chmod 700 /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T094926Z/launch-timing-li_7i792/tmp
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
        chmod -R a-w "$S/epochs/$COMMIT"
    fi
    if [[ "$mode" != preflight ]] && tk_has trainer_old; then
        local old_commit
        old_commit=$(/usr/bin/python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["trainer_old_commit"])' "$CUR")
        if [[ ! -d "$S/epochs/$old_commit" ]]; then
            tk_kitx trainer_old "$S/epochs/$old_commit"
            chmod -R a-w "$S/epochs/$old_commit"
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
    /usr/bin/python3 -I "$HX/b/s.py" "$CUR" "$HX" "$S" "$import_mode"
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
    BW+=(--dev-bind /dev /dev --proc /proc
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
    export R1_STUDENT_HEX=6d38613965 R1_MODEL_DIR=a32330d0
    export R1_MOUNT="$X" R1_TRAINER="$EPOCHS/$COMMIT" TRAINER="$EPOCHS/$COMMIT" ANYHOST_JOBS="$P/$CLOSURE_DIR"
    export R1_RUNTIME_RECORD ANYHOST_NEUTRAL_RUNTIME="$R1_RUNTIME_RECORD"
    export PILOT_VENV="$P/venvs/rwtrain_torch211_cu129"
    export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/usr/local/bin:/usr/bin:/bin"
    export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
    export STUDENT_ORCHARD=1 STUDENT_SLURM_SITE=orchard A_SITE_PROFILE="$X/b/profile.json"
    export STUDENT_MODEL_ROOT="$X/models"
    export STUDENT_FRAME_ROOT_MAP="{\"/data2\": \"$X/data2root\"}"
    export C1_INIT_LOCAL="$P/init"
    export HF_HOME="$TK_JOBDIR/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
    export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false WANDB_DISABLED=true
    export STUDENT_PRESERVE_CHECKPOINTS=1
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

# Per-job writable kit root: kit bytes from /home (read-only), prep outputs restored from the /home mirror.
tk_nx() {
    mkdir -p "$NR" "$NX/o" "$NX/runs" "$NX/arm" "$NX/ck" "$NX/data2root" "$NX/models" "$HM/o" "$HM/arm" "$HM/runs"
    rsync -rt "$HX/b" "$HX/k" "$HX/ANON_OK.json" "$HX/SHA256SUMS.txt" "$NX/"
    rsync -rt "$HM/arm/" "$NX/arm/"
}
tk_persist_small() {
    rsync -rt "$NX/o/" "$HM/o/" 2>/dev/null || true
    rsync -rt "$NX/arm/" "$HM/arm/" 2>/dev/null || true
    rsync -rt --prune-empty-dirs --exclude 'checkpoint_*' --exclude 'full_weights/' --exclude '*.pt' \
        --include '*/' --include '*.json' --include '*.jsonl' --exclude '*' "$NR/" "$HM/runs/" 2>/dev/null || true
}
# Upload each finished milestone export (tar of runs/<run>/m<step>) to GCS in 4 parts; idempotent via receipts.
tk_persist_exports() {
    local d run m tarf obj
    [[ -f "$HM/sess.json" ]] || return 0
    for d in "$NR"/*/m*/; do
        [[ -f "$d/artifact.json" ]] || continue
        run=$(basename "$(dirname "$d")"); m=$(basename "$d")
        [[ ! -f "$HM/o/gcs_${run}_${m}.done" ]] || continue
        tarf="$S/../up/${run}_${m}.tar"; obj="q8/$K/${run}_${m}.tar"
        # Sessions are minted per milestone name. A stop export (unknown step) takes the first unused stop generation
        # <run>_mstop, _mstopB, _mstopC; each generation is claimed once (.claim), so equal-sized parts never collide.
        if ! /usr/bin/python3 -I -c 'import json, sys; sys.exit(0 if sys.argv[2] + ".part00-of-04" in json.load(open(sys.argv[1])) else 1)' \
                "$HM/sess.json" "$obj" 2>/dev/null; then
            obj=""
            for g in mstop mstopB mstopC; do
                if [[ -f "$HM/o/gcs_${run}_${g}.claim" ]]; then
                    [[ "$(cat "$HM/o/gcs_${run}_${g}.claim")" == "$m" ]] && { obj="q8/$K/${run}_${g}.tar"; break; }
                    continue
                fi
                printf '%s\n' "$m" > "$HM/o/gcs_${run}_${g}.claim"; obj="q8/$K/${run}_${g}.tar"; break
            done
            [[ -n "$obj" ]] || { tk_step "export not uploaded: no unused stop generation for ${run}_${m}"; continue; }
        fi
        mkdir -p "$(dirname "$tarf")"
        [[ -f "$tarf" ]] || { tar cf "$tarf.part" -C "$NR/$run" "$m" && mv "$tarf.part" "$tarf"; }
        if /usr/bin/python3 -I "$HX/b/gcsput.py" split "$HM/sess.json" "$obj" "$tarf" 4 4 >> "$HM/o/gcs.log" 2>&1; then
            printf '%s %s %s\n' "$obj" "$(stat -c %s "$tarf")" "$(sha256sum < "$tarf" | cut -d' ' -f1)" > "$HM/o/gcs_${run}_${m}.done"
            tk_step "export uploaded: $obj"
        else
            tk_step "export upload failed: $obj (retry next pass)"
        fi
    done
}
