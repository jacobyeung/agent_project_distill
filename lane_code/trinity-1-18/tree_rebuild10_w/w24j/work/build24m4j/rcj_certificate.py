from common import *
import re,ast
p=L/'out/rcj/rcj.sh';s=p.read_text();bindings=[];names=set()
for i,line in enumerate(s.splitlines(),1):
 found=re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)=',line)
 # Scheduler directives are resource declarations, not environment assignments.
 if line.startswith('#'):continue
 if found:bindings.append(dict(line=i,expression=line,names=sorted(set(found))));names.update(found)
expected={'ROOT','H','N','TMPDIR','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','TRITON_CACHE_DIR','MPLCONFIGDIR','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','CUDA_VISIBLE_DEVICES','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','TOKENIZERS_PARALLELISM','rc'}
assert names==expected,(names^expected)
assert all(t not in s for t in ('eval ', 'source ', '${!', 'export ${','ssh ','srun ','scontrol '))
c=D/'rcj_scanner';c.mkdir()
J.write(c/'environment_shell21g.json',{'rcj/rcj.sh':dict(sha256=hashlib.sha256(s.encode()).hexdigest(),runtime_literal_names=sorted(names),bindings=bindings,reason='Reviewed literal assignments, fixed helper paths, EXIT publication trap and no dynamic dispatch; any source edit invalidates the certificate')})
p=D/'rcj_scan.py';s=p.read_text().replace("str(D/'scanners/qd/environment21f.py')","str(D/'rcj_scanner/environment21f.py')")
s=s.replace("  check('rcj/'+p.name,'file')","  check('rcj/'+p.name,'file')\n  for i,line in enumerate(p.read_text().splitlines(),1):check(line,'rcj/'+p.name+':'+str(i))")
s=s.replace("subprocess.run(['/bin/bash'",'''with patch.object(E,'__file__',str(D/'rcj_scanner/environment21f.py')):
 try:E.scan_shell((L/'out/rcj/rcj.sh').read_text()+'\\nexport ${DYNAMIC}=q\\n',check,'rcj/rcj.sh')
 except ValueError as e:assert str(e).startswith('ENV_UNRESOLVED:')
 else:raise AssertionError('Changed shell accepted certificate')
subprocess.run(['/bin/bash' ''')
replace(p,s)
(D/'rcj_scan.log').rename(L/'attic/build24m4j/rcj_scan_first.log')
