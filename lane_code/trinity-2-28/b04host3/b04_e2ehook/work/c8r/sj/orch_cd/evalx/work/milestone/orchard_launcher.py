import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import orchard_job as J
import orchard_stage as S


ROOT = Path(__file__).resolve().parent
CORE = ('orchard_launcher.py', 'orchard_job.py', 'orchard_stage.py', 'orchard_results.py',
        'chain_save.py', 'stdout_transfer.py', 'ORCHARD_ASSETS.json')
NOTICES = Path('/data3/jjyeung/orch_n13_20261026/rebuttal_iclr/ORCHARD_TO_MAIN_NOTICES.log')
SSH = ['timeout', '120', 'ssh', '-S', '/tmp/cm-okit-orchard', '-o', 'ConnectTimeout=15',
       '-o', 'ControlMaster=no', '-o', 'ProxyCommand=false', '-o', 'BatchMode=yes', 'orchard']


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def pin(path):
    return dict(path=str(Path(path).resolve()), sha256=S.sha(path))


def valid_token(token):
    if not re.fullmatch('[a-z][0-9a-f]{8,32}', token):
        raise ValueError('Invalid one-use read token')
    return token


def tar_bytes(files):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w:gz', compresslevel=6) as archive:
        for name, data in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size = len(data)
            item.mode = 0o700 if name.endswith('.sh') else 0o600
            archive.addfile(item, io.BytesIO(data))
    return raw.getvalue()


def render_batch(bundle, token):
    valid_token(token)
    encoded = base64.b64encode(bundle).decode()
    if len(encoded) > 3*1024**2:
        raise ValueError('The embedded batch package exceeds its 3 MiB limit')
    return '''#!/bin/bash
set -euo pipefail
exec python3 -I -s -B - <<'EVALX_BATCH_BOOTSTRAP'
import base64,hashlib,io,os,sys,tarfile
from pathlib import Path,PurePosixPath
job=os.environ.get('SLURM_JOB_ID','')
if not job.isdigit(): raise ValueError('An assigned Slurm batch job is required')
raw=base64.b64decode(%r,validate=True)
if hashlib.sha256(raw).hexdigest()!=%r: raise ValueError('Batch payload differs')
root=Path('/tmp')/('evalx_'+job+'_'+%r)
root.mkdir(mode=0o700)
seen=set()
total=0
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    for item in archive:
        name=PurePosixPath(item.name)
        total+=item.size
        if (name.is_absolute() or '..' in name.parts or not item.isfile()
                or item.name in seen or total>32*1024**2):
            raise ValueError('Unsafe batch package')
        seen.add(item.name)
        target=root/str(name)
        target.parent.mkdir(parents=True,exist_ok=True)
        with archive.extractfile(item) as source,target.open('xb') as output:
            output.write(source.read())
os.chdir(root)
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(root/'bootstrap/orchard_job.py'),
    '--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')])
EVALX_BATCH_BOOTSTRAP
''' % (encoded, hashlib.sha256(bundle).hexdigest(), token)


def submit_argv(script, token):
    valid_token(token)
    return ['sbatch', '--parsable', '--account=mt01', '--partition=general', '--nodes=1',
            '--ntasks=1', '--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=06:00:00',
            '--signal=B:USR1@300', '--no-requeue', '--output=/dev/null', '--error=/dev/null',
            '--chdir=/tmp', '--job-name=a15_cot_ap'+token]+([script] if script is not None else [])


def submit_command(token):
    code = (
        "import subprocess,sys\n"
        "body=sys.stdin.buffer.read(4*1024**2+1)\n"
        "if not body or len(body)>4*1024**2: raise ValueError('Invalid batch size')\n"
        "argv="+repr(submit_argv(None, token))+"\n"
        "test=subprocess.run(argv+['--test-only'],input=body,capture_output=True,timeout=50)\n"
        "sys.stderr.buffer.write(b'EVALX_TEST_ONLY_RC='+str(test.returncode).encode()+b'\\n'+test.stdout+test.stderr)\n"
        "if test.returncode: sys.exit(test.returncode)\n"
        "result=subprocess.run(argv,input=body,capture_output=True,timeout=50)\n"
        "sys.stdout.buffer.write(result.stdout)\n"
        "sys.stderr.buffer.write(result.stderr)\n"
        "sys.exit(result.returncode)\n")
    return ['python3', '-I', '-s', '-B', '-c', code]


