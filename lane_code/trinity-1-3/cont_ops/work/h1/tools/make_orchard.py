import base64,hashlib,io,json,tarfile
from pathlib import Path
from private_paths import CHECK
H=Path(__file__).resolve().parents[1];ids=json.loads((H/'ids.json').read_text());tok=ids['tokens'];B=H/'payload';O='/project/community/jjyeung/okh7';IN=O+'/i_'+tok['store'];KH=O+'/x_'+tok['kit'];RS=O+'/r/'+tok['root']
assert ids['job_name']=='a15_cot_ap'+tok['job']
for src,n in [('tools/derive_kit_h1.py','d.py'),('tools/staging_check.py','v.py'),('tools/orchard_records.py','r.py'),('ids.json','ids.json'),('EXPORT_OBJECTS.txt','names.txt')]: (B/n).write_bytes((H/src).read_bytes())
g=(H/'source/code/rows/faithful_gate.py').read_text().replace("parents[1]/'tree'","parent/'t'")
g=g.replace('import json','import json\nimport hashlib\nimport sqlite3').replace('(ValueError,KeyError,FileNotFoundError)', '(ValueError,KeyError,OSError,sqlite3.Error)')
g=g.replace("    text=json.dumps(result", "    result['source_receipt_sha256']=hashlib.sha256(Path(a.rows).read_bytes()).hexdigest()\n    text=json.dumps(result")
(B/'f.py').write_text(g)
common=f'''#!/bin/bash
set -euo pipefail
export TZ=UTC
{CHECK}BUN={IN}
KH={KH}
'''
(B/'o.sh').write_text(common+f'''private_dir "$BUN"
[[ ! -e "$KH" && ! -e {RS} && ! -e "$BUN/p" ]] || {{ echo 'target exists' >&2; exit 3; }}
cd "$BUN"
sha256sum -c sums.txt
python3 -B r.py prepare
python3 -B r.py stage
''')
# The routing receipt and rows stay byte-identical. A private read-only namespace maps their logical paths.
(B/'g.sh').write_text(common+f'''private_dir "$BUN"
cd "$BUN"
: "${{PY_GATE:?Set PY_GATE to the installed CPU interpreter with the pinned trainer dependencies}}"
BW_GATE="${{BW_GATE:-bwrap}}"
[[ ! -e "$BUN/t" && ! -e "$BUN/u" ]] || {{ echo 'gate target exists' >&2; exit 3; }}
sha256sum -c sums.txt
python3 -B r.py copy
python3 -B -c 'import hashlib,json; p=json.load(open("a.json")); h=hashlib.sha256(); f=open(p["file"],"rb"); [h.update(b) for b in iter(lambda:f.read(1<<20),b"")]; assert h.hexdigest()==p["sha256"]'
mkdir -m 700 "$BUN/t" "$BUN/u"
tar -xf {ids['trainer']['file']} -C "$BUN/t"
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
"$BW_GATE" --ro-bind / / --dev-bind /dev /dev --proc /proc --ro-bind "$BUN/u" "$AS" --ro-bind "$BUN/u" "$AL" --bind "$BUN" "$BUN" --unshare-user --uid "$(id -u)" --gid "$(id -g)" \
  nice -19 "$PY_GATE" -B "$BUN/f.py" "$AS/ap/5e1d07a4/f/h/r16/receipt.json" --out "$BUN/gate.json"
rc=$?
set -e
case "$rc" in
  0) printf 'Gate passed; independent review and separate GO remain required.\\n';;
  1) printf 'Gate below threshold: STOP. Return to the orchestrator for the allocation order.\\n';;
  *) printf 'Gate input or runtime blocker.\\n'; exit 2;;
esac
exit "$rc"
''')
(B/'z.sh').write_text(common+'''private_dir "$BUN"
cd "$BUN"
sha256sum -c sums.txt
case "${1:-}" in
 derive) python3 -B r.py final ;;
 certify) python3 -B r.py certify ;;
 *) echo 'Use derive after independent review; certify after the final content scan.' >&2; exit 2 ;;
esac
''')
(B/'s.sh').write_text(common+f'''private_dir "$BUN"
private_dir "$KH"
cd "$BUN"
sha256sum -c sums.txt
# The separate approval record is supplied by the operator, never inferred from 4.json.
python3 -B - "$KH" "$BUN" <<'P'
import hashlib,json,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:]);go=json.loads((b/'go.json').read_text());ids=json.loads((b/'ids.json').read_text())
assert go.get('production_go_granted') is True and go.get('config_sha256')==ids['identity'] and go.get('admission_contract_sha256')==ids['contract'] and go.get('wrapper_sha256')==hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest()
assert go.get('manifest_sha256')==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
sys.path.insert(0,str(k/'b'));import a;a.main(k)
P
TZ=UTC env -u TK_JOB_START sbatch -J {ids['job_name']} -o /dev/null -e "$KH/o/%j.err" \
  -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 --signal=B:USR1@3600 --no-requeue "$BUN/jb.sh"
''')
# No capabilities are bundled. Drafts are deliberately unable to authorize production.
(B/'go.template.json').write_text(json.dumps(dict(production_go_granted=False,job_name=ids['job_name'],config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],wrapper_sha256=hashlib.sha256((B/'jb.sh').read_bytes()).hexdigest(),manifest_sha256=None),sort_keys=True)+'\n')
# Frozen upload archive and checksums. All files are below 20 MB.
files=sorted(p for p in B.iterdir() if p.is_file() and p.name!='sums.txt')
(B/'sums.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files if p.name not in ('review.json','staging.json')))
files.append(B/'sums.txt');dst=H/'build/upload.tar'
with tarfile.open(dst,'w') as tf:
 for p in sorted(files):
  m=tarfile.TarInfo(p.name);m.size=p.stat().st_size;m.mode=0o600;tf.addfile(m,io.BytesIO(p.read_bytes()))
sha=hashlib.sha256(dst.read_bytes()).hexdigest();name='p_'+sha[:16]+'.tar';(H/'build'/name).write_bytes(dst.read_bytes())
script=common+f'''[[ ! -e "$BUN" && ! -e "$KH" && ! -e {RS} ]] || {{ echo 'target exists' >&2; exit 3; }}
mkdir -m 700 "$BUN"
private_dir "$BUN"
base64 -d > "$BUN/{name}" <<'B64'
'''+base64.encodebytes(dst.read_bytes()).decode()+f'''B64
[[ "$(sha256sum < "$BUN/{name}" | cut -d' ' -f1)" == {sha} ]] || exit 3
tar -xf "$BUN/{name}" -C "$BUN"
cd "$BUN"
sha256sum -c sums.txt
bash o.sh
'''
(H/'orch_h1.sh').write_text(script);(H/'fin_h1.sh').write_text(common+'private_dir "$BUN"\ncd "$BUN"\nbash z.sh "$@"\n')
(H/'UPLOAD.json').write_text(json.dumps(dict(archive=name,sha256=sha,bytes=dst.stat().st_size,script_bytes=len(script.encode()),destination=IN,files=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)]),indent=2)+'\n')
print('Upload archive',dst.stat().st_size,'script',len(script.encode()))
