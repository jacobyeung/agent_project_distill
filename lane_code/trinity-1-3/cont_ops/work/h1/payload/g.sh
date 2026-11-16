#!/bin/bash
set -euo pipefail
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
: "${PY_GATE:?Set PY_GATE to the installed CPU interpreter with the pinned trainer dependencies}"
BW_GATE="${BW_GATE:-bwrap}"
[[ ! -e "$BUN/t" && ! -e "$BUN/u" ]] || { echo 'gate target exists' >&2; exit 3; }
sha256sum -c sums.txt
python3 -B r.py copy
python3 -B -c 'import hashlib,json; p=json.load(open("a.json")); h=hashlib.sha256(); f=open(p["file"],"rb"); [h.update(b) for b in iter(lambda:f.read(1<<20),b"")]; assert h.hexdigest()==p["sha256"]'
mkdir -m 700 "$BUN/t" "$BUN/u"
tar -xf t_9588661986650d29.tar -C "$BUN/t"
tar -xf "$BUN/a_b8b60bce.tar" -C "$BUN/u"
python3 -B - <<'P'
import hashlib,json
from pathlib import Path
r=Path('u/ap/5e1d07a4/f/h/r16/receipt.json')
assert hashlib.sha256(r.read_bytes()).hexdigest()=='9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851'
p=Path('u/ap/5e1d07a4/f/h/r16/rows.sqlite');h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1<<20),b''):h.update(b)
assert h.hexdigest()=='3d1d2d05bc8d3fed3048618da0c25b330f693e6394c6e2564c3007d64c050001'
P
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir "$BUN/c"
export TMPDIR="$BUN/c" XDG_CACHE_HOME="$BUN/c" HF_HOME="$BUN/c"
set +e
"$BW_GATE" --ro-bind / / --dev-bind /dev /dev --proc /proc --ro-bind "$BUN/u" "$AS" --ro-bind "$BUN/u" "$AL" --bind "$BUN" "$BUN" --unshare-user --uid "$(id -u)" --gid "$(id -g)"   nice -19 "$PY_GATE" -B "$BUN/f.py" "$AS/ap/5e1d07a4/f/h/r16/receipt.json" --out "$BUN/gate.json"
rc=$?
set -e
case "$rc" in
  0) printf 'Gate passed; independent review and separate GO remain required.\n';;
  1) printf 'Gate below threshold: STOP. Return to the orchestrator for the allocation order.\n';;
  *) printf 'Gate input or runtime blocker.\n'; exit 2;;
esac
exit "$rc"
