from pathlib import Path
import shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';E=L.parent/'ext/m400real';sys.path.insert(0,str(L/'work/build24'));import joblib as J
records=[]
for p in E.rglob('*'):
 if p.is_file() and (p.suffix=='.json' or p.name in ('h.out','names.txt')):
  q=D/'inputs/m400real'/p.relative_to(E);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);records.append(dict(path=str(q.relative_to(L)),sha256=J.sha(q),bytes=q.stat().st_size))
assert sum(x['bytes'] for x in records)<30_000_000
for name,old,new in [
 ('init_tests.py',"REAL=L.parent/'ext/m400real';receipt=", "REAL=L.parent/'ext/m400real';REAL=REAL if REAL.exists() else D/'inputs/m400real';receipt="),
 ('resolver_tests.py',"K=B/'kits/n';real=L.parent/'ext/m400real';records=[]", "K=B/'kits/n';real=L.parent/'ext/m400real';real=real if real.exists() else D/'inputs/m400real';records=[]"),
 ('real_replay.py',"E=L.parent/'ext/m400real';O=", "E=L.parent/'ext/m400real';E=E if E.exists() else D/'inputs/m400real';O="),
 ('kit.py',"real=L.parent/'ext/m400real';receipt=", "real=L.parent/'ext/m400real';real=real if real.exists() else D/'inputs/m400real';receipt=")]:
 p=D/name;s=p.read_text();assert old in s,name;p.write_text(s.replace(old,new))
p=L/'work/build21/resolver21e.py';s=p.read_text();old="if not E.exists():E=D/'inputs/m400real'";new=old+"\nif not E.exists():E=L/'work/build24b/inputs/m400real'";assert old in s
shutil.copyfile(p,L/'attic/build24b/resolver21e.py');p.write_text(s.replace(old,new))
J.write(D/'PREREQUISITES.json',dict(files=records,total_bytes=sum(x['bytes'] for x in records),scope='Exact supplied small metadata, no weights, production databases or frames.'))
p=D/'run.sh';s=p.read_text().replace("export OMP_NUM_THREADS=8", "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\nexport OMP_NUM_THREADS=8");p.write_text(s)
print('Exact real small-file prerequisites:',len(records),sum(x['bytes'] for x in records),'bytes')
