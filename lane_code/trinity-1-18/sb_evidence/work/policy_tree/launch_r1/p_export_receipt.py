"""Bind a published non-stop export without asserting a checkpoint exists."""
from pathlib import Path
import argparse
import os
from student_pilot.p3_provenance import file_pin, load, pinned, write

SCHEMA = 'p-export-only-v1'
NO_CHECKPOINT = 'no checkpoint at this milestone'


def stop_step(cfg):
    from student_pilot.carrier_c1_sweep import recipe_for
    limits = [recipe_for(cfg)['steps']]
    for value in (cfg, cfg.get('h1', {}), cfg.get('r1_training', {})):
        limit = value.get('stop_after_step')
        if limit is not None:
            if type(limit) is not int or limit <= 0:
                raise ValueError('P_EXPORT_ONLY_STOP_INVALID')
            limits.append(limit)
    return min(limits)


def collect(p_run, artifact_pin):
    if set(p_run) != {'config', 'binding', 'preparation'}:
        raise ValueError('P_EXPORT_ONLY_RUN_KEYS')
    cfg, bound, prep = (load(pinned(p_run[k])) for k in ('config', 'binding', 'preparation'))
    artifact = load(pinned(artifact_pin))
    from student_pilot.r1_handover import export_identity
    from student_pilot.carrier_c1_sweep import recipe_for
    identity, step = export_identity(cfg), artifact.get('step')
    if type(step) is not int or step not in recipe_for(cfg)['milestones']:
        raise ValueError('P_EXPORT_ONLY_STEP_NOT_MILESTONE')
    if step >= stop_step(cfg):
        raise ValueError('P_EXPORT_ONLY_STOP_REQUIRES_CHECKPOINT')
    if (bound.get('config_sha256') != identity or artifact.get('config_sha256') != identity
            or cfg.get('preparation') != p_run['preparation']
            or bound.get('preparation') != p_run['preparation']
            or prep.get('config_sha256') != identity or prep.get('schema') != 'c1-preparation-v1'
            or not bound.get('trainer_commit')):
        raise ValueError('P_EXPORT_ONLY_RUN_BINDING_MISMATCH')
    closure = {'artifact': artifact_pin, **p_run}
    for key in ('heads', 'full_weights'):
        pinned(artifact[key]); closure[key] = artifact[key]
    weights = load(pinned(artifact['full_weights']))
    directory = pinned(artifact['full_weights']).parent
    for item in [weights['index'], *weights['files']]:
        name = item['name']
        path = (directory / name).resolve()
        if Path(name).is_absolute() or '..' in Path(name).parts or not path.is_relative_to(directory.resolve()):
            raise ValueError('P_EXPORT_ONLY_PATH_ESCAPE:'+name)
        pin = file_pin(path)
        if pin['sha256'] != item['sha256'] or ('bytes' in item and path.stat().st_size != item['bytes']):
            raise ValueError('P_EXPORT_ONLY_FILE_MISMATCH:'+name)
        if 'export/'+name in closure:
            raise ValueError('P_EXPORT_ONLY_DUPLICATE_FILE:'+name)
        closure['export/'+name] = pin
    if not weights['files'] or set(prep['streams']) != set(cfg['streams']):
        raise ValueError('P_EXPORT_ONLY_STREAMS_OR_WEIGHTS_MISSING')
    for name, stream in prep['streams'].items():
        pin = cfg['streams'][name]
        if stream['receipt'] != pin:
            raise ValueError('P_EXPORT_ONLY_STREAM_RECEIPT_MISMATCH:'+name)
        pinned(pin); closure['stream/'+name] = pin
        if stream.get('indices'):
            pinned(stream['indices']); closure['indices/'+name] = stream['indices']
    return closure, bound['trainer_commit'], step, stop_step(cfg)


def produce(p_run, artifact_pin, output, *, job_id, trainer_commit):
    if not job_id or not trainer_commit:
        raise ValueError('P_EXPORT_ONLY_JOB_IDENTITY_REQUIRED')
    pins, commit, step, stop = collect(p_run, artifact_pin)
    if commit != trainer_commit:
        raise ValueError('P_EXPORT_ONLY_TRAINER_COMMIT_MISMATCH')
    write(Path(output), dict(schema=SCHEMA, step=step, stop_step=stop,
                            checkpoint_status=NO_CHECKPOINT, job_id=str(job_id),
                            trainer_commit=commit, pins=pins))
    return file_pin(output)


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
