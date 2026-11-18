"""Source embedded in the sealed proof; no admission or staging in rehearsal."""

def rehearsal_program(wrapper, jobscript, kh, bw):
    boundary = '\n/bin/bash "$ROOT/b/r.sh" p 0\n'
    complete = program(wrapper, jobscript)
    if complete.count(boundary) != 1:
        raise ValueError('Proof admission boundary differs')
    tail = complete.split(boundary, 1)[1]
    # Use the exact production tail. Only provision its per-job kit and stop at
    # the first absent admission output, in a fresh empty run namespace.
    tail = tail.replace('tk_bwrap\n', 'tk_nx\ntk_bwrap\n', 1)
    for command, step in (('tk_bwrap', 'bwrap_setup'), ('tk_env', 'environment'),
                          ('tk_pythonpath p', 'pythonpath')):
        tail = tail.replace(command+'\n', command+"\nprintf 'REHEARSAL_STEP "+step+" PASS\\n'\n", 1)
    tail = tail.replace('import json, os, sys\n',
        'import json, os, sys\nprint("REHEARSAL_STEP namespace PASS", flush=True)\n', 1)
    tail = tail.replace('sys.path.insert(0, os.environ["TRAINER"])',
        'print("REHEARSAL_STEP trainer_tree PASS", flush=True)\nsys.path.insert(0, os.environ["TRAINER"])')
    tail = tail.replace('from student_pilot.loader_audit import main\n',
        'from student_pilot.loader_audit import main\nprint("REHEARSAL_STEP loader_import PASS", flush=True)\n')
    startup = '''
steps = dict(bwrap_setup='PASS', environment='PASS', pythonpath='PASS', namespace='PASS', trainer_tree='PASS', loader_import='PASS')
root = Path(sys.argv[1])
launch = json.loads((root/'k/launch.json').read_text())
cfg = json.loads((root/launch['config']['file']).read_text())
from student_pilot.p3_provenance import pinned, load
store = load(pinned(cfg['streams']['vqa']))
import sqlite3
database = Path(store['database']['path'])
with sqlite3.connect(database.as_uri()+'?mode=ro&immutable=1', uri=True) as connection:
    if not connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rows'").fetchone():
        raise ValueError('Staged store lacks rows')
steps['staged_store_startup'] = 'PASS'
print('REHEARSAL_STEP staged_store_startup PASS', flush=True)
expected = Path(launch['in_job_admission']['directory'])/'data_receipt.json'
if expected.exists():
    raise ValueError('Rehearsal must have no admission outputs')
try:
    main(sys.argv[1])
except FileNotFoundError as exc:
    if Path(exc.filename) != expected:
        raise
    steps['loader_main_startup'] = 'PASS'
    steps['admission_output_boundary'] = 'EXPECTED_MISSING'
else:
    raise ValueError('Loader did not stop at the admission output boundary')
receipt = dict(status='REHEARSAL_OK', steps=steps, production_authorized=False, admission_executed=False)
Path(os.environ['TK_JOBDIR'], 'tail.json').write_text(json.dumps(receipt, sort_keys=True)+'\\n')
print(json.dumps(receipt, sort_keys=True), flush=True)
'''
    if tail.count('main(sys.argv[1])\n') != 1:
        raise ValueError('Loader call boundary differs')
    tail = tail.replace('main(sys.argv[1])\n', startup)
    return namespace_probe(bw) + 'set -euo pipefail\numask 077\nROOT='+shlex.quote(str(kh))+'\n'+tail


def rehearsal_execute(args, script, kh, work, job, run_key):
    steps = {name: 'NOT_RUN' for name in ('bwrap_setup','environment','pythonpath','namespace',
        'trainer_tree','loader_import','staged_store_startup','loader_main_startup','admission_output_boundary')}
    receipt = work/('tmp/jjyeung/a_'+run_key+'/jobs/'+job+'.proof/tail.json')
    outcome = execute(args, script, kh/'o'/(job+'.rehearsal.log'), lambda: {})
    status = 'REHEARSAL_FAIL'
    log = kh/'o'/(job+'.rehearsal.log')
    if log.is_file():
        for name in re.findall(r'^REHEARSAL_STEP (\w+) PASS$', log.read_text(), re.M):
            if name in steps:
                steps[name] = 'PASS'
    if outcome['rc'] == 0 and receipt.is_file():
        inner = load(receipt)
        if inner.get('status') == 'REHEARSAL_OK':
            steps.update(inner['steps'])
            status = 'REHEARSAL_OK'
    if status != 'REHEARSAL_OK':
        for name in steps:
            if steps[name] == 'NOT_RUN':
                steps[name] = 'FAIL'
                break
    return dict(status=status, rc=0 if status=='REHEARSAL_OK' else outcome['rc'] or 1,
        steps=steps, admission_executed=False, training_executed=False,
        production_authorized=False, log=str(kh/'o'/(job+'.rehearsal.log')))
