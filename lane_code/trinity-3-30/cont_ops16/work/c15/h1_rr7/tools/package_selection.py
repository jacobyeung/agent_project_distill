"""Build a small opaque, self-checking offline login-node entrypoint."""
import base64,hashlib,json,zlib
from pathlib import Path
H=Path(__file__).resolve().parents[1]
files={'v.py':(H/'tools/selection_check.py').read_text(),
 'a.json':(H/'evidence/derivation/d0/k/pool_selection.json').read_text(),
 'b.json':(H/'payload/d_f232d4160d75b582.json').read_text(),
 'c.json':(H/'payload/7.json').read_text(),'f.json':(H/'build/fx/k/4aa7c6fc.json').read_text()}
raw=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
blob=base64.b64encode(zlib.compress(raw,9)).decode();checksum=hashlib.sha256(raw).hexdigest()
script=r'''#!/bin/bash
set -Eeuo pipefail
umask 077
export TZ=UTC
O=/project/community/jjyeung/okh7
BUN=$O/i_1be16f28
K=$O/x_07ca49df
W=$BUN/q_7b62108a
private_dir() {
 [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
  printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2; exit 3;
 }
}
private_dir "$O"
private_dir "$BUN"
private_dir "$K"
[[ ! -e "$W" && ! -L "$W" ]] || { echo 'Output already exists.' >&2; exit 2; }
PY_GATE=${PY_GATE:-/project/community/jjyeung/latency/envs/fit/bin/python3}
BW_GATE=${BW_GATE:-bwrap}
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mkdir -m 700 "$W"
mkdir -m 700 "$W/c"
export TMPDIR="$W/c" XDG_CACHE_HOME="$W/c" HF_HOME="$W/c"
# Bootstrap uses only the standard library, authenticates before extraction, and never overwrites.
nice -n 19 "$PY_GATE" -I -B - "$W" "$BUN" <<'P' >"$W/b.log" 2>&1
import base64,hashlib,json,sys,tarfile,zlib
from pathlib import Path
w,b=map(Path,sys.argv[1:])
data=zlib.decompress(base64.b64decode('@BLOB@'))
if hashlib.sha256(data).hexdigest()!='@SHA@':raise ValueError('Embedded bytes differ')
files=json.loads(data)
for name,value in files.items():
 if Path(name).name!=name:raise ValueError('Unsafe member')
 with (w/name).open('x') as f:f.write(value)
code=json.loads(files['c.json']);archive=b/Path(code['archive']['path']).name
h=hashlib.sha256()
with archive.open('rb') as f:
 for block in iter(lambda:f.read(1<<20),b''):h.update(block)
if archive.is_symlink() or h.hexdigest()!=code['archive']['sha256']:raise ValueError('Archive differs')
tree=w/'t';tree.mkdir(mode=0o700)
seen=set()
with tarfile.open(archive) as tf:
 for m in tf:
  rel=Path(m.name)
  if not m.isfile() or rel.is_absolute() or '..' in rel.parts or m.name in seen or m.name not in code['files'] or m.size>16000000:raise ValueError('Archive member differs')
  data=tf.extractfile(m).read()
  if hashlib.sha256(data).hexdigest()!=code['files'][m.name]:raise ValueError('Member digest differs')
  target=tree/rel;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(data)
  seen.add(m.name)
if seen!=set(code['files']):raise ValueError('Archive inventory differs')
P
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
mounts=()
shopt -s dotglob nullglob
host_entries() {
 local parent="$1" entry
 for entry in "$parent"/*; do
  case "$entry" in /dev|/proc|/tmp) continue;; esac
  if [[ "$entry" == "$AS" || "$entry" == "$AL" ]]; then continue
  elif [[ "$AS/" == "$entry/"* || "$AL/" == "$entry/"* ]]; then
   mounts+=(--dir "$entry")
   if [[ -d "$entry" && ! -L "$entry" ]]; then host_entries "$entry"; fi
  elif [[ -L "$entry" ]]; then mounts+=(--symlink "$(readlink -- "$entry")" "$entry")
  else mounts+=(--ro-bind "$entry" "$entry")
  fi
 done
}
host_entries ''
mounts+=(--dev /dev --proc /proc --tmpfs /tmp --dir "$AS" --dir "$AL")
rc=0
"$BW_GATE" "${mounts[@]}" --ro-bind "$K" "$AS/ap/8865619b" --ro-bind "$K" "$AL/ap/8865619b" \
 --bind "$W" "$W" --unshare-user --uid "$(id -u)" --gid "$(id -g)" --unshare-net --die-with-parent --new-session \
 nice -n 19 "$PY_GATE" -I -B "$W/v.py" --kit "$AS/ap/8865619b" --tree "$W/t" --records "$W" --out "$W/o" >"$W/r.log" 2>&1 || rc=$?
"$PY_GATE" -I -B - "$W" "$rc" <<'P'
import hashlib,json,sys
from pathlib import Path
w=Path(sys.argv[1]);q=json.loads((w/'o/q.json').read_text())
if int(sys.argv[2])!=0 or q.get('status')!='EQUAL' or q.get('regenerated') is not True:raise SystemExit('Comparison refused; inspect private records.')
if hashlib.sha256((w/'o/r.json').read_bytes()).hexdigest()!=q.get('selection_sha256'):raise SystemExit('Output differs.')
print('EQUAL; review private records before deriving.')
P
'''.replace('@BLOB@',blob).replace('@SHA@',checksum)
assert len(script.encode())<1_000_000
(H/'build/q.sh').write_text(script);(H/'build/q.sh').chmod(0o700)
# Local invocation uses precisely the same embedded records.
r=H/'evidence/fix7_selection/records';r.mkdir(exist_ok=True)
for n,v in files.items():(r/n).write_text(v)
print(json.dumps(dict(bytes=len(script.encode()),sha256=hashlib.sha256(script.encode()).hexdigest())))
