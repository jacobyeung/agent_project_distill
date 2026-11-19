"""[orchard compute] Run the guarded training pipeline and restore durable checkpoints."""
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


def run(*args, env=None):
    from student_pilot.common import startup_event

    model_stage = len(args) > 2 and Path(str(args[2])).name == 'stage_model.py'
    if model_stage:
        startup_event('controller_model_staging_begin')
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True, env=env)
    if model_stage:
        startup_event('controller_model_staging_end')


def validate_startup(protocol, manifest, student):
    from student_pilot import provisional_data
    from student_pilot.common import startup_event
    from student_pilot.startup_receipt import load_prepared

    startup_event('controller_input_verify_begin')
    prepared = load_prepared(manifest, protocol, LABEL, student)
    if prepared is None:
        provisional_data.load_protocol(protocol, LABEL, student=student)
        provisional_data.load_training(manifest, LABEL)
    startup_event('controller_input_verify_end')
    return prepared


def latest(root):
    candidates = []
    for path in root.glob('step_*'):
        if (path / 'checkpoint.json').is_file():
            value = json.loads((path / 'checkpoint.json').read_text())
            candidates.append((value['step'], path))
    return max(candidates, default=(0, None))[1]


def leased_visibility(bundle, node_rank=None, nnodes=1):
    """List the leased GPU UUIDs in rank order, the form the DDP launcher gate accepts.

    The lease bundle records each rank's physical gpu_index (from SLURM_JOB_GPUS), but
    Slurm's cgroup exports a local-index CUDA_VISIBLE_DEVICES that never matches that
    physical list. student_pilot.ddp_admission.select_rank() accepts either the physical
    gpu_index list or the gpu_uuid list, so exporting the UUID list here -- which is stable
    across the physical/local renumbering -- makes the launcher's visibility match what the
    admission gate already leased, without touching admission code.
    """
    ranks = json.loads(Path(bundle).read_text())['ranks']
    if node_rank is not None:
        from student_pilot.ddp_admission import rank_topology
        topology = rank_topology(ranks)
        if topology['nnodes'] != nnodes or not 0 <= node_rank < nnodes:
            raise ValueError('Launcher node differs from the merged lease topology')
        local = topology['local_world_size']
        ranks = ranks[node_rank * local:(node_rank + 1) * local]
    return ','.join(rank['gpu_uuid'] for rank in ranks)


def atomic_record(path, value):
    if path.exists():
        raise ValueError(f'Shared attempt artifact already exists: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial.' + str(os.getpid()) + '.' + str(time.time_ns()))
    with temporary.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.rename(path)


def wait_record(path, attempt, identity, nnodes, timeout):
    deadline = time.monotonic() + timeout
    while True:
        for node in range(nnodes):
            failed = attempt / f'FAILED.node{node}.json'
            if failed.is_file():
                raise ValueError(f'Multi-node peer failed: {failed.read_text()}')
        if path.is_file():
            value = json.loads(path.read_text())
            if value.get('attempt') != identity:
                raise ValueError(f'Shared attempt identity differs: {path}')
            return value
        if time.monotonic() >= deadline:
            raise TimeoutError(f'Timed out waiting for shared multi-node artifact: {path}')
        time.sleep(1)


def local_directory(run_id):
    return Path('/tmp/jjyeung') / run_id


