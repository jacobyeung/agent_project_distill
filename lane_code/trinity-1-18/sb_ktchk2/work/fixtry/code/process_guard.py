"""Freeze each part's scoring protocol before model output; refuse repeat scoring."""
from common import *

PARTS = ('A', 'B', 'C', 'H')

def directory(out, part):
 if part not in PARTS:raise ValueError('Unknown part '+part)
 return Path(out)/'parts'/part

def score_files(out, part):
 folder=directory(out,part)
 # This directory holds only the freeze pair and scores. Unknown files fail closed.
 files=[p for p in folder.rglob('*') if p.is_file() and not (p.parent==folder and p.name in ('BARS.json','FREEZE.json'))]
 legacy=[f'PER_ITEM_{part}_*.jsonl'] if part!='H' else ['PER_ITEM_*_heldout.jsonl']
 for pattern in legacy:files.extend(Path(out).glob(pattern))
 if (Path(out)/'PER_ITEM.jsonl').is_file():files.append(Path(out)/'PER_ITEM.jsonl')
 names={'A':['A_POSE.json','A_DISTANCE.txt'],'B':['B_LADDER_TRAIN.txt'],'C':['C_CAMERA.txt'],'H':['HELDOUT_once.txt']}[part]
 for name in names:
  path=Path(out)/name
  if path.is_file():
   value=read_json(path)
   if value.get('rows') or value.get('results'):files.append(path)
 return files

def protocol(part):
 cfg=read_json(ROOT/'configs/kit.json')
 shared=dict(part=part,code_sha256=digest(code_pins()),bootstrap=cfg['bootstrap'],positive_bar='paired CI lower endpoint > 0',
             protocol_sha256={n:sha(ROOT/n) for n in ('code/metrics.py','code/evaluate_v2.py','code/camera_pricing.py','code/exclusions.py','configs/KBOX_WINNING_BOX_RULE.json')})
 if part in ('A','B'):
  shared.update(population='K1 train outside withheld rooms',decision_rows=1012,full_rows_report_only=1037)
 if part=='A':shared.update(context_pays_pose='move_mra OR short_displacement_mra; G64 minus G32',reader_C64_licensed='context_pays_pose',lifting='C64_V32_GTmask minus C32_V32_GTmask',part_B_runs=True)
 if part=='B':shared.update(views_pay='C64_V64 minus C64_V32; frozen object rule when available, otherwise today',added_frame_gain='C64_V64_today minus C32_V32_today',flagged='REPORT_ONLY')
 if part=='C':shared.update(role='DIAGNOSTIC_ONLY',adoption='NONE',parity_required=440,parity_total=450)
 if part=='H':shared.update(role='REPORT_ONLY',adoption='NONE',requires='complete frozen A/B train decisions and one unused held-out look')
 return shared

def require_score(out, part):
 files=score_files(out,part)
 if files:raise RuntimeError('REFUSE: per-item score file already exists: '+str(files[0]))
 folder=directory(out,part);bars=folder/'BARS.json';receipt=folder/'FREEZE.json'
 if not bars.is_file() or not receipt.is_file():raise RuntimeError('REFUSE: missing frozen bars or freeze receipt: '+str(folder))
 frozen=read_json(receipt)
 if frozen.get('part')!=part or frozen.get('bars_sha256')!=sha(bars):raise RuntimeError('REFUSE: frozen bars sha256 differs from freeze')
 if read_json(bars).get('code_sha256')!=digest(code_pins()):raise RuntimeError('REFUSE: code differs from BARS.json')
 if frozen.get('code_sha256')!=digest(code_pins()):raise RuntimeError('REFUSE: code differs from freeze')
 return frozen

def freeze(out, part):
 folder=directory(out,part)
 if (folder/'BARS.json').exists() or (folder/'FREEZE.json').exists():return require_score(out,part)
 if score_files(out,part):raise RuntimeError('REFUSE: per-item scores exist before freeze')
 units=('C32','C64') if part=='C' else (part,) if part!='H' else ('A','B')
 for unit in units:
  if any(p.is_file() for p in (Path(out)/'captures'/unit).rglob('*')):raise RuntimeError('REFUSE: model output exists before bars freeze')
 # Legacy reports with rows are scored output, even without a PER_ITEM receipt.
 names={'A':['A_POSE.json','A_DISTANCE.txt'],'B':['B_LADDER_TRAIN.txt'],'C':['C_CAMERA.txt','C_PARITY.json'],'H':['HELDOUT_once.txt']}[part]
 for name in names:
  path=Path(out)/name
  if path.is_file():
   value=read_json(path)
   if value.get('rows') or value.get('checks') or value.get('results'):raise RuntimeError('REFUSE: scored output exists before bars freeze: '+str(path))
 value=protocol(part);code=digest(code_pins())
 folder.mkdir(parents=True,exist_ok=True)
 # Exclusive creation prevents a resumed command from replacing a frozen protocol.
 with (folder/'BARS.json').open('x') as f:json.dump(dict(value,input_sha256=dict(INPUTS)),f,sort_keys=True,indent=2)
 bars_sha=sha(folder/'BARS.json')
 with (folder/'FREEZE.json').open('x') as f:json.dump(dict(part=part,bars_sha256=bars_sha,code_sha256=code,input_sha256=dict(INPUTS)),f,sort_keys=True,indent=2)
 return require_score(out,part)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','check']);p.add_argument('part',choices=PARTS);a=p.parse_args()
 (freeze if a.action=='freeze' else require_score)(ROOT/'out/tower_frames',a.part)
