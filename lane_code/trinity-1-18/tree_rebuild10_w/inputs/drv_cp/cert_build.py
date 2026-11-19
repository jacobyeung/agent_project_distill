"""Build the certificate installer from independent packet-specific inputs."""
import argparse
import json
from pathlib import Path
from packet_config import PINS, MEMBERS, install_script
from cert_policy import EXEMPTION_RECORD, validate_certificate
W = Path(__file__).resolve().parent
ROOT = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30')
p = argparse.ArgumentParser()
p.add_argument('certificate', type=Path)
p.add_argument('--scan-record', type=Path)
p.add_argument('--scan-output', type=Path, default=W/'scan1.out')
a = p.parse_args()
assert a.certificate.resolve().parent == W and not a.certificate.is_symlink(), 'Certificate must be local'
cert = json.loads(a.certificate.read_text())
record = a.scan_record or Path(cert['scan_record'])
if not record.is_absolute():
    record = ROOT/record if record.parts[0] == 'events' else ROOT/'events'/record
result = validate_certificate(cert, record.read_bytes(), a.scan_output.read_bytes(), (ROOT/EXEMPTION_RECORD).read_bytes(), PINS, MEMBERS)
body = '''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
python3 -B - <<'PYCODE'
import hashlib,json,stat
from pathlib import Path
'''
body += 'k=Path('+repr(PINS['kit'])+');b=Path('+repr(PINS['bundle'])+')\ncert='+repr(result)+'\n'
body += '''def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
assert k.is_dir() and not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
assert b.is_dir() and not b.is_symlink() and stat.S_IMODE(b.stat().st_mode)==0o700
out=k/'ANON_OK.json'
assert not out.is_symlink(), 'linked certificate'
if out.exists():raise SystemExit('REFUSED: existing CLEAN or other certificate; inspect it')
assert sha(b/'p.tar')==cert['operator_archive_sha256']
assert json.loads((b/'BINDING.json').read_text())['config_identity']==cert['config_identity']
assert sha(k/'SHA256SUMS.txt')==cert['manifest_sha256']
seen=set()
for line in (k/'SHA256SUMS.txt').read_text().splitlines():
 digest,name=line.split('  ',1);rel=Path(name)
 assert not rel.is_absolute() and '..' not in rel.parts and name not in seen
 seen.add(name);target=k/rel
 assert not target.is_symlink() and target.is_file() and sha(target)==digest
for entry in cert['external']:
 target=Path(entry['path'])
 assert target.is_relative_to(b) and not target.is_symlink() and sha(target)==entry['sha256']
with out.open('x') as f:json.dump(cert,f,sort_keys=True);f.write('\\n')
out.chmod(0o600)
print('PASS independent CLEAN certificate installed for packet C; classified scan and ORCH 1758Z bound; no production GO')
PYCODE
'''
install_script(W/'sc1.sh', body)
print('READY sc1.sh; packet-C classified scan and ORCH 1758Z exemptions pinned')
