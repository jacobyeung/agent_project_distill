from pathlib import Path
import json
R=Path(__file__).resolve().parent
K=R/'kit'
def edit(name, pairs):
 p=K/name;s=p.read_text()
 for old,new in pairs:
  assert old in s,(name,old[:100]);s=s.replace(old,new)
 p.write_text(s)
edit('launcher/orchard_launcher.py',[
 ("'return_io.py', 'ORCHARD_ASSETS.json')","'return_io.py', 'export_stage.py', 'ORCHARD_ASSETS.json')"),
 ("SSH = ['bash',", "SSH = ['timeout', '300', 'bash',"),
 ("'[a-z][0-9a-f]{8,32}'","'[0-9a-f]{10,32}'"),
 ('def submit_argv(script, token, proof=False):','def submit_argv(script, token, proof=False, afterok=None):'),
 ("    return ['sbatch',", "    if not proof and (type(afterok) is not int or afterok <= 0):\n        raise ValueError('Require successful proof dependency')\n    return ['sbatch',"),
 ('--time=02:00:00','--time=00:20:00'),('--time=06:00:00','--time=00:24:00'),
 ("'--signal=B:USR1@300'", "'--signal=B:USR1@180'"),
 ("+([script] if script is not None else [])", "+([] if proof else ['--dependency=afterok:'+str(afterok)])+([script] if script is not None else [])"),
 ('def submit_command(token, proof=False):','def submit_command(token, proof=False, afterok=None):'),
 ('submit_argv(None, token, proof=proof)','submit_argv(None, token, proof=proof, afterok=afterok)'),
 ('EVALX_TEST_ONLY_RC','A_TEST_ONLY_RC'),('EVALX_BATCH_BOOTSTRAP','A_BATCH_BOOTSTRAP'),
 ("config['spec']['step']!=544","config['spec']['step'] not in (200,400,600,800,1000)"),
 ("    if config['spec']['artifact']['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef':\n        raise ValueError('Artifact differs')", "    expected = str(J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(config['spec']['step']))/'artifact.json')\n    if config['spec']['artifact'] != dict(kind='c1_export',path=expected,sha256=None):\n        raise ValueError('Artifact differs')\n    if config.get('phase_b'):\n        raise ValueError('Unregistered optional phase')\n    if config['mode']=='production' and (type(config.get('afterok')) is not int or config['afterok']<=0):\n        raise ValueError('Require proof dependency')"),
 ('phase_b=True):','phase_b=False, step=400, proof_destination=None):'),
 ("/project/community/jjyeung/okh7/x27ret","/project/community/jjyeung/okh7/6e29a4bc"),
 ("    if not Path(pool).is_absolute() or any(c in pool for c in \"\\n\\r\\x00\"):raise ValueError(\"Invalid pool path\")", "    if not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}',pool):raise ValueError('Invalid pool path')\n    if type(step) is not int or step not in (200,400,600,800,1000):raise ValueError('Invalid step')\n    afterok=None\n    if mode=='production':\n        if proof_destination is None:raise ValueError('Require proof preparation')\n        pd=Path(proof_destination);pc=json.loads((pd/'CONFIG.json').read_text());pr=json.loads((pd/'SUBMISSION.json').read_text())\n        validate_request(pc);validate_batch((pd/'BATCH.sh').read_text(),pc)\n        if (pc['mode']!='proof' or pc['spec']['step']!=step or pc['media_root']!=media_root\n            or pr.get('status')!='SUBMITTED' or pr.get('plan_sha256')!=pc['plan_sha256']\n            or pr.get('token')!=pc['token'] or pc['token']==token):raise ValueError('Proof identity differs')\n        afterok=pr['job']"),
 ("    spec=dict(schema='a1',step=544", "    models['cp1m200']=dict(kind='c1_export',path=str(J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(step))/'artifact.json'),sha256=None)\n    spec=dict(schema='a1',step=step"),
 ('vllm_isolated.sh','a1.sh'),
 ("    add(Path('launcher/MODELS.json'),(ROOT/'MODELS.json').read_bytes())", "    add(Path('launcher/MODELS.json'),(json.dumps(models,sort_keys=True)+'\\n').encode())"),
 ("    add(Path('TRANSPORT.json'),(ROOT/'TRANSPORT.json').read_bytes())", "    transport=(json.dumps(dict(step=step,run='359fcc3c',lineage='8865619b',parts=4,receipt='/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m'+str(step)+'.done'),sort_keys=True)+'\\n').encode()\n    add(Path('TRANSPORT.json'),transport)"),
 ("S.sha(ROOT/'TRANSPORT.json')", "hashlib.sha256(transport).hexdigest()"),
 ("mode=mode,phase_b=", "mode=mode,afterok=afterok,wall_seconds=1200 if mode=='proof' else 1440,phase_b="),
 ("    validate_request(config);validate_payload(payload,config)", "    if mode=='production':\n        if pc['launcher_pins']!=pins:raise ValueError('Proof code differs')\n        # Token prefixes differ; compare every payload byte by its relative path.\n        def normalized(pins):return {n.split('/p/',1)[1]:v for n,v in pins.items()}\n        if normalized(pc['payload_pins'])!=normalized(config['payload_pins']):raise ValueError('Proof payload differs')\n    validate_request(config);validate_payload(payload,config)"),
 ("submit_command(config['token'], proof=config.get('mode')=='proof')", "submit_command(config['token'], proof=config.get('mode')=='proof',afterok=config.get('afterok'))"),
 ("submit_command(cfg['token'],proof=cfg['mode']=='proof')", "submit_command(cfg['token'],proof=cfg['mode']=='proof',afterok=cfg.get('afterok'))"),
 ("    prepare_parser.add_argument('--media-root',required=True)", "    prepare_parser.add_argument('--step',type=int,choices=(200,400,600,800,1000),default=400)\n    prepare_parser.add_argument('--proof-destination')\n    prepare_parser.add_argument('--media-root',default='/project/community/jjyeung/okh7/313db5a47f11ff0c')"),
 ('args.media_root, not args.skip_phase_b)', 'args.media_root, False, args.step, args.proof_destination)'),
 ])
