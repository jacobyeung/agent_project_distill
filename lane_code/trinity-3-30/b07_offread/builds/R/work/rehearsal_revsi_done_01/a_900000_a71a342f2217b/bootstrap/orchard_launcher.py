import argparse
import base64
import hashlib
import gzip
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
        'chain_save.py', 'stdout_transfer.py', 'trace_runtime.py', 'return_io.py', 'ORCHARD_ASSETS.json', 'export_stage.py', 'gate.py', 's1.py')
SSH = ['bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh']


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
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, data in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size = len(data)
            item.mode = 0o700 if name.endswith('.sh') else 0o600
            archive.addfile(item, io.BytesIO(data))
    return gzip.compress(raw.getvalue(), compresslevel=6, mtime=0)


def render_batch(bundle, token, root_parent="/tmp"):
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
root=Path(%r)/('a_'+job+'_'+%r)
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
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(root/'bootstrap/trace_runtime.py'),
    '--script',str(root/'bootstrap/orchard_job.py'),'--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')])
EVALX_BATCH_BOOTSTRAP
''' % (encoded, hashlib.sha256(bundle).hexdigest(), root_parent, token)


def submit_argv(script, token, proof=False):
    valid_token(token)
    return ['sbatch', '--parsable', '--account=mt01', '--partition=general', '--nodes=1',
            '--ntasks=1', *(['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=02:00:00'] if proof else
            ['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=06:00:00']),
            '--signal=B:USR1@300', '--no-requeue', '--output=/dev/null', '--error=/dev/null',
            '--chdir=/tmp', '--job-name=a15_cot_ap'+token]+([script] if script is not None else [])


def submit_command(token, proof=False):
    code = (
        "import subprocess,sys\n"
        "body=sys.stdin.buffer.read(4*1024**2+1)\n"
        "if not body or len(body)>4*1024**2: raise ValueError('Invalid batch size')\n"
        "argv="+repr(submit_argv(None, token, proof=proof))+"\n"
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
    if script != render_batch(bundle, config['token'], config.get('bootstrap_parent','/tmp')):
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
    if config.get('proof_only') or config.get('bootstrap_parent','/tmp')!='/tmp':
        raise ValueError('Proof configurations cannot be submitted')
    if config.get('mode', 'production') not in ('proof', 'production'):
        raise ValueError('Invalid execution mode')
    if config.get('schema') != 'evalx-orchard-batch-v1' or config['spec']['step']!=544:
        raise ValueError('Invalid job contract')
    if canonical(config['spec'])!=config['plan_sha256']:
        raise ValueError('Plan differs')
    if config['spec']['artifact']['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef':
        raise ValueError('Artifact differs')


def validate_payload(raw, config):
    files={};total=0
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for entry in archive:
            S.relative(entry.name);total+=entry.size
            if not entry.isfile() or entry.name in files or total>32*1024**2:
                raise ValueError('Invalid payload')
            files[entry.name]=archive.extractfile(entry).read()
    if {n:hashlib.sha256(v).hexdigest() for n,v in files.items()}!=config['payload_pins']:
        raise ValueError('Payload inventory differs')


def prepare(token, destination, frame_plan=None, mode="production", pool="/project/community/jjyeung/okh7/x27ret", media_root=None, phase_b=True):
    if not Path(pool).is_absolute() or any(c in pool for c in "\n\r\x00"):raise ValueError("Invalid pool path")
    if not isinstance(media_root,str) or not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}/?',media_root):
        raise ValueError('Require an opaque --media-root under /project/community/jjyeung/okh7/')
    valid_token(token)
    destination=Path(destination)
    if destination.exists():raise FileExistsError('Require fresh preparation directory')
    package=ROOT.parent
    manifest=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
    if mode not in ('proof', 'production'):raise ValueError('Invalid execution mode')
    if frame_plan is not None:
        fp=json.loads(Path(frame_plan).read_text())
        if fp['mode']!='decode' or set(fp['videos'])!={r['relative_path'] for r in manifest}:
            raise ValueError('Require decoded plan for all 261 videos')
        for r in manifest:
            entry=fp['videos'][r['relative_path']]
            if entry['sha256']!=r['sha256']:raise ValueError('Frame plan video differs')
            import math
            total,fps=entry.get('total_frames'),entry.get('fps')
            if type(total) is not int or total!=32 or not isinstance(fps,(int,float)) or not math.isfinite(fps) or fps<=0:
                raise ValueError('Invalid decoded frame count or FPS')
            anchors=[i*(total-1)//31 for i in range(32)]
            expanded=[i for i in anchors for _ in range(2)]
            if entry.get('anchor_indices')!=anchors or entry.get('duplicate_indices')!=expanded or entry.get('timestamps')!=[i/fps for i in expanded]:
                raise ValueError('Frame plan does not use floor-uniform duplicate sampling')
    logical=J.SJ/('a'+token)
    payload_root=logical/'p'
    models=json.loads((ROOT/'MODELS.json').read_text())
    spec=dict(schema='a1',step=544,scope='direct',artifact=models['cp1m200'],models=models,
        run=str(logical/'r'),package=str(payload_root),
        interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',vllm=str(logical/'p/vllm_isolated.sh')),
        inputs=dict(rows=str(payload_root/'inputs/i1.json'),video_root=str(logical/'v0'),
                    frame_plan=str(payload_root/'cohort/FRAME_PLAN.json')))
    files={}
    def add(relative,raw):
        name=str(J.physical(Path('/'),payload_root/relative).relative_to('/'))
        files[name]=raw
    for directory in ('reader','cohort','parity','inputs'):
        for p in sorted((package/directory).rglob('*')):
            rel=p.relative_to(package)
            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and p.name not in ('meta_5130.jsonl','COHORT_OFFICIAL6.jsonl','FRAME_PLAN.json','REVSI_PUSH_FILES.json','REVSI999_PROVENANCE.json','cells_rv999_d32_cp1m200_on.json','cells_tr_rv999_cp1on.json'):
                add(rel,p.read_bytes())
    if frame_plan is not None:add(Path('cohort/FRAME_PLAN.json'),Path(frame_plan).read_bytes())
    for name in ('fakes.py','selection.py','runtime_checks.py','phase_b.py','pull.py'):
        add(Path('proof')/name,(package/'proof'/name).read_bytes())
    add(Path('launcher/MODELS.json'),(ROOT/'MODELS.json').read_bytes())
    add(Path('TRANSPORT.json'),(ROOT/'TRANSPORT.json').read_bytes())
    add(Path('vllm_isolated.sh'),('#!/bin/sh\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\n').encode())
    payload=tar_bytes(files)
    pins={n:S.sha(ROOT/n) for n in CORE}
    review=dict(schema='new-build-integrity-v1',code_pins_sha256=canonical(pins),historical_review_recovered=False)
    review_raw=(json.dumps(review,sort_keys=True)+'\n').encode()
    assets=json.loads((ROOT/'ORCHARD_ASSETS.json').read_text())
    config=dict(schema='evalx-orchard-batch-v1',mode=mode,phase_b=mode=='proof' and phase_b,media_root=media_root,pool=pool,token=token,spec=spec,output=str(logical/'o'),
        plan_sha256=canonical(spec),assets=assets,release=dict(transport=dict(path=str(payload_root/'TRANSPORT.json'),sha256=S.sha(ROOT/'TRANSPORT.json'))),
        payload_pins={n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
        payload_sha256=hashlib.sha256(payload).hexdigest(),launcher_pins=pins,
        launcher_review_pin=dict(path='REVIEW.json',sha256=hashlib.sha256(review_raw).hexdigest()),
        launcher_review=review,records={})
    validate_request(config);validate_payload(payload,config)
    boot={'bootstrap/'+n:(ROOT/n).read_bytes() for n in CORE}
    boot.update({'bootstrap/payload.tar.gz':payload,'bootstrap/CONFIG.json':(json.dumps(config,sort_keys=True)+'\n').encode(),
                 'bootstrap/REVIEW.json':review_raw})
    script=render_batch(tar_bytes(boot),token);validate_batch(script,config)
    destination.mkdir(parents=True,mode=0o700)
    (destination/'BATCH.sh').write_text(script)
    (destination/'CONFIG.json').write_text(json.dumps(config,sort_keys=True,indent=2)+'\n')
    (destination/'BATCH.pin.json').write_text(json.dumps(dict(pin(destination/'BATCH.sh'),config_sha256=S.sha(destination/'CONFIG.json')))+'\n')
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
            or config['launcher_pins'] != {name: S.sha(ROOT/name) for name in CORE}):
        raise ValueError('Batch script, configuration or source changed after packaging')
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
    result = remote(submit_command(config['token'], proof=config.get('mode')=='proof'), input=script)
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
    destination=Path(destination)
    config=json.loads((destination/'CONFIG.json').read_text())
    submission=json.loads((destination/'SUBMISSION.json').read_text())
    if submission.get('status')!='SUBMITTED':raise ValueError('Reconcile uncertain submission before fetching')
    token=valid_token(config['token']);pool=Path(config['pool'])/token
    cap=20_000_000 if config['mode']=='proof' else 90_000_000
    target=destination/'fetched';target.mkdir(mode=0o700,exist_ok=True)
    reader=('import sys;from pathlib import Path;p=Path(sys.argv[1]);'
            'assert not p.is_symlink() and p.stat().st_size<'+str(cap)+';'
            'sys.stdout.buffer.write(p.read_bytes())')
    cloud=['env','CLOUDSDK_CONFIG='+R.CLOUD_CONFIG,'gcloud','storage','cat']
    errors={}
    for channel in ('pool','gcs'):
        try:
            cmd=(['python3','-I','-B','-c',reader.replace('<'+str(cap),'<16384'),str(pool/'EXIT.json')]
                 if channel=='pool' else cloud+[R.GCS_ROOT+'/'+token+'/EXIT.json'])
            result=remote(cmd)
            if result.returncode or len(result.stdout)>16384:raise ValueError('Exit receipt unavailable')
            receipt=json.loads(result.stdout);ap=receipt.get('archive',{})
            if (receipt.get('token')!=token or str(receipt.get('job'))!=str(submission['job'])
                or receipt.get('plan_sha256')!=config['plan_sha256'] or receipt.get('synthetic') is not False):
                raise ValueError('Returned identity differs')
            if (ap.get('name')!='result.tar.gz' or type(ap.get('bytes')) is not int
                or not 0<ap['bytes']<cap or not re.fullmatch('[0-9a-f]{64}',ap.get('sha256',''))):
                raise ValueError('Missing bounded archive identity')
            command=(['python3','-I','-B','-c',reader,str(pool/'result.tar.gz')]
                     if channel=='pool' else cloud+[R.GCS_ROOT+'/'+token+'/result.tar.gz'])
            throttle=("import subprocess,sys,time\n"
                      "p=subprocess.Popen(sys.argv[1:],stdout=subprocess.PIPE)\n"
                      "start=time.monotonic();size=0\n"
                      "while True:\n"
                      " data=p.stdout.read(256*1024)\n"
                      " if not data:break\n"
                      " size+=len(data);time.sleep(max(0,size/8000000-(time.monotonic()-start)))\n"
                      " sys.stdout.buffer.write(data);sys.stdout.buffer.flush()\n"
                      "sys.exit(p.wait())\n")
            command=['python3','-I','-B','-c',throttle,*command]
            shell=shlex.join(SSH+[shlex.join(command)])+' > '+shlex.quote(str(target/'result.tar.gz'))
            if ap['bytes']>=20_000_000:
                (target/'EXIT.json').write_bytes(result.stdout)
                raise TransferRegistrationRequired('Register a governor stream before running this exact command:\n'+shell)
            archive=target/(channel+'.tar.gz')
            with archive.open('xb') as out, (target/(channel+'.stderr')).open('xb') as err:
                subprocess.run(SSH+[shlex.join(command)],stdout=out,stderr=err,check=True,timeout=180)
            if archive.stat().st_size!=ap['bytes'] or S.sha(archive)!=ap['sha256']:
                raise ValueError('Fetched archive SHA256/size differs')
            if receipt['status']=='COMPLETE':R.verify(receipt,archive,config['plan_sha256'])
            os.replace(archive,target/'result.tar.gz')
            (target/'EXIT.json').write_bytes(result.stdout)
            with tarfile.open(target/'result.tar.gz') as tf:
                try:trace=tf.getmember('TRACE.json.gz')
                except KeyError:trace=None
                if trace is not None:
                    if not trace.isfile() or trace.size>=900000:raise ValueError('Invalid packet trace')
                    (target/'TRACE.json.gz').write_bytes(tf.extractfile(trace).read())
            trace_status='archive snapshot'
            if config['mode']=='proof':
                try:
                    get=lambda n:remote(['python3','-I','-B','-c',reader.replace('<'+str(cap),'<900000'),str(pool/n)] if channel=='pool' else cloud+[R.GCS_ROOT+'/'+token+'/'+n])
                    pin_result=get('TRACE.pin.json');trace_result=get('TRACE.json.gz')
                    tp=json.loads(pin_result.stdout)
                    if (pin_result.returncode or trace_result.returncode or tp.get('token')!=token
                        or tp.get('plan_sha256')!=config['plan_sha256'] or len(trace_result.stdout)>=900000
                        or len(trace_result.stdout)!=tp.get('bytes') or hashlib.sha256(trace_result.stdout).hexdigest()!=tp.get('sha256')):
                        raise ValueError('Final trace identity differs')
                    (target/'TRACE.json.gz').write_bytes(trace_result.stdout)
                    (target/'TRACE.pin.json').write_bytes(pin_result.stdout);trace_status='final publisher trace'
                except Exception as error:errors['final_trace']=str(error)
            value=dict(status=receipt['status'],channel=channel,token=token,job=submission['job'],trace=trace_status,
                       archive=pin(target/'result.tar.gz'),fallback_errors=errors,no_files_removed=True)
            (target/'FETCH.json').write_text(json.dumps(value,indent=2)+'\n')
            return value
        except TransferRegistrationRequired:raise
        except Exception as error:errors[channel]=str(error)
    raise RuntimeError('Neither return verified: '+json.dumps(errors,sort_keys=True))


class TransferRegistrationRequired(RuntimeError):
    pass


def submission_record(destination):
    destination=Path(destination)
    config=json.loads((destination/'CONFIG.json').read_text())
    validate_batch((destination/'BATCH.sh').read_text(),config)
    answer=(destination/'SUBMIT.out').read_text().strip()
    if not re.fullmatch(r'[0-9]+(?:;[A-Za-z0-9_-]+)?',answer):
        raise ValueError('Submission is uncertain; inspect the queue and do not resubmit')
    value=dict(status='SUBMITTED',job=int(answer.split(';')[0]),token=config['token'],
        plan_sha256=config['plan_sha256'],mode=config['mode'])
    with (destination/'SUBMISSION.json').open('x') as stream:json.dump(value,stream,indent=2)
    return value


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest='action', required=True)
    prepare_parser = actions.add_parser('prepare')
    for name in ('token', 'destination'):
        prepare_parser.add_argument('--'+name, required=True)
    prepare_parser.add_argument('--media-root',required=True)
    prepare_parser.add_argument('--skip-phase-b',action='store_true')
    prepare_parser.add_argument('--frame-plan')
    prepare_parser.add_argument('--pool',default='/project/community/jjyeung/okh7/x27ret')
    prepare_parser.add_argument('--mode',choices=('proof','production'),default='production')
    submit_parser = actions.add_parser('submit')
    submit_parser.add_argument('--destination', required=True)
    command_parser=actions.add_parser('submit-command')
    command_parser.add_argument('--destination',required=True)
    record_parser=actions.add_parser('record-submission')
    record_parser.add_argument('--destination',required=True)
    fetch_parser = actions.add_parser('fetch')
    fetch_parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        value = prepare(args.token, args.destination, args.frame_plan, args.mode, args.pool, args.media_root, not args.skip_phase_b)
        print(json.dumps(dict(token=value['token'], plan_sha256=value['plan_sha256'])))
    elif args.action == 'submit-command':
        cfg=json.loads((Path(args.destination)/'CONFIG.json').read_text())
        validate_request(cfg);validate_batch((Path(args.destination)/'BATCH.sh').read_text(),cfg)
        print(shlex.join(submit_command(cfg['token'],proof=cfg['mode']=='proof')))
    elif args.action == 'record-submission':
        print(json.dumps(submission_record(args.destination),sort_keys=True))
    elif args.action == 'submit':
        print(json.dumps(submit(args.destination), sort_keys=True))
    else:
        print(json.dumps(fetch(args.destination), sort_keys=True))


if __name__ == '__main__':
    main()
