"""Atomic Stage-1 milestones; the kit supplies its authenticated trainer revision."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import re
import uuid

import numpy as np
import torch
import torch.distributed as dist


def revision():
    value = os.environ.get('STAGE1_TRAINER_COMMIT', '')
    if not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError('Require the authenticated trainer commit from the kit')
    return value


@contextmanager
def run_lock(output, rank):
    """An OS lock releases on cancellation; the file remains for later attempts."""
    if rank != 0:
        yield
        return
    Path(output).mkdir(parents=True, exist_ok=True)
    with (Path(output)/'.train.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Training run is already active') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def binding(cfg, config_identity, world, count):
    return dict(schema='stage1-resume-v1', config_sha256=config_identity,
                trainer_commit=revision(), world_size=world, row_count=count,
                preparation=cfg['preparation'], recipe=cfg['recipe'])


def rng_state():
    return dict(python=random.getstate(), numpy=np.random.get_state(),
                torch=torch.get_rng_state(),
                cuda=torch.cuda.get_rng_state() if torch.cuda.is_available() else None)


def restore_rng(value):
    random.setstate(value['python'])
    np.random.set_state(value['numpy'])
    torch.set_rng_state(value['torch'])
    if value['cuda'] is not None:
        torch.cuda.set_rng_state(value['cuda'])


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def pending_export(output, step, export):
    output = Path(output)
    destination = output/f'step_{step}'
    if destination.exists():
        raise ValueError('Existing export cannot be overwritten')
    pending = output/f'.step_{step}.{uuid.uuid4().hex}.pending'
    export(pending)
    artifact_path = pending/'heads.json'
    artifact = json.loads(artifact_path.read_bytes())
    artifact['weights']['path'] = str(destination.resolve()/'heads.safetensors')
    if 'encoder_copy' in artifact:
        artifact['encoder_copy']['weights']['path'] = str(destination.resolve()/'encoder.safetensors')
    artifact_path.write_text(json.dumps(artifact, sort_keys=True, separators=(',', ':'))+'\n')
    return pending, destination


def publish(pending, destination, names):
    for name in names:
        with (pending/name).open('rb') as stream:
            os.fsync(stream.fileno())
    sync_dir(pending)
    if destination.exists():
        raise ValueError('Existing export cannot be overwritten')
    pending.rename(destination)
    sync_dir(destination.parent)


def final_export(output, step, export):
    """A cancellation during the last export must also leave it unpublished."""
    pending, destination = pending_export(output, step, export)
    publish(pending, destination, [p.name for p in pending.iterdir()])


def save(output, step, model, optimizer, bound, export):
    """Publish export and state together, after every rank supplied its RNG.

    A cancelled write leaves a hidden pending directory. No consumer sees it as
    a milestone, and later attempts retain it without overwriting its files.
    """
    rank, world = dist.get_rank(), dist.get_world_size()
    states = [None]*world
    dist.all_gather_object(states, rng_state())
    if rank == 0:
        output = Path(output)
        pending, destination = pending_export(output, step, export)
        schedule = [dict(name=g['name'], initial_lr=g['initial_lr'], lr=g['lr'], step=step)
                    for g in optimizer.param_groups]
        payload = dict(binding=bound, step=step, next_batch=step, schedule=schedule,
                       weights={n:p.detach().cpu() for n,p in model.named_parameters() if p.requires_grad},
                       buffers={n:b.detach().cpu() for n,b in model.named_buffers()},
                       optimizer=optimizer.state_dict(), rng=states,
                       metrics=(output/'metrics.jsonl').read_bytes())
        with (pending/'resume.pt').open('xb') as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        names = ['heads.json', 'heads.safetensors', 'resume.pt']
        if bound['recipe'].get('encoder_learning_rate') is not None:
            names.append('encoder.safetensors')
        marker = dict(binding=bound, step=step, files={name:sha(pending/name) for name in names})
        with (pending/'complete.json').open('x') as stream:
            json.dump(marker, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        publish(pending, destination, names+['complete.json'])
    dist.barrier()


def newest(output, bound):
    """Fail closed on public partial milestones; never silently roll them back."""
    output = Path(output)
    candidates = []
    for directory in output.glob('step_*'):
        match = re.fullmatch(r'step_([0-9]+)', directory.name)
        if not match or int(match[1]) not in bound['recipe']['milestones']:
            raise ValueError('Unexpected milestone export')
        candidates.append((int(match[1]), directory))
    if not candidates:
        raise ValueError('Missing complete resume state')
    step, directory = max(candidates)
    if step == bound['recipe']['steps']:
        raise ValueError('Final export already exists')
    try:
        marker = json.loads((directory/'complete.json').read_bytes())
        if marker['binding'] != bound or marker['step'] != step:
            raise ValueError('Resume identity, trainer commit, world size or schedule differs')
        names = {'heads.json', 'heads.safetensors', 'resume.pt'}
        if bound['recipe'].get('encoder_learning_rate') is not None:
            names.add('encoder.safetensors')
        if set(marker['files']) != names or any(sha(directory/n) != marker['files'][n] for n in names):
            raise ValueError('Partial or changed resume state')
        payload = torch.load(directory/'resume.pt', map_location='cpu', weights_only=False)
        if (payload['binding'] != bound or payload['step'] != step or payload['next_batch'] != step
                or len(payload['rng']) != bound['world_size'] or any(s is None for s in payload['rng'])):
            raise ValueError('Partial or inconsistent resume state')
        records = [json.loads(line) for line in payload['metrics'].splitlines()]
        if [r['step'] for r in records] != list(range(1, step+1)):
            raise ValueError('Incomplete metric prefix in resume state')
        return payload
    except (OSError, KeyError, TypeError, EOFError) as error:
        raise ValueError('Missing or partial resume state') from error


def restore(payload, model, optimizer, rank):
    from .decoupled_v import learning_rate
    parameters = {n:p for n,p in model.named_parameters() if p.requires_grad}
    buffers = dict(model.named_buffers())
    for actual, saved in ((parameters, payload['weights']), (buffers, payload['buffers'])):
        if set(actual) != set(saved) or any(actual[n].shape != saved[n].shape or
                                          actual[n].dtype != saved[n].dtype for n in actual):
            raise ValueError('Resume model layout differs')
    recipe, step = payload['binding']['recipe'], payload['step']
    expected = [dict(name=g['name'], initial_lr=g['initial_lr'], step=step,
                     lr=learning_rate(step, {**recipe, 'learning_rate':g['initial_lr']}))
                for g in optimizer.param_groups]
    saved_groups = payload['optimizer']['param_groups']
    if (payload['schedule'] != expected or len(saved_groups) != len(expected)
            or any(any(group[k] != record[k] for k in ('name', 'initial_lr', 'lr'))
                   for group, record in zip(saved_groups, expected))):
        raise ValueError('Resume LR groups or schedule position differs')
    with torch.no_grad():
        for actual, saved in ((parameters, payload['weights']), (buffers, payload['buffers'])):
            for name, tensor in actual.items():
                tensor.copy_(saved[name])
    optimizer.load_state_dict(payload['optimizer'])
    restore_rng(payload['rng'][rank])


def restore_metrics(output, payload):
    """Retain any post-checkpoint tail; recover even after an interrupted restore."""
    output = Path(output)
    pending = output/f'.metrics.{uuid.uuid4().hex}.pending'
    with pending.open('xb') as stream:
        stream.write(payload['metrics'])
        stream.flush()
        os.fsync(stream.fileno())
    current = output/'metrics.jsonl'
    if current.exists():
        current.rename(output/f'metrics.{uuid.uuid4().hex}.jsonl')
    pending.rename(current)
    sync_dir(output)
