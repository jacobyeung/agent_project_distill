from pathlib import Path
import os,sys,shutil,json,subprocess,time,base64
J=Path.cwd();D=J/'work/build24m4z7';W=D/('exit_'+sys.argv[1]);W.mkdir();rows=[]
for version in ('before','after'):
 for mode in ('fail','stall'):
  r=W/(version+'_'+mode);r.mkdir();k=r/'kit';source=J.parent/'w24z4/out/kit_n' if version=='before' else J/'out/kit_n';shutil.copytree(source,k)
  x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=r/'n';n.mkdir();t=n/'p/q/r/checkpoint_7';t.mkdir(parents=True)
  (t/'complete.json').write_text('{"step":7}');(t/'q.bin').write_bytes(b'q'*(1<<20));(n/'q.log').write_text('last\n')
  v=json.loads((k/'k/y.json').read_text());v=json.loads(base64.b64decode(v['payload']))
  values={key+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+key+'.j41'+f'.part{i:02d}-of-04' for key in v['objects'].values() for i in range(4)}
  p=x/'n_s/sess_41.json';p.write_text(json.dumps(values));p.chmod(0o600)
  b=r/'bin';b.mkdir();(b/'python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(D/'runtime.py')+' "$@"\n');(b/'python3').chmod(0o700)
  env={**os.environ,'TEST_W':str(r),'TEST_X':str(x),'FAKE_SINK':str(r/'sink'),'STRICT_FAIL':mode,'STRICT_SELECT':'ckstop','ROOT':str(k),'N':str(n),'SLURM_JOB_ID':'41','PATH':str(b)+':'+os.environ['PATH']}
  with (r/'shell.log').open('w') as f:p=subprocess.run(['bash','-c','set -euo pipefail; source "$ROOT/b/pc.sh"; exit 0'],env=env,stdout=f,stderr=f,timeout=30)
  done=(n/'live_spool/state/gcs_o.done').exists()
  assert p.returncode==0 and done==(version=='after'),(version,mode,p.returncode,done)
  rows.append(dict(version=version,mode=mode,returncode=p.returncode,archive_receipt=done,source='actual pc.sh EXIT finalizer'))
(W/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
