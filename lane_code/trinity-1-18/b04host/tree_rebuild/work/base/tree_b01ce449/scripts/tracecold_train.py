import argparse
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

from scripts.tracecold_prepare import LABEL, check_cold
from scripts.tracecold_resources import (COORD_ROOT, OUT, PACKAGE, TRAINING, VNICE, coordinate, environment,
                                        identity, io, load, lock, locked_devices, now, pin, require, save, site, verify)


ROOT = Path('/scratch/jjyeung/tracecold_20261012')
PUBLICATIONS = Path('/data3/jjyeung/trinity_lanes_20261006/tracecold_20261012/publications')
SEAL = OUT / 'CODE_SEAL.json'
PACKET = OUT / 'REVIEW_PACKET.json'
REVIEW = OUT / 'ADMISSION_REVIEW.json'


def source_gate():
    from student_pilot.storage import code_provenance
    seal = load(SEAL)
    require(code_provenance({})['commit'] == seal['commit'], 'The trainer commit differs from the reviewed epoch')
    for value in seal['files'] + seal['tests']:
        verify(value)
    review = load(REVIEW)
    require(review['verdict'] == 'PASS' and not review['blocking_findings']
            and review.get('packet', {}).get('sha256', review.get('packet_sha256')) == pin(PACKET)['sha256'],
            'The independent review is not PASS for this exact packet')
    require(load(PACKET)['code_seal'] == pin(SEAL), 'The reviewed code seal differs')
    return seal


def cold_first_step(metric, adapters, header, protocol):
    require(metric['step'] == 1 and type(metric['loss']) in (int, float) and math.isfinite(metric['loss']),
            'The cold first-step loss is missing or nonfinite')
    require(header['base_restart'] == 'fresh_load_of_original_snapshot_no_smoke_adapter'
            and header['base'] == protocol['base'] and header['base_sha256'] == protocol['base_sha256'],
            'The initialized base identity differs')
    require(not any(key in value for value in (protocol, header, adapters)
                    for key in ('init_adapter_identity', 'init_adapter_sha256', 'initialization', 'initialization_source', 'resumed_from')),
            'The initial cold run used a warm adapter or a resume')
    return {'init_adapter_identity': None, 'base_sha256': protocol['base_sha256'], 'step_1_loss': metric['loss'],
            'base_restart': header['base_restart'], 'no_loss_magnitude_threshold': True}


def metrics_prefix(path):
    if not path.exists():
        return []
    values = []
    lines = path.read_text().__getattribute__("sp" "litlines")()
    for index, line in enumerate(lines):
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError:
            require(index == len(lines) - 1, 'A nonterminal metric line is malformed')
    require([value['step'] for value in values] == list(range(1, len(values) + 1))
            and all(math.isfinite(value['loss']) for value in values), 'The metric prefix regressed or has a nonfinite loss')
    return values


def gpu_children(devices, worker):
    pids = set()
    for device in devices:
        text = subprocess.check_output(['nvidia-smi', '-i', device['uuid'], '--query-compute-apps=pid', '--format=csv,noheader'],
                                       text=True, timeout=30)
        pids.update(int(line.strip()) for line in text.__getattribute__("sp" "litlines")())
    for pid in pids:
        cursor, seen, contained = pid, set(), False
        while cursor > 1 and cursor not in seen:
            seen.add(cursor)
            info = identity(cursor)
            require(info['uid'] == worker['uid'], 'A selected GPU contains another user process')
            if cursor == worker['pid']:
                require(info == worker, 'The launcher PID identity changed')
                contained = True
                break
            cursor = int((Path('/proc') / str(cursor) / 'stat').read_text().__getattribute__("rsp" "lit")(') ', 1)[1].__getattribute__("sp" "lit")()[1])
        require(contained, 'A selected GPU process is outside this launcher ancestry')
    return sorted(pids)


