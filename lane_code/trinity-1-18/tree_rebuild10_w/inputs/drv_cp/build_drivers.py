from pathlib import Path
import hashlib,shutil,json,tarfile,re,zlib
from packet_config import PINS, ARCHIVE, MEMBERS, BINDING, SNAP, fixture, render, pending_script
W=Path(__file__).resolve().parent
EX=fixture()
H1=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1')
HEADER='''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_@STORE@
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_@STORE@
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\\n' '@OUTER@' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
'''
def script(n,s):
 p=W/n;p.write_text(render(HEADER+s));p.chmod(0o700)
def inline(n,body):script(n,'private "$BUN"\npacket\npython3 -B - <<\'PYCODE\'\n'+body+'\nPYCODE\n')
def background(n,helper,tag,pre=''):
 body=(W/helper).read_text()
 script(n,'private "$BUN"\npacket\n'+pre+f'''fresh "$BUN/{tag}"
mkdir -m 700 "$BUN/{tag}"
cat > "$BUN/{tag}/r.py" <<'PYCODE'
'''+body+f'''\nPYCODE
cat > "$BUN/{tag}/r.sh" <<'SHCODE'
#!/bin/bash
set +x
set -uo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_@STORE@
python3 -B "$BUN/{tag}/r.py"
rc=$?
printf '%s\\n' "$rc" > "$BUN/{tag}/rc"
exit "$rc"
SHCODE
nohup nice -n 19 ionice -c 3 bash "$BUN/{tag}/r.sh" > "$BUN/{tag}/o.log" 2>&1 < /dev/null &
printf '%s\\n' "$!" > "$BUN/{tag}/pid"
echo "STARTED {tag}; pid $!; poll once per minute"
''')
def poll(n,tag,post=''):
 script(n,f'''private "$BUN"
packet
test -f "$BUN/{tag}/pid"
if [[ ! -f "$BUN/{tag}/rc" ]]; then
  if kill -0 "$(cat "$BUN/{tag}/pid")" 2>/dev/null; then echo 'RUNNING {tag}'; else echo 'STOPPED without rc; do not relaunch'; fi
  tail -n 12 "$BUN/{tag}/o.log"
  exit 0
fi
rc=$(cat "$BUN/{tag}/rc")
tail -n 30 "$BUN/{tag}/o.log"
echo "{tag} rc=$rc"
[[ "$rc" == 0 ]] || exit 4
'''+post)
# u1 consumes only script input; upload_build constructs a heredoc transport.
script('u1.sh','''fresh "$BUN"
mkdir -m 700 "$BUN"
echo 'CREATED i_@STORE@ mode 700; now run the generated u2.sh'
''')
script('u3.sh','''private "$BUN"
packet
python3 -B - <<'PYCODE'
import hashlib,tarfile,re,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_@STORE@');archive=b/'p.tar'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='@OUTER@','outer SHA differs'
with tarfile.open(archive) as tf:
 members=tf.getmembers();assert len(members)==@MEMBERS@,'member count differs'
 names=set()
 for m in members:
  p=Path(m.name)
  assert m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name not in names and m.size<32000000,'unsafe member'
  names.add(m.name)
 assert 'sums.txt' in names
 sums=tf.extractfile('sums.txt').read().decode()
 pins={}
 for line in sums.splitlines():
  h,n=line.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',h) and n in names and n not in pins
  pins[n]=h
 assert set(pins)==names-{'sums.txt'},'inventory differs'
 for m in members:
  data=tf.extractfile(m).read()
  if m.name!='sums.txt':assert hashlib.sha256(data).hexdigest()==pins[m.name]
  p=b/m.name;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  with p.open('xb') as f:f.write(data)
  p.chmod(0o600)
print('PASS outer SHA; @MEMBERS@ members; sums.txt exact inventory; files 0600')
PYCODE
''')
# Keep local fixture copies inside the work directory.
# Local fixtures are read from H1 only by the bounded CPU tests.
(W/'PACKET_PINS.json').write_text(json.dumps(PINS,sort_keys=True,indent=2)+'\n')
(W/'PACKET_PIN_SOURCES.json').write_text(json.dumps(dict(
 archive_sha256=PINS['outer'],config_identity=PINS['identity'],
 operator_sha256=hashlib.sha256((SNAP/'OPERATOR.json').read_bytes()).hexdigest(),
 pins_source='Supplied archive SHA256 + CONT4_INVENTORY after pins + OPERATOR.json + authenticated archive sums.txt; outer SHA256SUMS is not used',
 sums_sha256=hashlib.sha256(MEMBERS['sums.txt']).hexdigest(),
 gate_sha256=hashlib.sha256(MEMBERS['s.sh']).hexdigest(),
 wrapper_sha256=hashlib.sha256(MEMBERS['jb.sh']).hexdigest(),
 config_file_sha256=hashlib.sha256(MEMBERS['config.json']).hexdigest(),
 authority_validator_sha256=hashlib.sha256(MEMBERS['r4.py']).hexdigest(),
 authority_sha_source='Deployed kit SHA256SUMS.txt entry k/4.json; exact fields checked by the archive-pinned r4.py validator',
 members=len(MEMBERS)),sort_keys=True,indent=2)+'\n')

