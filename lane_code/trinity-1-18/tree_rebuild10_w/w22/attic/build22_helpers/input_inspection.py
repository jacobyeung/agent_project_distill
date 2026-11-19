from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/'work/build21'))
import joblib as J
K=L/'work/build21/kits/q'
for name in ('n','p','r'):
 v=J.load(K/('k/'+name+'.json'))
 print(name, {k:v.get(k) for k in (('s1_routing','r1_training') if name=='n' else ('p_run','p_kit_config','room_sha256') if name=='p' else tuple(v))})
print('wordings',[(k,type(v).__name__,len(v)) for k,v in J.load(Path('/scratch/jjyeung/orch_n30/sb_rowA/out/WORDINGS.json')).items()])
print('vqa',J.load(L/'work/build18/inputs/v7_receipt.json') if (L/'work/build18/inputs/v7_receipt.json').exists() else 'missing')
