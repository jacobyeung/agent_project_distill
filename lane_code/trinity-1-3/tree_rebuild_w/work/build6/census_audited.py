"""Compare both exact censuses under the package's installed audit hook."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,unquote
L=Path(__file__).resolve().parents[2];lane=L;tree=L/'work/tree_r1';temp_root=L/'work/tmp'
output=L/'work/build6/proofs/census';output.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/build6'));import compact_tmp
source=(L/'work/build6/test_runner.py').read_text();denied=[];reserve_probe=False
start=source.index('def writable(path):');end=source.index('sys.addaudithook(audit)')
exec(compile(source[start:end],str(L/'work/build6/test_runner.py'),'exec'))
sys.addaudithook(audit)
values=[];times=[]
for mode in ('0','1'):
 os.environ['R2_FAST_CENSUS']=mode;t=time.monotonic()
 values.append(compact_tmp.inventory(temp_root));times.append(time.monotonic()-t)
result=dict(equal=values[0]==values[1],files=len(values[0]),bytes=sum(values[0].values()),python_seconds=times[0],native_seconds=times[1],audit_source_sha256=hashlib.sha256(source.encode()).hexdigest())
(output/'EQUIVALENCE.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['equal'];print(json.dumps(result))
