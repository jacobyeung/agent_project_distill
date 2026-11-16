"""Execute the unchanged embedded batch with explicit, CPU-only fixture boundaries.

This module is packaged only in RH_1_3.tar. No production module imports it.
"""
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import time
import traceback
import uuid

PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE))
import rh_coverage as C


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def tracing(hits):
    def trace(frame, event, arg):
        filename = frame.f_code.co_filename
        if (filename.endswith('.py') and filename.startswith(('/scratch/', '/tmp/'))
                and '/site-packages/' not in filename and '/uv-python/' not in filename
                and '/runtime/uv/' not in filename):
            if event == 'line':
                hits.setdefault(filename, set()).add(frame.f_lineno)
            return trace
    return trace


def bootstrap(context):
    """The real shell passes its unchanged embedded Python through stdin."""
    import pathlib
    case = Path(context['case'])
    raw = sys.stdin.read()
    expected = (PACKAGE / 'packet/a7e31d84.sh').read_text().split("<<'A7E31D84'\n", 1)[1].rsplit('\nA7E31D84', 1)[0]+'\n'
    assert raw == expected
    filename = case / 'embedded_bootstrap.py'
    filename.write_text(raw)
    hits = {}
    sys.settrace(tracing(hits))
    original_path, original_exec = pathlib.Path, os.execv
    if context['mode'] == 'mapped':
        # The local directory stands in only for bootstrap's literal /tmp.
        concrete_path = type(original_path())
        pathlib.Path = lambda value: concrete_path(context['tmp'] if value == '/tmp' else value)
    def execute(executable, argv):
        pathlib.Path, os.execv = original_path, original_exec
        assert argv[1:4] == ['-I', '-s', '-B'] and Path(argv[4]).name == 'batch_entry.py'
        root = Path(argv[5])
        context['stage'] = str(root)
        context['bootstrap_python'] = sys.executable
        context['bootstrap_version'] = sys.version
        dump(case / 'CONTEXT.json', context)
        sys.path.insert(0, str(root))
        # Ensure these are the authenticated, unpacked job modules.
        import job_support as H
        assert Path(H.__file__).parent == root
        import stage_job as D
        S, R, NS, J = H.native()
        from rh_batch_fixture import make
        production = json.loads((root/'a.json').read_text())
        assert production == json.loads((PACKAGE/'packet/CONFIG.json').read_text())
        fixture, objects = make(PACKAGE, case, production, Path(context['python']),
                                project=context['mode'] == 'namespace')
        config = deepcopy(production)
        for key in ('pool', 'cloud', 'pointer'):
            config[key] = fixture[key]
        # Only return-transport destinations differ; every staging pin is sealed.
        assert {k:v for k,v in config.items() if k not in ('pool','cloud','pointer')} == {
                k:v for k,v in production.items() if k not in ('pool','cloud','pointer')}
        H.dump(case/'CONFIG_IDENTITY.json', dict(production_equal_except_transport=True,
            changed_fields=[k for k in config if config[k]!=production[k]],
            embedded_config_sha256=H.sha(root/'a.json')))
        H.dump(root/'a.json', config)
        from rh_transport import install
        install(H, S, NS, root, case, production, fixture, objects)
        context['runtime_sha256'] = fixture['assets']['runtime']['sha256']
        dump(case / 'CONTEXT.json', context)
        original_publish = H.publish
        def publish(*args, **kwargs):
            if context['scenario'] == 'publish_error':
                raise OSError('Injected return failure')
            kwargs['fixture'] = True
            return original_publish(*args, **kwargs)
        H.publish = publish
        original_probe = H.probe
        def probe(pool, local):
            evidence = original_probe(pool, local)
            H.dump(case/'REAL_PROBE.json', evidence)
            if context['scenario'] == 'pool_refusal':
                evidence['pool']['free'] = 600_000_000 + 1024**2 - 1
            if context['scenario'] == 'local_refusal':
                evidence['local']['free'] = 200*1024**3 - 1
            return evidence
        H.probe = probe
        original_proof = J.storage_proof
        def storage(path, **kwargs):
            if context['mode'] == 'namespace':
                result = original_proof(path, **kwargs)
            else:
                try:
                    original_proof(path, **kwargs)
                except J.StorageRefusal as error:
                    H.dump(case/'JOB_TMP_REFUSAL.json', dict(message=str(error), evidence=error.evidence))
                result = original_proof(path)
                result['rehearsal_substitution'] = 'Local directory; no assigned /tmp claim'
            H.dump(case/'STORAGE_PROOF.json', result)
            return result
        J.storage_proof = storage
        def cloud(record, root, assets):
            NS.cloud_uri(record)
            if context['scenario'] in ('staging_error', 'publish_error'):
                raise OSError('Injected staging error')
            return Path(objects[record['name']]['path']).open('rb')
        NS.cloud = cloud
        original_run = subprocess.run
        def process(command, *args, **kwargs):
            if command[:4] == ['/usr/bin/gcloud', 'storage', 'objects', 'describe']:
                name, generation = command[4][len('gs://cmu-gpucloud-jjyeung/'):].rsplit('#',1)
                record = objects[name]['production']
                assert generation == str(record['generation'])
                return subprocess.CompletedProcess(command, 0, json.dumps(dict(size=record['bytes'], generation=record['generation'], crc32c_hash=record.get('crc32c'))), '')
            assert command[0] == str(root/'bwrap'), command
            H.dump(case/'NAMESPACE_ARGV.json', command)
            if context['mode'] == 'mapped':
                index = command.index('-I') - 1
                actual = command[index:]
            else:
                index = command.index('-I') - 1
                extra = ['--bind', str(PACKAGE), str(PACKAGE)]
                for source, logical in context['runtimes']:
                    extra += ['--ro-bind', source, logical]
                actual = command[:index] + extra + command[index:]
            H.dump(case/'EXECUTED_ARGV.json', actual)
            return original_run(actual, *args, **kwargs)
        subprocess.run = process
        # Ensure all bind destinations exist before the staging root is read-only.
        original_namespace = D.namespace
        def namespace(root, config):
            if str(PACKAGE).startswith('/scratch/jjyeung/'):
                NS.physical(root, str(PACKAGE)).mkdir(parents=True, exist_ok=True)
            for source, logical in context['runtimes']:
                NS.physical(root, logical).mkdir(parents=True, exist_ok=True)
            return original_namespace(root, config)
        D.namespace = namespace
        sys.argv = argv[4:]
        runpy.run_path(argv[4], run_name='__main__')
        raise AssertionError('Batch did not exit')
    os.execv = execute
    code = 1
    try:
        exec(compile(raw, str(filename), 'exec'), dict(__name__='__main__'))
    except SystemExit as error:
        code = error.code
    except Exception:
        (case/'bootstrap_failure.log').write_text(traceback.format_exc())
    finally:
        sys.settrace(None)
        pathlib.Path, os.execv = original_path, original_exec
        dump(case/'BOOT_COVERAGE.json', C.report(hits))
    return code


