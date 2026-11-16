import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate,prooflib
def proof():
 a,_,b=gate.authorities()
 vsi=next(k for k,v in b['members'].items() if 'VSI-Bench' in v['benchmarks'])
 arkit=next(k for k,v in a.items() if v=='arkitscenes/venue381879')
 cases=['scannet/scene0380_01','scannet/scene0011_00',vsi,arkit,'unknown/nope','scannet/scene9999_99']
 for key in cases:assert not gate.eligible(*key.split('/')),key
 inv=json.loads((prooflib.LANE/'out/CAPTURES.json').read_text());assert len(inv['pilot'])==300
 receipt=gate.receipt([c['canonical'] for c in inv['pilot']]);assert receipt['refusals']==0
 assert {c['room'] for c in inv['pilot'] if c['split']=='train'}.isdisjoint({c['room'] for c in inv['pilot'] if c['split']=='heldout'})
 assert gate.eligible(*inv['pilot'][0]['canonical'].split('/'))
 return dict(planted_refusals=[gate.verdict(*k.split('/')) for k in cases],selected=receipt['selected'],refusals=0,input_sha256=receipt['inputs'])
if __name__=='__main__':raise SystemExit(not prooflib.run('P1',proof))
