from common import *
import re
s=(L/'out/rcj/rcj.sh').read_text();bindings=[];names=set()
for i,line in enumerate(s.splitlines(),1):
 if line.startswith('#'):continue
 found=re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)=',line)
 if found:bindings.append(dict(line=i,expression=line,names=sorted(set(found))));names.update(found)
expected={'ROOT','H','MODE','N','TMPDIR','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','TRITON_CACHE_DIR','MPLCONFIGDIR','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','CUDA_VISIBLE_DEVICES','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','TOKENIZERS_PARALLELISM','rc','R1_OPAQUE_LOGS','Q_E1','Q_E2','Q_E3','Q_E4','Q_E5','Q_E6','R1_MODEL_DIR','PYTHONNOUSERSITE','HF_HUB_DISABLE_TELEMETRY','WANDB_DISABLED','C1_EXPECT_FLA','R1_MOUNT'}
assert names==expected,names^expected
assert all(t not in s for t in ('eval ','source ','${!','export ${','ssh ','srun ','scontrol '))
assert '[[ "$MODE" == b || "$MODE" == r ]] || exit 2' in s
J.write(D/'rcj_scanner/environment_shell21g.json',{'rcj/rcj.sh':dict(sha256=hashlib.sha256(s.encode()).hexdigest(),runtime_literal_names=sorted(names),bindings=bindings,reason='Reviewed literal assignments; b/r enum; inherited native runtime aliases; fixed paths; EXIT publication outside sandbox; edits invalidate certificate')})
print('RCJ shell certificate binds',len(names),'literal variable names')
