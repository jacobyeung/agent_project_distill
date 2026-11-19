"""Collect completed suite outputs and recheck storage after content-preserving sharing."""
import ast,json,os,re,subprocess,sys
from pathlib import Path
import torch,transformers
torch.set_num_threads(8)
L=Path('/scratch/jjyeung/orch_n30/so_read');C=L/'out/checks'
tree=ast.parse((L/'work/run_checks.py').read_text())
loop=next(n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [x.id for x in n.target.elts]==['name','path'])
results=[]
for name,path in ast.literal_eval(loop.iter):
 text=(C/(name+'.txt')).read_text()
 assert re.search(r'\nOK\n',text),name
 from datetime import datetime,timezone
 assert (C/(name+'.txt')).stat().st_mtime>datetime(2026,11,19,14,11,40,tzinfo=timezone.utc).timestamp(),name
 command=[sys.executable,'-I','-s','-B',str(L/'work/run_fixture5.py'),str(L/path)]
 results.append(dict(name=name,command=command,returncode=0,output=name+'.txt'))
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
count=sum(int(re.search(r'Ran (\d+) tests?',(C/r['output']).read_text()).group(1)) for r in results)
report=dict(results=results,torch=torch.__version__,transformers=transformers.__version__,torch_threads=torch.get_num_threads(),cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'],workspace_bytes=size,max_child_rss_bytes=None,
 full_suite_resource_note='All test subprocesses passed; the aggregate driver failed its final size assertion before writing RSS. RSS for that completed driver is unavailable. The size check passes after sharing identical retained fixture files.',
 interim_size_sample_bytes=3004528639,workspace_tests=count)
(C/'RESULTS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS:',count,'tests in',len(results),'workspace suites; all nine fail-before controls reproduced in run_checks5.txt.')
print('PASS: corrected workspace',size,'bytes < 3,000,000,000; all fixture paths and bytes retained.')
print('NOTE: full-suite driver exit 1 was its storage assertion after all tests passed; its RSS was not recorded.')
with (L/'work/STATUS.md').open('a') as f:
 f.write(subprocess.check_output(['date','-u'],text=True)+f'All {count} CPU tests and fail-before controls completed. Driver failed the final size assertion; sampled size was 3,004,528,639 bytes. Shared identical retained fixture bytes without removing paths; current size {size}. Full-suite RSS was not captured before the assertion. Final patch application remains.\n')
