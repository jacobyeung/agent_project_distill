from pathlib import Path
import hashlib,shutil,json,tarfile,re,zlib
from packet_config import PINS, ARCHIVE, MEMBERS, BINDING, fixture, render, pending_script
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
assert (W/'fixture_h').is_dir(), 'Local H1 fixture is required; no automatic bulk copy'
(W/'PACKET_PINS.json').write_text(json.dumps(PINS,sort_keys=True,indent=2)+'\n')
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
base64 -d > "$BUN/p.tar" <<'PAYLOAD_FINAL_R1P'
'''+base64.encodebytes(archive).decode()+'''PAYLOAD_FINAL_R1P
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
background('ev1.sh','evidence_embedded.py','e0','test -f "$BUN/r1.json" || { echo "PENDING: run rv1.sh after the eight-review final-packet chain"; exit 4; }\nfresh "$BUN/e"\n')
poll('evp1.sh','e0')
background('dv1.sh','derive_body.py','d0','fresh "$KH"\ntest "$(cat "$BUN/e0/rc")" = 0\n')
poll('dvp1.sh','d0','cat "$BUN/compare.json"\n')
(W/'e.txt').write_bytes((EX/'e.txt').read_bytes())
proof=(EX/('p_'+PINS['run']+'.sh')).read_text()
encoded=re.search(r"base64.b64decode\('([^']+)'\)",proof).group(1)
decoded=zlib.decompress(base64.b64decode(encoded))
assert hashlib.sha256(decoded).hexdigest() in proof
(W/'proof_decoded.py').write_bytes(decoded)
p=W/'L1_mint.sh';p.write_text(render('''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
[[ $(hostname -s) == trinity-1-3 ]] || { echo 'REFUSED: run on trinity-1-3'; exit 3; }
W=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5
cd "$W"
/scratch/jjyeung/envs/p1cpu/bin/python -B -c 'import packet_config; print("PASS frozen packet "+packet_config.PINS["archive"])'
OUT=$W/sess_@RUN@.json
[[ ! -e "$W/mint_@RUN@.private.log" && ! -L "$W/mint_@RUN@.private.log" && ! -e "$OUT" && ! -L "$OUT" && ! -e "$W/mint_@RUN@.started" && ! -L "$W/mint_@RUN@.started" ]] || { echo 'REFUSED: existing mint attempt; no retry'; exit 3; }
(set -o noclobber; : > "$W/mint_@RUN@.started")
# The H1 helper uses authenticated GCS create-only resumable sessions.
if ! /scratch/jjyeung/envs/p1cpu/bin/python -I "$W/mint_fresh.py" "$OUT" 8865619b @RUN@ m100 m200 mstop mstopB mstopC > "$W/mint_@RUN@.private.log" 2>&1; then
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
script('pr1.sh','''PARTITION=${1:-general}
[[ $# -le 1 && ( "$PARTITION" == general || "$PARTITION" == advanced ) ]] || { echo 'REFUSED: partition must be general or advanced'; exit 4; }
private "$BUN"
packet
private "$KH"
exec 9> "$BUN/p0.lock"
flock -n 9 || { echo 'REFUSED: concurrent proof submission'; exit 4; }
fresh "$BUN/submission.started"
fresh "$BUN/job.id"
fresh "$BUN/a.json"
# Show the entire queue once, then use exactly that snapshot for the guard.
Q=$(squeue -h -o '%i|%j|%P|%T')
printf '%s\\n' 'JOBID|NAME|PARTITION|STATE' "$Q"
while IFS='|' read -r jid name part state; do
 [[ -n "$jid" ]] || continue
 if [[ "$name" == a15_cot_ap@RUN@ ]]; then echo 'REFUSED: job name already queued'; exit 4; fi
 part=${part//\\*/}
 if [[ ( "$name" == a15_cot_ap* || "$name" == jjy_* ) && ",$part," == *,"$PARTITION",* ]]; then echo "REFUSED: matching job on $PARTITION: $jid $state"; exit 4; fi
done <<< "$Q"
python3 -B - "$KH" "$BUN" "$PARTITION" <<'PYCODE'
import hashlib,json,stat,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:3]);partition=sys.argv[3];load=lambda p:json.loads(p.read_text())
assert (b/'d0/rc').read_text().strip()=='0' and load(b/'compare.json')['status']=='READY'
auth=load(k/'k/4.json');assert partition in auth['allowed_partitions'] and auth['modes']==['p'] and auth['production_go_granted'] is False
assert auth['gpu_cap']==4 and auth['max_parallel_jobs']==1 and auth['new_gpus']['p']==0
cert=load(k/'ANON_OK.json');assert cert['status']=='CLEAN' and cert['hits']==0 and cert.get('reviewer')
assert cert.get('config_identity')=='@IDENTITY@' and cert.get('operator_archive_sha256')=='@OUTER@'
assert cert.get('scan_record_sha256') and cert.get('exemption_sha256')=='22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720'
assert cert['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
for entry in cert.get('external',[]):assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256']
s=k/'sess.json';assert not s.is_symlink() and stat.S_IMODE(s.stat().st_mode)==0o600
sessions=load(s);assert set(sessions)==set((b/'e.txt').read_text().split()) and len(sessions)==20
assert len(set(sessions.values()))==20 and all(x.startswith('https://storage.googleapis.com/upload/') for x in sessions.values())
sys.path.insert(0,str(k/'b'));import a
a.main(k)
print('PASS sealed kit, independent scan, evidence, and 20 private sessions')
PYCODE
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
mkdir -p -m 700 "$KH/o"
# A timeout or uncertain sbatch result must be reconciled manually; never resubmit.
(set -o noclobber; date -u +%FT%TZ > "$BUN/submission.started")
printf '%s\\n' "TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap@RUN@ -A mt01 -p $PARTITION -N1 --ntasks=1 -c 48 --mem=800G -t 06:00:00 --no-requeue -o $KH/o/%j.out -e $KH/o/%j.err $BUN/p_@RUN@.sh $BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap@RUN@ -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 06:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" "$BUN/p_@RUN@.sh" "$BUN/a.json" > "$BUN/sbatch.out"
answer=$(cat "$BUN/sbatch.out")
[[ "$answer" =~ ^[0-9]+(\\;[A-Za-z0-9_-]+)?$ ]] || { echo 'UNCERTAIN: inspect queue; do not resubmit'; exit 4; }
job=${answer%%;*}
printf '%s\\n' "$job" > "$BUN/job.id"
echo "SUBMITTED job_id=$job; production GO remains false"
''')
script('pm1.sh','''private "$BUN"
packet
private "$KH"
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[0-9]+$ ]] || { echo 'REFUSED: invalid job id'; exit 4; }
squeue -u "$USER" -o '%i %j %P %T %M %R'
python3 -B - "$KH" "$job" <<'PYCODE'
import json,re,sys
from pathlib import Path
k=Path(sys.argv[1]);job=sys.argv[2]
def redact(s):
 s=re.sub(r'https?://[^\\s<>\\"\\x27]+','[URL WITHHELD]',s)
 s=re.sub(r'(?i)Bearer +[^ ,]+','Bearer [WITHHELD]',s)
 s=re.sub(r'ya29[.][A-Za-z0-9._-]+','[TOKEN WITHHELD]',s)
 return re.sub(r'(?i)(authorization|access_token|refresh_token|upload_id|password|secret|token)[\\"\\x27 \t]*[:=][\\"\\x27 \t]*[^\\s,}]+',r'\\1=[WITHHELD]',s)
for suffix in ('err','steps','w.steps'):
 p=k/'o'/(job+'.'+suffix);print(p.name)
 if not p.is_file():print('NOT_YET');continue
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-16384));raw=f.read()
 print(redact('\\n'.join(raw.decode(errors='replace').splitlines()[-20:])))
