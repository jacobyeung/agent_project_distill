import json,sys
from pathlib import Path
sys.path.insert(0,'.')
from packet_config import PINS, MEMBERS
from cert_policy import EXEMPTION_RECORD, validate_certificate
ROOT=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30')
cert=json.loads(Path('/tmp/jjyeung_cpanon_ANON_OK.json').read_text())
record=Path(cert['scan_record']); record=ROOT/record if record.parts[0]=='events' else ROOT/'events'/record
scan=Path('/scratch/jjyeung/orch_n30/r1_ops6/work/xfer/scan1.out')
r=validate_certificate(cert,record.read_bytes(),scan.read_bytes(),(ROOT/EXEMPTION_RECORD).read_bytes(),PINS,MEMBERS)
print('PASS',Path.cwd(),len(MEMBERS),r['scan_record_sha256'],r['exemption_sha256'],r['production_go_granted'])
