from pathlib import Path
import ast,hashlib,json,re
W=Path(__file__).resolve().parents[1];T=W/'work/new';B=W/'work/base';D=W/'work/donor_orig';O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fn(root,file,name):
 p=root/file;s=p.read_text();tree=ast.parse(s)
 n=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name)
 return '\n'.join(s.splitlines()[n.lineno-1:n.end_lineno])
checks={};inputs={str(Path(__file__).resolve()):sha(__file__),str(O/'unit_final.log'):sha(O/'unit_final.log')}
for file,names in [('student_pilot/carrier_c1_run.py',['identity','restore','gx_rule_rebind','bind_output','prepare','prepared']),('launch_r1/entry.py',['admit'])]:
 for root in (T,B,D):inputs[str(root/file)]=sha(root/file)
 for name in names:
  a,b,c=(fn(r,file,name) for r in (B,D,T));checks[file+':'+name]=dict(base_sha256=hashlib.sha256(a.encode()).hexdigest(),donor_sha256=hashlib.sha256(b.encode()).hexdigest(),patched_sha256=hashlib.sha256(c.encode()).hexdigest(),unchanged_from_donor=b==c,unchanged_from_base=a==c)
assert all(x['unchanged_from_donor'] for x in checks.values())
log=(O/'unit_final.log').read_text();assert 'test_pre_donor_resume_binding_stays_fail_closed' in log and log.strip().endswith('OK')
r=dict(input_sha256=inputs,status='DOCUMENTED_NOT_IMPLEMENTED',reason='Adding scale_donor changes the admitted config identity and native checkpoint binding. prepare/prepared alone cannot authorize the requested native resume. Extending restore/gx_rule_rebind changes resume legality; no such change is made.',preparation_requirement='Fresh preparation with donor bound; current prepared() rejects a missing donor in the old receipt.',native_checkpoint_test='Changed binding refuses; unchanged binding restores with donor attached and unchanged donor tensor pins.',functions=checks,command='python code/s1_boundary.py; native evidence: nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/run_unit.py')
(O/'S1_STATUS.json').write_text(json.dumps(r,indent=2)+'\n')
(W/'STATUS.md').write_text('The MUST regressions pass on base+donor2 and live seal 189df6ac. K1 V1/V2 scales differ, both authenticated captures reject the leaky-V1 control, and field-absent state/optimizer/export/reload parity is byte-identical. S2 and S3 are implemented. S1 remains documented because native checkpoint resume binds the complete admitted configuration and a donor change needs a resume-legality transition; the refusal is tested. Full and focused base/new/live suites are running. All patch applications are verified with zero fuzz and zero offset.\n')
