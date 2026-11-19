from pathlib import Path
import gzip,json,hashlib,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
doc=json.loads((D/'COMPRESSED_FIXTURES_2.json').read_text())
for r in doc['files']:
 if r['original'].startswith('work/build24k/proofs/resolver600_v2/'):
  p=L/r['original'];raw=gzip.decompress((L/r['retained_blob']).read_bytes());assert hashlib.sha256(raw).hexdigest()==r['original_sha256'];p.write_bytes(raw)
p=D/'integration_tests.py';p.write_text(p.read_text().replace("D/'integration_sealed'","D/'integration_verified'"))
sys.path.insert(0,str(L/'work/build24'));import joblib as J
cfg=J.load(L/'work/build24f/rehearsal3/seed.json')
for name,pin in [('receipt',cfg['r1_training']['handover_receipt']),('artifact',cfg['init_artifact']['artifact'])]:print(name,pin,Path(pin['path']).exists())
print('missing persisted',[(h,p) for h,p in cfg['r1_training']['persisted_files'].items() if not Path(p).exists()][:8])
