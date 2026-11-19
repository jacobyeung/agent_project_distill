from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import fcntl
import importlib.util
import os
from pathlib import Path
import re
import socket
import subprocess
import sys


PACKAGE = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('tracecold_private_io', PACKAGE / 'student_pilot/trace_io.py')
io = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(io)
LANE, OUT, load, pin, require, save, verify, now = io.LANE, io.OUT, io.load, io.pin, io.require, io.save, io.verify, io.now
COORD_ROOT = Path('/data2/jjyeung/agent_project/.coord')
COORD_TOOL = Path('/home/jjyeung/agent_project/agent/coord.py')
PROFILE = Path('/home/jjyeung/agent_project/agent/config/sites/trinity.json')
VNICE = Path('/data3/shared/scripts/vnice/vnice.sh')
TRAINING = {'trinity-0-3': (4, 5, 6, 7), 'trinity-2-28': (3, 4, 5, 6)}
EVALUATION = {'trinity-0-13': (0, 1, 2, 3), 'trinity-2-28': (0, 7)}


def site(cards, purpose):
    host = socket.gethostname().__getattribute__("sp" "lit")('.')[0]
    profile = load(PROFILE)
    require(profile['site_id'] == 'trinity' and profile['coord_root'] == str(COORD_ROOT) and COORD_ROOT.is_dir(),
            'The canonical coordination root or host/site mapping differs')
    allowed = TRAINING if purpose == 'training' else EVALUATION if purpose == 'evaluation' else {}
    require(host in allowed and type(cards) in (list, tuple) and cards and len(cards) == len(set(cards))
            and all(type(card) is int and card in allowed[host] for card in cards), 'The requested cards are outside this lane allocation')
    if purpose == 'training':
        require(tuple(cards) == allowed[host], 'Training requires the entire assigned four-Ada block')
    return host


def identity(pid):
    path = Path('/proc') / str(pid)
    fields = (path / 'stat').read_text().__getattribute__("rsp" "lit")(') ', 1)[1].__getattribute__("sp" "lit")()
    return {'pid': pid, 'uid': path.stat().st_uid, 'start_ticks': int(fields[19]), 'process_group': int(fields[2])}


def named_cards(value):
    result = set()
    for key in ('gpu_indices', 'cards', 'gpu_ids'):
        result.update(int(card) for card in value.get(key, []) if str(card).isdigit())
    if type(value.get('gpu_index')) is int:
        result.add(value['gpu_index'])
    result.update(int(card) for card in re.findall(r'(?:^|_)gpu([0-7])(?:_|$)', str(value.get('work_id', '')), re.I))
    for match in re.findall(r'\bGPUs?\s*([0-7](?:\s*[,/-]\s*[0-7])*)', str(value.get('command', '')), re.I):
        for part in re.__getattribute__("sp" "lit")(r'\s*[,/]\s*', match):
            if '-' in part:
                left, right = map(int, part.__getattribute__("sp" "lit")('-'))
                result.update(range(left, right + 1))
            else:
                result.add(int(part))
    return result


def blocks(value, host, cards, uuids):
    if value.get('status') != 'running' or value.get('host', '').__getattribute__("sp" "lit")('.')[0] != host:
        return False
    selected = named_cards(value)
    named_uuids = set(re.findall(r'GPU-[0-9a-fA-F-]{36}', str(value.get('command', ''))))
    named_uuids.update(value.get('gpu_uuids', []))
    if isinstance(value.get('gpu_uuid'), str):
        named_uuids.add(value['gpu_uuid'])
    if selected or named_uuids:
        return bool(selected & set(cards) or named_uuids & set(uuids))
    return True


def inspect_leases(host, cards, uuids, leases=None):
    records = ((path, load(path)) for path in sorted((COORD_ROOT / 'LEASES').glob('*.lock/lease.json'))) if leases is None else leases
    return [{'work_id': value.get('work_id'), 'lease': pin(path), 'named_cards': sorted(named_cards(value))}
            for path, value in records if blocks(value, host, cards, uuids)]


def probe(cards, purpose):
    host = site(cards, purpose)
    text = subprocess.check_output(['nvidia-smi', '-i', ','.join(map(str, cards)),
        '--query-gpu=index,uuid,name,memory.used,memory.free', '--format=csv,noheader,nounits'], text=True, timeout=30)
    devices = []
    for line in text.__getattribute__("sp" "litlines")():
        index, uuid, model, used, free = [part.strip() for part in line.__getattribute__("sp" "lit")(',')]
        active = subprocess.check_output(['nvidia-smi', '-i', uuid, '--query-compute-apps=pid', '--format=csv,noheader'],
                                         text=True, timeout=30).strip()
        require(model == 'NVIDIA RTX 6000 Ada Generation' and re.fullmatch(r'GPU-[0-9a-fA-F-]{36}', uuid)
                and 0 <= int(used) < 100 and int(free) >= 40000 and not active, 'A selected Ada GPU is not empty')
        devices.append({'host': host, 'index': int(index), 'uuid': uuid, 'name': model,
                        'used_mib': int(used), 'free_mib': int(free), 'checked_at': now()})
    require([device['index'] for device in devices] == list(cards), 'The physical-card membership differs')
    return devices