def worker(context, argv):
    """Run native_bootstrap with pinned stub imports, then the CPU phase boundary."""
    case, root = Path(context['case']), Path(context['stage'])
    sys.path.insert(0, str(root))
    import job_support as H
    S, R, NS, J = H.native()
    import native_bootstrap as B
    assert argv[:3] == ['-I', '-s', '-B']
    target = argv[3]
    assert Path(target).name == 'native_bootstrap.py'
    sys.argv = argv[3:]
    hits = {}
    sys.settrace(tracing(hits))
    original_runpath = runpy.run_path
    cpu_path = list(sys.path)
    def runpath(path, *args, **kwargs):
        if Path(path).name != 'phase_worker.py':
            return original_runpath(path, *args, **kwargs)
        assert H.sha(path) == H.sha(PACKAGE/'phase_worker.py')
        # The runtime admitted synthetic modules. The phase uses the packed CPU
        # environment's real numpy/PIL after those import guards have completed.
        for name in B.IMPORTS:
            sys.modules.pop(name, None)
        sys.path[:] = cpu_path
        tree, probes = C.observer_tree(path, hits)
        final = tree.body.pop()
        env = dict(__file__=str(path), __name__='rh_fixture_worker', **probes)
        exec(compile(tree, str(path), 'exec'), env)
        original = env['run']
        def run(config):
            if context['scenario'] == 'worker_failure':
                raise ValueError('Injected worker admission error')
            sys.path[:0] = [str(env['KIT']/'work'), str(env['KIT']/'native_kit')]
            import bindings as bindings
            import boundaries
            mapping = {}
            if context['mode'] == 'mapped':
                # Exact-file metadata mapping preserves all real pins and bytes.
                for index in (1, 3):
                    for member in config['assets']['small_objects'][index]['members']:
                        prefix, _, tail = member.partition('/')
                        logical = str((J.FSW if prefix == 'fsw' else J.SJ)/tail)
                        mapping[logical] = str(root/member)
                mapping[config['assets']['trainer_logical_archive']] = str(NS.physical(root, config['assets']['trainer_logical_archive']))
                config['source'] = str(NS.physical(root, config['source']))
            manifest = json.loads((PACKAGE/'manifest_v2/a40fbc19.json').read_text())
            if context['mode'] == 'mapped':
                for capture in manifest['captures']:
                    for frame in capture['dense_frames']:
                        mapping[frame['path']] = str(NS.physical(root, frame['path']))
                config['manifest'] = str(NS.physical(root, config['manifest']))
            config['metadata_mapping'] = mapping
            # Admission checks the unchanged production manifest and real anchor
            # pins. Only the CPU phase workload uses a six-capture fixture.
            short = deepcopy(manifest)
            short['captures'] = short['captures'][:6]
            anchor = NS.physical(root, manifest['captures'][0]['dense_frames'][0]['path'])
            for capture in short['captures']:
                for frame in capture['dense_frames']:
                    frame.update(bindings.pin(anchor))
                capture['model_row']['student_input']['frames'] = [dict(capture['dense_frames'][i]) for i in capture['anchor_slots']]
            boundary = boundaries.CPU()
            if context['scenario'] in ('deadline', 'allocation', 'zero_budget'):
                # Virtual time advances only at committed capture boundaries.
                # The real phase, STOP handling, publishers and pointer all run.
                clock = [1000.0]
                monotonic = time.monotonic
                class Clock:
                    @staticmethod
                    def time():
                        return clock[0]
                    pass
                Clock.monotonic = staticmethod(monotonic)
                env['time'] = Clock
                config.update(started_unix=1000.0, capture_reserve_seconds=0.5, return_margin_seconds=0.5)
                if context['scenario'] == 'deadline':
                    config['deadline_unix'] = 1005.0
                else:
                    config.pop('deadline_unix', None)
                    config['allocation_seconds'] = 5 if context['scenario']=='allocation' else 0
                original_own = boundary.own
                def own(*args, **kwargs):
                    value = original_own(*args, **kwargs)
                    clock[0] += 1.5
                    return value
                boundary.own = own
            result = original(config, dict(manifest=short, boundary=boundary, max_seconds=100))
            if context['scenario'] in ('deadline', 'allocation', 'zero_budget'):
                assert result['code'] == 4 and len(result['observations']) == (0 if context['scenario']=='zero_budget' else 3)
                out = Path(config['source'])/'native/probe'
                assert (out/'STOP').read_text().strip() == 'RESUME'
                assert not (Path(config['source'])/'FAILED.json').exists()
                assert not (out/'HALTED.json').exists()
                assert Path(config['pointer']).is_file()
                result['deadline_verified'] = dict(stop='RESUME', pointer_advanced=True,
                    failed_marker=False, allocation_seconds=0 if context['scenario']=='zero_budget' else 5, fixture_unix=clock[0])
            else:
                assert result['code'] == 0 and result['canary_returned'] and len(result['observations']) == 6
            H.dump(case/'WORKER_RESULT.json', result)
            return result
        env['run'] = run
        env['__name__'] = '__main__'
        exec(compile(ast.Module(body=[final], type_ignores=[]), str(path), 'exec'), env)
    runpy.run_path = runpath
    # Run the unchanged native bootstrap body with only the fixture archive
    # identity and CPU interpreter translation supplied at its configure boundary.
    bootstrap_env = dict(__file__=target, __name__='rh_fixture_bootstrap')
    exec(compile(Path(target).read_text(), target, 'exec'), bootstrap_env)
    configure = bootstrap_env['configure']
    def configured(spec):
        B.checked(spec['python'])
        sys.path.insert(0, str(Path(spec['python']['path']).parent.parent/'lib/python3.12/site-packages'))
        spec = deepcopy(spec)
        spec['python'] = dict(path=sys.executable, sha256=H.sha(sys.executable))
        return configure(spec)
    bootstrap_env.update(ARCHIVE=context['runtime_sha256'], configure=configured)
    code = 0
    try:
        bootstrap_env['main']()
    except SystemExit as error:
        code = error.code
    except Exception:
        code = 1
        traceback.print_exc()
    finally:
        sys.settrace(None)
        dump(case/'WORKER_COVERAGE.json', C.report(hits))
    return code


