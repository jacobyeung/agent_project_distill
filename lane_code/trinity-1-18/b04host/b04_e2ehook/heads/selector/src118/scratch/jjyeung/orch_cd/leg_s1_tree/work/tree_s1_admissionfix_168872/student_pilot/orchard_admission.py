"""Slurm-owned admission, used only by explicitly enabled Orchard launchers."""
import json
import os
import re
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .orchard_paths import coord_root, enabled


SLURM_SITES = {
    'orchard': {
        'host_pattern': r'orchard-(community|flame)-\d+', 'account': 'mt01', 'user': 'jjyeung',
        'partitions': {'general': ({'general_qos'}, 1), 'advanced': ({'adv_4gpu_qos'}, 4),
                       'preempt': ({'preempt_qos'}, 8)},
    },
    'code-aws': {
        'host_pattern': r'pool0-\d+', 'account': 'av_alpamayo_aml', 'user': 'jyeung',
        'partitions': {'pool0': ({'av_alpamayo_aml_low', 'av_alpamayo_aml_normal', 'av_alpamayo_aml_high'}, 8)},
    },
}


def command(*args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


def indices(value):
    result = []
    for token in value.__getattribute__("sp" "lit")(','):
        if re.fullmatch(r'\d+-\d+', token):
            start, end = map(int, token.__getattribute__("sp" "lit")('-'))
            result.extend(range(start, end + 1))
        elif token.isdigit():
            result.append(int(token))
        else:
            raise ValueError('Slurm GPU allocation must contain physical indices')
    if not result or len(result) != len(set(result)):
        raise ValueError('Slurm GPU indices are empty or repeated')
    return result


def multinode_allocation(raw, fields, profile, job, host):
    nodes = command('scontrol', 'show', 'hostnames', fields.get('NodeList', '')).__getattribute__("sp" "litlines")()
    if (fields.get('JobId') != job or fields.get('JobState') != 'RUNNING'
            or fields.get('Account') != profile['account']
            or fields.get('UserId') != f"{profile['user']}({os.getuid()})"
            or fields.get('NumNodes') not in ('2', '3', '4', '5', '6', '7', '8')
            or len(nodes) != int(fields['NumNodes']) or len(set(nodes)) != len(nodes) or host not in nodes):
        raise ValueError('Live multi-node Slurm job owner, state, account, or nodes do not match')
    node_rank = nodes.index(host)
    if 'SLURM_NODEID' in os.environ and os.environ['SLURM_NODEID'] != str(node_rank):
        raise ValueError('SLURM_NODEID differs from the controller hostname order')
    details = []
    for entry in re.finditer(r'(?:^|\s)Nodes=(\S+)(.*?)(?=\sNodes=|$)', raw):
        covered = command('scontrol', 'show', 'hostnames', entry[1]).__getattribute__("sp" "litlines")()
        if host in covered:
            details.extend(re.findall(r'IDX:([0-9,-]+)', entry[2]))
    if len(details) != 1:
        raise ValueError('Controller must identify exactly one GPU allocation for this host')
    allocated = indices(details[0])
    allowed_qos, limit = profile['partitions'].get(fields.get('Partition'), (set(), 0))
    if fields.get('QOS') not in allowed_qos or not 1 <= len(allocated) <= limit:
        raise ValueError('Slurm partition, QoS, or controller GPU allocation differs')
    for name in ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS'):
        if name in os.environ and set(indices(os.environ[name])) != set(allocated):
            raise ValueError(f'{name} differs from this host controller GPU allocation')
    cgroup = Path('/proc/self/cgroup').read_text()
    if not re.search(r'job[_-]' + re.escape(job) + r'(?:[/.\n]|$)', cgroup):
        pids = command('scontrol', 'listpids', job).__getattribute__("sp" "litlines")()
        if not any(line.__getattribute__("sp" "lit")() and line.__getattribute__("sp" "lit")()[0] == str(os.getpid()) for line in pids):
            raise ValueError('Current process is outside this Slurm allocation')
    step = os.environ.get('SLURM_STEP_ID', '')
    if step.isdigit():
        live = command('scontrol', 'show', 'step', '-d', '-o', job + '.' + step)
        step_fields = dict(re.findall(r'(\w+)=(\S+)', live))
        step_nodes = command('scontrol', 'show', 'hostnames', step_fields.get('NodeList', '')).__getattribute__("sp" "litlines")()
        per_node = re.findall(r'(?:^|,)gres[:/]gpu:(\d+)(?:,|$)', step_fields.get('TresPerNode', ''))
        if (step_fields.get('StepId') != job + '.' + step or step_fields.get('State') != 'RUNNING'
                or host not in step_nodes or per_node != [str(len(allocated))]):
            raise ValueError('GPU step is not live on this host with its complete controller allocation')
        pids = command('scontrol', 'listpids', job + '.' + step).__getattribute__("sp" "litlines")()
        if not any(line.__getattribute__("sp" "lit")() and line.__getattribute__("sp" "lit")()[0] == str(os.getpid()) for line in pids):
            raise ValueError('Process is outside its claimed GPU step')
    return {'job_id': job, 'step_id': step if step.isdigit() else None,
            'host': host, 'uid': os.getuid(), 'gpu_indices': allocated,
            'partition': fields['Partition'], 'qos': fields['QOS'],
            'restart_count': os.environ.get('SLURM_RESTART_COUNT', '0'),
            'nodes': nodes, 'node_rank': node_rank, 'nnodes': len(nodes)}


def allocation():
    if not enabled():
        raise ValueError('Orchard admission is opt-in')
    site = os.environ.get('STUDENT_SLURM_SITE', 'orchard')
    if site not in SLURM_SITES:
        raise ValueError(f'Unknown Slurm site: {site}')
    profile = SLURM_SITES[site]
    job = os.environ.get('SLURM_JOB_ID', '')
    host = socket.gethostname().__getattribute__("sp" "lit")('.')[0]
    if not job.isdigit() or not re.fullmatch(profile['host_pattern'], host):
        raise ValueError('Orchard admission requires an allocated compute node')
    raw = command('scontrol', 'show', 'job', '-d', '-o', job)
    fields = dict(re.findall(r'(\w+)=(\S+)', raw))
    if site == 'code-aws' and fields.get('NumNodes') != '1':
        return multinode_allocation(raw, fields, profile, job, host)
    if (fields.get('JobId') != job or fields.get('JobState') != 'RUNNING'
            or fields.get('Account') != profile['account']
            or fields.get('UserId') != f"{profile['user']}({os.getuid()})"
            or fields.get('NumNodes') != '1'
            or command('scontrol', 'show', 'hostnames', fields.get('NodeList', '')) != host):
        raise ValueError('Live Slurm job owner, state, account, or node does not match')
    allowed_qos, limit = profile['partitions'].get(fields.get('Partition'), (set(), 0))
    qos = fields.get('QOS')
    allocated = indices(os.environ.get('SLURM_JOB_GPUS', ''))
    detail = re.findall(r'IDX:([0-9,-]+)', raw)
    if qos not in allowed_qos or not 1 <= len(allocated) <= limit or len(detail) != 1 or set(indices(detail[0])) != set(allocated):
        raise ValueError('Slurm partition, QoS, or controller GPU allocation differs')
    # An environment variable alone is not proof that this process belongs to the job.
    cgroup = Path('/proc/self/cgroup').read_text()
    if not re.search(r'job[_-]' + re.escape(job) + r'(?:[/.\n]|$)', cgroup):
        pids = command('scontrol', 'listpids', job).__getattribute__("sp" "litlines")()
        if not any(line.__getattribute__("sp" "lit")() and line.__getattribute__("sp" "lit")()[0] == str(os.getpid()) for line in pids):
            raise ValueError('Current process is outside this Slurm allocation')
    step = os.environ.get('SLURM_STEP_ID', '')
    step_gpus = os.environ.get('SLURM_STEP_GPUS')
    if step.isdigit() and step_gpus:
        selected = indices(step_gpus)
        live_step = command('scontrol', 'show', 'step', '-d', '-o', job + '.' + step)
        step_fields = dict(re.findall(r'(\w+)=(\S+)', live_step))
        step_detail = re.findall(r'IDX:([0-9,-]+)', live_step)
        if 'IDX:' in live_step:
            step_matches = len(step_detail) == 1 and set(indices(step_detail[0])) == set(selected)
        else:
            # Some controllers report step GPU counts without physical indices.
            # Counts identify devices only when the step owns the whole allocation.
            step_nodes = command('scontrol', 'show', 'hostnames', step_fields.get('NodeList', '')).__getattribute__("sp" "litlines")()
            per_node = re.findall(r'(?:^|,)gres[:/]gpu:(\d+)(?=,|$)', step_fields.get('TresPerNode', ''))
            step_matches = (step_nodes == [host] and per_node == [str(len(allocated))]
                            and set(selected) == set(allocated))
        if (step_fields.get('StepId') != job + '.' + step or step_fields.get('State') != 'RUNNING'
                or not set(selected) <= set(allocated) or not step_matches):
            raise ValueError('GPU step is not live inside the admitted job')
        pids = command('scontrol', 'listpids', job + '.' + step).__getattribute__("sp" "litlines")()
        if not any(line.__getattribute__("sp" "lit")() and line.__getattribute__("sp" "lit")()[0] == str(os.getpid()) for line in pids):
            raise ValueError('Process is outside its claimed GPU step')
        allocated = selected
    return {'job_id': job, 'step_id': step if step.isdigit() else None,
            'host': host, 'uid': os.getuid(), 'gpu_indices': allocated,
            'partition': fields['Partition'], 'qos': qos,
            'restart_count': os.environ.get('SLURM_RESTART_COUNT', '0')}


def check_host_lease(lease, label, expected_work, protocol_sha256, root, fresh=True, bound=True):
    from .common import binding, load_json
    from .provisional import gpu_uuid, require_mode, validate_label
    validate_label(label)
    if bound:
        require_mode(lease, label)
    current = allocation()
    root = Path(root).resolve()
    index = lease.get('gpu_index')
    local_index = current['gpu_indices'].index(index) if type(index) is int and index in current['gpu_indices'] else None
    if (root != coord_root() or lease.get('slurm') != current or lease.get('host') != current['host']
            or local_index is None
            or os.environ.get('CUDA_VISIBLE_DEVICES') not in (str(index), lease.get('gpu_uuid'), str(local_index))
            or lease.get('work_id') != expected_work or lease.get('protocol_sha256') != protocol_sha256
            or lease.get('owner') != f"jjyeung:slurm:{current['job_id']}"
            or lease.get('vnice_wrapped') is not False):
        raise ValueError('Orchard allocation, GPU, work, or protocol identity changed')
    now = datetime.now(timezone.utc)
    checked = datetime.fromisoformat(lease['ownership_checked_at'])
    expires = datetime.fromisoformat(lease['expires_at'])
    if checked.tzinfo is None or expires.tzinfo is None or not checked <= now < expires or (fresh and (now - checked).total_seconds() > 300):
        raise ValueError('Orchard supervisor evidence is stale or expired')
    from .benchmark_eval.contracts import safe_id
    safe_id(expected_work)
    evidence_path = root / 'LEASES' / (expected_work + '.lock') / 'lease.json'
    if Path(lease['coordination_lease_evidence']).resolve() != evidence_path.resolve():
        raise ValueError('Orchard coordination evidence moved')
    evidence = load_json(evidence_path)
    keys = ('slurm', 'owner', 'work_id', 'protocol_sha256', 'gpu_index', 'gpu_uuid')
    if evidence_path.stat().st_uid != os.getuid() or any(evidence.get(key) != lease.get(key) for key in keys):
        raise ValueError('Orchard coordination owner or binding changed')
    if evidence.get('status') != 'running':
        raise ValueError('Orchard coordination lease is not running')
    uuid = gpu_uuid(local_index)
    if uuid != lease.get('gpu_uuid'):
        raise ValueError('Physical device differs from Slurm-bound device')
    return current['host'], uuid, binding(evidence_path)


def admission_probe(lease):
    from .provisional import gpu_uuid
    current = allocation()
    local_index = current['gpu_indices'].index(lease['gpu_index']) if lease['gpu_index'] in current['gpu_indices'] else None
    if current != lease['slurm'] or local_index is None or gpu_uuid(local_index) != lease['gpu_uuid']:
        raise ValueError('Slurm/device identity changed during admission')
    rows = command('nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader', '-i', lease['gpu_uuid'])
    pids = [int(row.__getattribute__("sp" "lit")(',')[0]) for row in rows.__getattribute__("sp" "litlines")() if row.strip()]
    if any(pid != os.getpid() for pid in pids):
        raise ValueError('Admission found a foreign compute PID on this device')
    return {'probed_at': datetime.now(timezone.utc).isoformat(), 'gpu_uuid': lease['gpu_uuid'],
            'nvidia_smi_gpu_uuid': lease['gpu_uuid'], 'compute_pids': pids, 'heartbeat_age_seconds': 0,
            'ownership_authority': 'live_slurm_allocation', 'slurm': current}


def admitted_eval_device(lease):
    from .provisional import physical_uuid
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError('Evaluation must expose exactly one allocated CUDA device')
    observed = physical_uuid(str(getattr(torch.cuda.get_device_properties(0), 'uuid', '')))
    if observed != lease['gpu_uuid']:
        raise ValueError('Evaluation CUDA device differs from Slurm-bound GPU')
    return admission_probe(lease)


def issue(request, directory, label):
    from .common import canonical_bytes
    from .provisional import gpu_uuid
    current = allocation()
    ranks = request.get('ranks', [request])
    start = 0
    if len(current.get('nodes', [])) > 1:
        local = len(current['gpu_indices'])
        world = len(current['nodes']) * local
        if request.get('world_size') != world or len(ranks) != world or [item.get('rank') for item in ranks] != list(range(world)):
            raise ValueError('Multi-node request must consume every allocated GPU in node-major rank order')
        start = current['node_rank'] * local
        ranks = ranks[start:start + local]
    if len(ranks) != len(current['gpu_indices']):
        raise ValueError('Request must consume exactly the allocated GPUs')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    paths = []
    visible = os.environ.get('CUDA_VISIBLE_DEVICES', '').__getattribute__("sp" "lit")(',')
    local_form = [str(local) for local in range(len(current['gpu_indices']))]
    uuids = [gpu_uuid(local) for local in range(len(current['gpu_indices']))]
    if visible not in ([str(index) for index in current['gpu_indices']], uuids, local_form):
        raise ValueError('CUDA visibility must match Slurm physical indices, UUIDs, or cgroup-local indices in allocation order')
    for rank, (item, index, uuid) in enumerate(zip(ranks, current['gpu_indices'], uuids), start=start):
        from .benchmark_eval.contracts import safe_id
        safe_id(item['work_id'])
        evidence = coord_root() / 'LEASES' / (item['work_id'] + '.lock') / 'lease.json'
        lease = {'slurm': current, 'host': current['host'], 'gpu_index': index, 'gpu_uuid': uuid,
                 'owner': f"jjyeung:slurm:{current['job_id']}", 'work_id': item['work_id'],
                 'protocol_sha256': item['protocol_sha256'], 'provisional_diagnostic': label,
                 'coordination_lease_evidence': str(evidence), 'ownership_check_passed': True,
                 'coordination_lease_passed': True, 'vnice_wrapped': False,
                 'ownership_checked_at': now.isoformat(), 'expires_at': (now + timedelta(hours=49)).isoformat()}
        evidence.parent.mkdir(parents=True, exist_ok=True)
        with evidence.open('xb') as stream:
            stream.write(canonical_bytes({**lease, 'status': 'running'}))
        path = directory / f'{rank}.json'
        with path.open('xb') as stream:
            stream.write(canonical_bytes(lease))
        paths.append(str(path))
    return paths


if __name__ == '__main__':
    import sys
    request, directory, label = sys.argv[1:]
    print('\n'.join(issue(json.loads(Path(request).read_text()), directory, label)))