p=k/'o'/(job+'.proof.json')
if not p.is_file():print(p.name,'NOT_YET')
else:
 d=json.loads(p.read_text());print(p.name);print(redact(json.dumps(d,sort_keys=True,indent=2)))
b=Path('/project/community/jjyeung/okh7/i_@STORE@')
t=b/'training.job.id'
if t.exists():
 assert not t.is_symlink()
 training=t.read_text().strip();assert re.fullmatch('[1-9][0-9]*',training) and training not in (job,'170956')
 print('CANARY training_job='+training+' proof_job='+job)
 for suffix in ('err','steps','w.steps'):
  p=k/'o'/(training+'.'+suffix);print(p.name)
  if not p.is_file():print('NOT_YET');continue
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-16384));raw=f.read()
  print(redact(raw.decode(errors='replace')))
 record=b/'training.json'
 if record.is_file():print(redact(record.read_text()))
elif (b/'training.started').exists():print('UNCERTAIN training attempt; no training.job.id; inspect training.sbatch.out; do not resubmit')
PYCODE
''')

# Gate placeholders are inert until independent artifacts arrive. Never copy capabilities.
for name in ('rv1.sh','sc1.sh','si1.sh'):
 path=W/name
 if not path.exists():
  path.write_text(pending_script(name));path.chmod(0o600 if name=='si1.sh' else 0o700)
# Every alternate submission entry uses the same S2-on proof-2 lock and marker.
(W/'pr2.sh').write_text((W/'pr1.sh').read_text());(W/'pr2.sh').chmod(0o700)
for name in ('wait_general.sh','wait_general2.sh'):
 (W/name).write_text('#!/bin/bash\nset +x\necho "REFUSED: use pr1.sh general once after the queue clears; no automatic submission loop" >&2\nexit 4\n')
for name in ('pq.sh','qcheck.sh'):
 script(name, 'squeue -u "$USER" -o \'%i|%j|%P|%T|%M|%R\'\n')
# Migration uses old identity only as an explicit source guard.
collision={BINDING['deployed_database']['path']:BINDING['database_sha256']}
prefix=str(Path(BINDING['deployed_database']['path']).parent)
for n in BINDING['record_files']+['s.json']:collision[prefix+'/'+n]=hashlib.sha256(MEMBERS[n]).hexdigest()
for n,item in BINDING['unit_binding']['artifacts'].items():collision[item['path']]=item['sha256']
(W/'collision_pins.json').write_text(json.dumps(collision,sort_keys=True,indent=2)+'\n')
# m0.sh and m0.v1.sh already ran; preserve their operator-reviewed bytes.
canary=(W/'canary_submit.tpl').read_text()
for token,member in (('GATE_SHA','s.sh'),('SUMS_SHA','sums.txt'),('WRAPPER_SHA','jb.sh')):
 canary=canary.replace('@'+token+'@',hashlib.sha256(MEMBERS[member]).hexdigest())
p=W/'go_submit_canary_9dd2fbb7.sh';p.write_text(render(canary));p.chmod(0o700)
print('PASS drivers built from frozen packet; '+PINS['archive']+'; '+PINS['outer'])
