"""Build a small opaque, self-checking offline login-node entrypoint."""
import ast,base64,hashlib,json,zlib
from pathlib import Path
from selection_stage import resolve
H=Path(__file__).resolve().parents[1]
metadata=(H/'evidence/derivation/empty/k/0.json').read_bytes()
# Production bytes independently recorded in orchard_q_run2.txt:12. The
# enclosing local fixture manifest is not the production manifest authority.
assert len(metadata)==1664013
assert hashlib.sha256(metadata).hexdigest()=='620a7ed162cd2f9722724be13ef09bae4123b2aba70ea3147fcc25ce91eced83'
# Read the production authority as a literal, without executing the deriver.
deriver=ast.parse((H/'tools/derive_kit_h1.py').read_text())
manifest_sha=next(ast.literal_eval(n.value) for n in deriver.body
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SEALED_MANIFEST' for t in n.targets))
config=json.loads(metadata)
inputs=json.loads((H/'evidence/fix7_selection/inputs.json').read_text())
prefix='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
catalog=json.loads((H/'build/fx/k/4aa7c6fc.json').read_text())['s1_routing']['catalog']
for item in inputs:
 assert catalog[item['sha256']]==item['logical_path']
 assert item['logical_path'].startswith(prefix+'ap/8865619b/')
 item['relative']=item['logical_path'][len(prefix+'ap/8865619b/'):]
selected,resolutions=resolve(config['staged_inputs'],inputs)
# Check the remaining production staging routes by destination, including AL.
other={}
for i,entry in enumerate(config['tars']):
 for name in entry['files']:other.setdefault(prefix+name,[]).append('tars[%d]'%i)
for i,entry in enumerate(config['extra']):
 name=entry['dest'].replace('/lustre/fsw/','/scratch/fsw/',1)
 other.setdefault(name,[]).append('extra[%d]'%i)
for i,entry in enumerate(config['staged_inputs']['directories']):
 pin=entry['manifest'];data=(H/'build/fx'/pin['file']).read_bytes()
 assert hashlib.sha256(data).hexdigest()==pin['sha256']
 for row in json.loads(data)['files']:
  other.setdefault(prefix+'ap/8865619b/'+row['destination'],[]).append('directories[%d]'%i)
assert not any(item['logical_path'] in other for item in inputs),'Additional staging route needs support'
authority=dict(manifest_sha256=manifest_sha,
 packages=[entry for (kind,_),entry in selected.items() if kind=='packages'],
 inputs=[{k:v[k] for k in ('relative','sha256','bytes')} for v in inputs])
files={'v.py':(H/'tools/selection_check.py').read_text(),
 'j.py':(H/'tools/selection_stage.py').read_text(),
 'j.json':json.dumps(authority,sort_keys=True,separators=(',',':')),
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
W=$BUN/q_f28a4d73
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
nice -n 19 "$PY_GATE" -I -B - "$W" "$BUN" "$K" <<'P' >"$W/b.log" 2>&1
import base64,hashlib,json,sys,tarfile,zlib
from pathlib import Path
w,b,k=map(Path,sys.argv[1:])
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
scope={}
exec(compile(files['j.py'],'j.py','exec'),scope)
scope['stage'](k,w,json.loads(files['j.json']))
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
inputs=()
while IFS= read -r -d '' source && IFS= read -r -d '' destination; do
 inputs+=(--ro-bind "$source" "$AS/ap/8865619b/$destination" --ro-bind "$source" "$AL/ap/8865619b/$destination")
done <"$W/m"
rc=0
"$BW_GATE" "${mounts[@]}" --dir "$AS/ap/8865619b" --dir "$AL/ap/8865619b" \
 --ro-bind "$K/k" "$AS/ap/8865619b/k" --ro-bind "$K/k" "$AL/ap/8865619b/k" \
 "${inputs[@]}" --bind "$W" "$W" --ro-bind "$W/p" "$W/p" --unshare-user --uid "$(id -u)" --gid "$(id -g)" --unshare-net --die-with-parent --new-session \
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
(H/'evidence/fix7_selection/resolution7d.json').write_text(json.dumps(dict(
 manifest_sha256=manifest_sha,manifest_source='tools/derive_kit_h1.py:140',
 package_expectations_source='evidence/derivation/empty/k/0.json; production bytes/SHA256 from evidence/fix7_selection/orchard_q_run2.txt:12',inputs=resolutions,
 other_routes_checked=dict(tars=len(config['tars']),extra=len(config['extra']),
 directories=len(config['staged_inputs']['directories']),matches=0)),sort_keys=True,indent=2)+'\n')
table=['Every selection input resolves from the source below. `K` is `/project/community/jjyeung/okh7/x_07ca49df`; `P` is `/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar` on Orchard. The sealed production manifest authenticates `K/k/0.json`; its selected package entry must exactly match the embedded expectation. Members are extracted beneath `BUN/q_f28a4d73/p` and mounted read-only at both logical roots. The full original pins remain in `inputs.json`.','',
 '| Original input | Kit-relative logical path | SHA256 | Bytes | Source |',
 '|---|---|---|---:|---|']
for row in resolutions:
 source=('K/'+row['relative'] if row['staging']=='kit' else 'P :: '+row['relative'].split('/',2)[2])
 table.append('| '+' | '.join(['`'+row['original_path']+'`','`'+row['relative']+'`','`'+row['sha256']+'`',str(row['bytes']),'`'+source+'`'])+' |')
table+=['','All 38 input occurrences are covered: 25 kit files and 13 package members. No selection input matches any additional staged file, archive, raster-directory entry, top-level tar or extra-file destination. `resolution7d.json` records the source mapping and production manifest authority.']
(H/'evidence/fix7_selection/INPUTS.md').write_text('\n'.join(table)+'\n')
print(json.dumps(dict(bytes=len(script.encode()),sha256=hashlib.sha256(script.encode()).hexdigest())))
