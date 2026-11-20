import sys,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
original=J.load(D/'ORIGINAL_KITS.json');seals={};changed={};identities={}
files=inventory(T);tree=digest(files);assert tree=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
for n in NAMES:
 k=kit(n);seals[n]=verify(k);changed[n]=[]
 assert J.load(k/'k/a.json')['GO']==J.load(k/'BUILD.json')['GO']==(n=='n_go')
 check_archive(file_pin(k/J.load(k/'k/a.json')['source']['path']),files)
 for rel,before in original[n].items():
  p=k/rel
  if J.sha(p)==before['sha256']:continue
  changed[n].append(rel)
  stored=L/'attic/build24m4h'/k.relative_to(L)/rel
  assert stored.is_file() and J.sha(stored)==before['sha256'],rel
 for p in (k/'b').glob('*.py'):compile(p.read_text(),str(p),'exec')
 identities[n]={}
 for rel in ('k/c.json','k/n.json'):
  before=J.load(L/'attic/build24m4h'/k.relative_to(L)/rel);after=J.load(k/rel)
  b=identity(before);a=identity(after);assert a!=b
  assert before['remove_files']==after['remove_files']
  identities[n][rel]=dict(before=b,after=a,payload_sha256=J.load_raw(k/rel)['sha256'],file_sha256=J.sha(k/rel))
for rel in J.load(D/'CHANGED_B.json'):
 hs={J.sha(kit(n)/'b'/rel) for n in NAMES};assert len(hs)==1,(rel,hs)
# Check all new catalog hashes have inventory authority, including P's U inputs.
sys.path.insert(0,str(kit('q')/'b'));from px import inventory as pin_inventory
spec=J.load(kit('q')/'k/p.json');authority=set(pin_inventory(kit('q')))|{x['sha256'] for x in spec['uploads']}
for row in J.load(W/'ext/m400real/MANIFEST.json')['files']:authority.add(row['sha256'])
# P run metadata pins already in the supplied Orchard listing are explicit authority.
listing={line.split()[1]:int(line.split()[0]) for line in (W/'work/pin_eac5f9f0/ORCHARD_U_LIST.txt').read_text().splitlines() if len(line.split())==2 and line.split()[0].isdigit()}
missing=[h for h in J.load(kit('q')/'k/c.json')['s1_routing']['catalog'] if h not in authority]
assert not missing,missing
assert 'e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536' not in listing
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=tree,kits=seals,changed=changed,config_identities=identities,changed_b_identical=True,removal_lists_unchanged=True,catalog_inventory_closure=True,p_tree_copy_required=True,original_kit_files_preserved=True,GO='false except out/kit_n_go'))
print('AUDIT PASS',tree,seals)
