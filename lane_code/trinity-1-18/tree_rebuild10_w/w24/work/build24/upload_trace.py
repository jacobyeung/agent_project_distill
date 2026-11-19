from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24';sys.path.insert(0,str(D));import joblib as J
r=J.load(D/'UPLOAD_REASONS.json');files={x['sha256']:x for x in J.load(D/'UPLOADS_q.json')['files']}
for h in ['ef7303ba61d9c0f240324853b9dd602426447f471f64486c1444b10c6607fcb2']:
 print('Parent',h,'reasons',r.get(h));x=files[h];v=J.load(x['local_path']);print(json.dumps(v,indent=2)[:5000])
cat=J.load(L/'work/build22/inputs/row_sources.json')
for key,v in cat.items():
 if isinstance(v,dict) and v.get('source'):
  h=v['source']['sha256'];print('source',key,h,files.get(h,{}).get('bytes'),r.get(h))
