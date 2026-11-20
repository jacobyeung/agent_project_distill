from common import *
from unittest.mock import patch
from copy import deepcopy
import tarfile,subprocess
sys.path[:0]=[str(kit('n')/'b'),str(L/'work/build21')]
import z,resolver21e as R
root=L/'work/build24m2c/resolver/proofs/real';pool=root/'pool';listing=root/'listing.json'
f=dict(external=J.load(listing)['metadata']);records=[]
native=z.load
for name in ('q','n','n_go','qd'):
 k=kit(name);spec=deepcopy(J.load(k/'k/p.json'));m=pool/spec['milestone']
 with tarfile.open(m/'s.tar') as t:spec['m4']['v']=hashlib.sha256(t.extractfile('MANIFEST.json').read()).hexdigest()
 marker=(pool/spec['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();spec['m4'].update(t=marker[2],b=int(marker[1]))
 with R.external_boundary(f,module=z),patch.object(z,'load',side_effect=lambda p:deepcopy(spec) if Path(p)==k/'k/p.json' else native(p)),patch.object(z,'write'):
  value=z.resolve(k,pool,listing,D/'unused_resolver_output.json')
 h=spec['code_sha256'];assert value['config']['code']['sha256']==h and h in value['paths']
 assert spec['pin_paths']=={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']}
 records.append(dict(kit=name,seal=J.seal(k),source_sha256=h,resolver='PASS'))
J.write(D/'SOURCE_PIN_TESTS.json',dict(status='PASS',records=records,boundary='Retained real-receipt fixture; external model payload boundary only; final output serialization suppressed to conserve disk.'))

