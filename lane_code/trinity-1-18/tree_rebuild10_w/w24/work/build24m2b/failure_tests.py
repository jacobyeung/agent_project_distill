from pathlib import Path
import base64, hashlib, json, os, shutil, subprocess, sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m2b';F=D/'failure_tests';F.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(L/'work/tree_r1'),str(L/'out/kit_n_go/b')]
import joblib as J
from kit24f import reseal
from launch_r1.entry import check_host_runtime
def cap(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
 path.write_text(json.dumps(dict(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest(),encoding='base64')))
k=F/'kit'
def kitcopy(a,b):
 if Path(a).name in ('p.json','BUILD.json','SHA256SUMS.txt'):return shutil.copyfile(a,b)
 os.link(a,b);return b
shutil.copytree(L/'work/build24/kits/n',k,copy_function=kitcopy)
target=F/'target';(target/'o/94/live').mkdir(parents=True)
spec=J.load(k/'k/p.json');spec['n_root']=str(target);cap(k/'k/p.json',spec);reseal(k)
node=F/'node';node.mkdir()
bw=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(node),'/tmp/q_22c714e1','--bind',str(target/'o/94/live'),str(target/'o/94/live'),'--chdir','/tmp/q_22c714e1','--setenv','SLURM_JOB_ID','bad']
with (node/'raw.log').open('w') as log:
 p=subprocess.run(bw+[sys.executable,'-B','-I','-s',str(k/'b/a.py'),'r','/tmp/q_22c714e1/p','/tmp/q_22c714e1/r.json'],stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==1
with (node/'raw.log').open('rb') as inp,(node/'q.log').open('wb') as out:
 subprocess.run(['/usr/bin/python3','-B','-I','-s',str(k/'b/l.py'),str(k)],stdin=inp,stdout=out,check=True)
subprocess.run(['/usr/bin/python3','-B','-I','-s',str(k/'b/rd.py'),str(node),'94',str(p.returncode)],check=True)
assert J.load(target/'o/94/r0.json')['refusal']=='ValueError:R1_ROUTING_JOB_ID_REQUIRED'
assert (target/'o/94/q.log').read_bytes()==(node/'q.log').read_bytes()
assert J.load(target/'o/94/r1.json')['returncode']==1
assert sum(x.stat().st_size for x in (target/'o/94').iterdir() if x.is_file())<5_000_000
# Tail retention remains bounded even after an unusually verbose failure.
with (node/'q.log').open('wb') as out:out.seek(2_100_000);out.write(b'\nLAST\n')
subprocess.run(['/usr/bin/python3','-B','-I','-s',str(k/'b/rd.py'),str(node),'95','7'],check=True)
assert (target/'o/95/q.log').stat().st_size<=2_000_000
assert (target/'o/95/q.log').read_bytes().endswith(b'LAST\n')
assert J.load(target/'o/95/r1.json')['returncode']==7

cfg=J.load(L/'work/build24k/mode_r_test_v5/request.json')['_resolved']['config']
request=J.load(k/'k/h.json');bindir=F/'bin';bindir.mkdir();pool=F/'pool';pool.mkdir()
(bindir/'python3').symlink_to(sys.executable);(bindir/'bash').symlink_to('/bin/bash');(pool/'bwrap').symlink_to('/usr/bin/bwrap')
with patch.dict(os.environ,PATH=str(bindir)):
 try:check_host_runtime(cfg,request,{'assertions':{}})
 except ValueError as e:assert str(e)=='R1_BINARY_MISSING:bwrap'
 else:raise AssertionError('missing binary accepted')
with patch.dict(os.environ,PATH=str(pool)+':'+str(bindir)):
 result={'assertions':{}};check_host_runtime(cfg,request,result)
 assert result['assertions']['runtime_binaries']
J.write(D/'FAILURE_TESTS.json',dict(status='PASS',refusal='R1_ROUTING_JOB_ID_REQUIRED',failed_mode_evidence_published=True,exit_codes_preserved=[1,7],log_cap=2_000_000,total_cap=5_000_000,host_publisher_python='system Python 3.6',binary_before='R1_BINARY_MISSING:bwrap',binary_after='PASS'))
print('refusal, failure publication, cap, system Python and bwrap PATH tests PASS')
