"""[orchard compute] Generate one frozen shard, then score only a complete cohort."""
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
    subprocess.run(list(map(str, args)), check=True, env=env)


def resolve_thinking_args(model, variant, env):
    """Build the --thinking pass-through for benchmark_eval from EVAL_THINKING.

    EVAL_THINKING is unset for almost every cell, and an unset value adds
    nothing so existing cells keep the pinned template unchanged. Only the
    Qwen base controls may run with thinking off; OneThinker's template
    ignores the switch, so minting a second authority over a byte-identical
    prompt is refused there (ruling 2026-09-21 14:12Z).
    """
    thinking = env.get('EVAL_THINKING')
    if thinking is None:
        return []
    if thinking not in ('pinned', 'off'):
        raise ValueError('EVAL_THINKING must be pinned or off')
    if thinking == 'off' and not (model in ('qwen35', 'qwen36_27b') and variant == 'base'):
        raise ValueError('EVAL_THINKING=off is refused outside a Qwen base cell')
    return ['--thinking', thinking]


def resolve_model_args(variant, env):
    """Build the evaluated publication's head and geometry pass-through from EVAL_CARRIERS and EVAL_GEOMETRY_STORE[_SHA256].

    A camera-head publication must name its carriers: EVAL_CARRIERS=none for CPD (Cambrian-P: question rows train
    without camera tokens) and insert for PDG_S2 (its question rows train with them). A G3T publication names its eval
    feature store: EVAL_GEOMETRY_STORE (manifest path) with EVAL_GEOMETRY_STORE_SHA256. A head-call arm (HC, HX, HA)
    decodes with its heads answering the trace's calls: EVAL_HEADCALL=decode, which needs EVAL_CARRIERS=insert. Unset
    adds nothing, so every other cell keeps its exact commands and identity.
    """
    carriers = env.get('EVAL_CARRIERS')
    headcall = env.get('EVAL_HEADCALL')
    if headcall is not None and headcall not in ('none', 'decode'):
        raise ValueError('EVAL_HEADCALL must be none or decode')
    if headcall == 'decode' and carriers != 'insert':
        raise ValueError('EVAL_HEADCALL=decode needs EVAL_CARRIERS=insert')
    store, store_sha256 = env.get('EVAL_GEOMETRY_STORE'), env.get('EVAL_GEOMETRY_STORE_SHA256')
    cam_store, cam_store_sha256 = env.get('EVAL_GEOMETRY_CAMERA_MANIFEST'), env.get('EVAL_GEOMETRY_CAMERA_SHA256')
    if carriers is not None and carriers not in ('none', 'insert'):
        raise ValueError('EVAL_CARRIERS must be none or insert')
    if (store is None) != (store_sha256 is None):
        raise ValueError('EVAL_GEOMETRY_STORE and EVAL_GEOMETRY_STORE_SHA256 are set together')
    if (cam_store is None) != (cam_store_sha256 is None) or (cam_store is not None and store is None):
        raise ValueError('EVAL_GEOMETRY_CAMERA_MANIFEST and EVAL_GEOMETRY_CAMERA_SHA256 are set together with EVAL_GEOMETRY_STORE')
    args = (['--carriers', carriers] if carriers is not None else []) + (
        ['--geometry-store-manifest', store, '--geometry-store-sha256', store_sha256] if store is not None else []) + (
        ['--geometry-camera-manifest', cam_store, '--geometry-camera-sha256', cam_store_sha256] if cam_store is not None else []) + (
        ['--headcall', headcall] if headcall is not None else [])
    if args and variant != 'distilled':
        raise ValueError('Carriers, geometry stores and head-call decoding apply only to distilled publications')
    return args