# Resolved transport bytes are admitted before binding; the submitted plan retains receipt identity.
edit('launcher/orchard_stage.py',[("    for index, group in enumerate(assets['groups']):", "    for index, group in enumerate(assets['groups'][:2]):"),
 ("    camera = assets['camera_archive']\n    archive = archives/'a0.tar'\n    receipts['camera'] = copy_parts([camera], archive, lambda part: Path(part['path']).open('rb'))\n    unpack(archive, root)\n    phase('a0')", "    # The packaged reader supplies the code closure; no unused legacy tree is extracted.")])
p=K/'launcher/orchard_stage.py';s=p.read_text();start=s.index("    transport = json.loads(physical(root, config['release']");end=s.index("    receipts['videos']",start)
s=s[:start]+"    import export_stage\n    receipts['export'] = export_stage.fetch_and_stage(root, config)\n    phase('export_admission')\n"+s[end:];p.write_text(s)
# Use the byte-identical packaged checker, avoiding the unused legacy runtime tree.
edit('launcher/export_stage.py',[("CHECKER = J.SJ/'orch_cd/legs1_reads/out/export_check.py'", "CHECKER = Path('reader/out/export_check.py')"),
 ("    for name, pin in CHECKER_PINS.items():", "    checker = Path(config['spec']['package'])/CHECKER\n    for name, pin in CHECKER_PINS.items():"),
 ('CHECKER.parent/name','checker.parent/name'),('str(CHECKER),','str(checker),'),
 ("    config['admission'] = result", "    config['admission'] = result\n    package = J.physical(root, config['spec']['package'])\n    A.atomic_json(package/'launcher/MODELS.json',config['spec']['models'])")])