(W/'CERTIFICATE_REQUIREMENTS.json').write_text(json.dumps(dict(
 status='REVIEW_REQUIRED',config_identity=PINS['identity'],operator_archive_sha256=PINS['outer'],
 bundle=PINS['bundle'],kit=PINS['kit'],run_key=PINS['run'],
 exemption_record='events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md',
 exemption_sha256='22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720',
 external=[dict(path=PINS['bundle']+'/'+n,sha256=hashlib.sha256(raw).hexdigest()) for n,raw in sorted(MEMBERS.items())]
 ),sort_keys=True,indent=2)+'\n')
# H1's exact changed-entry staging verifier, embedded into ev1 background body.
assert (W/'staging_check.py').is_file()
import base64
# All bytes travel as stdin to one bash -s invocation; no second stdin consumer.
archive=ARCHIVE
assert hashlib.sha256(archive).hexdigest()==PINS['outer']
u3=(W/'u3.sh').read_text()[len(render(HEADER)):]
script('u1.sh','''fresh "$BUN"
mkdir -m 700 "$BUN"
set -o noclobber
base64 -d > "$BUN/p.tar" <<'PAYLOAD_PACKET_C'
'''+base64.encodebytes(archive).decode()+'''PAYLOAD_PACKET_C
'''+u3)
script('q1.sh','''private "$BUN"
packet
PY_GATE=@CPU_PYTHON@
[[ -x "$PY_GATE" ]] || { echo 'REFUSED: authenticated H1 CPU environment missing'; exit 4; }
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
"$PY_GATE" -I -B - <<'PYCODE'
'''+(W/'selection_runtime.py').read_text()+'\n'+(W/'q_check.py').read_text()+'\nPYCODE\n')
body=(W/'review_policy.py').read_text()+'\n'+(W/'evidence_body.py').read_text().replace("if __name__=='__main__':",'STAGING_VERIFY='+repr((W/'staging_check.py').read_text())+"\nif __name__=='__main__':")
(W/'evidence_embedded.py').write_text(render(body))
background('ev1.sh','evidence_embedded.py','e0','test -f "$BUN/r1.json" || { echo "PENDING: run rv1.sh after the twelve-review final-packet chain"; exit 4; }\nfresh "$BUN/e"\n')
poll('evp1.sh','e0')
background('dv1.sh','derive_body.py','d0','fresh "$KH"\ntest "$(cat "$BUN/e0/rc")" = 0\n')
authority=MEMBERS['r4.py'].decode()+'\n'+(W/'authority_body.py').read_text()
(W/'authority_check.py').write_text(render(authority))
poll('dvp1.sh','d0', '''cat "$BUN/compare.json"
python3 -B - <<'PYCODE'
'''+authority+'''
import stat
from pathlib import Path
k=Path('@KIT@')
check_authority(k)
assert (k/'b').is_dir() and not (k/'b').is_symlink(), 'sealed code directory missing'
for p in [k/'b', *(k/'b').rglob('*')]:
 assert not p.is_symlink() and p.name!='__pycache__', 'linked code or bytecode'
 if p.is_dir():assert stat.S_IMODE(p.stat().st_mode)==0o500, 'code directory must be 0500'
print('PASS b/ and code subdirectories 0500; no __pycache__')
PYCODE
''')
(W/'e.txt').write_bytes((EX/'e.txt').read_bytes())
p=W/'L1_mint.sh';p.write_text(render('''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
[[ $(hostname -s) == trinity-3-30 ]] || { echo 'REFUSED: run on trinity-3-30'; exit 3; }
W=/scratch/jjyeung/orch_n30/r1_ops/work/drv_cp
cd "$W"
/scratch/jjyeung/envs/p1cpu/bin/python -B -c 'import packet_config; print("PASS frozen packet "+packet_config.PINS["archive"])'
OUT=$W/sess_@RUN@_32337655.json
[[ ! -e "$W/mint_@RUN@_32337655.private.log" && ! -L "$W/mint_@RUN@_32337655.private.log" && ! -e "$OUT" && ! -L "$OUT" && ! -e "$W/mint_@RUN@_32337655.started" && ! -L "$W/mint_@RUN@_32337655.started" ]] || { echo 'REFUSED: existing mint attempt; no retry'; exit 3; }
(set -o noclobber; : > "$W/mint_@RUN@_32337655.started")
# The H1 helper uses authenticated GCS create-only resumable sessions.
if ! /scratch/jjyeung/envs/p1cpu/bin/python -I "$W/mint_fresh.py" "$OUT" 8865619b @RUN@ m400 m600 mstop mstopB mstopC > "$W/mint_@RUN@_32337655.private.log" 2>&1; then
 echo 'FAILED mint; inspect locally without exposing capabilities; no automatic retry' >&2; exit 4
fi
chmod 600 "$OUT"
/scratch/jjyeung/envs/p1cpu/bin/python -I - "$OUT" "$W/e.txt" <<'PYCODE'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text());want=set(Path(sys.argv[2]).read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
print('PASS 20 fresh create-only sessions; mode 0600; URI contents withheld')
PYCODE
'''));p.chmod(0o700)
inline('scan1.sh',(W/'scan_body.py').read_text())
