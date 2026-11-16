import argparse
import ast
from contextlib import contextmanager, ExitStack
from datetime import datetime
import time
import difflib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracecold_resources import (COORD_ROOT, EVALUATION, LANE, OUT, PACKAGE, VNICE, coordinate, environment,
                                 identity, io, load, lock, locked_devices, now, pin, require, reviewed_epoch, save, verify)


LANES = LANE.parent
DONOR = LANES / 'count9_20261009/work/scorer_runtime01'
BOUND = LANES / 'count9_20261009/out/SCORER_TRANSPORT_BOUND_01.json'
NATIVE = LANES / 'trinity_exec_20260930/eval/r1835_vsibench_answerable500_r2/checkout/91d47a0ee099df925ddcd1591e773430d71d3637'
RUNTIME = PACKAGE / 'step0_runtime_v1'
ROOT = OUT / 'step0_v1'
STAGED = OUT / 'STEP0_TRANSPORT.json'
CELLS = tuple(kind + '_' + arm + '_s' + str(seed) for kind in ('bare', 'heldout') for arm in ('CS', 'CA') for seed in (17, 18))
GENERATION = {'attempts': 1, 'do_sample': False, 'max_new_tokens': 4096, 'num_beams': 1, 'seed': 17}


def digest(path):
    return pin(path)['sha256']


def replace_once(text, before, after):
    require(text.count(before) == 1, 'A frozen transport source anchor changed')
    return text.replace(before, after, 1)


def function_text(text, name):
    node = next(value for value in ast.parse(text).body if isinstance(value, ast.FunctionDef) and value.name == name)
    return ast.get_source_segment(text, node)


def stage():
    require(not STAGED.exists() and not RUNTIME.exists(), 'Preserve every transport epoch')
    bound = load(BOUND)
    donor = load(verify(bound['staged']))
    require(bound['status'] == 'TESTED_BOOKKEEPING_BOUND_NO_ADMISSION_OR_SCORING_AUTHORITY'
            and donor['generation'] == GENERATION and donor['generation_and_decoding_byte_identical'] is True,
            'The donor transport is not the tested fixed-generation source')
    source = {Path(value['path']).name: value for value in donor['runtime_code']}
    names = ('diag_common.py', 'diag_worker.py', 'route_generation_config.py', 'run_cell.py', 'ddp_config.py')
    texts = {name: verify(source[name]).read_text() for name in names}
    common = replace_once(texts['diag_common.py'],
        'from count9_common import LANE, BULK as LANE_BULK, pin, sha as digest\nfrom scorer_transport01 import CELLS, ROOT, contract_for',
        'from tracecold_transport import LANE, CELLS, ROOT, contract_for, pin, digest\nLANE_BULK = ROOT')
    common = replace_once(common, "os.environ.get('COUNT9_SCORER_CELL', '')", "os.environ.get('TRACECOLD_STEP0_CELL', '')")
    common = replace_once(common, 'COUNT = 269', "COUNT = 251 if CELL.startswith('bare_') else 269")
    common = replace_once(common, "raise ValueError('The counting gate requires exactly 269 unique frozen questions')",
                          "raise ValueError(f'The counting gate requires exactly {COUNT} unique frozen questions')")
    for name in ('encode', 'object_digest', 'validate_row', 'tensor_digest'):
        require(function_text(common, name) == function_text(texts['diag_common.py'], name), 'A model-input operation changed')
    controller = replace_once(texts['run_cell.py'],
        "command = [sys.executable, '-B', '-u', str(WORK / 'diag_worker.py'), '--arm', ARMS[0], '--worker-index', '0', '--attempt', str(attempt)]",
        "command = ['bash', '/data3/shared/scripts/vnice/vnice.sh', sys.executable, '-B', '-u', str(WORK / 'diag_worker.py'), '--arm', ARMS[0], '--worker-index', '0', '--attempt', str(attempt)]")
    outputs = {'diag_common.py': common, 'eval_common.py': 'from diag_common import *\n',
               'diag_admission.py': 'from tracecold_transport import worker_admission as admission, identity, lock\n',
               'route_admission.py': 'from diag_admission import admission\n', 'run_cell.py': controller,
               **{name: texts[name] for name in ('diag_worker.py', 'route_generation_config.py', 'ddp_config.py')}}
    RUNTIME.mkdir(exist_ok=False)
    runtime = []
    for name, text in outputs.items():
        ast.parse(text)
        runtime.append(io.write_bytes(RUNTIME / name, text.encode()))
    require(digest(RUNTIME / 'diag_worker.py') == source['diag_worker.py']['sha256']
            and digest(RUNTIME / 'route_generation_config.py') == source['route_generation_config.py']['sha256'],
            'Generation or decoding bytes changed')
    diffs = []
    for name, before, after in (('common', texts['diag_common.py'], common), ('controller', texts['run_cell.py'], controller)):
        text = ''.join(difflib.unified_diff(before.__getattribute__("sp" "litlines")(True), after.__getattribute__("sp" "litlines")(True), fromfile='count9_frozen', tofile='tracecold_transport'))
        diffs.append(io.write_bytes(ROOT / (name + '.diff'), text.encode()))
    return save(STAGED, {'schema': 'tracecold-step0-transport-v1', 'status': 'STAGED_NOT_GPU_ADMITTED', 'donor': pin(BOUND),
        'donor_stage': bound['staged'], 'source_code': [source[name] for name in names], 'runtime_code': runtime, 'diffs': diffs,
        'generation': GENERATION, 'generation_and_decoding_byte_identical': True, 'cells': list(CELLS),
        'admission': pin(Path(__file__).with_name('tracecold_resources.py')), 'builder': pin(__file__),
        'bare_count': 251, 'heldout_count': 269, 'supports_decisions': False, 'score_nomination_allowed': False})


