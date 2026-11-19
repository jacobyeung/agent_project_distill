"""Check proof-root paths without claiming synthetic data is production data."""
import hashlib,json,os,shlex,shutil,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];OLD=W.parent/'prior2b';root=W/'work/host_wrapper_tests';root.mkdir(exist_ok=True)
inputs={}
def pin(p):
 p=Path(p).resolve();v=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest());inputs[str(p)]=v;return v
def load(p):pin(p);return json.loads(Path(p).read_text())
pin(__file__);pin(W/'out/run_on_host.py');pin(W/'out/prove_on_prepared.py')
for name in ('config.json','receipt.json'):pin(OLD/'work/mix_fixture'/name)
common=['nice','-n','10',sys.executable,str(W/'out/run_on_host.py'),'--base-tree',str(OLD/'work/sealed_base'),
        '--patched-tree',str(OLD/'work/sealed_new')]
env=dict(os.environ,OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',PYTHONDONTWRITEBYTECODE='1')
records=[]
for stage in ('b','h','population','missing'):
 proof=root/'proof_root'
 if stage!='missing':
  (proof/stage).mkdir(parents=True,exist_ok=True)
  for name in ('config.json','receipt.json'):shutil.copyfile(OLD/'work/mix_fixture'/name,proof/stage/name)
  args=['--proof-root',str(proof),'--stage',stage]
 else:args=['--proof-root',str(root/'MISSING_PROOF_ROOT')]
 out=root/(stage+'_result');cmd=common+args+['--output-dir',str(out)]
 proc=subprocess.run(cmd,env=env,text=True,capture_output=True)
 (root/(stage+'.log')).write_text(proc.stdout+proc.stderr)
 command=load(out/'HOST_COMMAND.json');checks=dict(exit_refuses=proc.returncode==1)
 if stage=='missing':
  checks.update(missing_status=command['status']=='MISSING',named_path=str(root/'MISSING_PROOF_ROOT/b/config.json') in command.get('error',''))
 else:
  result=load(out/'proof/RESULT.json')
  checks.update(named_fixture_refusal='FIXTURE_CANNOT_BE_USED_AS_REAL_PREPARATION' in result.get('error',''),
                correct_stage_config=str(proof/stage/'config.json') in command['command'],
                correct_stage_receipt=str(proof/stage/'receipt.json') in command['command'])
 records.append(dict(name=stage,status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
                     command=shlex.join(cmd),result=pin(out/'HOST_COMMAND.json')))
 print(stage,records[-1]['status'],flush=True)
(W/'out/HOST_WRAPPER_TESTS.json').write_text(json.dumps(dict(
 status='PASS' if all(r['status']=='PASS' for r in records) else 'FAIL',records=records,inputs=list(inputs.values()),
 command=shlex.join(sys.argv)),sort_keys=True,indent=2)+'\n')
raise SystemExit(0 if all(r['status']=='PASS' for r in records) else 1)
