from pathlib import Path
import json
K=Path(__file__).resolve().parents[1];P=K.parent/'pull/x27/gs/f665/sj/orch_cd/evalx/work/milestone'
f=K/'launcher/orchard_launcher.py';s=(P/f.name).read_text()
a=s.index("NOTICES =");b=s.index('\n\ndef canonical',a)
s=s[:a]+"SSH = ['bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh']\n"+s[b:]
s=s.replace('def render_batch(bundle, token):','def render_batch(bundle, token, root_parent="/tmp"):')
s=s.replace("root=Path('/tmp')/('evalx_'+job+'_'+%r)","root=Path(%r)/('a_'+job+'_'+%r)")
s=s.replace('hashlib.sha256(bundle).hexdigest(), token)','hashlib.sha256(bundle).hexdigest(), root_parent, token)')
s=s.replace("render_batch(bundle, config['token'])","render_batch(bundle, config['token'], config.get('bootstrap_parent','/tmp'))")
a=s.index('def validate_request(');b=s.index('def queue_admission(',a)
s=s[:a]+'''def validate_request(config):
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


def prepare(token, destination, frame_plan):
    valid_token(token)
    destination=Path(destination)
    if destination.exists():raise FileExistsError('Require fresh preparation directory')
    package=ROOT.parent
    manifest=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
    fp=json.loads(Path(frame_plan).read_text())
    if fp['mode']!='decode' or set(fp['videos'])!={r['relative_path'] for r in manifest}:
        raise ValueError('Require decoded plan for all 288 videos')
    for r in manifest:
        if fp['videos'][r['relative_path']]['sha256']!=r['sha256']:raise ValueError('Frame plan video differs')
    logical=J.SJ/('a'+token)
    payload_root=logical/'p'
    models=json.loads((ROOT/'MODELS.json').read_text())
    spec=dict(schema='a1',step=544,scope='direct',artifact=models['cp1m200'],models=models,
        run=str(logical/'r'),package=str(payload_root),
        interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',vllm=str(logical/'p/vllm_isolated.sh')),
        inputs=dict(rows=str(logical/'q0.jsonl'),video_root='/project/community/jjyeung/3e0e8a36',
                    frame_plan=str(payload_root/'cohort/FRAME_PLAN.json')))
    files={}
    def add(relative,raw):
        name=str(J.physical(Path('/'),payload_root/relative).relative_to('/'))
        files[name]=raw
    for directory in ('reader','cohort'):
        for p in sorted((package/directory).rglob('*')):
            rel=p.relative_to(package)
            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and 'work' not in rel.parts and p.name!='meta_5130.jsonl':
                add(rel,p.read_bytes())
    add(Path('cohort/FRAME_PLAN.json'),Path(frame_plan).read_bytes())
    add(Path('TRANSPORT.json'),(ROOT/'TRANSPORT.json').read_bytes())
    add(Path('vllm_isolated.sh'),('#!/bin/sh\\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\\n').encode())
    payload=tar_bytes(files)
    pins={str(ROOT/n):S.sha(ROOT/n) for n in CORE}
    review=dict(schema='new-build-integrity-v1',code_pins_sha256=canonical(pins),historical_review_recovered=False)
    review_raw=(json.dumps(review,sort_keys=True)+'\\n').encode()
    assets=json.loads((ROOT/'ORCHARD_ASSETS.json').read_text())
    config=dict(schema='evalx-orchard-batch-v1',token=token,spec=spec,output=str(logical/'o'),
        plan_sha256=canonical(spec),assets=assets,release=dict(transport=dict(path=str(payload_root/'TRANSPORT.json'),sha256=S.sha(ROOT/'TRANSPORT.json'))),
        payload_pins={n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
        payload_sha256=hashlib.sha256(payload).hexdigest(),launcher_pins=pins,
        launcher_review_pin=dict(path='REVIEW.json',sha256=hashlib.sha256(review_raw).hexdigest()),
        launcher_review=review,records={})
    validate_request(config);validate_payload(payload,config)
    boot={'bootstrap/'+n:(ROOT/n).read_bytes() for n in CORE}
    boot.update({'bootstrap/payload.tar.gz':payload,'bootstrap/CONFIG.json':(json.dumps(config,sort_keys=True)+'\\n').encode(),
                 'bootstrap/REVIEW.json':review_raw})
    script=render_batch(tar_bytes(boot),token);validate_batch(script,config)
    destination.mkdir(parents=True,mode=0o700)
    (destination/'BATCH.sh').write_text(script)
    (destination/'CONFIG.json').write_text(json.dumps(config,sort_keys=True,indent=2)+'\\n')
    (destination/'BATCH.pin.json').write_text(json.dumps(dict(pin(destination/'BATCH.sh'),config_sha256=S.sha(destination/'CONFIG.json')))+'\\n')
    return config


'''+s[b:]
a=s.index("    if S.sha(config['launcher_review_pin']['path'])");b=s.index('    validate_request(config)',a);s=s[:a]+s[b:]
a=s.index('    if not NOTICES.parent');b=s.index("    result = remote(submit_command",a);s=s[:a]+s[b:]
s=s.replace("for name in ('token', 'artifact', 'transport', 'order', 'launcher-review', 'destination'):","for name in ('token', 'destination', 'frame-plan'):")
s=s.replace("    prepare_parser.add_argument('--stop-export-step', type=int)\n",'')
s=s.replace("value = prepare(args.token, args.artifact, args.transport, args.order,\n                        args.launcher_review, args.destination, args.stop_export_step)","value = prepare(args.token, args.destination, args.frame_plan)")
f.write_text(s)
f=K/'launcher/orchard_stage.py';s=(P/f.name).read_text();a=s.index("    frames = physical(root,");s=s[:a]+'''    receipts['videos'] = stage_videos(root, config, physical)
    phase('videos')
    room(root)
    return receipts


def stage_videos(root, config, physical):
    root=Path(root)
    package=physical(root,config['spec']['package'])
    rows=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
    destination=root/'v'
    destination.mkdir()
    for row in rows:
        source=Path(row['alias_path'])
        if not any(source.is_relative_to(Path('/project/community/jjyeung')/a) for a in ('3e0e8a36','8b677689')):
            raise ValueError('Unregistered video alias')
        target=destination/(row['sha256']+'.mp4')
        copy_parts([dict(path=str(source),bytes=source.stat().st_size,sha256=row['sha256'])],target,
                   lambda part:Path(part['path']).open('rb'))
    question=Path('/project/community/jjyeung/cp4tk_eval/official/meta_5130.jsonl')
    target=physical(root,config['spec']['inputs']['rows']);target.parent.mkdir(parents=True,exist_ok=True)
    copy_parts([dict(bytes=question.stat().st_size,sha256='d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc')],
               target,lambda part:question.open('rb'))
    return dict(videos=len(rows),verified=True)
''';s=s.replace("archive = archives/'camera.tar'","archive = archives/'a0.tar'").replace("phase('camera_package')","phase('a0')")
f.write_text(s)
f=K/'launcher/orchard_job.py';s=(P/f.name).read_text();s=s.replace("'[/]evalx/work/milestone|[/]legs1_reads/out/direct.py'","'[/]a[a-z][0-9a-f]+/p/reader/chain.py'")
s=s.replace('def namespace(root):','def namespace(root, config=None):')
s=s.replace('    return argv\n\n\ndef environment', '''    if config is not None:
        package=physical(root,config['spec']['package'])
        for row in json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text()):
            argv += ['--ro-bind',str(root/'v'/(row['sha256']+'.mp4')),
                     config['spec']['inputs']['video_root']+'/'+row['relative_path']]
    return argv


def environment''')
a=s.index('        command = namespace(root)+');b=s.index("        with (root/'chain.log')",a)
s=s[:a]+'''        command = namespace(root,config)+[config['spec']['interpreters']['vllm'], '-s', '-B',
            str(Path(config['spec']['package'])/'reader/chain.py'),
            '--config', str(root/'bootstrap/CONFIG.json')]
'''+s[b:]
s=s.replace("            result = R.publish", "            A.ARCHIVE_LIMIT = 200000000 - 1\n            result = R.publish")
a=s.index("    if (S.sha(Path(args.config).parent/'REVIEW.json')");b=s.index("    import orchard_launcher as L",a)
s=s[:a]+'''    if (S.sha(Path(args.config).parent/'REVIEW.json') != config['launcher_review_pin']['sha256']
            or review.get('schema') != 'new-build-integrity-v1' or review.get('code_pins_sha256') != digest):
        raise ValueError('Build integrity record differs')
    for path, expected in config['launcher_pins'].items():
        if S.sha(Path(args.config).parent/Path(path).name) != expected:
            raise ValueError('A packaged dependency differs')
'''+s[b:]
f.write_text(s)
f=K/'launcher/chain_save.py';s=(P/f.name).read_text();s=s.replace('ARCHIVE_LIMIT = 900000000','ARCHIVE_LIMIT = 199999999')
a=s.index('    for family in');b=s.index("    selected.extend((source/'metadata'",a)
s=s[:a]+"    selected.extend(source/'a0'/name for name in DIRECT_FILES)\n    selected.extend((source/'report', source/'a0/CODE_PINS.json'))\n"+s[b:];f.write_text(s)
f=K/'launcher/ORCHARD_ASSETS.json';a=json.loads(f.read_text());a['base_archive']='/project/community/jjyeung/f3069074.tar';a.pop('frames_root');f.write_text(json.dumps(a,indent=2)+'\n')