def validate_batch(script, config):
    match = re.search(r"^raw=base64\.b64decode\('([A-Za-z0-9+/=]+)',validate=True\)$", script, re.M)
    if not match:
        raise ValueError('The batch script has no registered embedded package')
    bundle = base64.b64decode(match[1], validate=True)
    if script != render_batch(bundle, config['token']):
        raise ValueError('The batch script differs from the reviewed template')
    files, total = {}, 0
    with tarfile.open(fileobj=io.BytesIO(bundle)) as archive:
        for entry in archive:
            total += entry.size
            if (not entry.isfile() or entry.name in files or entry.size < 0
                    or len(files) > 32 or total > 32*1024**2):
                raise ValueError('Invalid embedded batch inventory')
            files[entry.name] = archive.extractfile(entry).read()
    expected = {'bootstrap/'+name for name in CORE}
    expected.update(('bootstrap/CONFIG.json', 'bootstrap/REVIEW.json', 'bootstrap/payload.tar.gz'))
    if set(files) != expected or json.loads(files['bootstrap/CONFIG.json']) != config:
        raise ValueError('The submitted configuration differs from its package')
    if json.loads(files['bootstrap/ORCHARD_ASSETS.json']) != config['assets']:
        raise ValueError('The asset registry differs from its reviewed bytes')
    for path, digest in config['launcher_pins'].items():
        if hashlib.sha256(files['bootstrap/'+Path(path).name]).hexdigest() != digest:
            raise ValueError('The batch package changed a reviewed source file')
    if (hashlib.sha256(files['bootstrap/REVIEW.json']).hexdigest() != config['launcher_review_pin']['sha256']
            or hashlib.sha256(files['bootstrap/payload.tar.gz']).hexdigest() != config['payload_sha256']):
        raise ValueError('The batch evidence or reader payload differs')


def validate_request(config):
    import chain as C
    import execute_chain as E
    if config.get('schema') != 'evalx-orchard-batch-v1':
        raise ValueError('Unrecognized Orchard batch contract')
    plan = C.validate_release(config['spec'], config['authorization'], config['release'], config['output'])
    E.validate_stage(config['spec'], config['stage'])
    if plan['plan_sha256'] != config['plan_sha256'] or config['spec']['scope'] != 'direct':
        raise ValueError('The submission is not the authenticated direct plan')


def validate_payload(raw, config):
    files, total = {}, 0
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for entry in archive:
            S.relative(entry.name)
            total += entry.size
            if (not entry.isfile() or entry.name in files or entry.size < 0
                    or len(files) >= 256 or total > 32*1024**2):
                raise ValueError('Invalid reader payload inventory')
            files[entry.name] = archive.extractfile(entry).read()
    paths = dict(config['stage']['code_pins'])
    records = (config['stage']['review_admission'], config['stage']['vnice'],
               config['authorization']['orch_order'])
    records += tuple(config['release'][name] for name in
                     ('transport', 'done_line', 'part_receipts', 'operator_identity'))
    if config['spec'].get('stop_export') is not None:
        records += tuple(config['spec']['stop_export'][name] for name in ('artifact', 'transport'))
    paths.update((record['path'], record['sha256']) for record in records)
    terminator = str(Path(config['stage']['vnice']['path']).with_name('terminator.sh'))
    paths[terminator] = config['assets']['terminator_sha256']
    if config['stage']['vnice']['sha256'] != config['assets']['vnice_sha256']:
        raise ValueError('The vnice wrapper differs from its frozen asset pin')
    expected = set()
    for path, digest in paths.items():
        name = str(J.physical(Path('/'), path).relative_to('/'))
        expected.add(name)
        if hashlib.sha256(files.get(name, b'')).hexdigest() != digest:
            raise ValueError('A packaged reader dependency differs: '+path)
    for name, field in (('SPEC', 'spec'), ('AUTHORIZATION', 'authorization'), ('RELEASE', 'release'), ('STAGE', 'stage')):
        path = str(J.physical(Path('/'), config['records'][name]).relative_to('/'))
        expected.add(path)
        if json.loads(files[path]) != config[field]:
            raise ValueError('Packaged execution records differ')
    wrapper = str(J.physical(Path('/'), config['spec']['interpreters']['vllm']).relative_to('/'))
    expected.add(wrapper)
    command = '#!/bin/sh\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\n'
    if files.get(wrapper) != command.encode() or set(files) != expected:
        raise ValueError('The isolated interpreter or payload inventory differs')


