from common import *
import subprocess,importlib.util
F=D/'discovery_shell_protected_final';node=F/'nodes/q_22c714e1_94';k=F/'kit';live=F/'target/o/94/live'
report=node/'c5.json';pub=live/'c4.json';raw=report.read_bytes();assert pub.read_bytes()==raw
cfg=J.load(node/'v.json');seals={n:J.seal(kit(n)) for n in ('q','n','n_go','qd')}
args=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(node),str(node),'--bind',str(node),'/tmp/q_22c714e1','--bind',str(F/'target'),str(F/'target'),sys.executable,'-B','-s',str(k/'b/rv.py'),'/tmp/q_22c714e1','/tmp/q_22c714e1/v.json','94']
records=[]
for case,code in [('missing','R1_CENSUS_RECEIPT_MISSING'),('identity','R1_CENSUS_IDENTITY_DIFFERS'),('store','R1_CENSUS_STORE_PINS_DIFFER:pointing'),('source','R1_CENSUS_SOURCE_PINS_DIFFER:pointing'),('keyhash','R1_REVIEW_FILE_UNUSABLE'),('pin','R1_CENSUS_RECEIPT_PIN_DIFFERS')]:
 value=json.loads(raw)
 if case=='missing':report.rename(node/'c5_retained_missing.json')
 else:
  if case=='identity':value['config_identity']='0'*64
  if case=='store':value['streams']['pointing']['store_pins']['count']+=1
  if case=='source':value['streams']['pointing']['source_pins'][0]['count']+=1
  if case=='keyhash':value['streams']['pointing']['protected_keys']['sha256']='0'*64
  body=(json.dumps(value,indent=1)+'\n').encode();replace(report,body);replace(pub,body)
 p=subprocess.run(args,capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'94'})
 replace(D/('rv_final_'+case+'.log'),p.stdout+p.stderr)
 refusal=J.load(live/'REVIEW_REFUSED.json')['refusal']
 if case=='missing':(node/'c5_retained_missing.json').rename(report)
 else:replace(report,raw)
 replace(pub,raw)
 assert p.returncode and refusal.startswith(code),(case,p.returncode,refusal)
 records.append(dict(case=case,refusal=refusal))
p=subprocess.run(args,capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'94'});assert p.returncode==0,(p.stdout,p.stderr)
assert J.sha(live/'h0.json')==cfg['r1_training']['host_receipt']['sha256'];assert J.load(live/'h0.json')['protected_census']['sha256']==J.sha(pub)
sp=importlib.util.spec_from_file_location('delta',L/'out/bind_protected.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
pose=D/'pose_role_fixture.jsonl';pose.write_text('{"row_key":"fixture-pose"}\n')
try:mod.apply(L,'pose',pose)
except ValueError as e:assert str(e).startswith('R1_ROLE_LIST_REQUIRES_TREE_DELTA:');refusal=str(e)
else:raise AssertionError('Tree C accepted a role delta')
assert seals=={n:J.seal(kit(n)) for n in seals}
J.write(D/'RV_AND_DELTA_TESTS.json',dict(status='PASS',rv=records,clean_discovery='WAITING_REVIEW',census_status=J.load(pub)['status'],published_pins_match=True,delta_refusal=refusal,kits_unchanged=seals))
print('rv tamper/missing/stale checks, qd continuation and C role-delta refusal PASS')
