"""Run every registered suite and the report mutants, retaining all local fixtures."""
from pathlib import Path
import datetime,json,os,re,subprocess,sys
B=Path(__file__).resolve().parents[1];O=B/'out'
sys.path.insert(0,str(O/'guard_kit'))
from guard_core import read,write,sha
report_sha256=sha(B.parent/'report/guard_read.py')
family_sha256=sha(O/'FAMILY.json')
build_round='G5' if '--g5' in sys.argv else 'G4'
reuse_mutants='--reuse-mutants' in sys.argv
assert not (build_round=='G5' and reuse_mutants), 'G5 requires a fresh mutant run'
if reuse_mutants:
    prior=read(O/'TESTS.json')
    assert prior['build_round']=='G4' and prior['report_sha256']==report_sha256 and prior['mutants_returncode']==0

env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
commands=[('C8r','work/run_c8r_tests.py','C8R_TESTS.json'),
          ('G2','out/tests/test_g2.py','G2_TESTS.json'),
          ('processes','out/tests/test_processes.py','PROCESS_TESTS.json'),
          ('returns','out/tests/test_return.py','RETURN_TESTS.json'),
          ('report','work/report_tests.py','REPORT_TESTS.json'),
          ('G1','out/tests/test_g1.py','G1_TESTS.json'),
          ('stager','out/tests/test_stage.py','STAGE_TESTS.json'),
          ('G4','out/tests/test_g4.py','G4_TESTS.json')]
suites=[]
for name,script,result in commands:
    log=O/(build_round.lower()+'_'+name.lower()+'_tests.log')
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log.open('w') as stream:
        run=subprocess.run([sys.executable,'-I','-s','-B',str(B/script)],cwd=B,env=env,stdout=stream,stderr=subprocess.STDOUT)
    output=log.read_text();match=re.search(r'Ran (\d+) tests?',output)
    count=int(match[1]) if match else 0
    failures=re.search(r'failures=(\d+)',output);errors=re.search(r'errors=(\d+)',output)
    summary=dict(tests=count,failures=int(failures[1]) if failures else 0,errors=int(errors[1]) if errors else 0,
                 status='PASS' if run.returncode==0 and count and '\nOK\n' in output else 'FAIL')
    if name in ('G1','stager'):
        write(O/result,summary)
    elif summary['status']=='PASS':
        actual=read(O/result)
        assert all(actual[k]==summary[k] for k in ('tests','failures','errors'))
    suites.append(dict(name=name,path='out/'+result,log=str(log.relative_to(B)),command=[sys.executable,'-I','-s','-B',script],
                       start_utc=start,returncode=run.returncode,**summary))
    (B/'STATUS.md').write_text(build_round+' validation is running.\n'+''.join(f"{row['name']}: {row['status']} ({row['tests']} tests; {row['log']}).\n" for row in suites)+'The report mutants and final audit follow the suites.\n')
    print(name,summary['status'],count,flush=True)
mutant_log=O/(build_round.lower()+'_mutants.log')
if reuse_mutants:
    mutant_returncode=prior['mutants_returncode']
else:
    with mutant_log.open('w') as stream:
        run=subprocess.run([sys.executable,'-I','-s','-B',str(B/'work/run_mutants.py')],cwd=B,env=env,stdout=stream,stderr=subprocess.STDOUT)
    mutant_returncode=run.returncode
mutants=read(O/'MUTANTS.json')
mutants_ok=mutant_returncode==0 and mutants['complete'] and mutants['killed']==mutants['total']
print('mutants','PASS' if mutants_ok else 'FAIL',mutants.get('killed'),flush=True)
assert sha(B.parent/'report/guard_read.py')==report_sha256,'Report changed during validation'
assert sha(O/'FAMILY.json')==family_sha256,'Family changed during validation'
old=read(O/'TESTS.json')
old.update(status='PASS' if all(r['status']=='PASS' for r in suites) and mutants_ok else 'FAIL',
           tests=sum(r['tests'] for r in suites),suites=suites,build_round=build_round,
           family_sha256=sha(O/'FAMILY.json'),admission_sha256=sha(O/'guard_kit/admission.py'),
           report_sha256=sha(B.parent/'report/guard_read.py'),
           mutants_log=str(mutant_log.relative_to(B)),mutants_returncode=mutant_returncode,
           mutants_report_sha256=report_sha256,mutants_reused_from_same_g4_source=reuse_mutants,
           whole_worker='out/rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json',
           whole_worker_evidence_source='Operator report supplied in the G3 task; whole-worker run was not repeated.',
           completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
write(O/'TESTS.json',old)
sys.exit(old['status']!='PASS')