def verified_review(path, pins):
    value = json.loads(Path(path).read_text())
    if (value.get('verdict') != 'ACCEPT' or not value.get('reviewer') or value.get('synthetic') is True
            or value.get('code_pins_sha256') != canonical(pins)):
        raise ValueError('The frozen Orchard launcher requires its ACCEPT receipt')
    for name, expected in pins.items():
        if S.sha(name) != expected:
            raise ValueError('A reviewed launcher file changed: '+name)
    return value


def prepare(token, artifact, transport, order, launcher_review, destination, stop_export_step=None):
    import chain as C
    import execute_chain as E
    valid_token(token)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Require a fresh submission directory')
    pins = {str(ROOT/name): S.sha(ROOT/name) for name in CORE}
    review = verified_review(launcher_review, pins)
    artifact_value = json.loads(Path(artifact).read_text())
    wrapper = json.loads(Path(transport).read_text())
    step = wrapper['step']
    if (S.sha(artifact) != wrapper['artifact_sha256']
            or type(artifact_value.get('step')) is not int or artifact_value['step'] != step
            or artifact_value['training_source_seal']['tree_sha256'] != C.SOURCE):
        raise ValueError('Production metadata does not bind this authorized step')
    stop_export = (C.R.stop_export_record(stop_export_step, artifact, transport)
                   if stop_export_step is not None else None)
    C.R.admit_step(step, stop_export, S.sha(artifact))
    records = ROOT/'requests'/token
    spec = dict(schema=C.SCHEMA, build_only=False, step=step, scope='direct', site='orchard',
                artifact=dict(path=C.C.PRODUCTION_ARTIFACT.format(step=step), sha256=S.sha(artifact)),
                source_map_sha256=C.SOURCE, template_identity=C.CONFIG,
                config_identity=artifact_value['config_sha256'], run=str(ROOT/'runs'/token),
                interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',
                                  vllm=str(records/'vllm_isolated.sh')),
                inputs=dict(models=str(ROOT.parent/'camera/models.json'),
                    kit='/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt',
                    frames_root=str(ROOT/'assets'/token/'frames'),
                    tokenizer_dir=str(J.AP/'85fc3486'),
                    tokenizer_manifest=str(J.AP/'90da7ac2/m/base_manifest.json')))
    if stop_export is not None:
        spec['stop_export'] = stop_export
    output = str(ROOT/'saves'/token)
    release = dict(schema='evalx-production-export-release-v2', kind='production', run='469ddece',
        artifact=spec['artifact'], step=step, config_identity=spec['config_identity'],
        template_identity=C.CONFIG, source_map_sha256=C.SOURCE, production_job=int(wrapper['job']),
        transport=pin(transport), done_line=dict(path=wrapper['done_path'], sha256=wrapper['done_file_sha256']),
        part_receipts=dict(path=wrapper['receipt_path'], sha256=wrapper['receipt_file_sha256']),
        operator_identity=pin(transport))
    authorization = dict(schema='evalx-read-authorization-v2', issuer='ORCH', site='orchard',
        scope='direct', partition='general', gpus=1, steps=[step], spec_sha256=C.canonical(spec),
        output=output, orch_order=pin(order))
    plan = C.validate_release(spec, authorization, release, output)
    reader_pins = json.loads((ROOT/'SCOPED_REVIEW_REQUEST_GATES.json').read_text())['direct']['code_pins']
    reader_review = Path('/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_DIRECT_RECEIPT_GATES.json')
    stage = dict(schema='evalx-isolated-read-staging-v1', status='READY', synthetic=False,
        spec_sha256=C.canonical(spec), producer_paths_mutated=False, all_runtime_paths_node_local=True,
        code_pins=reader_pins, review_admission=pin(reader_review),
        vnice=pin(ROOT.parent/'camera/vnice/vnice.sh'))
    E.validate_stage(spec, stage)
    files = {}

    def add(path):
        path = Path(path)
        if path.stat().st_size > 8*1024**2 or path.is_symlink():
            raise ValueError('The reader package accepts only small regular input files')
        name = str(J.physical(Path('/'), path).relative_to('/'))
        files[name] = path.read_bytes()

    for path in reader_pins:
        add(path)
    for path in (reader_review, order, transport, wrapper['done_path'], wrapper['receipt_path'],
                 ROOT.parent/'camera/vnice/vnice.sh', ROOT.parent/'camera/vnice/terminator.sh'):
        add(path)
    if stop_export is not None:
        add(stop_export['artifact']['path'])
    values = dict(SPEC=spec, AUTHORIZATION=authorization, RELEASE=release, STAGE=stage)
    for name, value in values.items():
        path = J.physical(Path('/'), records/(name+'.json')).relative_to('/')
        files[str(path)] = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    interpreter = str(J.AP/'19252904/e/bin/python')
    files[str(J.physical(Path('/'), records/'vllm_isolated.sh').relative_to('/'))] = (
        '#!/bin/sh\nexec '+shlex.quote(interpreter)+' -I "$@"\n').encode()
    payload = tar_bytes(files)
    config = dict(schema='evalx-orchard-batch-v1', token=token, spec=spec, authorization=authorization,
                  release=release, stage=stage, output=output, plan_sha256=plan['plan_sha256'],
                  assets=json.loads((ROOT/'ORCHARD_ASSETS.json').read_text()),
                  records={name:str(records/(name+'.json')) for name in values},
                  payload_sha256=hashlib.sha256(payload).hexdigest(),
                  launcher_pins=pins, launcher_review=review, launcher_review_pin=pin(launcher_review))
    validate_payload(payload, config)
    boot = {'bootstrap/'+name:(ROOT/name).read_bytes() for name in CORE}
    boot['bootstrap/payload.tar.gz'] = payload
    boot['bootstrap/CONFIG.json'] = (json.dumps(config, sort_keys=True)+'\n').encode()
    boot['bootstrap/REVIEW.json'] = Path(launcher_review).read_bytes()
    script = render_batch(tar_bytes(boot), token)
    validate_batch(script, config)
    destination.mkdir(mode=0o700)
    (destination/'BATCH.sh').write_text(script)
    (destination/'CONFIG.json').write_text(json.dumps(config, indent=2, sort_keys=True)+'\n')
    batch_pin = dict(pin(destination/'BATCH.sh'), config_sha256=S.sha(destination/'CONFIG.json'))
    (destination/'BATCH.pin.json').write_text(json.dumps(batch_pin)+'\n')
    return config


