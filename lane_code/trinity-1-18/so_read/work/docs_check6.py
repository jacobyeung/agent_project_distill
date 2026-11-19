"""Validate the documented shell blocks and the exact adopted CPU assertions."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
readme=(L/'out/kit_parity50/README.md').read_text()
blocks=re.findall(r'```bash\n(.*?)\n```',readme,re.S)
for block in blocks:
    result=subprocess.run(['bash','-n'],input=block,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
print('PASS:',len(blocks),'README shell blocks parse; owner operations were not executed.')
tree=ast.parse((L/'work/src/u0/a20.py').read_text())
submit=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='SUBMIT_CHECK' for t in n.targets))
ast.parse(submit,feature_version=(3,6))
ref=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/o_sub_A4.sh')
reference=ref.read_text().split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0]
assert reference in submit
print('PASS: complete cont_ops A4 CPU assertion block is verbatim; SUBMIT_CHECK parses as Python 3.6.')
for name in ('package/a/5.py','unpack_return.py','tower_sequence.py'):
    ast.parse((L/'work/operator4'/name).read_text(),feature_version=(3,6))
print('PASS: changed operator helpers parse as Python 3.6.')
base=Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch')
files=[base/'cuda/__init__.py',base/'_C/__init__.pyi']
receipt=dict(cont_ops_reference=str(ref),cont_ops_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),
    installed_sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    source_lines={'cuda/__init__.py':'641-695','_C/__init__.pyi':'12448-12453'},
    official_pages_read_utc='2026-11-19',official_pages=[
        'https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html',
        'https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_capability.html'])
(L/'out/checks/SOURCE_EVIDENCE6.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print('PASS: source hashes and official device-property references recorded; no CUDA call executed.')
