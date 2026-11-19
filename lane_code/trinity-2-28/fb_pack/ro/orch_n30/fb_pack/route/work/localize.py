"""Materialize transport envelopes for the current staging root; never changes row bytes."""
import sys,json
from pathlib import Path
import route as R
from route import ROOT,BASE,load,pin,write
R.COMMAND=R.PREFIX+'work/localize.py'
pin(__file__);pin(ROOT/'work/route.py')
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--tree',default=str(R.TREE));args=parser.parse_args()
R.TREE=Path(args.tree).resolve();sys.path.insert(0,str(R.TREE))
index=load(ROOT/'out/ENVELOPE_INDEX.json');acc=load(ROOT/'out/EXCLUSION_ACCOUNTING.json')
from student_pilot.r2_exclusions import upstream
from student_pilot.r2_intake import intake
from student_pilot.r2_withheld import Withheld

def absolute(p):
 if p['path'].startswith('u/'):
  f=ROOT/p['path'];pin(f,p['sha256'])
  return dict(path=str(f),sha256=p['sha256'])
 return p
out={}
for name,item in index['slices'].items():
 e=load(ROOT/f'out/envelopes/{name}.json');s=acc['slices'][name]
 exclusions={k:absolute(p) for k,p in e['exclusions'].items()}
 cov=load(ROOT/f'out/coverage/{name}_final.json');cov={k:v for k,v in cov.items() if k not in ['inputs','command']};cov['exclusions']=exclusions
 cp=write(f'out/localized/{name}/coverage.json',cov)
 u=load(ROOT/f'out/upstream/{name}.json');u={k:v for k,v in u.items() if k not in ['inputs','command']};u.update(exclusions=exclusions,coverage=cp,withheld_rooms=absolute(e['withheld_rooms']),dev_scene_exclusions=absolute(e['dev_scene_exclusions']))
 up=write(f'out/localized/{name}/upstream.json',u)
 e={k:v for k,v in e.items() if k not in ['inputs','command']}
 for k in ['rows','extent_receipt','withheld_rooms','dev_scene_exclusions','frame_map','frame_plan','fps_authority']:
  if k in e:e[k]=absolute(e[k])
 e['required_exclusion_pins']={k:absolute(p) for k,p in e['required_exclusion_pins'].items()}
 e.update(exclusions=exclusions,scene_coverage=cp,upstream_receipts=[up])
 ep=write(f'out/localized/{name}/envelope.json',e)
 assert upstream([up],exclusions);Withheld(e['withheld_rooms'])
 # This check uses no relocation scope and no environment or hostname overrides.
 items,report=intake(ep['path'],limit=2000);del items
 rp=write(f'out/localized/{name}/intake.json',report)
 out[name]=dict(envelope=ep,coverage=cp,upstream_receipt=up,rows=e['rows'],intake=rp,counts=report['counts'])
 print(name,'localized native intake complete',flush=True)
write('out/LOCALIZED_INDEX.json',dict(slices=out,root=str(ROOT),scope='Absolute active pins for native intake without relocation. Production stages raw blobs under its own root/u/<sha>, adapts ROOT in the packaged route helper to the unpacked root, and reruns this script to regenerate the mutually bound coverage, upstream and envelope hashes. Bind these new envelope pins and their exact rows/extent pins into config and request; do not bind the portable transport-envelope hash as a localized envelope. The kit inline config/request localizer alone does not recurse into these envelope files.'))
