"""Package the repaired kit and final evidence without redundant test payloads."""
import hashlib,json,os,sys,tarfile
from pathlib import Path
sys.path.insert(0,'kit/files');import count_guard as G
R=Path.cwd();O=R/'out'
required=['FIX_REPORT.md','GPU_NEED.json','COMMANDS.md','METRIC_TEST.json','MRA_PIN_VERIFICATION.json','K1_TRAIN_SELECTION.json','K1_REFERENCE_RECOMPUTE.json','MANIFEST_R0DEV.json','STUB_SCORE.json','STUB_SCORE_CATEGORY_ERRORS.json','STUB_REPLAY_TEST.json','CPU_AUDIT.json','CONTROL_AUDIT.json','CONTROL_TESTS.json','RUNTIME_TESTS.json','DEADLINE_TEST.json','MISSING_INPUTS.json','PILOT_STATUS.json','selftest.log','training.log','manifest.log','stub_run_final.log','stub_score.log','cpu_audit.log','control_audit.log','control_tests.log','runtime_tests.log','deadline_test.log','k1_references.log']
for name in required:assert (O/name).is_file(),name
# All evidence must pin the code/config that is actually delivered.
for name in ['METRIC_TEST.json','STUB_SCORE.json','CPU_AUDIT.json','CONTROL_TESTS.json','RUNTIME_TESTS.json','DEADLINE_TEST.json']:
 d=G.read(O/name)
 for p,h in G.pins().items():assert d['inputs_sha256'].get(p)==h,(name,p,'stale evidence')
assert len((O/'FIX_REPORT.md').read_text().splitlines())<=50
for c in G.manifest(O/'MANIFEST_R0DEV.json')['captures']:G.validate_done(O/'stub_final',c,O/'MANIFEST_R0DEV.json',None,True)
assert not (G.LEDGER/'R0-dev-counting.json').exists()
(R/'STATUS.md').write_text('Complete: CPU validation passes, including 1,605 stored scores, 60 threshold cases, 385/385 stub coverage, 34 control checks, six resume checks, the in-flight deadline, and both reviewer audits. K1 training rejects the GPU comparison; no real R0-dev look is consumed. out/FIX_REPORT.md, out/GPU_NEED.json, and out/sb_cntfix.tar with its SHA256 sidecar form the delivery. Exact missing pilot and fixture paths are recorded in out/MISSING_INPUTS.json.\n')
kitfiles=[p for p in sorted((R/'kit/files').iterdir()) if p.is_file() and p.name!='KIT_SHA256SUMS']
(R/'kit/files/KIT_SHA256SUMS').write_text(''.join(G.sha(p)+'  '+p.name+'\n' for p in kitfiles))
files=[]
for dirname in ('kit','inputs','review','k1','state'):
 files.extend(p for p in sorted((R/dirname).rglob('*')) if p.is_file() and '__pycache__' not in p.parts)
files.extend(O/n for n in required)
files.extend(p for p in sorted((O/'stub_final').rglob('*')) if p.is_file() and 'cache' not in p.parts)
files.extend(p for p in sorted(R.glob('*.py')) if p.is_file())
files.extend([R/'cpu.sh',R/'STATUS.md'])
files=sorted(set(files))
G.write(O/'PACKAGE_PROVENANCE.json',dict(schema='count-package-v1',inputs_sha256={str(p.relative_to(R)):G.sha(p) for p in files},files=len(files),host=os.uname().nodename,official_item_files_read=0,real_look_consumed=False,notes='Files under inputs/, review/, kit/work/, and k1/ preserve supplied source records; new evidence JSONs carry direct input hashes. Frame images and the external SAM environment/weights are not duplicated.'))
files.append(O/'PACKAGE_PROVENANCE.json')
archive=O/'sb_cntfix.tar'
with tarfile.open(archive,'w') as t:
 for p in files:t.add(p,arcname=str(p.relative_to(R)),recursive=False)
h=G.sha(archive);(O/'sb_cntfix.tar.sha256').write_text(h+'  sb_cntfix.tar\n')
with tarfile.open(archive) as t:
 names=t.getnames();assert len(names)==len(files)
 for member in t:
  f=t.extractfile(member);got=hashlib.sha256()
  for b in iter(lambda:f.read(1<<20),b''):got.update(b)
  assert got.hexdigest()==G.sha(R/member.name),member.name
G.write(O/'DELIVERY_VERIFICATION.json',dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(files),every_member_hash_matches=True,inputs_sha256={str(archive):h,str(O/'PACKAGE_PROVENANCE.json'):G.sha(O/'PACKAGE_PROVENANCE.json'),str(__file__):G.sha(__file__)}))
print(json.dumps(dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(files))))