def install_metadata_reader():
    sys.path.insert(0, str(NATIVE))
    import student_pilot
    require(Path(student_pilot.__file__).resolve().parent.parent == NATIVE, 'Another student package shadows the frozen diagnostic worker')
    spec = importlib.util.spec_from_file_location('student_pilot.ddp_config', RUNTIME / 'ddp_config.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[spec.name] = module
    student_pilot.ddp_config = module


def validate_job(job, cell, transport):
    expected = 251 if cell.startswith('bare_') else 269
    require(cell in CELLS and job['cell'] == cell and job['expected_count'] == expected and set(job['models']) == {cell},
            'The diagnostic cell or cohort denominator differs')
    require(job['generation'] == GENERATION and job['code'] == transport['runtime_code'] and len(job['assignments']) == 1,
            'The diagnostic generation, source or placement differs')
    host, card = job['assignments'][0]
    require(host in EVALUATION and type(card) is int and card in EVALUATION[host], 'The diagnostic placement is outside this lane')
    require(job['status'] == 'APPROVED_FOR_DIAGNOSTIC_EVALUATION' and job['supports_decisions'] is False
            and job['score_nomination_allowed'] is False, 'Step 0 cannot acquire decision or nomination authority')


def contract_for(cell):
    reviewed_epoch()
    transport = load(STAGED)
    for value in transport['runtime_code'] + transport['source_code'] + transport['diffs'] + [transport['admission'], transport['builder']]:
        verify(value)
    path = ROOT / 'cells' / cell / 'EVAL_FROZEN.json'
    job = load(path)
    validate_job(job, cell, transport)
    require(job['transport'] == pin(STAGED), 'The diagnostic job names a different transport epoch')
    audit = load(verify(job['model_audit']))
    require(audit['model'] == job['models'][cell] and audit['source_cell'] == '_'.join(cell.__getattribute__("sp" "lit")('_')[1:]),
            'The requested adapter is not the named count9 publication')
    for value in audit['source_evidence']:
        verify(value)
    ready = load(verify(job['route_preflight']))
    require(ready['expected_count'] == ready['checked_count'] == job['expected_count'] and not ready['failures']
            and ready['native_prompt_parity'] is True and ready['native_RGB_parity'] is True, 'Step 0 lacks complete native input-parity proof')
    install_metadata_reader()
    return job, pin(path)


@contextmanager
def worker_admission(arm, index, attempt, job_sha):
    job, frozen = contract_for(arm)
    require(index == 0 and attempt == 1 and frozen['sha256'] == job_sha, 'A diagnostic worker has another attempt or job identity')
    host, card = job['assignments'][0]
    require(socket.gethostname().__getattribute__("sp" "lit")('.')[0] == host, 'The diagnostic worker is on another host')
    directory = ROOT / 'cells' / arm / 'inference' / arm / 'workers/0_a1'
    directory.mkdir(parents=True, exist_ok=False)
    process = identity(os.getpid())
    owner = 'tracecold_step0_' + arm
    work = 'tracecold_step0__' + arm + '__gpu' + str(card) + '__' + job_sha[:16]
    stop, failures = threading.Event(), []
    claimed, success = False, False
    with ExitStack() as stack:
        lock(stack, ROOT / 'cells' / arm / 'control/worker.lock')
        devices = stack.enter_context(locked_devices((card,), 'evaluation'))
        device = devices[0]
        try:
            coordinate('claim', work, owner, directory / 'coordination.jsonl', '--pid', os.getpid(), '--group-id', owner,
                       '--command', f'tracecold Step0 {arm} GPU {card} gpu_uuid={device["uuid"]}')
            claimed = True
            lease = COORD_ROOT / 'LEASES' / (work + '.lock') / 'lease.json'
            def check():
                require(not failures and identity(process['pid']) == process, 'The diagnostic owner or heartbeat failed')
                value = load(lease)
                require(value.get('agent_id') == owner and value.get('status') == 'running' and value.get('pid') == process['pid']
                        and value.get('work_id') == work and value.get('host', '').__getattribute__("sp" "lit")('.')[0] == host,
                        'The diagnostic canonical lease changed owner')
                stamp = value['last_heartbeat']
                timestamp = float(stamp) if isinstance(stamp, (int, float)) else datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()
                require(-10 <= time.time() - timestamp <= 180, 'The diagnostic heartbeat is stale')
                return value
            def heartbeat():
                while not stop.wait(60):
                    try:
                        coordinate('heartbeat', work, owner, directory / 'coordination.jsonl')
                        io.heartbeat('Running Step-zero cell ' + arm)
                    except Exception as error:
                        failures.append(type(error).__name__ + ': ' + str(error))
                        return
            check()
            os.environ.update(CUDA_VISIBLE_DEVICES=device['uuid'], CUDA_DEVICE_ORDER='PCI_BUS_ID')
            receipt = save(directory / 'admission.json', {'schema': 'tracecold-step0-admission-v1', 'cell': arm,
                'job_sha256': job_sha, 'process': process, 'device': {'gpu_uuid': device['uuid'], **device},
                'coordination_root': str(COORD_ROOT), 'lease_path': str(lease), 'lease_at_claim': load(lease), 'at_utc': now(), 'vnice_wrapped': True})
            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            try:
                yield {'check': check, 'directory': directory, 'receipt': receipt, 'device': {'gpu_uuid': device['uuid'], **device}, 'process': process}
                check()
                success = True
            finally:
                stop.set()
                thread.join(timeout=65)
                require(not thread.is_alive(), 'Heartbeat remains alive; retain the lease')
        finally:
            if claimed:
                coordinate('complete' if success else 'fail', work, owner, directory / 'coordination.jsonl',
                           '--result' if success else '--error', str(directory))


def freeze(cell, host, card):
    reviewed_epoch()
    require(cell in CELLS, 'Unknown Step-0 cell')
    transport = load(STAGED)
    kind, source_cell = cell.__getattribute__("sp" "lit")('_', 1)
    ready_path = ROOT / kind / 'READY.json'
    ready = load(ready_path)
    source_job_path = Path('/data3/jjyeung/trinity_lanes_20261006/count9_20261009/scorer_evaluation01/cells') / source_cell / 'EVAL_FROZEN.json'
    source_job = load(source_job_path)
    donor = load(verify(source_job['transport']))
    require(source_job['transport']['sha256'] == pin(BOUND)['sha256'] and donor['status'] == 'TESTED_BOOKKEEPING_BOUND_NO_ADMISSION_OR_SCORING_AUTHORITY',
            'The warm adapter source job is not the authenticated count9 transport')
    source_audit = load(verify(source_job['model_audit']))
    model = source_job['models'][source_cell]
    require(source_audit['cell'] == source_cell and source_audit['native_model'] == model, 'The count9 model audit differs')
    for value in source_audit['evidence']:
        verify(value)
    install_metadata_reader()
    from student_pilot.trinity_eval.common import inspect_publication
    require(inspect_publication(model['source']) == model, 'The native model publication changed')
    destination = ROOT / 'cells' / cell
    require(not destination.exists(), 'Preserve every frozen diagnostic cell')
    job = {'cell': cell, 'status': 'APPROVED_FOR_DIAGNOSTIC_EVALUATION', 'expected_count': 251 if kind == 'bare' else 269,
           'models': {cell: model}, 'generation': GENERATION, 'code': transport['runtime_code'], 'assignments': [[host, card]],
           'route_preflight': pin(ready_path), 'transport': pin(STAGED), 'supports_decisions': False, 'score_nomination_allowed': False}
    validate_job(job, cell, transport)
    require(ready['expected_count'] == ready['checked_count'] == job['expected_count'] and not ready['failures'], 'Input preparation is incomplete')
    job['model_audit'] = save(destination / 'MODEL_AUDIT.json', {'model': model, 'source_cell': source_cell,
        'source_evidence': [pin(source_job_path), source_job['model_audit'], *source_audit['evidence']]})
    return save(destination / 'EVAL_FROZEN.json', job)


def launch(cell):
    job, frozen = contract_for(cell)
    require(socket.gethostname().__getattribute__("sp" "lit")('.')[0] == job['assignments'][0][0], 'Launch from the frozen diagnostic host')
    control = ROOT / 'cells' / cell / 'control'
    control.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        lock(stack, control / 'dispatch.lock')
        require(not (control / 'DISPATCH.json').exists() and not (control / 'attempt_1.launch.json').exists(), 'A diagnostic producer already exists')
        env = environment()
        env.update(TRACECOLD_STEP0_CELL=cell, PYTHONPATH=str(RUNTIME) + ':' + str(Path(__file__).parent))
        command = [sys.executable, '-B', '-u', str(RUNTIME / 'run_cell.py'), 'run', '--attempt', '1']
        with (control / 'supervisor.log').open('x') as log:
            child = subprocess.Popen(command, cwd=RUNTIME, env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        return save(control / 'DISPATCH.json', {'at_utc': now(), 'cell': cell, 'frozen_job': frozen, 'process': identity(child.pid),
                                               'host': socket.gethostname().__getattribute__("sp" "lit")('.')[0], 'command': command})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'freeze', 'launch'))
    parser.add_argument('--cell', choices=CELLS)
    parser.add_argument('--host', choices=tuple(EVALUATION))
    parser.add_argument('--card', type=int)
    args = parser.parse_args()
    result = stage() if args.action == 'stage' else freeze(args.cell, args.host, args.card) if args.action == 'freeze' else launch(args.cell)
    print(io.canonical({'output': result}), flush=True)


if __name__ == '__main__':
    main()
