from pathlib import Path
import json,subprocess,sys,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';R=L/'work/build24f/rehearsal3'
args=['--ro-bind' if x=='--bind' else x for x in json.loads((R/'VIEW.json').read_text())]
args+=['--bind',str(D),str(D),'--chdir',str(L)]
raise SystemExit(subprocess.run(args+[sys.executable,'-I','-s','-B',str(D/'evidence_retained.py')],env={**os.environ,'TMPDIR':str(D)}).returncode)
