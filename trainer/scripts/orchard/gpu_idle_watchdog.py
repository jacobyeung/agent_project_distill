import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import io
import json
import math
import os
from pathlib import Path
import pwd
import re
import socket
import subprocess
import time


SCHEMA = 'gpu-idle-watchdog-v1'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def run_command(command, timeout=5):
    resources = ('SLURM_MEM_PER_CPU', 'SLURM_MEM_PER_NODE', 'SLURM_MEM_PER_GPU', 'SLURM_NTASKS',
                 'SLURM_NTASKS_PER_NODE', 'SLURM_CPUS_PER_TASK', 'SLURM_GPUS', 'SLURM_GPUS_PER_TASK',
                 'SLURM_TRES_PER_TASK', 'SLURM_CPU_BIND', 'SLURM_STEP_ID', 'SRUN_CPUS_PER_TASK')
    env = {key: value for key, value in os.environ.items() if key not in resources}
    result = subprocess.run(command, env={**env, 'TZ': 'UTC', 'LC_ALL': 'C'}, capture_output=True,
                            text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f'{command[0]} exited {result.returncode}: {result.stderr.strip()[:600]}')
    return result.stdout


def parse_queue(text, user):
    result = []
    for line in text.__getattribute__("sp" "litlines")():
        if not line.strip():
            continue
        parts = line.strip().__getattribute__("sp" "lit")('|')
        if (len(parts) != 2 or parts[1] != user or not re.fullmatch(r'\d+(?:[_+]\d+)*', parts[0])
                or parts[0] in result):
            raise ValueError('Unexpected owner, job identifier, or duplicate in running queue')
        result.append(parts[0])
    return result


def gpu_indices(value):
    result = []
    for token in value.__getattribute__("sp" "lit")(','):
        if not re.fullmatch(r'\d+(?:-\d+)?', token):
            raise ValueError('GPU allocation has no usable physical indices')
        bounds = [int(part) for part in token.__getattribute__("sp" "lit")('-')]
        low, high = bounds[0], bounds[-1]
        if not 0 <= low <= high < 1024:
            raise ValueError('Invalid GPU allocation range')
        result.extend(range(low, high + 1))
    if len(result) != len(set(result)):
        raise ValueError('Duplicate GPU allocation index')
    return sorted(result)


def parse_job(text, queue_id, user, uid, expand):
    fields = dict(re.findall(r'(?:^|\s)(\w+)=(\S+)', text))
    if fields.get('UserId') != f'{user}({uid})' or fields.get('JobState') != 'RUNNING':
        raise ValueError('Job owner or running state changed')
    allocation_id = fields.get('JobId', '')
    identities = {allocation_id}
    if 'ArrayJobId' in fields and 'ArrayTaskId' in fields:
        identities.add(fields['ArrayJobId'] + '_' + fields['ArrayTaskId'])
    for prefix in ('HetJob', 'PackJob'):
        if prefix + 'Id' in fields and prefix + 'Offset' in fields:
            identities.add(fields[prefix + 'Id'] + '+' + fields[prefix + 'Offset'])
    if queue_id not in identities or not re.fullmatch(r'\d+', allocation_id):
        raise ValueError('Queue identifier does not match the allocation')
    tres = fields['AllocTRES'].__getattribute__("sp" "lit")(',')
    generic = [int(value.__getattribute__("sp" "lit")('=')[1]) for value in tres if re.fullmatch(r'gres/gpu=\d+', value)]
    count = generic[0] if generic else sum(int(value.__getattribute__("sp" "lit")('=')[1]) for value in tres if re.fullmatch(r'gres/gpu:[^=]+=\d+', value))
    if count == 0:
        return None
    start = fields['StartTime']
    datetime.fromisoformat(start)
    nodes = {}
    groups = re.findall(r'(?:^|\s)Nodes=(\S+)\s+CPU_IDs=\S+\s+Mem=\S+\s+GRES=(\S+)', text)
    for host_list, gres in groups:
        matches = re.findall(r'(gpu(?::[^:(),\s]+)?):(\d+)\(IDX:([^)]*)\)', gres)
        indices, requests = [], []
        for resource, declared, allocated in matches:
            if re.search(r'mig|\dg\.\d+gb', resource, re.I):
                raise ValueError('MIG utilization is not supported by this physical-GPU probe')
            parsed = gpu_indices(allocated)
            if len(parsed) != int(declared):
                raise ValueError('GPU allocation count differs from its index mask')
            indices += parsed
            requests.append(resource + ':' + declared)
        if not indices or len(indices) != len(set(indices)):
            raise ValueError('Missing or duplicate per-node GPU allocation')
        for host in expand(host_list):
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', host) or host in nodes:
                raise ValueError('Invalid or duplicate allocated host')
            nodes[host] = {'indices': sorted(indices), 'gres': ','.join(requests)}
    if len(nodes) != int(fields['NumNodes']) or sum(len(value['indices']) for value in nodes.values()) != count:
        raise ValueError('Could not reconcile every allocated GPU and node')
    return {'job_id': queue_id, 'allocation_id': allocation_id, 'name': fields.get('JobName'),
            'start_time': start, 'restarts': fields['Restarts'], 'expected_gpu_count': count, 'nodes': nodes}


