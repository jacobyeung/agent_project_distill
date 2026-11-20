import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
n=z.load(kit('n')/'k/n.json');p=z.load(input_file(n['r1_training']['p_run']['config']['sha256']))
print('pins',n['extent_receipt'],p.get('extent_receipt'));print('N streams',n['streams'])
for base in [n,p]:
 receipt=z.load(input_file(base['streams']['pose']['sha256']))
 print('pose keys',list(receipt))
 if 'model' not in receipt:
  receipt=z.load(input_file(receipt['sources'][0]['receipt']['sha256']))
 mp=receipt['model'];v=z.load(input_file(mp['sha256']))
 print('base',mp,v)
 write(D/('META_'+str(len(list(D.glob('META_*'))))+'.json'),dict(pin=mp,value=v))
m=json.loads((L/'work/build24m4p/PACKAGE_MANIFEST.json').read_bytes())['files']
print('extent paths',[(n,v.get('bytes')) for n,v in m.items() if ('extent' in n.lower() or 'c072905b' in n) and not '/tests/' in n][:45])
