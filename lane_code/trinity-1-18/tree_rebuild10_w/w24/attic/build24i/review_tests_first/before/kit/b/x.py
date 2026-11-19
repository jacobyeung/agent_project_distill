from pathlib import Path
import os,subprocess,sys
k=Path(sys.argv[1]);r=Path(sys.argv[3])
for helper,args in [('h.py',[r/'p',r/'v.json']),('rv.py',[r,r/'v.json','91'])]:
 result=subprocess.run([sys.executable,'-B','-I','-s',str(k/'b'/helper),*map(str,args)])
 if result.returncode:raise SystemExit(result.returncode)
(r/'T_STARTED').write_text('t.py boundary; no training executed\n')
