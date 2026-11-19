"""P allocation wrapper receipt; run after checkpoint and export publication."""
from pathlib import Path
import argparse
import os
from student_pilot.p3_provenance import file_pin, load, pinned, write


def collect(p_run, artifact_pin):
    """Hash the complete published closure, never copy model or database bytes."""
    if set(p_run) != {'config', 'binding', 'preparation', 'checkpoint'}:
        raise ValueError('P_HANDOVER_RUN_KEYS')
    records = {key: load(pinned(pin)) for key, pin in p_run.items()}
    artifact = load(pinned(artifact_pin))
    cfg, bound, prep, complete = (records[k] for k in ('config','binding','preparation','checkpoint'))
    from student_pilot.r1_handover import export_identity
    identity = export_identity(cfg)
    if (artifact.get('step') != 200 or complete.get('step') != 200
            or complete.get('schema') != 'c1-checkpoint-v1'
            or complete.get('binding') != bound
            or bound.get('config_sha256') != identity or artifact.get('config_sha256') != identity
            or cfg.get('preparation') != p_run['preparation']
            or bound.get('preparation') != p_run['preparation']
            or prep.get('config_sha256') != identity):
        raise ValueError('P_HANDOVER_RUN_BINDING_MISMATCH')
    closure = {'artifact': artifact_pin, **p_run}
    for key in ('heads', 'full_weights'):
        pinned(artifact[key]);closure[key] = artifact[key]
    weights = load(pinned(artifact['full_weights']))
    directory = Path(artifact['full_weights']['path']).parent
    def listed(root, name, pin, label):
        path = (root/name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('P_HANDOVER_PATH_ESCAPE:'+label)
        actual = file_pin(path)
        if actual['sha256'] != pin['sha256'] or ('bytes' in pin and path.stat().st_size != pin['bytes']):
            raise ValueError('P_HANDOVER_FILE_MISMATCH:'+label)
        closure[label] = actual
    for item in [weights['index'], *weights['files']]:
        listed(directory, item['name'], item, 'export/'+item['name'])
    files = complete.get('files')
    if not files or not complete.get('layouts') or not any(k.startswith('rng') for k in files):
        raise ValueError('P_HANDOVER_CHECKPOINT_FILES_REQUIRED')
    for name, pin in files.items():
        listed(Path(p_run['checkpoint']['path']).parent, name, pin, 'checkpoint/'+name)
    if set(prep['streams']) != set(cfg['streams']):
        raise ValueError('P_HANDOVER_STREAMS_MISMATCH')
    for name, stream in prep['streams'].items():
        pin = cfg['streams'][name]
        if stream['receipt'] != pin:
            raise ValueError('P_HANDOVER_STREAM_RECEIPT_MISMATCH:'+name)
        pinned(pin);closure['stream/'+name] = pin
        if stream.get('indices'):
            pinned(stream['indices']);closure['indices/'+name] = stream['indices']
    return closure, bound['trainer_commit']


def produce(p_run, artifact_pin, output, *, job_id, trainer_commit):
    if not job_id or not trainer_commit:
        raise ValueError('P_HANDOVER_JOB_IDENTITY_REQUIRED')
    closure, actual_commit = collect(p_run, artifact_pin)
    if actual_commit != trainer_commit:
        raise ValueError('P_HANDOVER_TRAINER_COMMIT_MISMATCH')
    write(Path(output), dict(schema='p-handover-v1', step=200, job_id=str(job_id),
                            trainer_commit=trainer_commit, pins=closure))
    return file_pin(output)


def verify_receipt(receipt_pin, p_run, artifact_pin):
    if not receipt_pin:
        raise ValueError('P_EXPORT_HANDOVER_RECEIPT_REQUIRED')
    try:
        receipt = load(pinned(receipt_pin))
    except (OSError, ValueError) as error:
        raise ValueError('P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED') from error
    if (receipt.get('schema') != 'p-handover-v1' or receipt.get('step') != 200
            or not receipt.get('job_id') or not receipt.get('trainer_commit')):
        raise ValueError('P_EXPORT_HANDOVER_RECEIPT_INVALID')
    for key, pin in {**p_run, 'artifact': artifact_pin}.items():
        if receipt.get('pins', {}).get(key) != pin:
            raise ValueError('P_EXPORT_HANDOVER_PIN_MISMATCH:'+key)
    closure, commit = collect(p_run, artifact_pin)
    if receipt['pins'] != closure or receipt['trainer_commit'] != commit:
        raise ValueError('P_EXPORT_HANDOVER_CLOSURE_MISMATCH')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-pins', required=True)
    parser.add_argument('--artifact', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--trainer-commit', required=True)
    args = parser.parse_args(argv)
    return produce(load(args.run_pins), file_pin(args.artifact), args.output,
                   job_id=os.environ.get('SLURM_JOB_ID'), trainer_commit=args.trainer_commit)


if __name__ == '__main__':
    main()
