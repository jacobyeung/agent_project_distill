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
# payload/g.sh is the canonical gate entrypoint; package its reviewed bytes unchanged.
assert (B/'g.sh').is_file()
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
import hashlib,json,sys,os,re
from pathlib import Path
k,b=map(Path,sys.argv[1:]);go=json.loads((b/'go.json').read_text());ids=json.loads((b/'ids.json').read_text())
assert go.get('production_go_granted') is True and go.get('config_sha256')==ids['identity'] and go.get('admission_contract_sha256')==ids['contract'] and go.get('wrapper_sha256')==hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest()
assert go.get('manifest_sha256')==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
job=os.environ.get('PROOF_JOB','')
assert re.fullmatch('[1-9][0-9]*',job), 'PROOF_JOB must identify the completed CPU proof'
proof=json.loads((k/'o'/(job+'.proof.json')).read_text())
launch=json.loads((k/'k/launch.json').read_text())
assert proof.get('status')=='PASS' and proof.get('rc')==0 and proof.get('job')==job
assert proof.get('config_identity')==ids['identity'] and proof.get('contract_sha256')==ids['contract']
assert proof.get('config')==launch['config'] and proof.get('manifest_sha256')==go['manifest_sha256']
assert proof.get('wrapper_sha256')==go['wrapper_sha256'] and proof.get('cuda_visible_devices')==''
assert proof.get('effective_config_verified') is True and proof.get('first_batch_executed') is False
assert proof.get('training_executed') is False and proof.get('admission_result', dict()).get('status')=='PREPARED'
assert proof.get('prepared_seals') and proof.get('real_job_reuse') is False

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
