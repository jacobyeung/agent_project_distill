"""Exercise review/session/certificate builders with local simulated inputs."""
import json,os,shutil,subprocess,tempfile
from pathlib import Path
from packet_config import PINS, ARCHIVE, BINDING
from review_policy import build_chain
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='builders_final_',dir=W))
py=os.sys.executable
base={'r1.txt':'# REVIEW_VERDICT_R1P: GO AFTER FIXES\n1. HIGH, blocks proof. LOCAL FIXTURE.',
      'r2.txt':'# REVIEW_VERDICT_R1P2: GO AFTER FIXES\n1. MEDIUM, fix needed. LOCAL FIXTURE.',
      'r3.txt':'# REVIEW_VERDICT_R1P3: GO — LOCAL TEST ONLY\n'+PINS['outer']}
def chain(texts):return build_chain(texts,PINS['identity'],PINS['tree'],PINS['outer'])
record=chain(base)
assert record['reviews']['review_r1p']['verdict']=='GO AFTER FIXES'
assert record['reviews']['review_r1p2']['verdict']=='GO AFTER FIXES'
assert record['final_verdict']=='GO' and len(record['reviewers'])==3
assert not record['production_go_granted']
print('PASS conditional antecedents retained; three reviewers; final exact-archive GO accepted')
final='# REVIEW_VERDICT_R1P3: GO AFTER FIXES\n'+PINS['identity']+'\n1. LOW, non-blocking: Add an optional explanatory note.\n'
assert len(chain(dict(base,**{'r3.txt':final}))['nonblocking_fixes'])==1
assert len(chain(dict(base,**{'r3.txt':final+'2. PASS. The MEDIUM census issue is resolved by fix 7.\n'}))['nonblocking_fixes'])==1
print('PASS final exact-identity GO AFTER FIXES accepted only for explicit LOW non-blocking fixes')
cases={
 'missing final':{k:v for k,v in base.items() if k!='r3.txt'},
 'old final':dict(base,**{'r3.txt':'# GO\n'+'0'*64}),
 'no go':dict(base,**{'r3.txt':'# NO-GO\n'+PINS['identity']}),
 'pending':dict(base,**{'r3.txt':'# PENDING\n'+PINS['identity']}),
 'go if':dict(base,**{'r3.txt':'# GO IF a fix lands\n'+PINS['identity']}),
 'medium fix':dict(base,**{'r3.txt':final.replace('LOW','MEDIUM')}),
 'blocking low':dict(base,**{'r3.txt':final.replace('non-blocking','blocking')}),
 'unlabelled fix':dict(base,**{'r3.txt':final+'2. Add another test.\n'}),
 'no fixes listed':dict(base,**{'r3.txt':'# GO AFTER FIXES\n'+PINS['identity']}),
 'ambiguous severity':dict(base,**{'r3.txt':final.replace('LOW, non-blocking','LOW')}),
 'bad antecedent':dict(base,**{'r1.txt':'# NO-GO'}),
}
for name,texts in cases.items():
 try:chain(texts)
 except ValueError:pass
 else:raise AssertionError('Accepted '+name)
print('PASS 11 review refusals: missing/stale/negative/conditional/above-LOW/blocking/unlabelled verdicts')
for n in ('review_build.py','review_policy.py','packet_config.py','session_build.py','cert_build.py','e.txt'):
 shutil.copyfile(W/n,T/n)
for n,t in base.items():(T/n).write_text(t)
args=[py,'-B',str(T/'review_build.py'),'--r1p',str(T/'r1.txt'),'--r1p2',str(T/'r2.txt'),'--r1p3',str(T/'r3.txt')]
r=subprocess.run(args,check=True,capture_output=True,text=True)
assert 'READY rv1.sh' in r.stdout
subprocess.run(['bash','-n',str(T/'rv1.sh')],check=True)
root=T/'remote';root.mkdir(mode=0o700)
k=root/Path(PINS['kit']).name;k.mkdir(mode=0o700)
b=root/Path(PINS['bundle']).name;b.mkdir(mode=0o700)
(b/'p.tar').write_bytes(ARCHIVE);(b/'BINDING.json').write_text(json.dumps(BINDING))
p=T/'rv_local.sh';p.write_text((T/'rv1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
subprocess.run(['bash',str(p)],check=True,capture_output=True,text=True)
assert json.loads((b/'r1.json').read_text())==record
assert all((b/n).stat().st_mode & 0o777==0o600 for n in ('r1.json','r1.txt','r2.txt','r3.txt'))
r=subprocess.run(['bash',str(p)],capture_output=True,text=True);assert r.returncode!=0
# The low non-blocking branch must print every remaining item to the operator.
low=T/'low';low.mkdir()
for n in ('review_build.py','review_policy.py','packet_config.py'):shutil.copyfile(W/n,low/n)
(low/'r3.txt').write_text(final)
r=subprocess.run([py,'-B',str(low/'review_build.py'),'--r1p',str(T/'r1.txt'),'--r1p2',str(T/'r2.txt'),'--r1p3',str(low/'r3.txt')],capture_output=True,text=True,check=True)
assert 'OPERATOR LOW NON-BLOCKING:' in r.stdout and 'Add an optional explanatory note.' in r.stdout
print('PASS rv1 installs exact review bytes and private record; refuses overwrite; prints LOW non-blocking fixes')
sessions={n:'https://storage.googleapis.com/upload/LOCAL_TEST_FAKE_'+str(i) for i,n in enumerate((T/'e.txt').read_text().split())}
p=T/('sess_'+PINS['run']+'.json');p.write_text(json.dumps(sessions));p.chmod(0o600)
r=subprocess.run([py,'-B',str(T/'session_build.py')],check=True,capture_output=True,text=True)
assert 'https://' not in r.stdout+r.stderr
subprocess.run(['bash','-n',str(T/'si1.sh')],check=True)
shutil.copyfile(T/'e.txt',b/'e.txt')
p=T/'si_local.sh';p.write_text((T/'si1.sh').read_text().replace('/project/community/jjyeung/okh7',str(root)))
r=subprocess.run(['bash',str(p)],check=True,capture_output=True,text=True);assert 'https://' not in r.stdout+r.stderr
assert json.loads((k/'sess.json').read_text())==sessions and (k/'sess.json').stat().st_mode & 0o777==0o600
r=subprocess.run(['bash',str(p)],capture_output=True,text=True);assert r.returncode!=0
print('PASS session exact key set, secret-free output, mode 0600, and overwrite refusal')
cert=dict(status='CLEAN',hits=0,reviewer='LOCAL FIXTURE ONLY',manifest_sha256='0'*64,scan_sha256='1'*64,external=[dict(path=PINS['bundle']+'/p.py',sha256='2'*64)])
(T/'fake_cert.json').write_text(json.dumps(cert))
subprocess.run([py,'-B',str(T/'cert_build.py'),str(T/'fake_cert.json')],check=True,capture_output=True)
subprocess.run(['bash','-n',str(T/'sc1.sh')],check=True)
assert PINS['kit'] in (T/'sc1.sh').read_text()
print('PASS certificate builder targets final kit; simulated certificate syntax only')
print('No gcloud, network, real session minting, or real approval occurred')
print('Test artifacts:',T)
