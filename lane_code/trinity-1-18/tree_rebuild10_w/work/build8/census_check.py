import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
sys.path.insert(0,str(B));import compact_tmp as new
spec=importlib.util.spec_from_file_location('old_census',L/'work/build6/compact_tmp.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
P=B/'proofs/census';P.mkdir(parents=True,exist_ok=True)
root=L/'work/tmp/b7_census_fixture';root.mkdir(exist_ok=True)
for name,data in [('a',b'a'*600),('b',b'b'*700),('c',b'c'*20)]: (root/name).write_bytes(data)
os.environ['R2_FAST_CENSUS']='0'
before=old.inventory(root);after=new.inventory(root)
assert {str(k):v for k,v in before.items()}==after
new.compact(root,files=after,preserved_files={root/'a'},package_files={root/'b'})
assert (root/'a').read_bytes()==b'a'*600 and (root/'b').read_bytes()==b'b'*700
new.compact(root,files=new.inventory(root),protected=(root/'a',),preserved_files={str(root/'b')})
assert (root/'a').read_bytes()==b'a'*600 and (root/'b').read_bytes()==b'b'*700
# The package test will retain a fresh census on both sides of every test.
times=[];values=[]
for name,module in [('path_keys',old),('string_keys',new),('native_string_keys',new)]:
 os.environ['R2_FAST_CENSUS']='1' if name=='native_string_keys' else '0'
 t=time.monotonic();v=module.inventory(L/'work/tmp');times.append(dict(method=name,seconds=time.monotonic()-t,files=len(v),bytes=sum(v.values())))
 values.append({str(k):n for k,n in v.items()})
changed=[k for k in values[0].keys()|values[1].keys()|values[2].keys() if values[0].get(k)!=values[1].get(k) or values[0].get(k)!=values[2].get(k)]
result=dict(fixture_exact=True,protected_files_retained=True,measurements=times,
 concurrent_packet_changes=changed,exact_live_equality=not changed,
 source_sha256=hashlib.sha256((B/'compact_tmp.py').read_bytes()).hexdigest())
(P/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
