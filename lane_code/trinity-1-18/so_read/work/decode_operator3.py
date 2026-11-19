import ast,io,tarfile
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4')
s=(A/'package/BATCH.sh').read_text()
line=next(x for x in s.splitlines() if x.startswith('b=bytes.fromhex('))
raw=bytes.fromhex(ast.literal_eval(line[len('b=bytes.fromhex('):-1]))
out=L/'work/operator3-original';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw)) as a:
 for e in a:
  if e.isfile():
   assert '/' not in e.name
   (out/e.name).write_bytes(a.extractfile(e).read())
print(sorted(p.name for p in out.iterdir()))
