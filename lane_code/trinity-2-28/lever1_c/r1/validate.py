"""Run every CPU check and seal the evidence to the current delivery."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import datetime
import hashlib
import json
import re
import subprocess
import time
import import_audit as A

def write(name,value): (HERE/'out'/name).write_text(json.dumps(value,indent=2)+'\n')
info=json.loads((HERE/'out/BUILD.json').read_text());initial=A.sha((HERE/'out/delivery.tgz').read_bytes())
assert initial==info['delivery_sha256']
write('VALIDATION.json',dict(passed=False,status='Validation in progress',delivery_sha256=initial))
suites=[]
if '--resume' in sys.argv:
    progress=json.loads((HERE/'out/VALIDATION_PROGRESS.json').read_text())
    assert progress['delivery_sha256']==initial
    for entry in progress['suites']:
        assert entry['returncode']==0
        assert A.sha((HERE/entry['log']).read_bytes())==entry['sha256']
        assert A.sha((HERE/entry['script']).read_bytes())==entry['script_sha256']
    suites=progress['suites']
for script,log in [('tests/test_all.py','TEST_ALL.log'),('tests/check_imports.py','TEST_IMPORTS.log'),
                   ('tests/test_fixes.py','TEST_FIXES.log'),('tests/test_failure.py','TEST_FAILURE.log'),
                   ('tests/test_import_audit.py','TEST_AUDIT.log')]:
    if any(s['script']==script for s in suites):continue
    start=time.monotonic()
    with (HERE/'out'/log).open('w') as stream:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(HERE/script)],cwd=HERE,env=os.environ.copy(),stdout=stream,stderr=subprocess.STDOUT)
    data=(HERE/'out'/log).read_bytes();match=re.search(rb'Ran (\d+) tests?',data)
    entry=dict(script=script,script_sha256=A.sha((HERE/script).read_bytes()),log='out/'+log,tests=int(match[1]) if match else 0,seconds=time.monotonic()-start,returncode=result.returncode,sha256=A.sha(data))
    suites.append(entry);print(json.dumps(entry),flush=True)
    assert result.returncode==0,(script,data.decode()[-6000:])
    write('VALIDATION_PROGRESS.json',dict(delivery_sha256=initial,suites=suites))
    assert A.sha((HERE/'out/delivery.tgz').read_bytes())==initial
outer=A.unpack((HERE/'out/delivery.tgz').read_bytes());payload=A.unpack(outer['0.tgz'])
count=0
for prefix,files in [('D',outer),('P',payload)]:
    for name,data in files.items():
        if name.endswith('.py'):compile(data,prefix+'/'+name,'exec');count+=1
for name,digest in info['files'].items():assert A.sha(outer[name])==digest
for name,digest in info['payload_files'].items():assert A.sha(payload[name])==digest
shell={str(path.relative_to(HERE)):subprocess.run(['bash','-n',str(path)]).returncode for path in sorted((HERE/'orchard').glob('*.sh'))}
assert not any(shell.values())
syntax=dict(passed=True,delivery_sha256=initial,python_files=count,shell=shell,all_package_and_payload_pins=True);write('SYNTAX_CHECKS.json',syntax)
result=subprocess.run([sys.executable,'-I','-s','-B',str(HERE/'relift.py'),'--depth',str(HERE/'returned/0.gz'),'--receipt',str(HERE/'returned/4.json'),'--out',str(HERE/'out/DRY_RUN.json')],cwd=HERE,env=os.environ.copy(),capture_output=True,text=True)
assert result.returncode==0,(result.stdout,result.stderr)
dry=json.loads((HERE/'out/DRY_RUN.json').read_text());assert 'depth return missing' in json.dumps(dry)
evidence={}
for name in ('CPU_ENTRY_STUB','FIX_CHECKS','FAILURE_CHECKS','IMPORT_CHECK','IMPORT_AUDIT','SYNTAX_CHECKS','BUDGET_CHECK','REAL_PARITY_20','DRY_RUN'):
    data=(HERE/'out'/(name+'.json')).read_bytes();evidence[name]=dict(path='out/'+name+'.json',sha256=A.sha(data))
    obj=json.loads(data)
    if 'delivery_sha256' in obj:assert obj['delivery_sha256']==initial
checks={name:json.loads((HERE/'out'/(name+'.json')).read_text()) for name in ('IMPORT_AUDIT','IMPORT_CHECK','FAILURE_CHECKS','CPU_ENTRY_STUB')}
assert checks['IMPORT_AUDIT']['passed'] and checks['IMPORT_CHECK']['passed']
assert not checks['IMPORT_AUDIT']['unresolved']
workspace=sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file());assert workspace<10_000_000_000
validation=dict(passed=True,status='All required CPU validation passed for the exact rebuilt delivery',
    scope='CPU correctness, sealed import closure, naming, simulated deadlines and local production failure fetch; no live GPU timing',
    validated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    **{k:info[k] for k in ('token','delivery_sha256','delivery_bytes','payload_sha256','plan_sha256','payload_expanded_bytes')},
    required_tests=43,tests_run=sum(s['tests'] for s in suites),suites=suites,import_checks=2,cpu_rehearsal_runs=2,
    syntax=syntax,production_failure_fetch=checks['FAILURE_CHECKS']['production_fetch'],import_audit={k:checks['IMPORT_AUDIT'][k] for k in ('passed','files_parsed','retained_sources','vendor_files','reachable_files','reachable_imports','unresolved')},
    evidence=evidence,budget=info['forecast'],workspace_bytes=workspace,workspace_cap_bytes=10_000_000_000,moved_fixtures=[])
assert validation['tests_run']==validation['required_tests']
write('VALIDATION.json',validation)
print(json.dumps(dict(passed=True,tests=validation['tests_run'],delivery_sha256=initial,workspace_bytes=workspace)),flush=True)
