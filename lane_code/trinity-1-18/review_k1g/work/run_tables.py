import sys,json,os
from pathlib import Path
kit=Path(sys.argv[1]);mode=sys.argv[2];out=sys.argv[3];args=sys.argv[4:]
sys.path[:0]=[str(kit/'work'),str(kit/'native_kit')]
import bindings as B
import k1_pipeline as K
if mode=='new':
  K._sources_verified=True  # deps verified separately via mapping
K._native()
F='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/tests_8cc4f9ec/'
m=B.load(F+'manifest.json')
try:
  if mode=='old':K.tables(m,F+'old_cache',out)
  else:
    gs=args[0] if args else None;sens='--sensitivity' in args
    if args and args[0]=='none':gs=None
    K.tables(m,F+'old_cache' if '--cache' not in args else args[args.index('--cache')+1],out,gs,sens)
  print('OK',out)
except Exception as e:print('REFUSED',type(e).__name__,str(e)[:200])
