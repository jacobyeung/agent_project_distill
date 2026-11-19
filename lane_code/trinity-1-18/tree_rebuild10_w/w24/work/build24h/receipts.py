from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path.insert(0,str(L/'work/build24'));import joblib as J

def put(p,s):
 old=L/'attic/build24h'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and not old.exists():p.rename(old)
 p.write_text(s)
for k in (L/'work/build24/kits/n',L/'out/kit_n_go'):
 put(k/'b/h.py',(D/'h.py').read_text())
 s=(k/'b/a.py').read_text()
 # Capture actual entry.frame_host returns only. This does not invent a PASS.
 marker="if sys.argv[1]=='q':\n"
 insertion="""from launch_r1 import entry as host_entry
from student_pilot.p3_provenance import write as host_write
original_host = host_entry.frame_host
def recorded_host(*args, **kwargs):
 result = original_host(*args, **kwargs)
 host_write(root/'host.json',result)
 return result
host_entry.frame_host = recorded_host
"""
 assert s.count(marker)==1;s=s.replace(marker,insertion+marker)
 put(k/'b/a.py',s)
 s=(k/'b/z.py').read_text()
 marker="    cfgpin=write(root/'n.json',resolved['config'])"
 insertion="""    review=load(kit/'k/a.json').get('review')
    if review is not None:
        if not isinstance(review,dict) or set(review)!={'path','sha256'}:
            raise ValueError('R1_REVIEW_PIN_INVALID')
        review_sha=review['sha256']
        if not isinstance(review_sha,str) or len(review_sha)!=64 or any(c not in '0123456789abcdef' for c in review_sha) or review['path']!='u/'+review_sha:
            raise ValueError('R1_REVIEW_PIN_INVALID')
        review_source=Path(spec['n_root'])/review['path']
        if not review_source.is_file() or review_source.is_symlink():
            raise ValueError('R1_REVIEW_RECEIPT_MISSING')
        review_raw=review_source.read_bytes()
        if hashlib.sha256(review_raw).hexdigest()!=review_sha:
            raise ValueError('R1_REVIEW_RECEIPT_CHANGED')
        (u/review_sha).write_bytes(review_raw)
        resolved['paths'][review_sha]=ns+'/'+review['path']
        resolved['request']['staged_pins'].append(dict(path=ns+'/'+review['path'],sha256=review_sha))
"""
 assert marker in s;s=s.replace(marker,insertion+marker)
 put(k/'b/z.py',s)
print('strict receipt attachment installed; q has no native frame_host producer')
