"""Read P's persisted handover closure without opening optimizer state."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import re
from .p3_provenance import load, pinned, sha256

_paths = ContextVar('handover_content_paths', default={})
_proof = ContextVar('handover_proof_mode', default=False)


@contextmanager
def proof_scope():
    token = _proof.set(True)
    try:
        yield
    finally:
        _proof.reset(token)


INIT_POLICY = 'step400_export_weights_fresh_v1'


def init_policy(value):
    """The pinned declaration permits only fresh initialization from step 400."""
    if 'init_policy' not in value:
        return None
    if value['init_policy'] != INIT_POLICY:
        raise ValueError('P_EXPORT_INIT_POLICY_INVALID')
    if value.get('proof_mode') != 'train':
        raise ValueError('P_EXPORT_INIT_TRAIN_MODE_REQUIRED')
    if not value.get('handover_receipt') or 'persisted_files' not in value:
        raise ValueError('P_EXPORT_INIT_RECEIPT_REQUIRED')
    return INIT_POLICY


def export_only(receipt, mode=None, *, init_policy=None):
    if init_policy is not None:
        if init_policy != INIT_POLICY:
            raise ValueError('P_EXPORT_INIT_POLICY_INVALID')
        if mode != 'train':
            raise ValueError('P_EXPORT_INIT_TRAIN_MODE_REQUIRED')
        if receipt.get('schema') != 'p-export-only-v1' or type(receipt.get('step')) is not int or receipt['step'] != 400:
            raise ValueError('P_EXPORT_INIT_STEP400_ONLY')
    if receipt.get('schema') != 'p-export-only-v1':
        return False
    if init_policy is None and (mode != 'q' or not _proof.get()):
        raise ValueError('P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED')
    return True


def relocated(pin):
    return _paths.get().get(pin['sha256'], pin['path'])


def active():
    return bool(_paths.get())


@contextmanager
def scope(paths):
    token = _paths.set({**_paths.get(), **paths})
    try:
        yield
    finally:
        _paths.reset(token)


def verify(receipt_pin, p_run, artifact_pin, paths, *, weights=False, proof_mode=None, init_policy=None):
    """The caller pins h.json from the trusted ledger, independently of this bundle."""
    if not receipt_pin:
        raise ValueError('P_EXPORT_HANDOVER_RECEIPT_REQUIRED')
    try:
        receipt = load(pinned(receipt_pin))
    except (OSError, ValueError) as error:
        raise ValueError('P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED') from error
    only = export_only(receipt, proof_mode, init_policy=init_policy)
    if (receipt.get('schema') not in ('p-handover-v1', 'p-export-only-v1') or type(receipt.get('step')) is not int
            or not receipt.get('job_id') or not receipt.get('trainer_commit')):
        raise ValueError('P_EXPORT_HANDOVER_RECEIPT_INVALID')
    pins = receipt.get('pins', {})
    for key, pin in {**p_run, 'artifact':artifact_pin}.items():
        if pins.get(key, {}).get('sha256') != pin.get('sha256'):
            raise ValueError('P_EXPORT_HANDOVER_PIN_MISMATCH:'+key)
    run_keys = {'config','binding','preparation'} | (set() if only else {'checkpoint'})
    if set(p_run) != run_keys:
        raise ValueError('P_EXPORT_HANDOVER_RUN_KEYS')
    if any(not isinstance(p,dict) or set(p) != {'path','sha256'}
           or not re.fullmatch('[0-9a-f]{64}',p.get('sha256','')) for p in pins.values()):
        raise ValueError('P_EXPORT_HANDOVER_PIN_INVALID')
    if set(paths) - {p['sha256'] for p in pins.values()}:
        raise ValueError('P_EXPORT_HANDOVER_UNBOUND_RELOCATION')
    resolved = {p['sha256']:paths.get(p['sha256'],p['path']) for p in pins.values()}
    reads, absent, unread = {}, {}, {}

    def read(label):
        if label not in pins:
            raise ValueError('P_EXPORT_HANDOVER_FILE_REQUIRED:'+label)
        pin = pins[label]
        path = Path(resolved[pin['sha256']])
        if not path.is_absolute() or not path.is_file():
            raise ValueError('P_EXPORT_HANDOVER_FILE_REQUIRED:'+label)
        if sha256(path) != pin['sha256']:
            raise ValueError('P_EXPORT_HANDOVER_FILE_MISMATCH:'+label)
        reads[label] = dict(path=str(path),sha256=pin['sha256'])
        return path

    records = {k:load(read(k)) for k in ('artifact', *sorted(run_keys))}
    artifact, cfg, bound, prep = (records[k] for k in ('artifact','config','binding','preparation'))
    complete = records.get('checkpoint', {})
    from .r1_handover import export_identity
    from .carrier_c1_sweep import recipe_for
    identity = export_identity(cfg)
    if only:
        from launch_r1.p_export_receipt import stop_step, NO_CHECKPOINT
        if receipt['step'] >= stop_step(cfg):
            raise ValueError('P_EXPORT_ONLY_STOP_REQUIRES_CHECKPOINT')
        if receipt.get('checkpoint_status') != NO_CHECKPOINT or receipt.get('stop_step') != stop_step(cfg):
            raise ValueError('P_EXPORT_ONLY_CHECKPOINT_STATUS_MISMATCH')
    if (receipt['step'] != artifact.get('step')
            or (not only and complete.get('step') != artifact.get('step'))
            or artifact.get('step') not in recipe_for(cfg)['milestones']
            or (not only and (complete.get('schema') != 'c1-checkpoint-v1' or complete.get('binding') != bound))
            or bound.get('config_sha256') != identity or artifact.get('config_sha256') != identity
            or cfg.get('preparation') != pins['preparation'] or bound.get('preparation') != pins['preparation']
            or prep.get('config_sha256') != identity or receipt['trainer_commit'] != bound.get('trainer_commit')):
        raise ValueError('P_EXPORT_HANDOVER_RUN_BINDING_MISMATCH')
    expected = {'artifact','heads','full_weights'} | run_keys
    for key in ('heads','full_weights'):
        if artifact.get(key) != pins.get(key):
            raise ValueError('P_EXPORT_HANDOVER_CLOSURE_MISMATCH:'+key)
    files = complete.get('files', {})
    if not only and (not files or not complete.get('layouts') or not any(k.startswith('rng') for k in files)):
        raise ValueError('P_EXPORT_HANDOVER_CHECKPOINT_FILES_REQUIRED')
    for name, pin in files.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('P_EXPORT_HANDOVER_PATH_ESCAPE:'+name)
        label = 'checkpoint/'+name
        expected.add(label)
        if pins.get(label,{}).get('sha256') != pin.get('sha256'):
            raise ValueError('P_EXPORT_HANDOVER_CLOSURE_MISMATCH:'+label)
        if name.startswith('rng'):
            path = read(label)
            if 'bytes' in pin and path.stat().st_size != pin['bytes']:
                raise ValueError('P_EXPORT_HANDOVER_FILE_MISMATCH:'+label)
        else:
            # N initializes from the export; checkpoint state never enters N's model.
            unread[label] = dict(pin=pins[label], present=Path(resolved[pins[label]['sha256']]).is_file(),
                                 reason='receipt-bound checkpoint state; not read by export initialization')
            if not unread[label]['present']:
                absent[label] = pins[label]
    if set(prep['streams']) != set(cfg['streams']):
        raise ValueError('P_EXPORT_HANDOVER_STREAMS_MISMATCH')
    for name, stream in prep['streams'].items():
        label = 'stream/'+name; expected.add(label)
        if stream['receipt'] != cfg['streams'][name] or pins.get(label) != stream['receipt']:
            raise ValueError('P_EXPORT_HANDOVER_STREAM_RECEIPT_MISMATCH:'+name)
        read(label)
        if stream.get('indices'):
            label = 'indices/'+name; expected.add(label)
            if pins.get(label) != stream['indices']:
                raise ValueError('P_EXPORT_HANDOVER_CLOSURE_MISMATCH:'+label)
            read(label)
    export_labels = {k for k in pins if k.startswith('export/')}
    if not export_labels:
        raise ValueError('P_EXPORT_HANDOVER_EXPORT_FILES_REQUIRED')
    expected |= export_labels
    if set(pins) != expected:
        raise ValueError('P_EXPORT_HANDOVER_CLOSURE_MISMATCH')
    for label in ['heads','full_weights',*sorted(export_labels)]:
        path = Path(resolved[pins[label]['sha256']])
        if weights or path.is_file():
            read(label)
        else:
            absent[label] = pins[label]
    if 'full_weights' in reads:
        manifest = load(read('full_weights'))
        listed = [manifest['index'],*manifest['files']]
        if {'export/'+p['name'] for p in listed} != export_labels:
            raise ValueError('P_EXPORT_HANDOVER_EXPORT_MANIFEST_MISMATCH')
        for pin in listed:
            name = pin['name']; label = 'export/'+name
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('P_EXPORT_HANDOVER_PATH_ESCAPE:'+label)
            if pins[label]['sha256'] != pin['sha256']:
                raise ValueError('P_EXPORT_HANDOVER_CLOSURE_MISMATCH:'+label)
            if label in reads and 'bytes' in pin and Path(reads[label]['path']).stat().st_size != pin['bytes']:
                raise ValueError('P_EXPORT_HANDOVER_FILE_MISMATCH:'+label)
    return dict(receipt=receipt, paths=resolved, verified=reads, absent=absent, unread=unread,
                export_bytes_verified=all(k in reads for k in {'heads','full_weights',*export_labels}))


def admission(cfg, *, weights=False, official=False):
    value = cfg['r1_training']
    result = verify(value.get('handover_receipt'),value.get('p_run',{}),cfg['init_artifact']['artifact'],
                    value.get('persisted_files',{}),weights=weights,proof_mode=value.get('proof_mode'),init_policy=init_policy(value))
    from .r1_training import start
    with scope(result['paths']):
        if official or cfg.get('r2_evaluation'):
            from .r1_components import guard
            guard(load(pinned(cfg['init_artifact']['artifact'])), ['VSI-Bench', 'VSTI', 'ReVSI'], 'official-handover')
        step = start(cfg)
    return dict(result, status='ADMIT',absolute_resume_step=step,init_milestone=result['receipt']['step'])
