"""Read-only adapter to pinned sb_kbox4 training outputs, not a live geometry API."""
from common import *
import gzip
from functools import lru_cache

@lru_cache(maxsize=1)
def binding():return js(ROOT/'inputs/KBOX_SNAPSHOT.json')

@lru_cache(maxsize=1)
def capture(canonical):
 b=binding();entry=b['captures'].get(canonical)
 if entry is None:raise Missing('Registered training capture '+canonical)
 path=ROOT/entry['snapshot_path']
 if sha(path)!=entry['snapshot_sha256']:raise ValueError('Box snapshot changed')
 return json.loads(gzip.decompress(read(path)))

def object_source(canonical, arm):
 rows=[r for r in capture(canonical)['items'] if r['arm']==arm]
 if not rows:raise Missing(canonical+' '+arm)
 return rows

def count_objects(canonical, arm):
 result={}
 for row in object_source(canonical,arm):
  for name,d in row['diagnostics'].items():
   value={k:d.get(k) for k in ('n_all','n_conf','n_operand')}
   if name in result and result[name]!=value:raise ValueError('Inconsistent object count')
   result[name]=value
 return result

def stage1_replay():
 b=binding();p=ROOT/b['replay']['path']
 if sha(p)!=b['replay']['sha256']:raise ValueError('Replay receipt changed')
 r=js(p)
 if r['status']!='PASS':raise Missing('Serving reference replay did not pass')
 return r

def price_k1_tracks(*args,**kwargs):
 raise Missing('/scratch/jjyeung/orch_n30/sb_kbox4/box_math.py::price_k1_tracks and completed K1 CUDA tracks')
