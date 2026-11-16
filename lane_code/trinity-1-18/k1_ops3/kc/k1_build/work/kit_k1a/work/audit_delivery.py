import ast,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
L=Path(__file__).resolve().parents[1];O=L/'out'
required=['CAPTURES.json','RUNCARD_K1.md','K1_RULES.json','K1_RULES.sha256','PROOFS.md','HEAVY_IO_QUESTION.md','DESIGN_RECORD.md','DESIGN_RECORD_b6_build_20261115.md','FIRST_BATCH_32.jsonl','STAGING_REQUIREMENTS.json']
assert all((O/n).is_file() for n in required)
proofs={n:json.loads((O/(n+'_RESULT.json')).read_text())['status'] for n in ['P1','P2','P3','P4','P5','P6','P7','KIT','HANDOFF']}
assert all(v=='PASS' for v in proofs.values()),proofs
p2=json.loads((O/'P2_RESULT.json').read_text())
original={p:h for p,h in p2['input_sha256'].items() if p.endswith(('/build.py','/fit.py','/fit_pairs.py','/setlib.py'))}
assert all(gate.sha(p)==h for p,h in original.items())
assert gate.sha(O/'K1_RULES.json')==(O/'K1_RULES.sha256').read_text().split()[0]
for p in (L/'work').rglob('*.py'):ast.parse(p.read_text())
receipts=list((L/'work/refit').rglob('FIT_RECEIPT.json'))
assert all({'python','numpy','sklearn'}<=set(json.loads(p.read_text())['versions']) for p in receipts)
import torch
env=dict(interpreter=sys.executable,torch_version=torch.__version__,compiled_cuda=torch.version.cuda,device_query_performed=False)
(O/'GPU_ENVIRONMENT_METADATA.json').write_text(json.dumps(env,indent=2)+'\n')
files={str(p.relative_to(L)):gate.sha(p) for p in (L/'work').rglob('*.py')}
size=sum(p.stat().st_size for p in L.rglob('*') if p.is_file());assert size<2_000_000_000
report=dict(status='PASS',proofs=proofs,original_fit_code_unchanged=True,fit_receipts_with_versions=len(receipts),
 code_sha256=files,rules_sha256=gate.sha(O/'K1_RULES.json'),lane_bytes=size,gpu_environment=env,
 real_gpu_execution=False,production_ready=False,staging_performed=False)
(O/'DELIVERY_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='code_sha256'},indent=2))
