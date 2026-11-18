def validate_switches(cfg):
    """Admit only S2 with S1 off and both own-sampling probabilities zero."""
    h=cfg.get('h1',{})
    schedules=(cfg.get('scheduled_sampling',{}),cfg.get('recipe',{}).get('scheduled_sampling',{}))
    if (h.get('routing_pose_targets') is not True or h.get('faithful_own_camera_rows') is not False
            or any(type(s.get('max_own_probability')) not in (int,float)
                   or s['max_own_probability']!=0 for s in schedules)):
        raise ValueError('Launch requires S2=true, S1=false, and both max_own_probability=0')

"""Execute certified production preparation in isolated physical run locations."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def load(p): return json.loads(Path(p).read_text())

HOST_PATH = '/usr/local/bin:/usr/bin:/bin'
HOST_TOOLS = ('stat', 'date', 'mkdir', 'df', 'awk', 'hostname', 'tail', 'chmod',
              'dirname', 'readlink', 'cut', 'sha256sum', 'mv', 'touch', 'cat',
              'du', 'find', 'sort', 'cp', 'rsync', 'flock', 'tar', 'free', 'id', 'sleep',
              'basename', 'tee', 'seq')

def environment():
    # Slurm supplies allocation identity; no login shell or inherited caches,
    # Python paths, dynamic-loader overrides, or Bash startup hooks are needed.
    env = {k: v for k, v in os.environ.items() if k.startswith('SLURM_')}
    env.update(PATH=HOST_PATH, HOME='/tmp/jjyeung', TMPDIR='/tmp', TZ='UTC',
               LC_ALL='C', CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    os.environ.clear()
    os.environ.update(env)

def host_preflight():
    inventory = {}
    if sys.version_info < (3, 9):
        raise ValueError('Production requires /usr/bin/python3 >= 3.9')
    for name in ('bash', 'python3', 'sed', 'head', 'gzip', 'nice', 'ionice', 'which', 'env') + HOST_TOOLS:
        if shutil.which(name, path=HOST_PATH) is None:
            raise ValueError('Production host program unavailable: '+name)
        path = Path(shutil.which(name, path=HOST_PATH)).resolve()
        inventory[name] = dict(path=str(path), sha256=sha(path))
    inventory['driver'] = dict(path=str(Path(sys.executable).resolve()), sha256=sha(Path(sys.executable).resolve()))
    return inventory

def kit_bwrap(kh):
    pin = load(kh/'k/0.json')['bwrap']
    path = Path(pin['file'])
    if (not path.is_absolute() or not path.is_file() or not os.access(str(path), os.X_OK)
            or not re.fullmatch('[0-9a-f]{64}', pin['sha256'])
            or sha(path) != pin['sha256']):
        raise ValueError('Kit bwrap executable or sha256 differs: '+str(path))
    return str(path)

def namespace_probe(bw):
    # Match tk_bwrap's root enumeration and namespace/device/proc/home flags.
    # Staged bind sources are checked by production after staging. This probe
    # catches kernel/userns/UID-map/device/proc failures before reading archives.
    return '''set -euo pipefail
BW=('''+shlex.quote(bw)+''')
for entry in /* /.[!.]* /..?*; do
    case "$entry" in /home|/dev|/proc) continue ;; esac
    [[ -e "$entry" || -L "$entry" ]] || continue
    if [[ -L "$entry" ]]; then BW+=(--symlink "$(readlink "$entry")" "$entry"); else BW+=(--ro-bind "$entry" "$entry"); fi
done
BW+=(--dev-bind /dev /dev --proc /proc --tmpfs /home --dir /home
     --remount-ro /home --unshare-user --uid "$(id -u)" --gid "$(id -g)")
"${BW[@]}" /bin/bash -c 'test -r /proc/self/status && test -w /dev/null && test -d /home'
printf '%s\\n' 'nested production namespace preflight PASS'
'''

def private(p):
    p = Path(p)
    try:
        info = p.lstat()
    except FileNotFoundError:
        raise ValueError('Directory must be private: '+str(p)) from None
    if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_uid != os.geteuid()):
        raise ValueError('Directory must be private: '+str(p))

def create_work(work, run_key):
    # A batch allocation may start with an empty /tmp. Never chmod or follow an
    # existing parent; require the same private directory after mkdir or EEXIST.
    try:
        work.parent.mkdir(mode=0o700)
    except FileExistsError:
        pass
    private(work.parent)
    work.mkdir(mode=0o700)
    for n in ('tmp', 'tmp/jjyeung', 'tmp/jjyeung/a_'+run_key, 'slots', 'arm', 'runs'):
        (work/n).mkdir(mode=0o700)

def program(wrapper, jobscript):
    # Preserve production commands verbatim. End the outer wrapper before restore
    # or mirror workers, and job.sh before its training-mode selection/exec.
    end = 'read -r slot sstep < <(newest || true)'
    assert wrapper.count(end) == 2
    prefix = wrapper[:wrapper.index(end)]
    marker = 'RUN="$(/usr/bin/python3 -I -c '
    assert jobscript.count(marker) == 1
    jobprefix = jobscript[:jobscript.index(marker)]
    root = 'ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"'
    assert jobprefix.count(root) == 1
    # Sourcing from stdin has no BASH_SOURCE path; ROOT remains the exact KH.
    jobprefix = jobprefix.replace(root, 'ROOT="$KH"')
    return ('set -e\nexport CUDA_VISIBLE_DEVICES=""\n' + prefix + '\nset -e\n' + jobprefix
            + '\n/bin/bash "$ROOT/b/r.sh" p 0\n'
            + 'export TK_KIT_HOME="$ROOT"\nsource "$ROOT/b/c.sh"\n'
            + 'export TK_RUNS_DIR="$NR"\n'
            + 'export TK_JOBDIR="${S%/root}/jobs/${SLURM_JOB_ID:?}.proof"\n'
            + 'umask 077\nmkdir -p -m 700 "${TK_JOBDIR%/*}"\nmkdir -m 700 "$TK_JOBDIR"\n'
            + 'read -r proof_record proof_record_sha < <(tk_current record)\n'
            + 'sha_is "$S/c7d31ddd/anyhost/$proof_record_sha.json" "$proof_record_sha"\n'
            + 'export R1_RUNTIME_RECORD="$P/anyhost/$proof_record_sha.json"\n'
            + 'tk_bwrap\ntk_env\ntk_pythonpath p\n'
            + '"${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X" <<P\nimport json, os, sys\nfrom pathlib import Path\nfrom v import tree\ncur = json.loads((Path(sys.argv[1])/"k/0.json").read_text())\ntree({"path": cur["record"]["file"], "sha256": cur["record"]["sha256"]}, os.environ["TRAINER"], cur["commit"])\nsys.path.insert(0, os.environ["TRAINER"])\nfrom student_pilot.loader_audit import main\nmain(sys.argv[1])\nP\n')

def command(bw, kh, work, rs):
    # The whole filesystem is read-only except proof storage and job receipts.
    # Overlay KH mirrors as well: c.sh persists JSON and arm state after mode p.
    # /proc must be a fresh writable mount: inner bwrap writes UID/GID maps.
    # A network namespace adds a host requirement absent from production.
    if rs.parent.parent != kh.parent:
        raise ValueError('Persistent root must share the production operator root')
    args = [bw, '--unshare-user', '--die-with-parent', '--unshare-pid', '--ro-bind', '/', '/',
            '--proc', '/proc', '--dev', '/dev', '--bind', str(work/'tmp'), '/tmp',
            '--tmpfs', str(kh.parent)]
    # Production creates O/r if absent. A read-only host root cannot do that;
    # overlay O and expose its other entries read-only without host mutations.
    for path in sorted(kh.parent.iterdir()):
        if path.name in (kh.name, rs.parent.name): continue
        if path.is_symlink():
            args += ['--symlink', os.readlink(str(path)), str(path)]
        else:
            args += ['--ro-bind', str(path), str(path)]
    args += ['--tmpfs', str(rs.parent), '--bind', str(work/'slots'), str(rs),
             '--tmpfs', str(kh)]
    for p in sorted(kh.iterdir()):
        if p.name in ('o', 'arm', 'runs'): continue
        if p.is_symlink(): raise ValueError('Linked kit entry')
        args += ['--ro-bind', str(p), str(p)]
    for n in ('arm', 'runs'): args += ['--bind', str(work/n), str(kh/n)]
    args += ['--bind', str(kh/'o'), str(kh/'o'), '--chdir', str(kh),
             '--setenv', 'CUDA_VISIBLE_DEVICES', '', '/bin/bash', '-c',
             'set -e; chmod 700 -- "$1" "$2" "$3"; exec /bin/bash -s',
             'a', str(kh), str(rs.parent), str(kh.parent)]
    return args

def verify_prepared(kh, physical_run):
    sys.path.insert(0, str(kh/'b'))
    from d import effective
    launch = load(kh/'k/launch.json')
    cfg = load(kh/launch['config']['file'])
    derived = effective(kh, cfg, dict(launch, run_directory=str(physical_run)))
    data_path = physical_run/'inputs/data_receipt.json'
    data = load(data_path)
    if data['status'] != 'PREPARED' or data['gpu_first_step_pending'] is not True:
        raise ValueError('Preparation did not reach the first-batch boundary')
    return dict(admission_result=data, data_receipt_sha256=sha(data_path),
                prepared_seals=dict(source=data['source_seal'], preparation=data['preparation'],
                                    config=data['config'], frames=data['frames']),
                effective_config_verified=True, first_batch_executed=False)

def execute(args, script, log, verify, runner=subprocess.run):
    started = time.time()
    result = dict(status='FAIL', rc=1, started_epoch=started, admission_result=None,
                  prepared_seals=None, first_batch_executed=False, training_executed=False)
    try:
        with log.open('x') as f:
            p = runner(args, input=script, text=True, stdout=f, stderr=subprocess.STDOUT)
        result['rc'] = p.returncode if p.returncode >= 0 else 128-p.returncode
        if p.returncode == 0:
            result.update(verify())
            result['status'] = 'PASS'
    except BaseException as exc:
        rc = exc.code if isinstance(exc, SystemExit) and isinstance(exc.code, int) else 1
        result.update(status='FAIL', rc=rc or 1, error=type(exc).__name__+': '+str(exc))
    result.update(finished_epoch=time.time(), elapsed_seconds=time.time()-started)
    return result

def proof_allocation(authority):
    partition=os.environ.get('SLURM_JOB_PARTITION')
    if partition not in ('advanced','general','bootstrap') or partition!=authority['partition']:raise ValueError('Proof partition differs')
    if partition not in authority.get('allowed_partitions',('advanced','general','bootstrap')):raise ValueError('Proof partition is not authorized')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Proof must run CPU-only')
    if os.environ.get('SLURM_GPUS_ON_NODE','0') not in ('','0'):raise ValueError('CPU proof allocated GPUs')
    return dict(partition=partition,node=os.environ.get('SLURMD_NODENAME') or os.uname().nodename)

def directory_modes(work):
    bad=[]
    for directory,children,files in os.walk(work):
        path=Path(directory)
        if path.is_symlink() or stat.S_IMODE(path.stat().st_mode)!=0o700:bad.append(str(path))
    return dict(status='FAIL' if bad else 'PASS',bad=bad)

def export_plan(bundle,cfg,run_key):
    milestones=sorted(set(cfg['recipe']['milestones']))
    stopped=bool(cfg['recipe'].get('export_at_stop'))
    count=len(milestones)+int(stopped)
    if cfg['checkpoint_disk_guard']['planned_weight_exports']!=count:raise ValueError('Export disk count differs')
    names=['m'+str(i) for i in milestones]+(['mstop','mstopB','mstopC'] if stopped else [])
    expected=sorted('q8/8865619b/'+run_key+'_'+name+'.tar.part%02d-of-04'%i for name in names for i in range(4))
    if sorted((bundle/'e.txt').read_text().splitlines())!=expected:raise ValueError('Export destinations differ')
    return dict(planned_weight_exports=count,milestones=milestones,stop_fallback_names=3 if stopped else 0,reserved_part_destinations=len(expected))

def temporary_paths(args,kh,work):
    mounts=[]
    for i,arg in enumerate(args):
        if arg!='--bind':continue
        source=Path(args[i+1]);target=args[i+2]
        if source!=kh/'o' and not source.resolve().is_relative_to(work.resolve()):raise ValueError('Ambient writable dependency')
        mounts.append(dict(source=str(source),target=target))
    return dict(status='PASS',work_root=str(work),writable_mounts=mounts,
        external_receipt_directory=str(kh/'o'),read_only_inputs='Explicit kit, bundle, staged source parts and runtime binaries')

def resume_fixture(kh,work):
    import importlib.util
    spec=importlib.util.spec_from_file_location('c0',kh/'b/c0.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result,_,_=module.fixture(work/'c0',load(kh/'k/a0.json'),load(kh/'k/7.json'))
    return result

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


def main(authority, rehearsal_root=None):
    os.umask(0o077)
    environment()
    def stopped(signum, frame): raise SystemExit(128+signum)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1): signal.signal(sig, stopped)
    job = os.environ.get('SLURM_JOB_ID', '')
    if not re.fullmatch('[1-9][0-9]*', job): raise ValueError('Numeric allocation required')
    if os.environ.get('SLURM_JOB_NAME') != ('a15_cot_ap05b8ac6a' if rehearsal_root else authority['job_name']): raise ValueError('Job name differs')
    kh, bun = Path(authority['kh']), Path(authority['bun'])
    for p in (kh.parent, kh, bun, kh/'o'): private(p)
    destination = kh/'o'/(job+('.rehearsal.json' if rehearsal_root else '.proof.json'))
    # Reserve the receipt name before expensive work. A failure is never PASS.
    with destination.open('x') as f:
        json.dump(dict(status='REHEARSAL_RUNNING' if rehearsal_root else 'RUNNING', job=job, rc=None, production_authorized=False), f)
        f.write('\n')
    result = dict(partition=os.environ.get('SLURM_JOB_PARTITION'),node=os.environ.get('SLURMD_NODENAME') or os.uname().nodename,status='FAIL', rc=1, job=job, production_authorized=False,
                  started_epoch=time.time(), admission_result=None, prepared_seals=None)
    try:
        allocation=proof_allocation(authority)
        result.update(allocation)
        binaries = host_preflight()
        os.chdir(str(kh))
        ids = load(bun/'ids.json')
        assert ids['identity'] == authority['identity'] and ids['contract'] == authority['contract']
        assert sha(bun/'jb.sh') == authority['wrapper_sha256']
        for name,expected in authority['bundle_files'].items():
            if sha(bun/name)!=expected:raise ValueError('Proof bundle differs: '+name)
        for n, h in authority['runtime'].items():
            if sha(kh/n) != h: raise ValueError('Production runtime differs: '+n)
        launch = load(kh/'k/launch.json')
        cfg = load(kh/launch['config']['file'])
        validate_switches(cfg)
        sys.path.insert(0, str(kh/'b'))
        from i import identity, allocation_gpus
        from d import contract, digest
        import a
        a.main(kh)
        assert launch['status'] == 'READY' and identity(cfg) == authority['identity']
        assert digest(contract(launch, cfg)) == authority['contract']
        assert allocation_gpus('p', cfg) == 0
        assert cfg['s1_routing']['selection']['sha256'] == authority['selection_sha256']
        assert sha(kh/'k/selection_equality.json') == authority['equality_sha256']
        compared = load(bun/'compare.json')
        assert compared['manifest_sha256'] == sha(kh/'SHA256SUMS.txt')
        assert compared['config_key']+'.json' == Path(launch['config']['file']).name
        result['export_destinations']=export_plan(bun,cfg,authority['run_key'])
        bw = kit_bwrap(kh)
        binaries['bwrap'] = dict(path=str(Path(bw).resolve()),sha256=sha(Path(bw).resolve()))
        work = Path('/tmp/jjyeung')/('p_'+authority['tag']+'_'+job)
        create_work(work, authority['run_key'])
        if launch['run_directory']!='/tmp/jjyeung/a_'+authority['run_key']+'/runs/'+authority['run_key']:raise ValueError('Run is outside its own temporary root')
        if list((work/'slots').iterdir()) or (work/('tmp/jjyeung/a_'+authority['run_key']+'/root/.stamp')).exists():raise ValueError('Proof root is not empty')
        rs = Path(launch['persistent_run_root'])
        assert str(rs) == authority['persistent_root']
        physical = work/('tmp/jjyeung/a_'+authority['run_key']+'/runs/'+authority['run_key'])
        script = namespace_probe(bw) + program((bun/'jb.sh').read_text(), (kh/'job.sh').read_text())
        if rehearsal_root:
            if authority['partition']!='general':raise ValueError('Rehearsal requires general')
            stage=Path(rehearsal_root)
            if not stage.is_absolute() or stage.is_symlink() or not stage.is_dir():raise ValueError('Staged root unavailable')
            stage=stage.resolve()
            if not str(stage).startswith('/tmp/jjyeung/'):raise ValueError('Rehearsal requires node-local staged root')
            script=rehearsal_program((bun/'jb.sh').read_text(), (kh/'job.sh').read_text(),kh,bw)
        (work/'entry.sh').write_text(script)
        args = command(bw, kh, work, rs)
        if rehearsal_root:
            index=args.index('/bin/bash')
            args[index:index]=['--ro-bind',str(stage),'/tmp/jjyeung/a_'+authority['run_key']+'/root']
        paths=temporary_paths(args,kh,work)
        result.update(checks=dict(temporary_paths=paths,empty_root=dict(status='PASS',path=str(work)),runtime_binaries=dict(status='PASS',binaries=binaries)),config_identity=identity(cfg), config=launch['config'],
                      manifest_sha256=sha(kh/'SHA256SUMS.txt'), contract_sha256=digest(contract(launch,cfg)),
                      selection=cfg['s1_routing']['selection'], equality_sha256=authority['equality_sha256'],
                      wrapper_sha256=authority['wrapper_sha256'], runtime_sha256=authority['runtime'],
                      entry_sha256=sha(work/'entry.sh'), physical_run=str(physical),
                      physical_slots=str(work/'slots'), staging_root=str(work/('tmp/jjyeung/a_'+authority['run_key']+'/root')),
                      real_job_reuse=False, cuda_visible_devices='',
                      allocation_gpus=os.environ.get('SLURM_GPUS_ON_NODE', '0'))
        if rehearsal_root:
            result.update(rehearsal_execute(args,script,kh,work,job,authority['run_key']))
        else:
            outcome=execute(args, script, kh/'o'/(job+'.proof.log'), lambda: verify_prepared(kh, physical))
            result.update(outcome)
            result['checks']['resume_pointer']=resume_fixture(kh,work)
            audit_path=physical/'inputs/a.json'
            if audit_path.exists():
                audit=load(audit_path)
                if audit['original_config_identity']!=authority['identity']:raise ValueError('Loader proof identity differs')
                if sha(physical/'inputs/l.json')!=audit['checks']['loader_audit']['pin']['sha256']:raise ValueError('Loader audit bytes differ')
                result['checks'].update(audit['checks'])
                result['absent_on_P']=audit['checks']['required_families']['absent_on_P']
            else:
                result['checks']['loader_audit']=dict(status='NOT_RUN')
            result['checks']['directory_modes']=directory_modes(work)
            required={'resume_pointer','disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'}
            if not required<=set(result['checks']) or any(result['checks'][k]['status']!='PASS' for k in required if k in result['checks']):
                result.update(status='FAIL',rc=result['rc'] or 1)
    
    except BaseException as exc:
        rc = exc.code if isinstance(exc, SystemExit) and isinstance(exc.code, int) else 1
        result.update(status='FAIL', rc=rc or 1, error=type(exc).__name__+': '+str(exc))
    if rehearsal_root:
        result.update(rehearsal=True,admission_executed=False,staged_source=str(rehearsal_root))
        result.setdefault('steps',dict(preflight='FAIL'))
        if result['status']!='REHEARSAL_OK':result.update(status='REHEARSAL_FAIL',rc=result['rc'] or 1)
    result.setdefault('finished_epoch', time.time())
    result.setdefault('elapsed_seconds', result['finished_epoch']-result['started_epoch'])
    with destination.open('w') as f:
        json.dump(result, f, sort_keys=True, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    print(json.dumps(dict(status=result['status'], rc=result['rc'], receipt=str(destination))))
    return result['rc']
