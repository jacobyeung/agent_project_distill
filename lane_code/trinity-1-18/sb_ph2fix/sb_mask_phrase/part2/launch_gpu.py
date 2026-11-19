"""One-card launch admission and cumulative 1.2 GPU-hour budget. No automatic retry."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import uuid
from gate import check

KIT = Path(__file__).resolve().parents[1]
HARD_SECONDS = 4320.0
WAIT_SECONDS = 300


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value, pins):
    value = dict(value, input_sha256=pins)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=1) + '\n')
    temporary.replace(path)


def admit_state(out):
    for name in ('RUNNING', 'KILLED', 'KILLED.json', 'STOP', 'STOP.json'):
        if (out/name).exists():
            raise RuntimeError(f'REFUSED: {name}; RUNNING without a clean end counts as KILLED; never resume STOP/KILLED')
    if (out/'PASS_COMPLETE.json').exists():
        raise RuntimeError('REFUSED: pass already complete')
    spent = 0.0
    if (out/'CLEAN_END.json').exists():
        record = json.loads((out/'CLEAN_END.json').read_text())
        spent = float(record['spent_seconds'])
        if record['status'] != 'CLEAN' or not math.isfinite(spent) or spent < 0:
            raise RuntimeError('REFUSED: invalid clean-end budget')
    elif out.exists() and any(out.iterdir()):
        raise RuntimeError('REFUSED: unaccounted partial output; no clean end')
    if spent >= HARD_SECONDS:
        raise RuntimeError('REFUSED: GPU budget exhausted')
    return spent


def reading(card, smi='nvidia-smi', run=subprocess.run):
    query = [smi, '-i', str(card), '-q', '-x']
    result = run(query, check=True, capture_output=True, text=True)
    import xml.etree.ElementTree as ET
    tree = ET.fromstring(result.stdout)
    cards = tree.findall('gpu')
    if len(cards) != 1:
        raise RuntimeError('REFUSED: nvidia-smi did not return one card')
    gpu = cards[0]
    def mib(name):
        raw = gpu.findtext('fb_memory_usage/' + name, '')
        if not re.fullmatch(r'\d+ MiB', raw.strip()):
            raise RuntimeError('REFUSED: unknown GPU memory')
        return int(raw.split()[0])
    processes = gpu.find('processes')
    if processes is None or (processes.text or '').strip() not in ('', 'None'):
        raise RuntimeError('REFUSED: unknown GPU process state')
    used, total = mib('used'), mib('total')
    identity = gpu.findtext('uuid')
    cap = gpu.findtext('compute_cap', '')
    # A separate query is needed on drivers whose XML omits compute capability.
    if not cap:
        cap = run([smi, '-i', str(card), '--query-gpu=compute_cap', '--format=csv,noheader,nounits'],
                  check=True, capture_output=True, text=True).stdout.strip()
    data = dict(at_monotonic=time.monotonic(), card=card, uuid=identity, used_mib=used,
                total_mib=total, compute_cap=cap, xml=result.stdout)
    data['eligible'] = bool(identity and total * 1048576 >= 48_000_000_000 and used <= 1024
                            and len(processes) == 0 and float(cap) >= 8.0)
    return data


def environment(kit, out, identity, deadline, mode, aliases):
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    env.update(CUDA_VISIBLE_DEVICES=identity, CUDA_DEVICE_ORDER='PCI_BUS_ID', PART2_GO='1',
               PART2_STAGED='1', PART2_KIT=str(kit), PART2_OUT=str(out), PART2_MODE=mode,
               PART2_PYTHON=str(kit.parent/'payload/environment/bin/python'),
               PART2_ALL_ALIASES='1' if aliases else '', PART2_DEADLINE_MONOTONIC=str(deadline),
               PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    for name, suffix in dict(HF_HOME='hf', TORCH_HOME='torch', XDG_CACHE_HOME='xdg',
                             TRITON_CACHE_DIR='triton', TORCHINDUCTOR_CACHE_DIR='inductor',
                             CUDA_CACHE_PATH='cuda', MPLCONFIGDIR='mpl', TMPDIR='tmp', HOME='home').items():
        env[name] = str(out/'cache'/suffix)
    for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[name] = '8'
    return env


def preflight(kit):
    pins = json.loads((kit/'part2/vendor/PINS.json').read_text())['sha256']
    for name, expected in pins.items():
        path = kit/'part2/vendor'/name
        if sha(path) != expected:
            raise RuntimeError(f'REFUSED: vendor hash {path}')
    inventory = json.loads((kit.parent/'out/STAGING_PART2.json').read_text())
    if inventory['status'] != 'PASS':
        raise RuntimeError('REFUSED: staging did not pass')
    for row in inventory['inventory']:
        p = kit.parent/row['staged_path']
        if not p.is_file() or p.stat().st_size != row['bytes']:
            raise RuntimeError(f'MISSING or wrong size: {p}')
        if 'control' in row['roles'] and sha(p) != row['sha256']:
            raise RuntimeError(f'REFUSED: control hash {p}')
    inputs = [Path(__file__), kit/'part2/gate.py', kit/'part2/BARS_PART2.json',
              kit/'part2/vendor/PINS.json', kit.parent/'out/STAGING_PART2.json']
    return {str(p): sha(p) for p in inputs} | {str(kit/'part2/vendor'/n): h for n,h in pins.items()}


def launch(card, mode='both', aliases=False, *, kit=KIT, host=None, sample=reading,
           sleep=time.sleep, run=subprocess.run, prepare=preflight, clock=time.monotonic):
    check('pass', kit)  # Preserve bars-first admission before every write, including logs.
    out = kit/'out/pool_part2'
    spent = admit_state(out)
    host = host or socket.gethostname().split('.')[0]
    if not re.fullmatch(r'trinity-\d+-\d+', host) or host == 'trinity-0-13':
        raise RuntimeError('REFUSED: use a compute node other than trinity-0-13')
    if card < 0:
        raise RuntimeError('REFUSED: --node-local requires a nonnegative card index')
    if out.resolve() != out:
        raise RuntimeError('REFUSED: GPU output must not be a symlink')
    pins = prepare(kit)
    out.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also prevents two launchers from racing during the five-minute wait.
    with (out/'RUNNING').open('x') as f:
        json.dump(dict(status='RUNNING', host=host, input_sha256=pins), f)
    receipt = dict(host=host, node_local=card, readings=[], spent_before=spent, mode=mode, all_aliases=aliases)
    receipt_path = out/('LAUNCH_'+uuid.uuid4().hex+'.json')
    start = None
    try:
        receipt['readings'].append(sample(card))
        sleep(WAIT_SECONDS)
        receipt['readings'].append(sample(card))
        write(receipt_path, receipt, pins)
        a, b = receipt['readings']
        if not a['eligible'] or not b['eligible'] or a['uuid'] != b['uuid']:
            raise RuntimeError('REFUSED: card must be empty and at most 1024 MiB in both readings')
        start = clock()
        deadline = start + HARD_SECONDS - spent
        for phase in (('step5', 'pass') if mode == 'both' else (mode,)):
            remaining = deadline - clock()
            if remaining <= 0:
                raise TimeoutError('hard stop reached')
            env = environment(kit, out, b['uuid'], deadline, phase, aliases)
            for name in ('TMPDIR', 'HOME'):
                Path(env[name]).mkdir(parents=True, exist_ok=True)
            # SIGKILL has no grace period: a blocked native/CUDA call cannot extend the hard stop.
            command = ['timeout', '--signal=KILL', f'{remaining:.6f}s', 'bash',
                       str(kit/'part2/vendor/vnice.sh'), 'bash', str(kit/'part2/gpu_inner.sh')]
            receipt.setdefault('commands', []).append(command)
            write(receipt_path, receipt, pins)
            with (out/(phase+'.log')).open('a') as log:
                result = run(command, env=env, cwd=out, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            if result.returncode != 0:
                raise RuntimeError(f'pass failed or KILLED: exit {result.returncode}')
            expected = out/('STEP5.json' if phase == 'step5' else 'PASS_COMPLETE.json')
            record = json.loads(expected.read_text())
            if phase == 'step5' and record['status'] != 'PASS':
                raise RuntimeError('STEP5 failed')
            if clock() >= deadline:
                raise TimeoutError('hard stop reached')
        receipt.update(status='CLEAN', spent_seconds=spent + clock()-start)
        write(receipt_path, receipt, pins)
        write(out/'CLEAN_END.json', receipt, pins)
        # Rename clears RUNNING only after durable clean-end evidence; no deletion is needed.
        (out/'RUNNING').replace(out/'LAST_CLEAN_START.json')
        return 0
    except BaseException as error:
        receipt.update(status='KILLED', reason=str(error), spent_seconds=spent+(clock()-start if start else 0))
        write(receipt_path, receipt, pins)
        write(out/'KILLED.json', receipt, pins)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--node-local', type=int, required=True)
    p.add_argument('--mode', choices=('both', 'step5', 'pass'), default='both')
    p.add_argument('--all-aliases', action='store_true')
    args = p.parse_args()
    return launch(args.node_local, args.mode, args.all_aliases)


if __name__ == '__main__':
    raise SystemExit(main())
