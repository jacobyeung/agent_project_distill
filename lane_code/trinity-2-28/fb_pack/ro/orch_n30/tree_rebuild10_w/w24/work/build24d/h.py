import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,checked,seal,write
k=Path(__file__).resolve().parents[1];seal(k)
if len(sys.argv)!=3:raise ValueError('E84')
r=Path(sys.argv[1]);q=load(r/'q/RESULT.json')
if q.get('status')!='ADMIT' or q.get('init_milestone')!=400:raise ValueError('E81')
p=q['config'];cfg=load(checked(p['path'],p['sha256']))
if cfg.get('world_size')!=4 or cfg.get('r1_training',{}).get('init_policy')!='step400_export_weights_fresh_v1':raise ValueError('E85')
write(sys.argv[2],cfg)
