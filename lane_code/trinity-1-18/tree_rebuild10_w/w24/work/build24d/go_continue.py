from pathlib import Path
import json,subprocess,sys,time
D=Path(__file__).resolve().parent
result=D/'GO_CANARY_FINAL.json'
while not result.is_file():time.sleep(60)
value=json.loads(result.read_text())
if value.get('result',{}).get('status')!='ADMIT':
 print('Canary refused:',value.get('result',{}).get('refusal'),flush=True);raise SystemExit(1)
print('Canary ADMIT; continuing once through room audit, config producer and launcher.',flush=True)
raise SystemExit(subprocess.run([sys.executable,'-I','-s','-B',str(D/'go_train.py')]).returncode)
