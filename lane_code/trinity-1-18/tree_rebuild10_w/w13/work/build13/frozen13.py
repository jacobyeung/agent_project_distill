from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build13'
for args in ([str(B/'storage13.py')],[str(B/'delivery13.py')]):
    r=subprocess.run([sys.executable,'-I','-s','-B',*args])
    if r.returncode:raise SystemExit('Stopped after failed delivery check')
delivery=json.loads((B/'DELIVERY.json').read_text())
r=subprocess.run([sys.executable,'-I','-s','-B',str(B/'package13.py'),str(L/delivery['path'])])
if r.returncode:raise SystemExit('Stopped after package suite error')
subprocess.run([sys.executable,'-I','-s','-B',str(B/'compare13.py')],check=True)
