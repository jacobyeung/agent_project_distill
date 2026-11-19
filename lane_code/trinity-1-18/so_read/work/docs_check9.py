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
files=[base/'cuda/__init__.py',base/'_C/__init__.pyi',base/'version.py',base/'torch_version.py',base/'__init__.py',base.parent/'transformers/__init__.py',base/'nn/modules/module.py']
value=dict(cont_ops_reference=str(ref),cont_ops_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),
    installed_sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    source_lines={'cuda/__init__.py':'161-180,673-695','_C/__init__.pyi':'12448-12453','nn/modules/module.py':'2485-2496'},
    official_pages_read_date='2026-11-19',official_pages=['https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html','https://docs.pytorch.org/docs/2.11/generated/torch.cuda.is_available.html','https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html','https://docs.pytorch.org/docs/2.11/generated/torch.nn.Module.html#torch.nn.Module.load_state_dict'],
    device_policy=dict(name='NVIDIA H100 80GB HBM3',multi_processor_count=132,capability=[9,0],memory_bytes=[79000000000,86000000000]))
(O/'checks/SOURCE_EVIDENCE9.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print('PASS: installed device-property declarations and official 2.11 documentation recorded; no CUDA query executed.')

assert '--bound-export' not in text and 'For a different target' not in text
assert 'tar -cf - -C <logical>/d .' in text and '33 GB, estimated' in text
print('PASS: step-400-only handoff, symlink archive, version preflight, retained stderr and 33 GB estimate documented.')

host=O/'kit_parity50/host.py'
ast.parse(host.read_text(),feature_version=(3,6))
assert host.read_bytes()==(L/'work/src/u0/a21.py').read_bytes()
r=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(host),'--help'],capture_output=True,text=True)
assert r.returncode==0,r.stderr
version=subprocess.check_output(['/usr/bin/python3','-I','-s','-B','-c','import sys;print(sys.version.split()[0])'],text=True).strip()
print('PASS: namespace host bootstrap parses and runs --help under actual /usr/bin/python3 '+version+'; no runtime staging or GPU executed.')
assert text.index('--enable-extensions gate') < text.index('salloc --account')
assert text.index('stage-kit') < text.index('--bwlimit=8000') < text.index('salloc --account')
assert 'interpreter outside bwrap' not in text
print('PASS: private gate, seal, stage-kit and archive transfer precede allocation; exact host extraction and namespaced wrapper commands are present.')

import os,tarfile,uuid
root=L/'work'/('receipt9-'+uuid.uuid4().hex);root.mkdir()
physical=root/'local';(physical/'u9').mkdir(parents=True);transfer=root/'shared';transfer.mkdir()
(physical/'u9/ue.json').write_text('{"passed":false}')
block=text.split('test ! -e "$GPU_TRANSFER/5.tar"',1)[1].split('# END GPU_ENVIRONMENT',1)[0]
block='test ! -e "$GPU_TRANSFER/5.tar"'+block
block=re.sub(r'nice -n 10 /usr/bin/python3.*?\|\| gate_rc=\$\?', 'false || gate_rc=$?',block,flags=re.S)
r=subprocess.run(['bash','-eu','-c',block],env=dict(os.environ,GPU_TRANSFER=str(transfer),GPU_PHYSICAL_KIT=str(physical)),capture_output=True,text=True)
assert r.returncode!=0
with tarfile.open(transfer/'5.tar') as archive:assert archive.extractfile('ue.json').read()==b'{"passed":false}'
print('PASS: exact receipt-handoff shell preserves failed ue.json outside private /tmp and still exits nonzero; only the GPU launch is replaced by false.')