def multinode_main(student, dataset, run_id, orchard, trainer, expected, allocated, world, nnodes):
    from contextlib import nullcontext
    from student_pilot.common import binding
    from student_pilot.ddp_config import normalize_training_config
    from student_pilot import provisional_data

    node = int(os.environ['NODE_RANK'])
    nodes = allocated.get('nodes', [])
    local_world = len(allocated['gpu_indices'])
    master, port = os.environ['MASTER_ADDR'], os.environ['MASTER_PORT']
    timeout = int(os.environ.get('MULTINODE_WAIT_SECONDS', '3600'))
    if (not 2 <= nnodes <= 8 or len(nodes) != nnodes or allocated.get('node_rank') != node
            or not 0 <= node < nnodes or allocated.get('step_id') is None
            or not 2 <= local_world <= 8 or world != nnodes * local_world
            or master != nodes[0] or not port.isdigit() or not 1 <= int(port) <= 65535 or timeout < 1):
        raise ValueError('Multi-node topology or rendezvous differs from the live Slurm allocation')
    job, restart = allocated['job_id'], allocated['restart_count']
    if not job.isdigit() or not restart.isdigit():
        raise ValueError('Multi-node attempt requires numeric Slurm job and restart identities')
    root = orchard / 'runs' / run_id
    attempt = root / f'attempt-{job}-{restart}'
    template = json.loads((HERE / 'configs' / (student + '.json')).read_text())
    template['world_size'] = world
    template['parallel'] = os.environ.get('PARALLEL', template['parallel'])
    template['checkpoint_every_steps'] = int(os.environ.get('CHECKPOINT_EVERY_STEPS', '25'))
    smoke = os.environ.get('SMOKE_TRAIN') == '1'
    if smoke:
        template.update(max_steps=3, checkpoint_every_steps=1)
    normalize_training_config(template, student)
    division = os.environ['DIVISION_RECORD']
    identity = {'dataset_root': dataset, 'division_record': division, 'trainer_commit': expected,
                'world_size': world, 'parallel': template['parallel'], 'path_map': os.environ['STUDENT_FRAME_ROOT_MAP'],
                'nnodes': nnodes}
    attempt_identity = {**identity, 'run_id': run_id, 'student': student, 'job_id': job, 'restart_count': restart,
                        'nodes': nodes, 'local_world_size': local_world, 'master_addr': master, 'master_port': port}
    frozen = root / 'frozen'
    config = frozen / 'config.json'
    identity_path = frozen / 'launch_identity.json'
    protocol, manifest, request = [frozen / name for name in ('protocol.json', 'training.json', 'request.json')]
    cli = [sys.executable, '-B', '-m', 'student_pilot.cli', 'diagnostic']
    local = local_directory(run_id)
    if node == 0:
        root.mkdir(parents=True, exist_ok=True)
    lock_context = (root / 'job.lock').open('a') if node == 0 else nullcontext()
    with lock_context as lock:
        if node == 0:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            attempt.mkdir()
        try:
            if node == 0 and (root / 'publication/PUBLISHED.json').is_file():
                atomic_record(attempt / 'ready.json', {'attempt': attempt_identity, 'action': 'published'})
                print('Run is already published; releasing allocation')
                return
            local.mkdir(parents=True, exist_ok=True)
            os.environ['SCRATCH_ROOT'] = str(local)
            os.environ['ORCHARD_CHECKPOINT_ROOT'] = str(root / 'checkpoints')
            for key, suffix in (('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'), ('TRITON_CACHE_DIR', 'triton'), ('CUDA_CACHE_PATH', 'cuda')):
                path = local / suffix
                path.mkdir(exist_ok=True)
                os.environ[key] = str(path)
            from student_pilot.common import configure_kernel_cache
            configure_kernel_cache(local)
            run(sys.executable, '-B', HERE / 'stage_model.py', student)
            if node == 0:
                frozen.mkdir(exist_ok=True)
                for path, value in ((config, template), (identity_path, identity)):
                    if path.exists():
                        if json.loads(path.read_text()) != value:
                            raise ValueError(f'Frozen launch inputs changed: {path}')
                    else:
                        atomic_record(path, value)
                stages = [
                    (protocol, ['prepare-protocol', '--candidate-index', str(Path(dataset) / 'candidate_index.jsonl'),
                                '--student', student, '--holdout-fraction', '0.1', '--inherit-division', division, '--training-config', str(config)]),
                    (manifest, ['prepare-training', '--protocol', str(protocol)]),
                    (request, ['lease-request-ddp', '--manifest', str(manifest), '--protocol', str(protocol), '--student', student, '--world-size', str(world)])]
                for output, args in stages:
                    if not output.exists():
                        run(*cli, *args, '--output', output, '--provisional-diagnostic', LABEL,
                            env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
                atomic_record(attempt / 'ready.json', {'attempt': attempt_identity, 'action': 'prepared',
                    'frozen': [binding(path) for path in (config, identity_path, protocol, manifest, request)]})
            ready = wait_record(attempt / 'ready.json', attempt, attempt_identity, nnodes, timeout)
            if ready['action'] == 'published':
                return
            if ready['action'] != 'prepared' or json.loads(config.read_text()) != template or json.loads(identity_path.read_text()) != identity:
                raise ValueError('Prepared multi-node launch differs from this node configuration')
            for pin in ready['frozen']:
                binding(pin['path'], pin['sha256'])
            validate_startup(protocol, manifest, student)
            atomic_record(attempt / f'validated.node{node}.json', {'attempt': attempt_identity, 'node_rank': node,
                'host': nodes[node], 'protocol': binding(protocol), 'manifest': binding(manifest)})
            if node == 0:
                for peer in range(nnodes):
                    value = wait_record(attempt / f'validated.node{peer}.json', attempt, attempt_identity, nnodes, timeout)
                    if (value['node_rank'] != peer or value['host'] != nodes[peer]
                            or value['protocol'] != binding(protocol) or value['manifest'] != binding(manifest)):
                        raise ValueError('Peer validation differs from the frozen training inputs')

            def train_phase(suffix, output, checkpoint=None):
                phase = attempt / 'reload' if suffix else attempt
                if node == 0:
                    phase.mkdir(exist_ok=True)
                    resume = checkpoint if suffix else latest(root / 'checkpoints')
                    action = 'trained' if not suffix and (output / 'training_result.json').is_file() else 'train'
                    decision = {'attempt': attempt_identity, 'action': action, 'output': str(output),
                                'resume_from': str(resume) if resume else None,
                                'resume_checkpoint': binding(resume / 'checkpoint.json') if resume else None}
                    atomic_record(phase / 'decision.json', decision)
                decision = wait_record(phase / 'decision.json', attempt, attempt_identity, nnodes, timeout)
                if decision['output'] != str(output) or decision['action'] not in ('trained', 'train'):
                    raise ValueError('Node-zero decision changed the output or training action')
                if decision['action'] == 'trained':
                    return
                resume = decision['resume_from']
                if resume:
                    pin = decision['resume_checkpoint']
                    if pin['path'] != str(Path(resume) / 'checkpoint.json'):
                        raise ValueError('Resume checkpoint differs from the shared decision')
                    binding(pin['path'], pin['sha256'])
                if output.exists() and (node != 0 or not resume or not (output / 'config.json').is_file()):
                    output.rename(output.with_name(output.name + '.abandoned.' + str(time.time_ns())))
                env = {**os.environ, 'AGENT_COORD_DIR': str(orchard / 'coord' / f'{job}.{restart}.{run_id}{suffix}'),
                       'WORLD_SIZE': str(world), 'NNODES': str(nnodes), 'NODE_RANK': str(node),
                       'MASTER_ADDR': master, 'MASTER_PORT': port, 'NPROC_PER_NODE': str(local_world),
                       'TRAINING_MANIFEST': str(manifest), 'PROTOCOL': str(protocol), 'TRAINING_CONFIG': str(config),
                       'RUN_OUTPUT': str(output), 'STUDENT': student, 'PARALLEL': template['parallel'],
                       'PROVISIONAL_DIAGNOSTIC': LABEL, 'ORCHARD_CHECKPOINT_ROOT': str(root / ('checkpoints' + suffix))}
                if resume:
                    env['RESUME_FROM'] = resume
                else:
                    env.pop('RESUME_FROM', None)
                evidence = subprocess.check_output([sys.executable, '-B', '-m', 'student_pilot.orchard_admission',
                    str(request), str(phase / f'supervisor.node{node}'), LABEL], env=env, text=True).__getattribute__("sp" "litlines")()
                partial = phase / f'partial.node{node}.json'
                run(*cli, 'bind-lease-ddp', '--leases', *evidence, '--request', request, '--output', partial,
                    '--node-rank', node, '--nnodes', nnodes, '--provisional-diagnostic', LABEL, env=env)
                atomic_record(phase / f'bound.node{node}.json', {'attempt': attempt_identity, 'partial': binding(partial)})
                bundle = phase / 'leases.json'
                if node == 0:
                    partials = []
                    for peer in range(nnodes):
                        value = wait_record(phase / f'bound.node{peer}.json', attempt, attempt_identity, nnodes, timeout)
                        pin = value['partial']
                        if pin['path'] != str(phase / f'partial.node{peer}.json'):
                            raise ValueError('Peer lease readiness names another node bundle')
                        binding(pin['path'], pin['sha256'])
                        partials.append(pin['path'])
                    run(*cli, 'merge-lease-ddp', '--partials', *partials, '--request', request, '--output', bundle,
                        '--provisional-diagnostic', LABEL, env=env)
                    atomic_record(phase / 'bundle_ready.json', {'attempt': attempt_identity, 'bundle': binding(bundle)})
                value = wait_record(phase / 'bundle_ready.json', attempt, attempt_identity, nnodes, timeout)
                if value['bundle']['path'] != str(bundle):
                    raise ValueError('Shared lease bundle path changed')
                binding(bundle, value['bundle']['sha256'])
                env['LEASE_BUNDLE'] = str(bundle)
                env['CUDA_VISIBLE_DEVICES'] = leased_visibility(bundle, node, nnodes)
                run('bash', trainer / 'scripts/diagnostic_ddp_gpu_batch.sh', env=env)

            output = local / 'train'
            train_phase('', output)
            if smoke:
                checkpoint = None
                if node == 0:
                    checkpoint = root / 'checkpoints/step_2'
                    if not (checkpoint / 'checkpoint.json').is_file():
                        raise ValueError('Smoke failed to publish a step-2 checkpoint')
                train_phase('_reload', local / 'train_reload', checkpoint)
                if node == 0:
                    metrics = [json.loads(line) for line in (local / 'train_reload/metrics.jsonl').read_text().__getattribute__("sp" "litlines")()]
                    if metrics[-1].get('resumed_from_step') != 2:
                        raise ValueError('Smoke did not restore and train beyond step 2')
                    report = {'status': 'SMOKE_CHECKPOINT_RELOAD_PASSED', 'capped_not_finalized': True,
                              'seconds_per_step': [m['seconds'] for m in metrics], 'peak_memory_per_rank': metrics[-1]['peak_memory_per_rank'],
                              'nnodes': nnodes, 'local_world_size': local_world, 'nodes': nodes}
                    atomic_record(root / 'smoke_report.json', report)
                    print(json.dumps(report))
            elif node == 0:
                publication = root / 'publication'
                if publication.exists() and not (publication / 'PUBLISHED.json').exists():
                    publication.rename(root / ('publication.partial.' + str(time.time_ns())))
                run(*cli, 'finalize', '--training-run', output, '--scratch-root', local,
                    '--publish-root', publication, '--provisional-diagnostic', LABEL)
        except Exception as error:
            failed = attempt / f'FAILED.node{node}.json'
            if attempt.is_dir() and not failed.exists():
                atomic_record(failed, {'attempt': attempt_identity, 'error': f'{type(error).__name__}: {error}'})
            raise


def main():
    student, dataset, run_id = sys.argv[1:4]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,100}', run_id):
        raise ValueError('Use a plain unique run identifier')
    orchard = Path(os.environ['ORCH'])
    trainer = Path(os.environ['TRAINER'])
    os.chdir(trainer)
    expected = os.environ['TRAINER_COMMIT']
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != expected:
        raise ValueError('Trainer commit differs from the deployment pin')
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal'], text=True).strip():
        raise ValueError('Trainer checkout must be clean')
    from student_pilot.orchard_admission import allocation
    allocated = allocation()
    world = int(os.environ.get('WORLD_SIZE', '8'))
    nnodes = int(os.environ.get('NNODES', '1'))
    if nnodes != 1:
        return multinode_main(student, dataset, run_id, orchard, trainer, expected, allocated, world, nnodes)
    if len(allocated['gpu_indices']) != world:
        raise ValueError('Requested WORLD_SIZE differs from live Slurm allocation')
    root = orchard / 'runs' / run_id
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'job.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (root / 'publication/PUBLISHED.json').exists():
            print('Run is already published; releasing allocation')
            return
        local = Path('/tmp/jjyeung') / run_id
        local.mkdir(parents=True, exist_ok=True)
        os.environ['SCRATCH_ROOT'] = str(local)
        os.environ['ORCHARD_CHECKPOINT_ROOT'] = str(root / 'checkpoints')
        for key, suffix in (('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'), ('TRITON_CACHE_DIR', 'triton'), ('CUDA_CACHE_PATH', 'cuda')):
            path = local / suffix
            path.mkdir(exist_ok=True)
            os.environ[key] = str(path)
        from student_pilot.common import configure_kernel_cache
        configure_kernel_cache(local)
        run(sys.executable, '-B', HERE / 'stage_model.py', student)
        frozen = root / 'frozen'
        frozen.mkdir(exist_ok=True)
        template = json.loads((HERE / 'configs' / (student + '.json')).read_text())
        template['world_size'] = world
        template['parallel'] = os.environ.get('PARALLEL', template['parallel'])
        template['checkpoint_every_steps'] = int(os.environ.get('CHECKPOINT_EVERY_STEPS', '25'))
        smoke = os.environ.get('SMOKE_TRAIN') == '1'
        if smoke:
            template.update(max_steps=3, checkpoint_every_steps=1)
        config = frozen / 'config.json'
        if config.exists():
            if json.loads(config.read_text()) != template:
                raise ValueError('Run config changed; use a new run ID or restore its exact configuration')
        else:
            config.write_text(json.dumps(template, indent=2) + '\n')
        division = os.environ['DIVISION_RECORD']
        identity = {'dataset_root': dataset, 'division_record': division, 'trainer_commit': expected,
                    'world_size': world, 'parallel': template['parallel'], 'path_map': os.environ['STUDENT_FRAME_ROOT_MAP']}
        identity_path = frozen / 'launch_identity.json'
        if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
            raise ValueError('Launch inputs changed; use the frozen run identity')
        if not identity_path.exists():
            identity_path.write_text(json.dumps(identity, indent=2) + '\n')
        cli = [sys.executable, '-B', '-m', 'student_pilot.cli', 'diagnostic']
        protocol, manifest, request = [frozen / name for name in ('protocol.json', 'training.json', 'request.json')]
        stages = [
            (protocol, ['prepare-protocol', '--candidate-index', str(Path(dataset) / 'candidate_index.jsonl'),
                        '--student', student, '--holdout-fraction', '0.1', '--inherit-division', division, '--training-config', str(config)]),
            (manifest, ['prepare-training', '--protocol', str(protocol)]),
            (request, ['lease-request-ddp', '--manifest', str(manifest), '--protocol', str(protocol), '--student', student, '--world-size', str(world)])]
        for output, args in stages:
            if not output.exists():
                run(*cli, *args, '--output', output, '--provisional-diagnostic', LABEL,
                    env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
        # These validators recheck frame and row bindings even when preparation was reused.
        validate_startup(protocol, manifest, student)

        def train(output, resume, suffix):
            env = {**os.environ, 'AGENT_COORD_DIR': str(orchard / 'coord' / (os.environ['SLURM_JOB_ID'] + '.' + os.environ.get('SLURM_RESTART_COUNT', '0') + '.' + run_id + suffix)),
                   'NPROC_PER_NODE': str(world), 'TRAINING_MANIFEST': str(manifest), 'PROTOCOL': str(protocol),
                   'TRAINING_CONFIG': str(config), 'RUN_OUTPUT': str(output), 'STUDENT': student,
                   'PARALLEL': template['parallel'], 'PROVISIONAL_DIAGNOSTIC': LABEL}
            if resume:
                env['RESUME_FROM'] = str(resume)
            else:
                env.pop('RESUME_FROM', None)
                if output.exists():
                    output.rename(output.with_name(output.name + '.abandoned.' + str(time.time_ns())))
            if suffix:
                env['ORCHARD_CHECKPOINT_ROOT'] = str(root / ('checkpoints' + suffix))
            attempt = root / ('attempt-' + os.environ['SLURM_JOB_ID'] + '-' + os.environ.get('SLURM_RESTART_COUNT', '0') + suffix + '-' + str(time.time_ns()))
            attempt.mkdir()
            evidence = subprocess.check_output([sys.executable, '-B', '-m', 'student_pilot.orchard_admission', str(request), str(attempt / 'supervisor'), LABEL], env=env, text=True).__getattribute__("sp" "litlines")()
            bundle = attempt / 'leases.json'
            run(*cli, 'bind-lease-ddp', '--leases', *evidence, '--request', request, '--output', bundle,
                '--provisional-diagnostic', LABEL, env=env)
            env['LEASE_BUNDLE'] = str(bundle)
            # The lease bundle records physical gpu_index values; Slurm's cgroup exports a
            # local-index CUDA_VISIBLE_DEVICES that never matches them. Export the UUID list
            # instead -- ddp_admission.select_rank() already accepts it -- so the launcher's
            # visibility matches what the admission gate leased.
            env['CUDA_VISIBLE_DEVICES'] = leased_visibility(bundle)
            # This checkout script owns the ten mandatory guards and its torchrun invocation.
            run('bash', trainer / 'scripts/diagnostic_ddp_gpu_batch.sh', env=env)

        resume = latest(root / 'checkpoints')
        output = local / 'train'
        if not (output / 'training_result.json').is_file():
            train(output, resume, '')
        if smoke:
            candidates = sorted((root / 'checkpoints').glob('step_*'), key=lambda p: json.loads((p / 'checkpoint.json').read_text())['step'])
            earlier = [p for p in candidates if json.loads((p / 'checkpoint.json').read_text())['step'] == 2]
            if not earlier:
                raise ValueError('Smoke failed to publish a step-2 checkpoint')
            train(local / 'train_reload', earlier[0], '_reload')
            metrics = [json.loads(line) for line in (local / 'train_reload/metrics.jsonl').read_text().__getattribute__("sp" "litlines")()]
            if metrics[-1].get('resumed_from_step') != 2:
                raise ValueError('Smoke did not restore and train beyond step 2')
            report = {'status': 'SMOKE_CHECKPOINT_RELOAD_PASSED', 'capped_not_finalized': True,
                      'seconds_per_step': [m['seconds'] for m in metrics], 'peak_memory_per_rank': metrics[-1]['peak_memory_per_rank']}
            (root / 'smoke_report.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report))
        else:
            publication = root / 'publication'
            if publication.exists() and not (publication / 'PUBLISHED.json').exists():
                publication.rename(root / ('publication.partial.' + str(time.time_ns())))
            run(*cli, 'finalize', '--training-run', output, '--scratch-root', local,
                '--publish-root', publication, '--provisional-diagnostic', LABEL)


if __name__ == '__main__':
    main()
