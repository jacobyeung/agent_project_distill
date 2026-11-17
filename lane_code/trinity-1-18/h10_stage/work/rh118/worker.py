import sys
from pathlib import Path
p=Path('/scratch/jjyeung/b01ec87a6f29b/p'); sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
k=open('/scratch/jjyeung/orch_n30/h10_stage/work/rh118/k.txt').read().strip()
from h1eval.h10.launch import main
d='/scratch/jjyeung/b01ec87a6f29b/d'
raise SystemExit(main(['--items',str(p/'items/devs1_routed.json'),'--export',d+'/e','--artifact-manifest',d+'/binding.json',
  '--reader-root',str(p/'b'),'--settings',d+'/settings.json','--out','/scratch/jjyeung/b01ec87a6f29b/rh_out/3',
  '--arms','own','--shard',f'{k}/636','--device','cpu','--types','object_abs_distance','--modes','none']))