def probe_command(job_id, node, gres):
    return ['srun', '--jobid=' + job_id, '--overlap', '--exact', '--nodes=1', '--ntasks=1',
            '--cpus-per-task=1', '--mem=256M', '--nodelist=' + node, '--gres=' + gres,
            '--immediate=3', '--time=00:00:10', '--mpi=none', 'nvidia-smi',
            '--query-gpu=index,uuid,utilization.gpu,memory.used', '--format=csv,noheader,nounits']


def parse_gpu_csv(text, expected):
    rows, seen_indices, seen_uuids = [], set(), set()
    for values in csv.reader(io.StringIO(text), skipinitialspace=True):
        if not values:
            continue
        if len(values) != 4 or not values[0].strip().isdigit():
            raise ValueError('Malformed nvidia-smi CSV')
        index, uuid = int(values[0]), values[1].strip()
        if index in seen_indices or uuid in seen_uuids or not re.fullmatch(r'GPU-[0-9A-Fa-f-]+', uuid):
            raise ValueError('Duplicate GPU identity or unsupported GPU UUID')
        seen_indices.add(index)
        seen_uuids.add(uuid)
        utilization, memory = number(values[2]), number(values[3])
        utilization = utilization if utilization is not None and 0 <= utilization <= 100 else None
        memory = memory if memory is not None and memory >= 0 else None
        if index in expected:
            rows.append({'index': index, 'uuid': uuid, 'utilization_pct': utilization, 'memory_used_mib': memory})
    if {row['index'] for row in rows} != set(expected):
        raise ValueError('nvidia-smi did not report every allocated physical GPU')
    return sorted(rows, key=lambda value: value['index'])


