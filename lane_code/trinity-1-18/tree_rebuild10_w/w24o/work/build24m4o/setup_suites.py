from common import *
import re,shutil
I=L/'work/build24m4k'
def adapt(s):
 s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w(?:\d+[a-z]*)?(?=/|[\x27\"])',str(L),s)
 s=s.replace('work/build24m4k','work/build24m4o').replace('work/tree_r1','work/tree_r1c')
 return s
for p in I.glob('*.py'):
 if (D/p.name).exists() or p.name in ('inspect.py','setup.py'):continue
 (D/p.name).write_text(adapt(p.read_text()))
for p in (I/'scanners').rglob('*'):
 if p.is_file():
  q=D/p.relative_to(I);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(adapt(p.read_text()))
for n in ('guard_q','guard_n','inputs'):(D/n).mkdir(exist_ok=True)
for folder in ('build24m4k','build24m4j','build24m4i','build24m4h','build24m4e','build24m4d'):
 for p in (L/'work'/folder/'inputs').glob('*'):
  q=D/'inputs'/p.name
  if p.is_file() and not q.exists():os.link(p,q)
for name in ('CONFIG_DELTA.json','CONFIG_IDENTITIES.json','UPLOADS_n.json','CONFIG_INPUTS.json'):
 p=I/name
 if p.is_file():(D/name).write_bytes(p.read_bytes())
for name in NAMES:
 p=D/('naming24m1_'+name+'.py');s=p.read_text()
 maps=J.load(D/'DEPENDENT_PINS.json')[name]['source_maps']
 values={(rel,field):h for rel,fields in maps.items() for field,h in fields.items()}
 s=re.sub(r'^SOURCE_SEALS=.*$', 'SOURCE_SEALS='+repr(values),s,flags=re.M)
 p.write_text(s)
replace(L/'out/arm_routing.py',adapt((L/'out/arm_routing.py').read_text()).replace('Orchard q and n at 24m4j; exact recorded seals and file inventory','Orchard q and n after UPLOADS_24M4N; exact recorded seals and file inventory'))
# Arming consumes the delivered baseline, while the delivery delta uses BASE_*.
J.write(D/'ARM_BASE_SEALS.json',J.load(D/'SEALS.json'))
J.write(D/'ARM_BASE_FILES.json',{n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES})
p=L/'out/arm_routing.py';replace(p,p.read_text().replace('BASE_SEALS.json','ARM_BASE_SEALS.json').replace('BASE_FILES.json','ARM_BASE_FILES.json'))
print('Suites and arming baseline ready')