def queue_admission(text, user):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    if any(len(row) != 5 for row in rows):
        raise ValueError('The general queue observation is malformed')
    if any(row[2] == user and 'gpu' in row[4].lower() for row in rows):
        raise ValueError('An existing user GPU job has the general queue; coordinate before submitting')
    return rows


def remote(argv, **kwargs):
    return subprocess.run(SSH+[shlex.join(argv)], capture_output=True, timeout=135, **kwargs)


def submit(destination):
    destination = Path(destination)
    config = json.loads((destination/'CONFIG.json').read_text())
    script = (destination/'BATCH.sh').read_bytes()
    validate_batch(script.decode(), config)
    batch_pin = json.loads((destination/'BATCH.pin.json').read_text())
    if (S.sha(destination/'BATCH.sh') != batch_pin['sha256']
            or S.sha(destination/'CONFIG.json') != batch_pin['config_sha256']
            or config['launcher_pins'] != {str(ROOT/name): S.sha(ROOT/name) for name in CORE}):
        raise ValueError('Batch script, configuration or source changed after packaging')
    if S.sha(config['launcher_review_pin']['path']) != config['launcher_review_pin']['sha256']:
        raise ValueError('The launcher ACCEPT receipt changed')
    verified_review(config['launcher_review_pin']['path'], config['launcher_pins'])
    validate_request(config)
    if (destination/'SUBMIT_INTENT.json').exists():
        raise ValueError('Submission was already attempted; never repeat an uncertain submit')
    queue = remote(['squeue', '-p', 'general', '-h', '-o', '%i|%j|%u|%T|%b'], text=True)
    if queue.returncode:
        raise RuntimeError('Queue check failed; no submission: '+queue.stderr[-2000:])
    queue_admission(queue.stdout, 'jjyeung')
    value = dict(token=config['token'], plan_sha256=config['plan_sha256'],
                 utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), queue=queue.stdout,
                 batch_sha256=hashlib.sha256(script).hexdigest(), status='SUBMIT_INTENT')
    with (destination/'SUBMIT_INTENT.json').open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
    if not NOTICES.parent.is_dir():
        raise ValueError('The required main-notices directory is unavailable')
    with NOTICES.open('a') as stream:
        stream.write(value['utc']+' evalx successor18: submitting one detached Orchard general H100 read; '
                     +'token='+config['token']+' step='+str(config['spec']['step'])
                     +' under vnice with stall guard; main retains priority.\n')
        stream.flush()
        os.fsync(stream.fileno())
    result = remote(submit_command(config['token']), input=script)
    answer = result.stdout.decode(errors='replace').strip()
    job = answer.split(';')[0]
    value.update(status='SUBMITTED' if result.returncode == 0 and job.isdigit() else 'UNCERTAIN',
                 job=int(job) if job.isdigit() else None, returncode=result.returncode,
                 stdout=answer[-4000:], stderr=result.stderr.decode(errors='replace')[-4000:])
    with (destination/'SUBMISSION.json').open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
    if value['status'] != 'SUBMITTED':
        raise RuntimeError('Submission is uncertain; preserve the intent and do not submit again')
    return value


def fetch(destination):
    import orchard_results as R
    destination = Path(destination)
    config = json.loads((destination/'CONFIG.json').read_text())
    submission = json.loads((destination/'SUBMISSION.json').read_text())
    return R.fetch_return(config, submission, destination, remote)


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest='action', required=True)
    prepare_parser = actions.add_parser('prepare')
    for name in ('token', 'artifact', 'transport', 'order', 'launcher-review', 'destination'):
        prepare_parser.add_argument('--'+name, required=True)
    prepare_parser.add_argument('--stop-export-step', type=int)
    submit_parser = actions.add_parser('submit')
    submit_parser.add_argument('--destination', required=True)
    fetch_parser = actions.add_parser('fetch')
    fetch_parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        value = prepare(args.token, args.artifact, args.transport, args.order,
                        args.launcher_review, args.destination, args.stop_export_step)
        print(json.dumps(dict(token=value['token'], plan_sha256=value['plan_sha256'])))
    elif args.action == 'submit':
        print(json.dumps(submit(args.destination), sort_keys=True))
    else:
        print(json.dumps(fetch(args.destination), sort_keys=True))


if __name__ == '__main__':
    main()
