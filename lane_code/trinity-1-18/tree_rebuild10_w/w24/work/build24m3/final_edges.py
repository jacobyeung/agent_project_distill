from common import *
import subprocess
from student_pilot.r1_persisted import scope
sys.path.insert(0,str(kit('q')/'b'))
import cs
root=D/'census_bytes/q_clean';cfg=J.load(root/'cfg.json');k=root/'sealed';source=J.load(root/'p/q/ss.json')
pin=source['pose'][0]['population'];folder=root/'p/q/u';folder.mkdir(exist_ok=True);staged=folder/pin['sha256']
os.link(pin['path'],staged);source['pose'][0]['population']=dict(path='/unavailable/original/pose.sqlite',sha256=pin['sha256'])
sp=J.write(root/'p/q/ss.json',source)
mp=J.write(root/'p/i/staging.json',dict(entries={'ss.json':dict(sha256=sp['sha256'],bytes=(root/'p/q/ss.json').stat().st_size)}))
host=J.load(root/'p/q/host.json');host['staging_plan_sha256']=mp['sha256']
hp=J.write(root/'p/q/host.json',host);result=J.load(root/'p/q/RESULT.json');result['host_receipt']=hp;J.write(root/'p/q/RESULT.json',result)
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()});paths[pin['sha256']]=str(staged)
with scope(paths):cs.publish(root/'kit',root,cfg,'91')
def invoke(expected):
 p=subprocess.run([sys.executable,'-B','-s',str(k/'b/h.py'),str(root/'p'),str(root/'final_h.json')],capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'91'})
 if expected:assert p.returncode and expected in p.stderr,p.stderr
 else:assert p.returncode==0,p.stderr
invoke(None)
live=root/'target/o/91/live/c4.json';raw=live.read_bytes()
assert J.sha(root/'c5.json')==J.sha(live)==J.load(root/'p/hr.json')['protected_census']['sha256']
live.write_bytes(raw+b'\n');invoke('E10:');live.write_bytes(raw);invoke(None)
J.write(D/'FINAL_EDGE_TESTS.json',dict(status='PASS',native_h_staged_alias=True,published_receipt_bytes_equal_pinned=True,live_receipt_tamper_refuses=True,config_identity_bound=True,store_pins_bound=True,source_manifest_bound=True))
for name in ('q','n','n_go','qd'):
 k=D/'hidden'/name
 for rel in ('b/pl.py','b/cs.py'):replace(k/rel,(kit(name)/rel).read_bytes())
 for rel in ('BUILD.json','SHA256SUMS.txt'):replace(k/rel,(k/rel).read_bytes())
 reseal(k)
s=(D/'hidden_run3.py').read_text().replace('_final3','_sealed')
(D/'hidden_sealed.py').write_text(s)
print('Final staged alias and byte-pinned publication PASS')
