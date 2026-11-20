from common import *
I=L/'work/build24m4j'
for p in I.glob('*.py'):
 if (D/p.name).exists():continue
 s=p.read_text().replace(str(W/'w24j'),str(L)).replace('work/build24m4j','work/build24m4k')
 (D/p.name).write_text(s)
for p in (I/'scanners').rglob('*'):
 if p.is_file():
  q=D/p.relative_to(I);q.parent.mkdir(parents=True,exist_ok=True)
  q.write_bytes(p.read_bytes().replace(str(W/'w24j').encode(),str(L).encode()))
for n in ('guard_q','guard_n','inputs'):(D/n).mkdir(exist_ok=True)
for folder in ('build24m4j','build24m4i','build24m4h'):
 for p in (L/'work'/folder/'inputs').glob('*'):
  q=D/'inputs'/p.name
  if p.is_file() and not q.exists():os.link(p,q)
for name in ('CONFIG_DELTA.json','CONFIG_IDENTITIES.json','UPLOADS_n.json','CONFIG_INPUTS.json'):
 p=I/name
 if p.is_file():(D/name).write_bytes(p.read_bytes())
b=J.load(D/'BASELINE.json')
J.write(D/'BASE_SEALS.json',b['kits']);J.write(D/'SEALS.json',b['kits']);J.write(D/'BASE_FILES.json',b['files'])
p=L/'out/arm_routing.py';s=p.read_text().replace('work/build24m4j','work/build24m4k')
s=s.replace('Orchard q and n at 24m4i after UPLOADS_24M4I; includes all 24m4j changes','Orchard q and n at 24m4j; exact recorded seals and file inventory')
replace(p,s)
print('16 suites ready; baseline is actual 24m4j kit inventory')
