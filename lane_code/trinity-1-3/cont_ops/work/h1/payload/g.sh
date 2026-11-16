#!/bin/bash
set -Eeuo pipefail
export TZ=UTC
umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"
BUN=/project/community/jjyeung/okh7/i_1be16f28
KH=/project/community/jjyeung/okh7/x_4b3114cf
private_dir "$BUN"
cd "$BUN"
trap 'printf "Gate input or runtime blocker at line %s (status %s).\n" "$LINENO" "$?" >&2; exit 2' ERR
[[ ! -e "$BUN/gate.json" && ! -L "$BUN/gate.json" ]] || { echo 'gate.json already exists; refusing overwrite' >&2; exit 2; }
[[ -n "${PY_GATE:-}" ]] || { echo 'Set PY_GATE to the installed CPU interpreter with the pinned dependencies.' >&2; exit 2; }
BW_GATE="${BW_GATE:-bwrap}"
sha256sum -c sums.txt
if [[ ! -e "$BUN/a.json" && ! -L "$BUN/a.json" ]]; then
    python3 -B r.py copy
fi
# Reuse only exact archive contents; all extraction writes are create-only.
python3 -B - <<'P'
import hashlib,json,stat,tarfile
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def unpack(archive,root):
    if root.is_symlink():raise ValueError('linked extraction root')
    reuse=root.exists()
    if not reuse:root.mkdir(mode=0o700)
    expected=set()
    with tarfile.open(archive) as tf:
        for m in tf:
            rel=Path(m.name)
            if str(rel)=='.' and m.isdir():continue
            if rel.is_absolute() or '..' in rel.parts or str(rel)=='.':raise ValueError('unsafe archive member')
            if not (m.isfile() or m.isdir()):raise ValueError('unsupported archive member')
            p=root/rel
            for d in reversed(p.parents):
                if d==root or root in d.parents:
                    if d.is_symlink():raise ValueError('linked archive parent')
                    if not d.exists() and not reuse:d.mkdir(mode=0o700)
                    if not d.is_dir():raise ValueError('missing archive parent')
            if m.isdir():
                if p.is_symlink():raise ValueError('linked archive directory')
                if not p.exists() and not reuse:p.mkdir(mode=0o700)
                if not p.is_dir():raise ValueError('missing archive directory')
                continue
            if str(rel) in expected:raise ValueError('duplicate archive member')
            expected.add(str(rel))
            h=hashlib.sha256()
            with tf.extractfile(m) as inp:
                if reuse:
                    if not stat.S_ISREG(p.lstat().st_mode):raise ValueError('nonregular extracted member')
                    for b in iter(lambda:inp.read(1<<20),b''):h.update(b)
                    if sha(p)!=h.hexdigest():raise ValueError('extracted member digest differs: '+str(rel))
                else:
                    with p.open('xb') as out:
                        for b in iter(lambda:inp.read(1<<20),b''):out.write(b)
                    p.chmod(m.mode & 0o777)
    actual=set()
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('linked extracted member')
        if p.is_dir():continue
        if not p.is_file():raise ValueError('nonregular extracted member')
        actual.add(str(p.relative_to(root)))
    if actual!=expected:raise ValueError('extracted inventory differs')

record=json.loads(Path('a.json').read_text())
archive=Path('a_b8b60bce.tar')
if record['file']!=str(archive) or archive.is_symlink() or sha(archive)!=record['sha256']:
    raise ValueError('archive digest differs')
unpack(Path('t_9588661986650d29.tar'),Path('t'))
unpack(archive,Path('u'))
r=Path('u/ap/5e1d07a4/f/h/r16/receipt.json')
if sha(r)!='9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851':raise ValueError('receipt digest differs')
p=Path('u/ap/5e1d07a4/f/h/r16/rows.sqlite')
if sha(p)!='3d1d2d05bc8d3fed3048618da0c25b330f693e6394c6e2564c3007d64c050001':raise ValueError('database digest differs')
P
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p -m 700 "$BUN/c"
private_dir "$BUN/c"
export TMPDIR="$BUN/c" XDG_CACHE_HOME="$BUN/c" HF_HOME="$BUN/c"
# Keep a tmpfs skeleton at logical ancestors, including those present on the host.
# Everything beside those ancestors remains a read-only bind or a recreated link.
mounts=()
shopt -s dotglob nullglob
host_entries() {
    local parent="$1" entry
    for entry in "$parent"/*; do
        case "$entry" in /dev|/proc|/tmp) continue;; esac
        if [[ "$entry" == "$AS" || "$entry" == "$AL" ]]; then
            continue
        elif [[ "$AS/" == "$entry/"* || "$AL/" == "$entry/"* ]]; then
            mounts+=(--dir "$entry")
            if [[ -d "$entry" && ! -L "$entry" ]]; then host_entries "$entry"; fi
        elif [[ -L "$entry" ]]; then
            mounts+=(--symlink "$(readlink -- "$entry")" "$entry")
        else
            mounts+=(--ro-bind "$entry" "$entry")
        fi
    done
}
host_entries ''
mounts+=(--dev /dev --proc /proc --tmpfs /tmp --dir "$AS" --dir "$AL")
# gate.json must be created by this invocation; the preflight refused an existing file.
rc=0
"$BW_GATE" "${mounts[@]}" --ro-bind "$BUN/u" "$AS" --ro-bind "$BUN/u" "$AL" --bind "$BUN" "$BUN" --unshare-user --uid "$(id -u)" --gid "$(id -g)" \
    nice -n 19 "$PY_GATE" -B "$BUN/f.py" "$AS/ap/5e1d07a4/f/h/r16/receipt.json" --out "$BUN/gate.json" || rc=$?
# A process exit status is not a gate verdict. Require a fresh, bound JSON report.
verdict=0
python3 -B - "$rc" <<'P' || verdict=$?
import json,sys
from pathlib import Path
try:
    p=Path('gate.json')
    if p.is_symlink() or not p.is_file():raise ValueError('gate.json missing; sandbox or interpreter failed (status '+sys.argv[1]+')')
    report=json.loads(p.read_text())
    if report.get('source_receipt_sha256')!='9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851':
        raise ValueError('gate.json receipt digest differs')
    if report.get('passes') is False:sys.exit(1)
    if report.get('passes') is not True:raise ValueError('gate.json passes must be boolean')
    if sys.argv[1]!='0':raise ValueError('gate report passed but runtime exited '+sys.argv[1])
except (OSError,ValueError,TypeError,AttributeError) as exc:
    print('Gate input or runtime blocker: '+str(exc),file=sys.stderr);sys.exit(2)
P
case "$verdict" in
    0) printf 'Gate passed; independent review and separate GO remain required.\n';;
    1) printf 'Gate below threshold: STOP. Return to the orchestrator for the allocation order.\n';;
    *) exit 2;;
esac
exit "$verdict"
