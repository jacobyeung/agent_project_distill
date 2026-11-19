from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];D=W.parent/'donor'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=D/'out/TREE_FILES.sha256';rows={line.split('  ',1)[1]:line.split('  ',1)[0] for line in m.read_text().splitlines()}
f=D/'out/FILES_TOUCHED.json';changes=json.loads(f.read_text())['files']
expected=dict(rows);expected.update({e['path']:e['new_sha256'] for e in changes})
inputs={str(m):sha(m),str(f):sha(f),str(D/'out/TREE_SEAL.json'):sha(D/'out/TREE_SEAL.json'),str(Path(__file__).resolve()):sha(__file__)}
for label,files in [('base',rows),('new',expected)]:
 for n,h in files.items():
  p=D/'work'/label/n;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
  inputs[str(p)]=h
  out=W/'work'/('base' if label=='base' else 'donor_orig')/n;out.parent.mkdir(parents=True,exist_ok=True)
  if out.exists():assert out.read_bytes()==raw
  else:out.write_bytes(raw)
  if label=='new' and not (W/'work/new').exists():raise RuntimeError('Stage the new overlay from donor_orig before editing')
seal=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert seal=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
(W/'out/STAGING.json').write_text(json.dumps(dict(input_sha256=inputs,base_tree_sha256=seal,base_files=len(rows),donor_files=len(expected),status='PASS',command='python code/stage_local.py'),indent=2)+'\n')
print('Base and donor source inventories verified')
