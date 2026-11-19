"""Check executable handoff syntax, unchanged cont_ops assertions and source evidence."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
text=(O/'kit_parity50/README.md').read_text()
blocks=re.findall(r'```bash\n(.*?)\n```',text,re.S)
for b in blocks:
    r=subprocess.run(['bash','-n'],input=b,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    for code in re.findall(r"<<'PYASSET'\n(.*?)\nPYASSET",b,re.S):ast.parse(code,feature_version=(3,6))
assert '$LOCAL/step600' not in text and '$LOCAL/5.tar' not in text
assert '-s -E -B ./unpack_return.py' in text and 'salloc --account=mt01' in text
print('PASS:',len(blocks),'README shell blocks parse; archive-validation heredoc parses as Python 3.6; host paths and allocation documented.')
tree=ast.parse((L/'work/src/u0/a20.py').read_text())
submit=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SUBMIT_CHECK' for t in n.targets))
ast.parse(submit,feature_version=(3,6))
ref=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/o_sub_A4.sh')
reference=ref.read_text().split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0]
assert reference in submit
for name in ('package/a/5.py','unpack_return.py','tower_sequence.py'):ast.parse((L/'work/operator4'/name).read_text(),feature_version=(3,6))
print('PASS: cont_ops CPU assertion block remains verbatim; submit and operator helpers parse as Python 3.6.')
base=Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch')
files=[base/'cuda/__init__.py',base/'_C/__init__.pyi']
value=dict(cont_ops_reference=str(ref),cont_ops_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),
    installed_sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    source_lines={'cuda/__init__.py':'673-690','_C/__init__.pyi':'12448-12453'},
    official_pages_read_utc='2026-11-19T16:36:06Z',official_pages=['https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html'],
    device_policy=dict(name='NVIDIA H100 80GB HBM3',multi_processor_count=132,capability=[9,0],memory_bytes=[79000000000,86000000000]))
(O/'checks/SOURCE_EVIDENCE7.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print('PASS: installed device-property declarations and official 2.11 documentation recorded; no CUDA query executed.')
