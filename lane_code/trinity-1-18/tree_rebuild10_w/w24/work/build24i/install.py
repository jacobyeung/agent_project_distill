from pathlib import Path
import sys,base64,json,hashlib
L=Path(__file__).resolve().parents[2];D=L/'work/build24i'
sys.path.insert(0,str(L/'work/build24'));import joblib as J

def replace(p,raw):
 old=L/'attic/build24i'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and not old.exists():p.rename(old)
 p.write_bytes(raw.encode() if isinstance(raw,str) else raw)

def capsule(raw):
 if not isinstance(raw,bytes):raw=(json.dumps(raw,sort_keys=True,indent=2)+'\n').encode()
 return json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode()

for k in (L/'work/build24/kits/n',L/'out/kit_n_go'):
 h=(k/'b/h.py').read_text();a=h.index('control=load(k/');h=h[:a]+'''# Host evidence is pinned before the prepared config is published.
cfg['r1_training']['host_receipt']=write(r/'hr.json',host)
from rv import sync_preparation
sync_preparation(cfg,r,'ph.json')
if identity(cfg)!=value:raise ValueError('R1_HOST_IDENTITY_DIFFERS')
write(sys.argv[2],cfg)
'''
 replace(k/'b/h.py',h)
 replace(k/'b/rv.py',(D/'rv.py').read_bytes())
 c=J.load(k/'k/a.json');c.pop('review',None);c['review_wait_seconds']=7200;replace(k/'k/a.json',capsule(c))
 s=(k/'b/z.py').read_text();a=s.index("    review=load(kit/'k/a.json').get('review')");b=s.index("    cfgpin=write(root/'n.json'",a);s=s[:a]+s[b:];replace(k/'b/z.py',s)
 s=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
 marker='BW+=(--bind "$Q_ROOT" "$Q_NS" --setenv TK_JOB_START "${TK_JOB_START:?}")'
 s=s.replace(marker,marker+'\nQ_LIVE=$(/usr/bin/python3 -B -I -s "$Q_KIT/b/rv.py" --live "$Q_ROOT" "${SLURM_JOB_ID:?}")\nBW+=(--bind "$Q_LIVE" "$Q_LIVE")')
 marker='if [[ "$rc" == 0 ]]; then\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8'
 new='''if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
"${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "${SLURM_JOB_ID:?}" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rv.log"
rc=${PIPESTATUS[0]}
fi
if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8'''
 assert marker in s;s=s.replace(marker,new);replace(k/'k/j.json',capsule(s.encode()))
 s=(k/'b/sr.py').read_text();marker="            if any(v.endswith(b'/b/u.py') for v in args)"
 assert marker in s;s=s.replace(marker,"            if any(v.endswith(b'/b/rv.py') for v in args):\n                os.kill(child,signal.SIGUSR1);newly.append(child)\n            elif any(v.endswith(b'/b/u.py') for v in args)")
 replace(k/'b/sr.py',s)
print('review wait installed; host receipt still requires a genuine producer')