def main(mode, outer_python='/usr/bin/python3', selected=None):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    run = PACKAGE/'evidence'/('batch_'+uuid.uuid4().hex[:10])
    run.mkdir(parents=True)
    python = Path(sys.executable)
    runtimes = []
    for packed, logical in [('p1cpu', '/scratch/jjyeung/envs/p1cpu'),
                            ('uv', '/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu')]:
        source = PACKAGE/'runtime'/packed
        runtimes.append((str(source if source.exists() else Path(logical)), logical))
    if mode == 'namespace':
        python = Path('/scratch/jjyeung/envs/p1cpu/bin/python')
    scenarios = ('success', 'deadline', 'allocation', 'zero_budget', 'staging_error', 'pool_refusal', 'worker_failure', 'publish_error', 'local_refusal')
    if selected is not None:
        assert set(selected) <= set(scenarios)
        scenarios = tuple(selected)
    result = dict(mode=mode, outer_python=outer_python, production_interpreter=outer_python == '/usr/bin/python3', passed=False, full_job_rehearsal=False, synthetic=True, cases={},
        substitutions=['four tiny export parts; fixture base inventory separate from real model metadata',
            'production anchors and unchanged 300-capture manifest preflight; six CPU captures use one real PNG',
            'stub runtime/numpy/closure/FLA imports, CPU interpreter and CPU.own',
            'local cloud transport and verified synthetic pool/cloud returns',
            'bootstrap execv is intercepted to install in-memory fixture adapters',
            'mapped mode only: directory /tmp, path mapping, namespace command executed without bwrap'])
    reports = []
    try:
        for scenario in scenarios:
            case = run/scenario
            case.mkdir()
            tmp = case/'job_tmp'/'424242'
            tmp.mkdir(parents=True)
            context = dict(case=str(case), scenario=scenario, mode=mode, tmp=str(tmp),
                           python=str(python), runtimes=runtimes)
            dump(case/'CONTEXT.json', context)
            # Keep the payload and its interpreter; only route stdin through
            # the RH adapter that intercepts execv. No PATH python3 shim exists.
            script = (PACKAGE/'packet/a7e31d84.sh').read_text()
            before = "exec /usr/bin/python3 -I -s -B - <<'A7E31D84'"
            assert before in script
            launch = 'exec ' + shlex.quote(outer_python) + ' -I -s -B ' + shlex.quote(str(PACKAGE/'rh_batch.py'))
            launch += ' --bootstrap ' + shlex.quote(str(case/'CONTEXT.json')) + " <<'A7E31D84'"
            (case/'batch.sh').write_text(script.replace(before, launch, 1))
            env = dict(os.environ, PATH='/usr/bin:/bin', SLURM_JOB_ID='424242')
            project = case/'project'
            (project/'okh7/b7e31d84a90c62f5').mkdir(parents=True)
            (project/'gcloud').mkdir()
            if mode == 'namespace':
                # Distinct job IDs avoid bootstrap's intentional mkdir refusal.
                env['SLURM_JOB_ID'] = os.environ['SLURM_JOB_ID']
                # Each case gets its own real job-private /tmp bind.
                command = ['/usr/bin/bwrap']
                for name in ('usr','bin','sbin','lib','lib64','etc','opt','run','sys'):
                    path = Path('/')/name
                    if path.is_symlink():
                        command += ['--symlink', os.readlink(path), str(path)]
                    elif path.exists():
                        command += ['--ro-bind', str(path), str(path)]
                command += ['--dev-bind','/dev','/dev','--proc','/proc','--bind',str(tmp),'/tmp',
                            '--bind',str(PACKAGE),str(PACKAGE)]
                for source, logical in runtimes:
                    command += ['--ro-bind',source,logical]
                command += ['--dir','/project/community','--bind',str(project),'/project/community/jjyeung',
                            '--chdir',str(PACKAGE),'/bin/bash',str(case/'batch.sh')]
            else:
                command = ['/bin/bash', str(case/'batch.sh')]
            with (case/'batch.log').open('w') as log:
                process = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            context = json.loads((case/'CONTEXT.json').read_text())
            stage = Path(context.get('stage', tmp/'missing'))
            if mode == 'namespace' and 'stage' in context:
                stage = tmp / stage.relative_to('/tmp')
            for name in ('a01.json', 'a02.json', 'a03.json', 'a04.json', 'a05.json'):
                if (stage/name).is_file():
                    (case/name).write_bytes((stage/name).read_bytes())
            worker_log = stage/'sj/a7e31d84/r/a/logs/a.log'
            if worker_log.is_file():
                (case/'worker.log').write_bytes(worker_log.read_bytes())
            row = dict(returncode=process.returncode, bootstrap_entered='stage' in context)
            result['cases'][scenario] = row
            for name in ('BOOT_COVERAGE.json', 'WORKER_COVERAGE.json'):
                if (case/name).is_file():
                    reports.append((scenario+'/'+name, json.loads((case/name).read_text())))
            assert row['bootstrap_entered'], (scenario, 'bootstrap did not enter')
            expected = 0 if scenario in ('success', 'deadline', 'allocation', 'zero_budget') else 1
            assert process.returncode == expected, (scenario, process.returncode)
            exits = sorted((case/'cloud').glob('*/EXIT.json'))
            for path in exits:
                assert json.loads(path.read_text())['synthetic'] is True
            row['verified_returns'] = len(exits)
            if scenario in ('success', 'deadline', 'allocation', 'zero_budget'):
                worker_result = json.loads((case/'WORKER_RESULT.json').read_text())
                assert worker_result['admission']['prepared']['passed']
                assert len(exits) == (1 if scenario=='zero_budget' else 2)
                assert json.loads((stage/'a04.json').read_text())['code'] == 0
                if scenario in ('deadline','allocation','zero_budget'):
                    row['deadline_verified'] = worker_result['deadline_verified']
                row['bootstrap_python'] = context['bootstrap_python']
                row['bootstrap_version'] = context['bootstrap_version']
            elif scenario == 'publish_error':
                assert not exits and '"event": "a2"' in (case/'batch.log').read_text()
            else:
                assert len(exits) == 1
                failure = stage/'a06/FAILED.json' if scenario != 'worker_failure' else stage/'sj/a7e31d84/r/a/FAILED.json'
                assert failure.is_file()
                row['failure'] = json.loads(failure.read_text())
                expected_message = {'staging_error':'Injected staging error', 'pool_refusal':'Pool lacks room',
                                    'local_refusal':'Node-local staging reserve'}
                if scenario in expected_message:
                    assert expected_message[scenario] in row['failure']['message']
            row['passed'] = True
        result['passed'] = True
    except Exception:
        (run/'failure.log').write_text(traceback.format_exc())
    finally:
        coverage = C.union(reports)
        dump(run/'COVERAGE_UNION.json', coverage)
        # Match the ordinary coverage schema for collection across both rehearsals.
        dump(run/'COVERAGE.json', {row['sources'][0]:row for row in coverage.values()})
        dump(run/'RESULT.json', result)
        dump(PACKAGE/'evidence/BATCH_LATEST.json', dict(run=str(run)))
    print(json.dumps(dict(run=str(run), **result)))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    if sys.argv[1:2] == ['--bootstrap']:
        raise SystemExit(bootstrap(json.loads(Path(sys.argv[2]).read_text())))
    if sys.argv[1:2] == ['--worker']:
        raise SystemExit(worker(json.loads(Path(sys.argv[2]).read_text()), sys.argv[3:]))
    outer = sys.argv[sys.argv.index('--diagnostic-python') + 1] if '--diagnostic-python' in sys.argv else '/usr/bin/python3'
    selected = sys.argv[sys.argv.index('--cases')+1].split(',') if '--cases' in sys.argv else None
    raise SystemExit(main('namespace' if '--namespace' in sys.argv else 'mapped', outer, selected))
