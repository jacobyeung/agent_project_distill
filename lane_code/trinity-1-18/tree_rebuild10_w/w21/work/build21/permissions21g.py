from pathlib import Path
import datetime,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
view=J.load(D/'VIEW.json');probe=D/'proofs/view/permissions.py'
probe.write_text('''from pathlib import Path
import errno,json,os,sys
p=Path('/tmp/q_21g_probe');p.mkdir();(p/'a').write_text('q')
refused=[]
for root in ['/home/jjyeung',sys.argv[1]]:
 try:(Path(root)/'q_21g_probe').write_text('q')
 except OSError as e:
  assert e.errno in (errno.EROFS,errno.EACCES),(root,e)
  refused.append(root)
 else:raise AssertionError(root)
print(json.dumps(dict(tmp_writable=True,tmp_uid=Path('/tmp').stat().st_uid,uid=os.getuid(),readonly=refused)))
''')
args=J.load(D/'proofs/view/after.json')+[sys.executable,'-I','-s','-B',str(probe),view['variables']['P']]
p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
J.write(D/'PERMISSIONS.json',dict(command=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
assert p.returncode==0,p.stderr
print(p.stdout)
