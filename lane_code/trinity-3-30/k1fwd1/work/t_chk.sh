cd /scratch/jjyeung/orch_n30/sb_own400/in/own_400/native/probe && python3 -c "
import json,hashlib,os
n=ok=0
for d in sorted(os.listdir('.')):
    if not os.path.isdir(d): continue
    p=json.load(open(d+'/PHASE_COMPLETE.json')); n+=1
    h=hashlib.sha256(open(d+'/own.npz','rb').read()).hexdigest()
    ok+= p['checkpoint']['sha256'].startswith('5083243c') and p['phase']=='own' and not p['synthetic'] and p['files']['own.npz']==h
print(n,ok)"
