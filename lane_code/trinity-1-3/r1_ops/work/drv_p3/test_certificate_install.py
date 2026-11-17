"""Install a synthetic certificate only into the existing local READY fixture."""
import hashlib,json,os,shlex,subprocess,sys,tempfile
from pathlib import Path
from packet_config import PINS,MEMBERS,SNAP,fixture
from cert_policy import EXEMPTION_RECORD
W=Path(__file__).resolve().parent;ready=Path(sys.argv[1]).resolve();T=Path(tempfile.mkdtemp(prefix='cert_p3_',dir=W))
assert ready.is_relative_to(W) and ready.name=='derived_ready'
# Hardlink only immutable bundle members within the writable test tree.
b=T/'b';b.mkdir(mode=0o700)
source=fixture()
for name in MEMBERS:
 p=b/name;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);os.link(source/name,p)
(b/'p.tar').symlink_to(SNAP/PINS['archive'])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
manifest=sha((ready/'SHA256SUMS.txt').read_bytes())
scan=('PACKET '+PINS['identity']+' ARCHIVE '+PINS['outer']+' RUN '+PINS['run']+'\nMANIFEST '+manifest+'\n').encode()
review=dict(reviewer='LOCAL TEST ONLY',config_identity=PINS['identity'],inputs=dict(scan_sha256=sha(scan),manifest_sha256_in_scan=manifest),hits=[])
cert=dict(status='CLEAN',hits=0,reviewer='LOCAL TEST ONLY',config_identity=PINS['identity'],operator_archive_sha256=PINS['outer'],manifest_sha256=manifest,scan_sha256=sha(scan),scan_record='classified.json',exemption_record=EXEMPTION_RECORD,external=[dict(path=PINS['bundle']+'/'+n,sha256=sha(v)) for n,v in MEMBERS.items()])
for name in ('cert_build.py','cert_policy.py','packet_config.py'):(T/name).write_bytes((W/name).read_bytes())
(T/'scan.out').write_bytes(scan);(T/'classified.json').write_text(json.dumps(review));(T/'ANON_OK.json').write_text(json.dumps(cert))
subprocess.run([sys.executable,'-B',str(T/'cert_build.py'),str(T/'ANON_OK.json'),'--scan-record',str(T/'classified.json'),'--scan-output',str(T/'scan.out')],check=True,capture_output=True,text=True)
local=(T/'sc1.sh').read_text().replace(PINS['kit'],str(ready)).replace(PINS['bundle'],str(b)).replace('python3 -B',shlex.quote(sys.executable)+' -B')
(T/'local.sh').write_text(local)
r=subprocess.run(['bash',str(T/'local.sh')],capture_output=True,text=True,env=dict(os.environ,PATH=str(Path(sys.executable).parent)+':'+os.environ['PATH']))
assert r.returncode==0,(r.stdout,r.stderr)
assert json.loads((ready/'ANON_OK.json').read_text())['reviewer']=='LOCAL TEST ONLY'
assert (ready/'ANON_OK.json').stat().st_mode & 0o777==0o600
r=subprocess.run(['bash',str(T/'local.sh')],capture_output=True,text=True,env=dict(os.environ,PATH=str(Path(sys.executable).parent)+':'+os.environ['PATH']))
assert r.returncode!=0 and 'existing CLEAN' in r.stderr
print('PASS synthetic certificate installs into a fresh READY fixture without an existing ANON_OK; all member hashes verified; mode 0600; existing CLEAN refused')
print('No production certificate was created; test artifacts:',T)
