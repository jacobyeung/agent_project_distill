from pathlib import Path
import ast,hashlib,json
W=Path(__file__).resolve().parents[1];S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
inputs={};checks={}
def read(p):
 raw=p.read_bytes();inputs[str(p)]=hashlib.sha256(raw).hexdigest();return raw.decode()
blocker=json.loads(read(S/'work/build21h/HOST_FLAG_BLOCKER.json'))
for n,h in blocker['sealed_sources'].items():
 b=read(W/'work/tree_before'/n);assert hashlib.sha256(b.encode()).hexdigest()==h
checks['blocker_sealed_sources_match']=True
for n in ('r2_intake.py','r2_materialize.py'):
 b=read(W/'work/tree_before/student_pilot'/n)
 a=read(W/'work/tree_after/student_pilot'/n)
 restored=a.replace('from .job_env import key as env_key\n','').replace("os.environ.get(env_key('STUDENT_R2_FRAME_HOST'))","os.environ.get('STUDENT_R2_FRAME_HOST')")
 assert restored==b
 checks[n+'_other_bytes_unchanged']=True
b=read(W/'work/tree_before/student_pilot/job_env.py');a=read(W/'work/tree_after/student_pilot/job_env.py')
assert a.replace(", 'STUDENT_R2_FRAME_HOST': 'Q_E7'",'')==b
checks['key_function_unchanged']=True
for n in ('host.py','distributed.py'):
 b=read(W/'work/tree_before/launch_r2'/n);a=read(W/'work/tree_after/launch_r2'/n)
 assert a.count("os.environ.pop('Q_E7', None)")==1
 assert ''.join(line for line in a.splitlines(True) if "os.environ.pop('Q_E7', None)" not in line)==b
checks['P_setters_unchanged_except_alias_clear']=True
b=read(W/'work/tree_before/launch_r2/runtime.py');a=read(W/'work/tree_after/launch_r2/runtime.py')
restored=a.replace('r2_materialize as materializer, r2_intake as intake, carrier_c1_run as run','r2_materialize as materializer, carrier_c1_run as run')
start=restored.index('    lines, _ = inspect.getsourcelines(intake.intake)')
end=restored.index('    specs = ',start)
restored=restored[:start]+restored[end:]
restored=restored.replace("os.environ.get(env_key('STUDENT_R2_FRAME_HOST'))", "os.environ.get('STUDENT_R2_FRAME_HOST')")
assert restored==b
checks['runtime_only_exact_lookup_and_intake_precondition']=True
read(Path(__file__).resolve())
(W/'out/STATIC_CHECKS2.json').write_text(json.dumps(dict(input_sha256=inputs,checks=checks),indent=2)+'\n')
print(checks)
