"""Package the independent proof-2 certificate after checking its classified scan."""
import argparse,json
from pathlib import Path
from packet_config import PINS, MEMBERS, render, install_script
from cert_policy import EXEMPTION_RECORD, validate_certificate
W=Path(__file__).resolve().parent
ROOT=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30')
p=argparse.ArgumentParser()
p.add_argument('certificate',type=Path)
p.add_argument('--scan-record',type=Path)
p.add_argument('--scan-output',type=Path,default=W/'scan1.out')
p.add_argument('--exemption',type=Path,default=ROOT/EXEMPTION_RECORD)
a=p.parse_args();path=a.certificate.resolve()
if not path.is_relative_to(W):raise SystemExit('Certificate must be under the driver work directory')
d=json.loads(path.read_text())
record=a.scan_record or ROOT/d['scan_record']
d=validate_certificate(d,record.read_bytes(),a.scan_output.read_bytes(),a.exemption.read_bytes(),PINS,MEMBERS)
body='''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
python3 -B - <<'PYCODE'
import hashlib,json,stat,sys
from pathlib import Path
k=Path('@KIT@');b=Path('@BUNDLE@')
assert not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
'''
body+='d='+repr(d)+'\n'
body+='''assert d['config_identity']=='@IDENTITY@' and d['operator_archive_sha256']=='@OUTER@'
assert d['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
assert hashlib.sha256((b/'p.tar').read_bytes()).hexdigest()=='@OUTER@'
for entry in d['external']:
 p=Path(entry['path']);assert p.is_relative_to(b) and not p.is_symlink()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
p=k/'ANON_OK.json';assert not p.is_symlink()
if p.exists():assert json.loads(p.read_text()).get('status')!='CLEAN', 'REFUSED: existing CLEAN certificate'
# The fresh deriver does not create ANON_OK. Verify the manifest before writing it.
expected=set()
for line in (k/'SHA256SUMS.txt').read_text().splitlines():
 digest,name=line.split('  ',1);member=k/name
 assert name not in expected and not member.is_symlink() and member.resolve().is_relative_to(k.resolve())
 assert hashlib.sha256(member.read_bytes()).hexdigest()==digest
 expected.add(name)
actual={str(p.relative_to(k)) for directory in ('b','k') for p in (k/directory).rglob('*') if p.is_file()}
actual.update(name for name in ('job.sh','job8.sh') if (k/name).is_file())
assert actual==expected, 'Kit inventory differs'
with p.open('w') as f:json.dump(d,f,sort_keys=True);f.write('\\n')
p.chmod(0o600)
sys.path.insert(0,str(k/'b'));import a;a.main(k)
print('PASS independent CLEAN certificate installed for proof 2; classified scan and ORCH 1758Z bound; no production GO')
PYCODE
'''
install_script(W/'sc1.sh',render(body))
print('READY sc1.sh; proof-2 classified scan and ORCH 1758Z exemptions pinned')
