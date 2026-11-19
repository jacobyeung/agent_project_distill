from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';A=L/'attic/build24b'
for name in ('UPLOADS_q.json','UPLOADS_n.json','KIT.json'):
 p=B/name;shutil.copyfile(p,A/name);p.write_bytes((D/name).read_bytes())
p=D/'proofs/resolver600';p.rename(A/'resolver600_attempt')
p=B/'resolver_tests.py';s=p.read_text();old="        with R.external_boundary(f):result=J.resolve(R.K,f['pool'],f['listing'],O/'real400.json')"
new='''        original=J.load;sp=deepcopy(original(R.K/'k/p.json'))
        with tarfile.open(f['m']/'s.tar') as archive:sp['m4']['v']=hashlib.sha256(archive.extractfile('MANIFEST.json').read()).hexdigest()
        tokens=(f['pool']/sp['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();sp['m4'].update(t=tokens[2],b=int(tokens[1]))
        with R.external_boundary(f),patch.object(J,'load',side_effect=lambda p:deepcopy(sp) if Path(p)==R.K/'k/p.json' else original(p)):
            result=J.resolve(R.K,f['pool'],f['listing'],O/'real400.json')'''
assert old in s;s=s.replace(old,new);p.write_text(s)
