"""Exercise review/session/certificate builders with local simulated inputs."""
import json,os,shutil,subprocess,tempfile
from pathlib import Path
from packet_config import PINS, ARCHIVE, BINDING, MEMBERS, SNAP, pending_script
from review_policy import build_chain
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='builders_p5_',dir=W))
py=os.sys.executable
os.environ['PATH']=str(Path(py).parent)+':'+os.environ['PATH']
base={'r1.txt':'# REVIEW_VERDICT_R1P: GO AFTER FIXES\n1. HIGH, blocks proof. LOCAL FIXTURE.',
      'r2.txt':'# REVIEW_VERDICT_R1P2: GO AFTER FIXES\n1. MEDIUM, fix needed. LOCAL FIXTURE.',
      'r3.txt':'# REVIEW_VERDICT_R1P3: GO — LOCAL TEST ONLY',
      'r4.txt':'# REVIEW_VERDICT_R1P4: GO — LOCAL ANTECEDENT',
      'r5.txt':'# REVIEW_VERDICT_R1P5: GO — LOCAL ANTECEDENT',
      'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r7.txt':'# Packet A: p_a5dc8f30.tar: GO.',
      'r8.txt':'# Packet A: GO — LOCAL TEST ONLY\n'+PINS['outer']}
def chain(texts):return build_chain(texts,PINS['identity'],PINS['tree'],PINS['outer'])
record=chain(base)
assert record['reviews']['review_r1p']['verdict']=='GO AFTER FIXES'
assert record['reviews']['review_r1p2']['verdict']=='GO AFTER FIXES'
assert record['final_verdict']=='GO' and len(record['reviewers'])==8
assert not record['production_go_granted']
print('PASS conditional antecedents retained; eight reviewers; final exact-archive GO accepted')
final='# Packet A: GO AFTER FIXES\n'+PINS['identity']+'\n1. LOW, non-blocking: Add an optional explanatory note.\n'
assert len(chain(dict(base,**{'r8.txt':final}))['nonblocking_fixes'])==1
assert len(chain(dict(base,**{'r8.txt':final+'2. PASS. The MEDIUM census issue is resolved by fix 7.\n'}))['nonblocking_fixes'])==1
print('PASS final exact-identity GO AFTER FIXES accepts explicit LOW fixes')
cases={
 'missing final':{k:v for k,v in base.items() if k!='r8.txt'},
 'old final':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO\n'+'0'*64}),
 'no go':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: NO-GO\n'+PINS['identity']}),
 'pending':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: PENDING\n'+PINS['identity']}),
 'go if':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO IF a fix lands\n'+PINS['identity']}),
 'ambiguous go':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO / NO-GO\n'+PINS['identity']}),
 'questioned go':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO?\n'+PINS['identity']}),
 'extended hash':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO\n'+PINS['identity']+'0'}),
 'missing antecedent':{k:v for k,v in base.items() if k!='r4.txt'},
 'stale proof-2 final':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO\n2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d'}),
 'medium fix':dict(base,**{'r8.txt':final.replace('LOW','MEDIUM')}),
 'blocking low':dict(base,**{'r8.txt':final.replace('non-blocking','blocking')}),
 'unlabelled fix':dict(base,**{'r8.txt':final+'2. Add another test.\n'}),
 'no fixes listed':dict(base,**{'r6.txt':'# Packet A: GO — LOCAL ANTECEDENT',
      'r8.txt':'# Packet A: GO AFTER FIXES\n'+PINS['identity']}),
 'bad antecedent':dict(base,**{'r1.txt':'# NO-GO'}),
}
for name,texts in cases.items():
 try:chain(texts)
 except ValueError:pass
 else:raise AssertionError('Accepted '+name)
assert chain(dict(base,**{'r8.txt':final.replace('LOW, non-blocking','LOW')}))['final_verdict']=='GO AFTER FIXES'
print('PASS 15 review refusals: missing/stale/negative/ambiguous/conditional/above-LOW/blocking/unlabelled verdicts')
for n in ('review_build.py','review_policy.py','packet_config.py','session_build.py','cert_build.py','cert_policy.py','e.txt'):
 shutil.copyfile(W/n,T/n)
