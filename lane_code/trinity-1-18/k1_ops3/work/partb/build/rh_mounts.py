"""CPU-only regression for nested read-only PROJECT mount destinations."""
import errno
import json
import os
from pathlib import Path
import subprocess
import uuid
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_support as H
import stage_job as D

ROOT = Path(__file__).resolve().parent

def run():
    run = ROOT/'evidence'/('mounts_'+uuid.uuid4().hex[:10])
    run.mkdir(parents=True)
    project = '/project/community/jjyeung'
    config = dict(logical_run='/scratch/jjyeung/a7e31d84/r/a',
                  pointer=project+'/okh7/b7e31d84a90c62f5/a.json',
                  assets=dict(gcloud_config=project+'/gcloud'))
    pool = str(Path(config['pointer']).parent)
    backing = run/'backing'
    for name in ('pool','gcloud'):
        (backing/name).mkdir(parents=True)
    S,R,NS,J = H.native()
    result = dict(cases={}, passed=False)
    for fixed in (False, True):
        label = 'fixed' if fixed else 'without_F1'
        root = run/label
        for name in ('project/c7d31ddd','cache','temp','home','fsw','m/ap','sj/a7e31d84/r/a'):
            (root/name).mkdir(parents=True, exist_ok=True)
        # bwrap is executed from the system; all data lives under this workspace.
        if fixed:
            argv = D.namespace(root, config)
        else:
            argv = NS.namespace(root, config)
            physical_parent = str(NS.physical(root, Path(config['logical_run']).parent))
            argv += ['--bind',physical_parent,physical_parent,'--bind',physical_parent,str(Path(config['logical_run']).parent)]
            argv += ['--bind',pool,pool,'--bind',config['assets']['gcloud_config'],config['assets']['gcloud_config']]
        H.dump(root/'FULL_NAMESPACE_ARGV.json',argv)
        # Isolate the PROJECT submounts; the production staging root is /tmp,
        # while this small regression keeps its root under workspace /scratch.
        cut = argv.index(str(root)) - 1
        argv = ['/usr/bin/bwrap'] + argv[1:cut] + ['--dir','/project',
                '--dir','/project/community','--ro-bind',str(root/'project'),project] + argv[-6:]
        # Only host source locations differ; target paths and bind order are exact.
        for i, value in enumerate(argv):
            if value == '--bind' and argv[i+1] in (pool, config['assets']['gcloud_config']):
                argv[i+1] = str(backing/('pool' if argv[i+1] == pool else 'gcloud'))
        probe = """import errno,json
from pathlib import Path
project=Path('/project/community/jjyeung')
try:
    (project/'forbidden').write_text('must fail')
except OSError as e:
    assert e.errno == errno.EROFS
else:
    raise AssertionError('PROJECT is writable')
for p in (project/'okh7/b7e31d84a90c62f5',project/'gcloud'):
    (p/'probe').write_text('writable')
print(json.dumps(dict(project_read_only=True,pool_writable=True,gcloud_writable=True)))
"""
        argv += ['/usr/bin/python3','-I','-s','-B','-c',probe]
        H.dump(root/'ARGV.json',argv)
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        (root/'output.txt').write_text(proc.stdout)
        result['cases'][label] = dict(returncode=proc.returncode,output=proc.stdout)
    result['passed'] = (result['cases']['without_F1']['returncode'] == 1
        and 'Read-only file system' in result['cases']['without_F1']['output']
        and result['cases']['fixed']['returncode'] == 0)
    H.dump(run/'RESULT.json',result)
    print(json.dumps(dict(run=str(run),**result)))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(run())