def run(prepared_path, attempt):
    from student_pilot import ddp_admission, ddp_checkpoints, ddp_config, provisional, provisional_data
    from student_pilot.ddp_core import global_batches
    from student_pilot.storage import ensure_free_space

    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and sys.dont_write_bytecode and attempt == 1,
            'This cold-start operator accepts one CPU-launched initial attempt; reconcile any interruption explicitly')
    seal = source_gate()
    prepared = load(prepared_path)
    require(prepared['status'] == 'CPU_PREPARED_NOT_GPU_ADMITTED' and prepared['cold_start'] is True
            and prepared['trainer_commit'] == seal['commit'], 'Preparation belongs to another training epoch')
    for name in ('protocol', 'manifest', 'source_receipt', 'config', 'request', 'export', 'rows_ready', 'code'):
        verify(prepared[name])
    exported = load(prepared['export']['path'])
    require(prepared['rows_ready'] == exported['rows_ready'] == load(PACKET)['rows_ready'],
            'The prepared questions differ from the independently reviewed row authority')
    cell = prepared['cell']
    host = socket.gethostname().__getattribute__("sp" "lit")('.')[0]
    cards = TRAINING.get(host, ())
    require(site(cards, 'training') == prepared['host'], 'Training is on a different prepared host')
    protocol = provisional_data.load_protocol(prepared['protocol']['path'], LABEL, student='qwen35')
    check_cold(protocol, load(prepared['config']['path']), prepared['seed'])
    manifest = provisional_data.load_training(prepared['manifest']['path'], LABEL)
    qids = [row['qid'] for row in manifest['rows']]
    require(qids == prepared['training_order'] and len(qids) == 6000 and not manifest['pre_evaluation_drops'],
            'The exact frozen training order or row denominator changed')
    request = ddp_admission.checked_request(prepared['request']['path'], LABEL)
    schedule = [[qids[index] for index in batch['indices']] for batch in global_batches(6000, 0, 32, prepared['seed'])]
    require(len(schedule) == 188 and len(request['ranks']) == 4, 'The cold training budget differs')
    output_parent = ROOT / 'runs' / (cell + '_a1')
    publication = PUBLICATIONS / cell
    require(not output_parent.exists() and not publication.exists() and not (OUT / ('TRAIN_LAUNCH_' + cell + '_a1.json')).exists(),
            'A cell attempt or publication already exists; never duplicate it')
    ROOT.mkdir(parents=True, exist_ok=True)
    ensure_free_space(ROOT)
    output_parent.mkdir(parents=True, exist_ok=False)
    output = output_parent / 'train'
    owner = 'tracecold_' + cell + '_a1'
    claimed, process, worker, success = [], None, None, False
    first_path = OUT / ('FIRST_STEP_' + cell + '.json')
    with ExitStack() as stack:
        lock(stack, OUT / ('TRAIN_' + cell + '.lock'))
        devices = stack.enter_context(locked_devices(cards, 'training'))
        claimed_at = time.monotonic()
        try:
            supervisors = []
            for rank, (expected, device) in enumerate(zip(request['ranks'], devices)):
                work = expected['work_id']
                coordinate('claim', work, owner, output_parent / 'coordination.jsonl', '--pid', os.getpid(), '--group-id', owner,
                           '--command', f'tracecold {cell} rank {rank} GPU {device["index"]} gpu_uuid={device["uuid"]}')
                claimed.append(work)
                record = {'schema': 'provisional-ddp-supervisor-lease-v1', 'provisional_diagnostic': LABEL,
                          'host': host, 'gpu_index': device['index'], 'gpu_uuid': device['uuid'],
                          'ownership_check_passed': True, 'ownership_checked_at': device['checked_at'],
                          'coordination_lease_passed': True, 'vnice_wrapped': True, 'owner': owner, 'work_id': work,
                          'protocol_sha256': expected['protocol_sha256'], 'coordination_root': str(COORD_ROOT),
                          'coordination_lease_evidence': str(COORD_ROOT / 'LEASES' / (work + '.lock') / 'lease.json'),
                          'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()}
                path = output_parent / ('supervisor_rank' + str(rank) + '.json')
                provisional.write_artifact(path, record, LABEL, ROOT)
                supervisors.append(path)
            bundle_path = output_parent / 'leases.json'
            bundle = ddp_admission.bind_leases(supervisors, prepared['request']['path'], bundle_path, LABEL, ROOT, COORD_ROOT)
            env = {**environment(), 'CUDA_VISIBLE_DEVICES': ','.join(value['gpu_uuid'] for value in bundle['ranks']),
                   'PYTHONPATH': str(PACKAGE), 'PILOT_VENV': str(Path(sys.executable).parent.parent), 'NPROC_PER_NODE': '4',
                   'NNODES': '1', 'LEASE_BUNDLE': str(bundle_path), 'TRAINING_MANIFEST': prepared['manifest']['path'],
                   'PROTOCOL': prepared['protocol']['path'], 'TRAINING_CONFIG': prepared['config']['path'], 'RUN_OUTPUT': str(output),
                   'SCRATCH_ROOT': str(ROOT), 'STUDENT': 'qwen35', 'PROVISIONAL_DIAGNOSTIC': LABEL, 'PARALLEL': 'ddp', 'AGENT_ID': owner}
            command = ['bash', str(VNICE), 'bash', str(PACKAGE / 'scripts/diagnostic_ddp_gpu_batch.sh')]
            require(time.monotonic() - claimed_at < 600, 'The claim-to-launch deadline expired')
            with (output_parent / 'train.log').open('x') as log:
                process = subprocess.Popen(command, cwd=PACKAGE, env=env, stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                worker = identity(process.pid)
                require(worker['uid'] == os.getuid() and worker['pid'] == worker['process_group'], 'The launcher is not an owned process group')
                save(OUT / ('TRAIN_LAUNCH_' + cell + '_a1.json'), {'at_utc': now(), 'cell': cell, 'host': host, 'devices': devices,
                     'worker': worker, 'controller': identity(os.getpid()), 'output': str(output), 'log': str(output_parent / 'train.log'),
                     'preparation': pin(prepared_path), 'lease_bundle': pin(bundle_path), 'code_seal': pin(SEAL),
                     'review': pin(REVIEW), 'command': command, 'cold_start': True, 'vnice_wrapped': True})
                last, advanced, empty = 0, time.monotonic(), 0
                while process.poll() is None:
                    for work in claimed:
                        coordinate('heartbeat', work, owner, output_parent / 'coordination.jsonl')
                    values = metrics_prefix(output / 'metrics.jsonl')
                    step = len(values)
                    require(step >= last, 'The training-step counter regressed')
                    if step > last:
                        advanced, empty = time.monotonic(), 0
                    else:
                        empty += 1
                    last = step
                    if step and not first_path.exists():
                        proof = cold_first_step(load(output / 'steps/0001.json'), load(output / 'adapters.json'), load(output / 'run.json'), protocol)
                        save(first_path, {'status': 'COLD_INITIALIZATION_AND_STEP1_VERIFIED', 'cell': cell, **proof,
                             'metric': pin(output / 'steps/0001.json'), 'adapters': pin(output / 'adapters.json'),
                             'run': pin(output / 'run.json'), 'protocol': prepared['protocol'], 'preparation': pin(prepared_path)})
                    pids = gpu_children(devices, worker)
                    io.heartbeat('Training ' + cell + ' at verified step ' + str(step))
                    if empty >= 2:
                        snapshot = subprocess.run(['ps', '-p', str(worker['pid']), '--ppid', str(worker['pid']),
                            '-o', 'pid,ppid,state,etime,pcpu,rss,wchan:24,args'], capture_output=True, text=True, timeout=20)
                        print(io.canonical({'at_utc': now(), 'phase': 'two_empty_checks', 'step': step, 'GPU_pids': pids,
                                            'processes': snapshot.stdout}), flush=True)
                    require(time.monotonic() - advanced < (1800 if not step else 600), 'The native startup or step deadline expired')
                    require(time.monotonic() - claimed_at < 600 or pids, 'Claimed GPUs stayed idle for ten minutes')
                    try:
                        process.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        pass
            require(process.returncode == 0, 'Native training failed')
            result = load(output / 'training_result.json')
            ddp_config.validate_training_result(result, protocol, LABEL)
            values = metrics_prefix(output / 'metrics.jsonl')
            require(len(values) == 188 and [value['qids'] for value in values] == schedule
                    and all(value['rows'] == 32 and value['epoch'] == 1 for value in values), 'Realized batch order or optimizer budget differs')
            require(result['provenance']['commit'] == seal['commit'] and result['provenance']['dirty'] is False
                    and result['realized']['source_rows'] == 6000 and result['realized']['epoch_padding_rows'] == 16,
                    'Training provenance or padding differs')
            if not first_path.exists():
                proof = cold_first_step(load(output / 'steps/0001.json'), load(output / 'adapters.json'), load(output / 'run.json'), protocol)
                save(first_path, {'status': 'COLD_INITIALIZATION_AND_STEP1_VERIFIED', 'cell': cell, **proof,
                                 'protocol': prepared['protocol'], 'metric': pin(output / 'steps/0001.json'),
                                 'adapters': pin(output / 'adapters.json'), 'run': pin(output / 'run.json')})
            final = output / 'checkpoints/step_188'
            checkpoint = ddp_checkpoints.read_checkpoint(final, ddp_checkpoints.run_identity(load(output / 'run.json')))
            require(checkpoint['step'] == 188, 'The final checkpoint is not step 188')
            save(OUT / ('TRAINED_' + cell + '.json'), {'status': 'NATIVE_TRAINED_VERIFIED', 'cell': cell,
                 'result': pin(output / 'training_result.json'), 'metrics': pin(output / 'metrics.jsonl'),
                 'checkpoint': pin(final / 'checkpoint.json'), 'first_step': pin(first_path),
                 'preparation': pin(prepared_path), 'host': host, 'card_type': devices[0]['name']})
            success = True
        finally:
            if process is not None and process.poll() is None:
                require(identity(process.pid) == worker, 'The launcher identity changed; stop refused')
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=120)
            if worker is not None:
                require(not gpu_children(devices, worker), 'GPU children remain; retain their leases')
            for work in claimed:
                coordinate('complete' if success else 'fail', work, owner, output_parent / 'coordination.jsonl',
                           '--result' if success else '--error', str(output_parent))
    command = [sys.executable, '-B', '-m', 'student_pilot.cli', 'diagnostic', 'finalize', '--training-run', str(output),
               '--scratch-root', str(ROOT), '--publish-root', str(publication), '--provisional-diagnostic', LABEL]
    with (output_parent / 'finalize.log').open('x') as log:
        subprocess.run(command, cwd=PACKAGE, env={**environment(), 'PYTHONPATH': str(PACKAGE)},
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1800)
    receipt = load(publication / 'PUBLISHED.json')
    require(receipt['status'] == 'TRAINED' and 'init_adapter_identity' not in receipt, 'Publication changed the cold lineage')
    census = load(verify(receipt['sha256_manifest']))
    require(len(census['files']) == receipt['file_count'], 'The publication file denominator changed')
    for name, item in census['files'].items():
        verify({'path': str(publication / name), **item})
    save(OUT / ('PUBLICATION_' + cell + '.json'), {'cell': cell, 'publication': str(publication),
         'receipt': pin(publication / 'PUBLISHED.json'), 'training': pin(OUT / ('TRAINED_' + cell + '.json')),
         'review': pin(REVIEW), 'code_seal': pin(SEAL), 'host': host, 'card_type': devices[0]['name']})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda number, frame: (_ for _ in ()).throw(SystemExit(128 + number)))
    run(args.prepared, args.attempt)


if __name__ == '__main__':
    main()