for n,t in base.items():(T/n).write_text(t)
args=[py,'-B',str(T/'review_build.py'),'--r1p',str(T/'r1.txt'),'--r1p2',str(T/'r2.txt'),'--r1p3',str(T/'r3.txt'),'--r1p4',str(T/'r4.txt'),'--r1p5',str(T/'r5.txt'),'--r1p6',str(T/'r6.txt'),'--r1p7',str(T/'r7.txt'),'--r1p8',str(T/'r8.txt')]
(T/'rv1.sh').write_text(pending_script('rv1.sh'))
r=subprocess.run(args,check=True,capture_output=True,text=True)
assert 'READY rv1.sh' in r.stdout
subprocess.run(['bash','-n',str(T/'rv1.sh')],check=True)
root=T/'remote';root.mkdir(mode=0o700)
k=root/Path(PINS['kit']).name;k.mkdir(mode=0o700)
b=root/Path(PINS['bundle']).name;b.mkdir(mode=0o700)
(b/'p.tar').symlink_to(SNAP/PINS['archive']);(b/'BINDING.json').write_text(json.dumps(BINDING))
p=T/'rv_local.sh';p.write_text((T/'rv1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
subprocess.run(['bash',str(p)],check=True,capture_output=True,text=True)
assert json.loads((b/'r1.json').read_text())==record
assert all((b/n).stat().st_mode & 0o777==0o600 for n in ('r1.json','r1.txt','r2.txt','r3.txt','r4.txt','r5.txt','r6.txt','r7.txt','r8.txt'))
r=subprocess.run(['bash',str(p)],capture_output=True,text=True);assert r.returncode!=0
# The low non-blocking branch must print every remaining item to the operator.
low=T/'low';low.mkdir()
for n in ('review_build.py','review_policy.py','packet_config.py'):shutil.copyfile(W/n,low/n)
(low/'r8.txt').write_text(final)
r=subprocess.run([py,'-B',str(low/'review_build.py'),'--r1p',str(T/'r1.txt'),'--r1p2',str(T/'r2.txt'),'--r1p3',str(T/'r3.txt'),'--r1p4',str(T/'r4.txt'),'--r1p5',str(T/'r5.txt'),'--r1p6',str(T/'r6.txt'),'--r1p7',str(T/'r7.txt'),'--r1p8',str(low/'r8.txt')],capture_output=True,text=True,check=True)
assert 'OPERATOR LOW FIX:' in r.stdout and 'Add an optional explanatory note.' in r.stdout
print('PASS rv1 installs exact review bytes and private record; refuses overwrite; prints LOW fixes')
sessions={n:'https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_'+str(i) for i,n in enumerate((T/'e.txt').read_text().split())}
p=T/('sess_'+PINS['run']+'.json');p.write_text(json.dumps(sessions));p.chmod(0o600)
(T/'si1.sh').write_text(pending_script('si1.sh'))
r=subprocess.run([py,'-B',str(T/'session_build.py')],check=True,capture_output=True,text=True)
assert 'https://' not in r.stdout+r.stderr
subprocess.run(['bash','-n',str(T/'si1.sh')],check=True)
shutil.copyfile(T/'e.txt',b/'e.txt')
p=T/'si_local.sh';p.write_text((T/'si1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
r=subprocess.run(['bash',str(p)],check=True,capture_output=True,text=True);assert 'https://' not in r.stdout+r.stderr
assert json.loads((k/'sess.json').read_text())==sessions and (k/'sess.json').stat().st_mode & 0o777==0o600
r=subprocess.run(['bash',str(p)],capture_output=True,text=True);assert r.returncode!=0
print('PASS session exact key set, secret-free output, mode 0600, and overwrite refusal')
# The certificate must come from a classified independent record and the exact exemption.
from cert_policy import EXEMPTION_RECORD,validate_certificate
import copy,hashlib
sha=lambda raw:hashlib.sha256(raw).hexdigest()
scan=('PACKET '+PINS['identity']+' ARCHIVE '+PINS['outer']+' RUN '+PINS['run']+'\nMANIFEST '+'0'*64+'\n').encode()
classified=dict(reviewer='LOCAL FIXTURE ONLY',config_identity=PINS['identity'],inputs=dict(scan_sha256=sha(scan),manifest_sha256_in_scan='0'*64),hits=[dict(id='N1',surface='log line: KH/o/<job>.proof.log',**{'class':'new-visible'})])
raw=json.dumps(classified).encode()
authority=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30')/EXEMPTION_RECORD
exemption=authority.read_bytes()
cert=dict(status='CLEAN',hits=0,reviewer='LOCAL FIXTURE ONLY',config_identity=PINS['identity'],operator_archive_sha256=PINS['outer'],manifest_sha256='0'*64,scan_sha256=sha(scan),scan_record='classified.json',exemption_record=EXEMPTION_RECORD,private_tree_contents_accepted=['N1'],external=[dict(path=PINS['bundle']+'/'+n,sha256=sha(v)) for n,v in MEMBERS.items()])
assert validate_certificate(cert,raw,scan,exemption,PINS,MEMBERS)['exemption_sha256']==sha(exemption)
for change in ('old identity','changed scan','visible argv','unaccepted hit','missing external','changed exemption'):
 c=copy.deepcopy(cert);r=copy.deepcopy(classified);s=scan;e=exemption
 if change=='old identity':c['config_identity']='d8b03fd1'
 if change=='changed scan':s+=b'changed'
 if change=='visible argv':r['hits'][0]['surface']='argv on shared node'
 if change=='unaccepted hit':c['private_tree_contents_accepted']=[]
 if change=='missing external':c['external']=c['external'][:-1]
 if change=='changed exemption':e+=b'changed'
 try:validate_certificate(c,json.dumps(r).encode(),s,e,PINS,MEMBERS)
 except ValueError:pass
 else:raise AssertionError('Accepted '+change)
(T/'classified.json').write_bytes(raw);(T/'scan.out').write_bytes(scan)
(T/'fake_cert.json').write_text(json.dumps(cert));(T/'sc1.sh').write_text(pending_script('sc1.sh'))
subprocess.run([py,'-B',str(T/'cert_build.py'),str(T/'fake_cert.json'),'--scan-record',str(T/'classified.json'),'--scan-output',str(T/'scan.out')],check=True,capture_output=True)
subprocess.run(['bash','-n',str(T/'sc1.sh')],check=True)
assert PINS['kit'] in (T/'sc1.sh').read_text()
print('PASS classified certificate, six refusals, all 37 external pins, exemption SHA, pending installer replacement')
print('No gcloud, network, real session minting, or real approval occurred')
print('Test artifacts:',T)