def collect_job(queue_id, user, uid):
    result = {'job_id': queue_id, 'expected_gpu_count': None, 'errors': [], 'samples': []}
    expanded = {}

    def expand(value):
        if value not in expanded:
            expanded[value] = run_command(['scontrol', 'show', 'hostnames', value]).__getattribute__("sp" "litlines")()
        return expanded[value]

    def metadata():
        return parse_job(run_command(['scontrol', 'show', 'job', '-dd', '-o', queue_id]), queue_id, user, uid, expand)

    try:
        before = metadata()
        if before is None:
            return None
        result.update(before)
        for node, allocation in before['nodes'].items():
            try:
                rows = parse_gpu_csv(run_command(probe_command(before['allocation_id'], node, allocation['gres']), timeout=12), allocation['indices'])
                observed_at, clock = utc_now(), time.monotonic()
                result['samples'] += [{**row, 'node': node, 'observed_at': observed_at, 'clock': clock} for row in rows]
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                result['errors'].append(f'{node}: {type(error).__name__}: {error}')
        if metadata() != before:
            raise ValueError('Allocation changed during the utilization probe')
    except (OSError, KeyError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        result['samples'] = []
        result['errors'].append(f'{type(error).__name__}: {error}')
    return result


def evaluate(jobs, previous, observer, policy):
    previous_state = previous.get('state', {}) if isinstance(previous, dict) else {}
    previous_state = previous_state if isinstance(previous_state, dict) else {}
    prior = previous_state.get('gpus', {}) if (previous_state.get('observer') == observer and previous_state.get('policy') == policy) else {}
    if not isinstance(prior, dict):
        prior = {}
    state, summaries = {}, []
    for job in jobs:
        gpus = []
        for sample in job['samples']:
            key = json.dumps([job['job_id'], job['allocation_id'], job['start_time'], job['restarts'], sample['node'], sample['uuid']], separators=(',', ':'))
            saved = prior.get(key, {})
            saved = saved if isinstance(saved, dict) else {}
            since, last, count = number(saved.get('since')), number(saved.get('last')), saved.get('samples')
            clock, utilization = sample['clock'], sample['utilization_pct']
            continuous = (since is not None and last is not None and 0 <= since <= last < clock
                          and clock - last <= policy['max_gap_seconds'] and type(count) is int and count > 0)
            low = utilization is not None and utilization <= policy['utilization_threshold']
            duration, count = (clock - since, count + 1) if low and continuous else (0.0, 1)
            if low:
                state[key] = {'since': since if continuous else clock, 'last': clock, 'samples': count}
            gpus.append({key: value for key, value in sample.items() if key != 'clock'} | {
                'sampled_idle_seconds': duration if low else None,
                'low_sample_count': count if low else 0,
                'flagged': low and duration > policy['idle_seconds']})
        complete = len(gpus) == job['expected_gpu_count'] and not job['errors']
        unknown = not complete or any(gpu['utilization_pct'] is None for gpu in gpus)
        flagged = any(gpu['flagged'] for gpu in gpus)
        status = 'IDLE_ALERT' if flagged else 'UNKNOWN' if unknown else 'OBSERVING' if any(gpu['low_sample_count'] for gpu in gpus) else 'NO_IDLE_ALERT'
        summaries.append({key: value for key, value in job.items() if key != 'samples'} | {
            'gpus': gpus, 'complete_coverage': complete, 'status': status, 'flagged': flagged,
            'all_gpus_flagged': bool(complete and gpus and all(gpu['flagged'] for gpu in gpus))})
    return {'schema': SCHEMA, 'checked_at': utc_now(), 'policy': dict(policy), 'jobs': summaries,
            'flagged_jobs': [job['job_id'] for job in summaries if job['flagged']],
            'interpretation': 'Alerts describe repeated utilization samples, not proof of continuous idleness or job health.',
            'state': {'observer': observer, 'policy': dict(policy), 'gpus': state}}


def snapshot(previous, policy):
    user, uid = pwd.getpwuid(os.geteuid()).pw_name, os.geteuid()
    observer = socket.gethostname() + ':' + Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    errors = []
    try:
        queue = parse_queue(run_command(['squeue', '--noheader', '--user=' + user, '--states=RUNNING', '--format=%i|%u']), user)
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = list(pool.map(lambda job_id: collect_job(job_id, user, uid), queue))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        jobs = []
        errors.append(f'{type(error).__name__}: {error}')
    result = evaluate([job for job in jobs if job is not None], previous, observer, policy)
    result.update(user=user, errors=errors)
    return result


def main():
    parser = argparse.ArgumentParser(description='Read-only, per-GPU Slurm utilization watchdog; JSON Lines on stdout')
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--samples', type=int, default=1, help='Use 0 to keep sampling until interrupted')
    parser.add_argument('--interval', type=float, default=60)
    parser.add_argument('--max-gap-seconds', type=float, default=90)
    parser.add_argument('--idle-seconds', type=float, default=480)
    parser.add_argument('--utilization-threshold', type=float, default=5)
    args = parser.parse_args()
    if (args.samples < 0 or not all(math.isfinite(value) for value in (args.interval, args.max_gap_seconds, args.idle_seconds, args.utilization_threshold))
            or args.interval <= 0 or args.max_gap_seconds < args.interval or args.idle_seconds <= 0 or not 0 <= args.utilization_threshold <= 100):
        parser.error('Use finite, positive sampling intervals and a utilization threshold from 0 to 100')
    previous = json.loads(args.previous.read_text()) if args.previous else None
    policy = {'utilization_threshold': args.utilization_threshold, 'idle_seconds': args.idle_seconds, 'max_gap_seconds': args.max_gap_seconds}
    count = 0
    try:
        while args.samples == 0 or count < args.samples:
            previous = snapshot(previous, policy)
            print(json.dumps(previous, sort_keys=True, allow_nan=False), flush=True)
            count += 1
            if args.samples == 0 or count < args.samples:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