edit('reader/official_adapter.py',[("import os\n", "import os\nimport re\n"),
 ("EXPORT_SHA='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'", "STEPS=(200,400,600,800,1000)"),
 ("s['sha256']!=EXPORT_SHA", "not isinstance(s.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',s['sha256']) or s['sha256']=='0'*64"),
 ("'Step-544 artifact differs'", "'Unbound artifact'"),
 ("mode='production'):","mode='production',step=400):"),
 ("    model_specs(models)\n", "    model_specs(models)\n    if type(step) is not int or step not in STEPS:raise ValueError('Invalid step')\n"),
 ("check_export(models['cp1m200']['path'],EXPORT_SHA,models['base']['path'],544)", "check_export(models['cp1m200']['path'],models['cp1m200']['sha256'],models['base']['path'],step)"),
 ("reader=dict(step=544", "reader=dict(step=step"),
 ("check_export(cfg['models']['cp1m200']['path'],EXPORT_SHA,cfg['models']['base']['path'],544)", "check_export(cfg['models']['cp1m200']['path'],cfg['models']['cp1m200']['sha256'],cfg['models']['base']['path'],cfg['reader']['step'])")])
edit('reader/chain.py',[("'--reader-root','/scratch/jjyeung/orch_cd/legs1_reads',\n                 '--kit-root','/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt'", "'--reader-root',HERE,\n                 '--kit-root',HERE"),
 ("video_root'],mode=mode)","video_root'],mode=mode,step=spec['step'])"),
 ('scope=\'direct\',step=544','scope=\'direct\',step=spec[\'step\']'),
 ("contextlib.redirect_stdout(log),contextlib.redirect_stderr(log)","contextlib.redirect_stdout(HexLog(log)),contextlib.redirect_stderr(HexLog(log))"),
 ("def utility(spec,", "class HexLog:\n    def __init__(self,stream):self.stream=stream\n    def write(self,text):\n        self.stream.write(text.encode().hex()+'\\n');return len(text)\n    def flush(self):self.stream.flush()\n\n\ndef utility(spec,")])
edit('parity/prove_prompts.py',[("step=544,", "step=int(Path(models['cp1m200']['path']).parent.name[1:]),")])
# No test-file removal: retain the bounded fsync/hash evidence.
edit('launcher/return_io.py',[("only the explicitly authorized .wtest is removed", "the .wtest evidence is retained"),
 ("            # The user authorizes removal of this one test file only.\n            test.unlink()", "            # Retain the bounded write-test evidence.")])
edit('launcher/orchard_results.py',[("okh7/x27ret","okh7/6e29a4bc"),("q8/x27r","q8/6e29a4bc"),("'[a-z][0-9a-f]{8,32}'","'[0-9a-f]{10,32}'")])
# Deadlines cover staging as well as generation. The second alarm bounds return cleanup.
edit('launcher/orchard_job.py',[("    try:\n        evidence['pool_write_test']", "    signal.signal(signal.SIGALRM, interrupted)\n    signal.alarm(config.get('wall_seconds',1440)-180)\n    try:\n        evidence['pool_write_test']"),
 ("    finally:\n        source.mkdir", "    finally:\n        signal.signal(signal.SIGALRM, lambda n,f: (_ for _ in ()).throw(TimeoutError('Return deadline')))\n        signal.alarm(150)\n        source.mkdir"),
 ("        return code\n", "        signal.alarm(0)\n        return code\n")])
# Static registry has no stale accepted artifact.
p=K/'launcher/MODELS.json';v=json.loads(p.read_text());v['cp1m200'].update(path=v['cp1m200']['path'].replace('469ddece/m544','359fcc3c/m400'),sha256=None);p.write_text(json.dumps(v,indent=2)+'\n')
(K/'launcher/TRANSPORT.json').write_text(json.dumps(dict(run='359fcc3c',lineage='8865619b',steps=[200,400,600,800,1000],parts=4))+'\n')