def lock(stack, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    stream = stack.enter_context(os.fdopen(descriptor, 'a+'))
    require(os.fstat(stream.fileno()).st_uid == os.getuid(), 'A device or run lock belongs to another user')
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def locked_devices(cards, purpose):
    host = site(cards, purpose)
    devices = probe(cards, purpose)
    require(not inspect_leases(host, cards, [device['uuid'] for device in devices]), 'A foreign lease blocks a selected card')
    with ExitStack() as stack:
        for device in sorted(devices, key=lambda value: value['uuid']):
            lock(stack, COORD_ROOT / 'DEVICE_LOCKS' / (device['uuid'] + '.lock'))
            lock(stack, COORD_ROOT / 'GPU_LEASES' / f'{host}_gpu{device["index"]}.lock')
        fresh = probe(cards, purpose)
        require([device['uuid'] for device in fresh] == [device['uuid'] for device in devices]
                and not inspect_leases(host, cards, [device['uuid'] for device in fresh]), 'A GPU identity or lease changed during admission')
        yield fresh


def coordinate(action, work, owner, audit, *arguments):
    profile = load(PROFILE)
    require(profile['coord_root'] == str(COORD_ROOT) and socket.gethostname().__getattribute__("sp" "lit")('.')[0] in set(TRAINING) | set(EVALUATION),
            'A coordination command lacks its canonical site mapping')
    path = COORD_ROOT / 'LEASES' / (work + '.lock') / 'lease.json'
    if action != 'claim':
        value = load(path)
        require(value.get('agent_id') == owner and value.get('work_id') == work and value.get('status') == 'running'
                and value.get('pid') == os.getpid(), 'This process does not own the canonical lease')
    if action in ('complete', 'fail'):
        require(not (COORD_ROOT / ('COMPLETED' if action == 'complete' else 'FAILED') / (work + '.lock')).exists(),
                'A coordination transition would overwrite retained history')
    command = [sys.executable, '-B', str(COORD_TOOL), action, work, *map(str, arguments)]
    result = subprocess.run(command, env={**os.environ, 'AGENT_COORD_DIR': str(COORD_ROOT), 'AGENT_ID': owner},
                            capture_output=True, text=True, timeout=40)
    with Path(audit).open('a') as stream:
        stream.write(io.canonical({'at_utc': now(), 'action': action, 'work_id': work, 'returncode': result.returncode,
                                  'stdout': result.stdout, 'stderr': result.stderr}) + '\n')
    require(result.returncode == 0, 'Canonical coordination refused ' + action)


def reviewed_epoch():
    seal_path, packet_path, review_path = (OUT / name for name in ('CODE_SEAL.json', 'REVIEW_PACKET.json', 'ADMISSION_REVIEW.json'))
    seal, packet, review = load(seal_path), load(packet_path), load(review_path)
    commit = subprocess.check_output(['git', '-C', str(PACKAGE), 'rev-parse', 'HEAD'], text=True, timeout=30).strip()
    dirty = subprocess.check_output(['git', '-C', str(PACKAGE), 'status', '--porcelain', '--untracked-files=normal'],
                                    text=True, timeout=30).strip()
    require(not dirty and commit == seal['commit'], 'The reviewed package is dirty or has another commit')
    for value in seal['files'] + seal['tests']:
        verify(value)
    require(review['verdict'] == 'PASS' and not review['blocking_findings']
            and review.get('packet', {}).get('sha256', review.get('packet_sha256')) == pin(packet_path)['sha256']
            and packet['code_seal'] == pin(seal_path), 'The independent review does not admit this exact sealed package')
    return seal, packet


def environment():
    result = dict(os.environ)
    result.update(CUDA_VISIBLE_DEVICES='', CUDA_DEVICE_ORDER='PCI_BUS_ID', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                  HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='2',
                  MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', AGENT_COORD_DIR=str(COORD_ROOT))
    for key in ('INIT_ADAPTER', 'RESUME_FROM', 'STUDENT_EVAL_ROOTS', 'STUDENT_ORCHARD', 'STUDENT_TRINITY_EVAL',
                'STUDENT_FRAME_ROOT_MAP', 'ORCHARD_MEDIA_ATTESTATION', 'ORCHARD_MEDIA_ATTESTATION_SHA256',
                'STUDENT_STARTUP_RECEIPT', 'STUDENT_STARTUP_RECEIPT_SHA256', 'STUDENT_MEMORY_PROBE_CACHE',
                'STUDENT_MEMORY_PROBE_ENVIRONMENT', 'STUDENT_MEMORY_PROBE_ENVIRONMENT_SHA256'):
        result.pop(key, None)
    return result
