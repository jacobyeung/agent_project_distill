from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';sys.path.insert(0,str(D));import joblib as J
records={}
for name in ('final_focused','edges','producer_edges','build24_scanner','build24_resolver','build24_kit','build24_naming21c','build24_naming21d'):
 p=L/'work/build21/proofs'/name/'TESTS.json'
 if p.exists():
  r=J.load(p);records[name]=dict(tests=r['tests'],successful=r['successful'])
for name,p in [('build22',L/'work/build22/proofs/new_tests/TESTS.json'),('build23',D/'proofs/tests23/TESTS.json'),('build23_resolver',D/'proofs/resolver23/RESOLVER_TESTS.json'),('build23b',D/'proofs/tests23b/TESTS.json'),('kit24',D/'KIT_TESTS.json'),('resolver24',D/'RESOLVER_TESTS.json')]:
 r=J.load(p);records[name]={k:r[k] for k in ('tests','successful')}
J.write(D/'TEST_COUNTS.json',dict(suites=records,tests=sum(r['tests'] for r in records.values()),successful=all(r['successful'] for r in records.values())))
print(json.dumps(J.load(D/'TEST_COUNTS.json'),indent=2))
reasons=J.load(D/'UPLOAD_REASONS.json');files=J.load(D/'UPLOADS_q.json')['files']
for prefix in ('8ec1efd2','15387646','e3c72962'):
 hits=[x for x in files if x['sha256'].startswith(prefix)]
 print('Deferred source',prefix,[(x['opaque_name'],x['bytes'],reasons.get(x['sha256'])) for x in hits])
