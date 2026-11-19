"""Exercise the nested headcall suite with its own local fixture import path."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];which=sys.argv[1]
p=ROOT/'code/suite.py';source=p.read_text()
source=source.replace("('suite_'+which)","('headcall_'+which)")
source=source.replace("sys.path[:0]=[str(tree),str(tree/'tests')]","sys.path[:0]=[str(tree),str(tree/'tests'),str(tree/'tests/headcall')]")
source=source.replace("Path(start_dir).rglob(pattern)","(Path(start_dir)/'headcall').glob(pattern)")
source=source.replace('else:code=0','else:pass')
try:exec(compile(source,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
except SystemExit as e:code=e.code
else:code=0
result=ROOT/'out'/('headcall_'+which)/'TEST_RESULTS.json'
if result.exists():
 v=json.loads(result.read_text());v['input_sha256'][str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 v['command']='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/headcall_suite.py '+which
 result.write_text(json.dumps(v,indent=2)+'\n')
raise SystemExit(code)