def main():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('scripts/orchard/eval_job.py:main')
    argv = sys.argv[1:]
    print_args = bool(argv) and argv[0] == '--print-args'
    if print_args:
        argv = argv[1:]
    prepared, model, variant, cell_id = argv[:4]
    extras = argv[4:]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,100}', cell_id):
        raise ValueError('Use a plain cell identifier')
    if model not in ('onethinker', 'qwen35', 'qwen36_27b') or variant not in ('base', 'distilled'):
        raise ValueError('Invalid model or variant')
    if (variant == 'distilled' and len(extras) != 3) or (variant == 'base' and extras):
        raise ValueError('Distilled requires ADAPTER RECEIPT BASE_RUN; base takes none')
    adapter_args = ['--adapter', extras[0], '--training-receipt', extras[1]] if extras else []
    thinking_args = resolve_thinking_args(model, variant, os.environ)
    model_args = resolve_model_args(variant, os.environ)
    cli = [sys.executable, '-B', '-u', '-m', 'student_pilot.orchard_eval']
    if print_args:
        print(json.dumps({'cli': cli, 'adapter_args': adapter_args, 'thinking_args': thinking_args,
                          **({'model_args': model_args} if model_args else {})}))
        return
    orchard = Path(os.environ['ORCH'])
    trainer = Path(os.environ['TRAINER'])
    os.chdir(trainer)
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != os.environ['TRAINER_COMMIT']:
        raise ValueError('Harness deployment pin differs')
    if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
        raise ValueError('Harness requires a clean commit')
    shard = int(os.environ.get('EVAL_SHARD_INDEX', os.environ.get('SLURM_ARRAY_TASK_ID', '0')))
    count = int(os.environ.get('EVAL_SHARD_COUNT', '16'))
    local = Path('/tmp/jjyeung/orchard_eval_inputs')
    local.mkdir(parents=True, exist_ok=True)
    archive = Path(os.environ['BENCHMARK_ARCHIVE'])
    with (local / 'staging.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = local / (archive.stem + '.staged')
        if not marker.exists():
            run(sys.executable, '-B', HERE / 'unpack_inputs.py', archive, env={**os.environ, 'ORCH': str(local)})
            marker.write_text(Path(str(archive) + '.sha256').read_text())
    os.environ['STUDENT_FRAME_ROOT_MAP'] = json.dumps({'/data2': str(local / 'data2root'), '/home/jjyeung/agent_project': str(local / 'source_home')}, sort_keys=True)
    cell = orchard / 'runs/eval' / cell_id
    cell.mkdir(parents=True, exist_ok=True)
    identity = {'prepared': prepared, 'model': model, 'variant': variant, 'adapter_receipt_base': extras,
                'shard_count': count, 'trainer_commit': os.environ['TRAINER_COMMIT'],
                'media_attestation_sha256': os.environ['ORCHARD_MEDIA_ATTESTATION_SHA256']}
    if os.environ.get('EVAL_ITEMS_FILE'):
        identity['items_file'] = os.environ['EVAL_ITEMS_FILE']
    if model_args:
        identity['model_args'] = model_args
    with (cell / 'identity.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = cell / 'identity.json'
        if path.exists() and json.loads(path.read_text()) != identity:
            raise ValueError('Evaluation cell identity changed')
        if not path.exists():
            path.write_text(json.dumps(identity, indent=2) + '\n')
    runtime = Path('/tmp/jjyeung') / ('eval-' + cell_id + '-' + str(shard))
    runtime.mkdir(exist_ok=True)
    for key, suffix in (('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'), ('TRITON_CACHE_DIR', 'triton'), ('CUDA_CACHE_PATH', 'cuda')):
        path = runtime / suffix
        path.mkdir(exist_ok=True)
        os.environ[key] = str(path)
    run(sys.executable, '-B', HERE / 'stage_model.py', model)
    from student_pilot.orchard_admission import allocation, issue
    from student_pilot.provisional import bind_lease
    from student_pilot.orchard_eval.sharding import shard_work_id
    current = allocation()
    if len(current['gpu_indices']) != 1:
        raise ValueError('Each evaluation process requires one Slurm GPU step')
    shared = ['--artifact-root', str(orchard / 'runs/eval'), '--model-root', os.environ['STUDENT_MODEL_ROOT'],
              '--manifest', str(Path(prepared) / 'generation/manifest.json'), '--model', model,
              '--variant', variant, '--provisional-diagnostic', LABEL] + thinking_args + model_args
    controls = ['--items-file', os.environ['EVAL_ITEMS_FILE']] if os.environ.get('EVAL_ITEMS_FILE') else []
    if controls and variant == 'distilled':
        controls += ['--allow-distilled-controls']
    with (cell / 'preflight.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        preflight_path = cell / 'preflight/preflight.json'
        if not preflight_path.exists():
            directory = preflight_path.parent
            if directory.exists():
                directory.rename(cell / ('preflight.partial.' + str(time.time_ns())))
            run(*cli, 'cpu-check', *shared, *adapter_args, *controls, '--output', directory,
                env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
    preflight = json.loads(preflight_path.read_text())
    if preflight['status'] != 'CPU_READY' or preflight['failures']:
        raise ValueError('Complete matching RGB CPU preflight is required')
    request = {'work_id': shard_work_id(preflight['work_id'], shard, count), 'protocol_sha256': preflight['protocol_sha256']}
    attempt = cell / ('lease-' + os.environ['SLURM_JOB_ID'] + '-' + str(shard) + '-' + str(time.time_ns()))
    paths = issue(request, attempt, LABEL)
    bound = attempt / 'bound.json'
    lease = bind_lease(paths[0], bound, LABEL, request['work_id'], request['protocol_sha256'])
    output = cell / 'run'
    resume = ['--resume'] if (output / 'run.json').exists() else []
    pair = ['--base-run', extras[2]] if extras else []
    run(*cli, 'generate', *shared, *adapter_args, *controls, *pair, *resume, '--coord-root', os.environ['AGENT_COORD_DIR'],
        '--preflight', preflight_path, '--lease', bound, '--output', output,
        '--shard-index', str(shard), '--shard-count', str(count),
        env={**os.environ, 'CUDA_VISIBLE_DEVICES': lease['gpu_uuid']})
    if controls:
        print('RGB subset smoke finished; it is not a scored full cohort')
        return
    with (cell / 'score.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (output / 'completion.json').exists() and not (cell / 'score/scores.json').exists():
            if (cell / 'score').exists():
                (cell / 'score').rename(cell / ('score.partial.' + str(time.time_ns())))
            run(*cli, 'score', '--run', output, '--scoring-manifest', Path(prepared) / 'scoring/manifest.json',
                '--artifact-root', orchard / 'runs/eval', '--output', cell / 'score', '--provisional-diagnostic', LABEL)
            print('Diagnostic scores remain pending independent implementation review before publication')


if __name__ == '__main__':
    main()
