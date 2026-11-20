from common import *
import shutil
I=L/'work/build24m4i'
for p in I.glob('*.py'):
 if p.name in ('common.py','bootstrap.py','setup_tests.py','finalize.py','package.py','edit.py'):continue
 s=p.read_text().replace(str(W/'w24i'),str(L)).replace('work/build24m4i','work/build24m4j')
 (D/p.name).write_text(s)
for p in (I/'scanners').rglob('*'):
 if p.is_file():
  q=D/p.relative_to(I);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
for n in ('guard_q','guard_n','inputs'):(D/n).mkdir(exist_ok=True)
for p in (I/'inputs').iterdir():
 if p.is_file():os.link(p,D/'inputs'/p.name)
for name in ('CONFIG_DELTA.json','CONFIG_IDENTITIES.json','UPLOADS_n.json'):
 p=I/name
 if p.is_file():(D/name).write_bytes(p.read_bytes())
p=L/'out/arm_routing.py';s=p.read_text().replace('work/build24m4i','work/build24m4j')
s=s.replace('    rows=[];seals={};checks={};mutated=', '    baseline=J.load(D/"BASE_FILES.json")\n    rows=[];seals={};checks={};mutated=')
s=s.replace('            if J.sha(p)==J.sha(old) and p.stat().st_mode&511==old.stat().st_mode&511:continue', '            before=baseline[name].get(str(rel),{})\n            if str(rel) not in {"k/c.json","k/n.json","k/8.json","k/s.json"} and J.sha(p)==before.get("sha256") and p.stat().st_mode&511==before.get("mode"):continue')
s=s.replace('baseline="24m4h kits; apply UPLOADS_24M4H and ORCHARD_COPIES_24M4H first"','baseline="Orchard q and n at 24m4i after UPLOADS_24M4I; includes all 24m4j changes", baseline_kit_seals=J.load(D/"BASE_SEALS.json"), baseline_files={n:baseline[n] for n in ("q","n")}')
replace(p,s)
# Probe only modules that exist for the configured processor; force AutoProcessor
# and then the actual asset-selected processor inside the production child.
p=D/'closure.py';s=p.read_text().replace("|{'scipy.spatial.distance','scipy.spatial.transform','transformers.models.qwen3_5.processing_qwen3_5'}","|{'scipy.spatial.distance','scipy.spatial.transform'}");replace(p,s)
print('SUITES READY; arming manifest includes explicit config capsules and full baseline hashes')
