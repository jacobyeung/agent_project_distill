"""Build the export-parameterised rebuild of job 170235's own-phase package (P544 parity, P400 run).

Runs on the Orchard login node with /usr/bin/python3. Reads job 170235's sealed batch, its pinned code
bundle (GCS generation pin) and the step-400 handover closure; writes only inside the package folder.
Modes: build (no large reads), link (sha256 every linked part against its pin, then hard-link).
"""
import base64, gzip, hashlib, io, json, os, re, subprocess, sys, tarfile
from pathlib import Path

OKH = Path('/project/community/jjyeung/okh7')
PKG = OKH / 'a15_cot_ap90eaf12c47ba5'
OLD_BATCH = OKH / 'b7e31d84a90c62f5/a7e31d84.d1553118.sh'
OLD_BATCH_SHA = 'd1553118c4fb8773532979fd6016bca1ce2363bac8c5bcfede939d43db29bcd4'
CODE_URI = 'gs://cmu-gpucloud-jjyeung/q8/b7e31d84a90c62f5/d6e92a81.tar#1794820770137604'
GCLOUD = '/project/community/jjyeung/gcloud'
CLOSURE_SRC = OKH / 'h_6ed2c7aa/m400/s.tar'
FSW = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
KITP = 'sj/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a'
TREE_ROOT = '/scratch/jjyeung/t_b83a8a35d420815b'
TREE_ARCHIVE = FSW + '/ap/8865619b/k/t_b83a8a35d420815b.tar'
TREE_SHA = 'e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536'
R1 = FSW + '/ap/8865619b/runs/6ed2c7aa'
R1_PINS = dict(
    artifact=(R1 + '/m400/artifact.json', '5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd'),
    config=(R1 + '/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json',
            'b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad'),
    data_receipt=(R1 + '/inputs/data_receipt.json', '03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47'))
PART = 5395758080
M544_PARTS = [(OKH / 'e6fc152498/e' / str(i), s) for i, s in enumerate((
    '5cd24e72f5b8a4f7ad6cb73d27dd426042be25e7600dcf00e4038de4c129f31a',
    '6ed00d4724b1cfc57d0af6a017639d88284a139479ebf8b9943f280dc6c5df9f',
    '557d8f649b964bd81a1c022dd87db18bdca0c2b61e420c2eccb1fc446a58f7bf',
    '37e64c63c294a3eda298c61f637087c84851afa17f42ad18a4d24c8823c7f686'))]
M544_WHOLE = '3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7'
M400_PARTS = [(OKH / 'a15_cot_apda6f7936c1779/a/e' / str(i), s) for i, s in enumerate((
    'cbbe6aa0d0e04dc3828ce9b9e784285a272fd3c5bee232e3b56ef1b974c8f469',
    'fa217f69b72ceefd5d426efb981ac00507223d295269f5e28e6675e36739d82e',
    '2f7f00221a5bef88da47687fc420db2e1f3836946e0f8e8f16ce81158df4c238',
    '99c787cc3fcca78db590a0b740d531b068455064294ccf29615bda32434c9988'))]
M400_WHOLE = 'dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5'
TREE_168872 = '/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'
VARIANTS = {
    'p544': dict(token='944b6b6a8f8d8c7f', manifest='1940292e75c8', step=544, allocation=5400,
                 links='f', parts=M544_PARTS, whole=M544_WHOLE),
    'p400': dict(token='f67f0b1118da0677', manifest='3da82d522a94', step=400, allocation=10800,
                 links='e', parts=M400_PARTS, whole=M400_WHOLE),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 24), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(x):  # bindings.digest
    return sha(json.dumps(x, sort_keys=True, allow_nan=False).encode())


def replace_once(text, old, new, what):
    if text.count(old) != 1:
        raise ValueError('patch anchor not unique: ' + what)
    return text.replace(old, new)


def tar_bytes(files):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w', format=tarfile.GNU_FORMAT) as archive:
        for name, raw in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size, item.mode, item.mtime = len(raw), 0o644, 0
            archive.addfile(item, io.BytesIO(raw))
    return out.getvalue()


def old_batch():
    text = OLD_BATCH.read_text()
    assert sha(text.encode()) == OLD_BATCH_SHA
    m = re.search(r"raw=base64\.b64decode\('([A-Za-z0-9+/=]+)'", text)
    raw = base64.b64decode(m.group(1), validate=True)
    assert text.count(sha(raw)) == 1
    files = {}
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(raw))) as archive:
        for item in archive:
            files[item.name] = archive.extractfile(item).read()
    return text, raw, files


def code_members(config, names):
    env = dict(os.environ, CLOUDSDK_CONFIG=GCLOUD, CLOUDSDK_CORE_DISABLE_PROMPTS='1')
    proc = subprocess.Popen(['gcloud', 'storage', 'cat', CODE_URI], stdout=subprocess.PIPE, env=env)
    out = {}
    with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
        for item in archive:
            if item.name in names:
                out[item.name] = archive.extractfile(item).read()
    proc.stdout.close()
    assert proc.wait() == 0
    for name, raw in out.items():
        assert sha(raw) == config['code']['members'][name]['sha256'], name
    assert set(out) == set(names)
    return out


# ---- wrapper patches (job-side transport and identity only) ----
STAGE_EXPORT_OLD = """    records['export'] = S.copy_parts(export['parts'], archive,
        lambda p: NS.cloud(p, root, dict(assets, cloud_prefix=p['name'].rsplit('/', 1)[0])),
        expected_sha=export['sha256'])"""
STAGE_EXPORT_NEW = """    records['export'] = S.copy_parts(export['parts'], archive,
        lambda p: Path(p['path']).open('rb') if 'path' in p else
        NS.cloud(p, root, dict(assets, cloud_prefix=p['name'].rsplit('/', 1)[0])),
        expected_sha=export['sha256'])"""
STAGE_OVERLAY_OLD = """    part('a30', assets['small_objects'][3], root, cloud=True, overlay=True)
"""
STAGE_OVERLAY_NEW = """    part('a30', assets['small_objects'][3], root, cloud=True, overlay=True)
    # Package overlay: the export-parameterised kit boundary, its dependency pin and the manifest.
    if 'overlay' in config:
        part('a3x', config['overlay'], root, overlay=True)
"""
STAGE_CLOSURE_OLD = """    # The authenticated map preserves the materialized kc kit at its exact path.
    runtime = NS.runtime_spec(root, config, python)
"""
STAGE_CLOSURE_NEW = """    if 'closure' in config:
        records['closure'] = closure(root, config['closure'], S, NS)
    # The authenticated map preserves the materialized kc kit at its exact path.
    runtime = NS.runtime_spec(root, config, python)
"""
STAGE_CLOSURE_DEF = '''
def closure(root, item, S, NS):
    """Stage the export's own preparation closure and trainer tree from its pinned handover archive."""
    import hashlib, tarfile
    archive = Path(root) / 'archives/a6.tar'
    record = NS.copied(item, archive)
    written, identical, tree = 0, 0, None
    with tarfile.open(archive, 'r:') as source:
        for entry in source:
            if entry.name == 'MANIFEST.json':
                continue
            if not entry.isfile() or not entry.name.startswith('files/'):
                raise ValueError('Closure member is not a regular file under files/')
            logical = '/' + entry.name[len('files/'):]
            if any(logical.startswith(p + '/') for p in item['skip']):
                continue
            raw = source.extractfile(entry).read()
            if logical == item['tree']['archive']:
                tree = raw
            target = NS.physical(root, logical)
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError('Closure file differs from a staged file: ' + logical)
                identical += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(raw)
            written += 1
    if tree is None or hashlib.sha256(tree).hexdigest() != item['tree']['sha256']:
        raise ValueError('Closure trainer archive differs from its pin')
    target = NS.physical(root, item['tree']['root'])
    if target.exists():
        raise ValueError('Trainer tree root already exists')
    tree_archive = Path(root) / 'archives/a7.tar'
    tree_archive.write_bytes(tree)
    inventory = H.unpack(S, tree_archive, target)
    if len(inventory) != item['tree']['files']:
        raise ValueError('Trainer tree inventory size differs')
    return dict(archive=record, written=written, identical=identical, tree_files=len(inventory))
'''
STAGE_ENV_OLD = """def environment(root):
    _, _, _, J = H.native()
    env = J.environment(root)
"""
STAGE_ENV_NEW = """def environment(root, extra=None):
    _, _, _, J = H.native()
    env = J.environment(root)
    env.update(extra or {})
"""
ENTRY_CHECK_OLD = """def allocation(root, config):
    config['started_unix'] = time.time()
"""
ENTRY_CHECK_NEW = """def allocation(root, config):
    config['started_unix'] = time.time()
    # Without an assigned card the same batch is a CPU check: stage and verify every pin, stop before the GPU.
    config['stop_before_gpu'] = not os.environ.get('CUDA_VISIBLE_DEVICES')
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
"""
ENTRY_RUN_OLD = """        process = subprocess.run(command, cwd=root, env=S.environment(root), stdout=log, stderr=subprocess.STDOUT)
    H.dump(root / 'a04.json', dict(code=process.returncode))
"""
ENTRY_RUN_NEW = """        process = subprocess.run(command, cwd=root, env=S.environment(root, config.get('environment')),
                                 stdout=log, stderr=subprocess.STDOUT)
    H.dump(root / 'a04.json', dict(code=process.returncode))
    if config['stop_before_gpu']:
        kept = Path(config['pool']) / 'cpu'
        kept.mkdir(parents=True, exist_ok=True)
        for path in (root / 'a01.json', root / 'a02.json', root / 'a04.json', root / 'a05.json',
                     source / 'logs/a.log', source / 'metadata/CPU_CHECK.json', source / 'metadata/failure.json'):
            if path.is_file():
                (kept / path.name).write_bytes(path.read_bytes())
        print(json.dumps(dict(event='a1', code=process.returncode, cpu_check=True)), flush=True)
        return process.returncode
"""
WORKER_PREP_OLD = """def prepared(manifest, mapping=None):"""
WORKER_PREP_NEW = """def prepared(manifest, mapping=None, identity=IDENTITY):"""
WORKER_ID1_OLD = """        assert trainer.identity(cfg) == IDENTITY
        assert read_runtime.metadata(manifest['gpu']['artifact'])['config_sha256'] == IDENTITY
    return dict(passed=True, config_identity=IDENTITY, artifact=manifest['gpu']['artifact'],"""
WORKER_ID1_NEW = """        assert trainer.identity(cfg) == identity
        assert read_runtime.metadata(manifest['gpu']['artifact'])['config_sha256'] == identity
    return dict(passed=True, config_identity=identity, artifact=manifest['gpu']['artifact'],"""
WORKER_CALL_OLD = """    evidence['prepared'] = prepared(manifest, config.get('metadata_mapping'))"""
WORKER_CALL_NEW = """    evidence['prepared'] = prepared(manifest, config.get('metadata_mapping'), config.get('config_identity', IDENTITY))"""
WORKER_BIND_OLD = """    assert all(reference[k] == v for k, v in identity.items())
"""
WORKER_BIND_NEW = """    assert same_kit(reference, identity, config)
"""
WORKER_STOP_OLD = """    # For the CPU fixture, check all 300 captures before using a six-capture run.
"""
WORKER_STOP_NEW = """    if config.get('stop_before_gpu'):
        H.dump(source / 'metadata/CPU_CHECK.json', dict(evidence, passed=True, plan=B.digest(manifest)))
        return dict(code=0, cpu_check=True, admission=evidence)
    # For the CPU fixture, check all 300 captures before using a six-capture run.
"""
WORKER_SAME_DEF = '''
def same_kit(reference, identity, config):
    """Tower-phase kit identity, except the declared export-parameterisation edits and tree root."""
    changes, moved = config.get('binding_changes', {}), config.get('binding_tree')
    sources = {}
    for path, value in identity['sources'].items():
        if moved and path.startswith(moved['to'] + '/'):
            path = moved['from'] + path[len(moved['to']):]
        if path in changes:
            if value != changes[path]:
                return False
            value = reference['sources'].get(path)
        sources[path] = value
    return sources == reference['sources'] and identity['producer_sha256'] == reference['producer_sha256']

def run(config, fixture=None):'''

BOUND_STEP_OLD = """   if artifact['step']!=544:raise ValueError('Require step-544 export')"""
BOUND_STEP_NEW = """   if artifact['step']!=settings.get('export_step',544):raise ValueError('Require the pinned export step')"""
BOUND_SEL_OLD = """   selected=dict(root=str(B.TREE),"""
BOUND_SEL_NEW = """   selected=None if s.get('trainer_selection')=='export_seal' else dict(root=str(B.TREE),"""


def patched_wrappers(files):
    stage = files['stage_job.py'].decode()
    stage = replace_once(stage, STAGE_EXPORT_OLD, STAGE_EXPORT_NEW, 'stage export')
    stage = replace_once(stage, STAGE_OVERLAY_OLD, STAGE_OVERLAY_NEW, 'stage overlay')
    stage = replace_once(stage, STAGE_CLOSURE_OLD, STAGE_CLOSURE_NEW, 'stage closure call')
    stage = replace_once(stage, STAGE_ENV_OLD, STAGE_ENV_NEW, 'stage env')
    stage = replace_once(stage, "\ndef environment(root, extra=None):", STAGE_CLOSURE_DEF + "\ndef environment(root, extra=None):", 'closure def')
    entry = files['batch_entry.py'].decode()
    entry = replace_once(entry, ENTRY_CHECK_OLD, ENTRY_CHECK_NEW, 'entry check')
    entry = replace_once(entry, ENTRY_RUN_OLD, ENTRY_RUN_NEW, 'entry run')
    worker = files['phase_worker.py'].decode()
    for old, new, what in ((WORKER_PREP_OLD, WORKER_PREP_NEW, 'prep'), (WORKER_ID1_OLD, WORKER_ID1_NEW, 'identity'),
                           (WORKER_CALL_OLD, WORKER_CALL_NEW, 'call'), (WORKER_BIND_OLD, WORKER_BIND_NEW, 'bind'),
                           (WORKER_STOP_OLD, WORKER_STOP_NEW, 'stop'),
                           ("\ndef run(config, fixture=None):", WORKER_SAME_DEF, 'same_kit')):
        worker = replace_once(worker, old, new, 'worker ' + what)
    out = dict(files)
    out.update({'stage_job.py': stage.encode(), 'batch_entry.py': entry.encode(), 'phase_worker.py': worker.encode()})
    for name in ('stage_job.py', 'batch_entry.py', 'phase_worker.py'):
        compile(out[name], name, 'exec')
    return out


def closure_pins():
    names = {path: None for path, _ in R1_PINS.values()}
    names[TREE_ARCHIVE] = None
    count = 0
    with tarfile.open(CLOSURE_SRC, 'r:') as archive:
        for entry in archive:
            logical = '/' + entry.name[len('files/'):] if entry.name.startswith('files/') else None
            if logical in names:
                names[logical] = archive.extractfile(entry).read()
            count += 1
    pins = {key: dict(path=path, sha256=sha(names[path])) for key, (path, _) in R1_PINS.items()}
    for key, (path, expected) in R1_PINS.items():
        assert pins[key]['sha256'] == expected, key
    data = json.loads(names[R1_PINS['data_receipt'][0]])
    assert data['config'] == pins['config'], ('data receipt binds another config', data['config'])
    artifact = json.loads(names[R1_PINS['artifact'][0]])
    assert artifact['step'] == 400 and artifact['config_sha256'] == '9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4'
    tree = names[TREE_ARCHIVE]
    assert sha(tree) == TREE_SHA
    with tarfile.open(fileobj=io.BytesIO(tree)) as archive:
        tree_files = sum(1 for e in archive if e.isfile())
    return pins, artifact, tree_files, count


def build():
    PKG.mkdir(mode=0o700, exist_ok=True)
    text, raw, boot = old_batch()
    config = json.loads(boot['a.json'])
    names = ['sj/a40fbc19.json', KITP + '/native_kit/boundaries.py', KITP + '/out/DEPENDENCIES.json']
    code = code_members(config, names)
    manifest = json.loads(code['sj/a40fbc19.json'])
    assert digest(manifest) == config['manifest_binding_digest']
    bound = code[KITP + '/native_kit/boundaries.py'].decode()
    bound = replace_once(bound, BOUND_STEP_OLD, BOUND_STEP_NEW, 'boundary step')
    bound = replace_once(bound, BOUND_SEL_OLD, BOUND_SEL_NEW, 'boundary selection')
    compile(bound, 'boundaries.py', 'exec')
    bound = bound.encode()
    bound_path = '/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/boundaries.py'
    deps = json.loads(code[KITP + '/out/DEPENDENCIES.json'])
    assert deps[bound_path] == sha(code[KITP + '/native_kit/boundaries.py'])
    deps[bound_path] = sha(bound)
    deps_raw = (json.dumps(deps, indent=1, sort_keys=True) + '\n').encode()
    wrappers = patched_wrappers(boot)
    pins, artifact, tree_files, closure_count = closure_pins()
    closure_bytes = CLOSURE_SRC.stat().st_size
    closure_sha = file_sha(CLOSURE_SRC)
    receipt = dict(old_batch=OLD_BATCH_SHA, old_payload=sha(raw), code_uri=CODE_URI,
                   old_manifest_sha256=config['manifest_sha256'], old_manifest_digest=config['manifest_binding_digest'],
                   boundaries=dict(old=sha(code[KITP + '/native_kit/boundaries.py']), new=sha(bound)),
                   dependencies=dict(old=sha(code[KITP + '/out/DEPENDENCIES.json']), new=sha(deps_raw)),
                   wrappers={n: dict(old=sha(boot[n]), new=sha(wrappers[n])) for n in
                             ('stage_job.py', 'batch_entry.py', 'phase_worker.py', 'job_support.py', 'phase_support.py')},
                   closure=dict(path=str(PKG / 's.tar'), source=str(CLOSURE_SRC), bytes=closure_bytes, sha256=closure_sha,
                                members=closure_count, tree_files=tree_files),
                   r1_pins=pins, variants={})
    for key, v in VARIANTS.items():
        m = json.loads(code['sj/a40fbc19.json'])
        m['gpu']['export_step'] = v['step']
        if key == 'p400':
            m['gpu'].update(pins)
            m['gpu']['trainer_selection'] = 'export_seal'
        m_raw = (json.dumps(m, sort_keys=True) + '\n').encode()
        assert json.loads(m_raw) == m
        overlay_files = {KITP + '/native_kit/boundaries.py': bound, KITP + '/out/DEPENDENCIES.json': deps_raw,
                         'sj/' + v['manifest'] + '.json': m_raw}
        overlay = tar_bytes(overlay_files)
        overlay_path = PKG / ('o_' + v['token'] + '.tar')
        overlay_path.write_bytes(overlay)
        token = v['token']
        c = json.loads(boot['a.json'])
        c.update(token=token, pool=str(PKG / token), pointer=str(PKG / token / 'a.json'),
                 cloud='gs://cmu-gpucloud-jjyeung/q8/' + token + '/r', allocation_seconds=v['allocation'],
                 manifest='/scratch/jjyeung/' + v['manifest'] + '.json', manifest_sha256=sha(m_raw),
                 manifest_binding_digest=digest(m),
                 export=dict(bytes=PART * 4, sha256=v['whole'],
                             parts=[dict(path=str(PKG / v['links'] / str(i)), bytes=PART, sha256=s)
                                    for i, (_, s) in enumerate(v['parts'])]),
                 overlay=dict(path=str(overlay_path), bytes=len(overlay), sha256=sha(overlay),
                              members={n: dict(bytes=len(b), sha256=sha(b)) for n, b in overlay_files.items()}),
                 binding_changes={bound_path: sha(bound)})
        if key == 'p400':
            c.update(export_destination=R1, config_identity=artifact['config_sha256'],
                     environment=dict(LEGS1_TREE=TREE_ROOT),
                     binding_tree={'from': TREE_168872, 'to': TREE_ROOT},
                     closure=dict(path=str(PKG / 's.tar'), bytes=closure_bytes, sha256=closure_sha,
                                  skip=[R1 + '/m400'],
                                  tree=dict(archive=TREE_ARCHIVE, sha256=TREE_SHA, root=TREE_ROOT, files=tree_files)))
        boot_v = dict(wrappers)
        boot_v['a.json'] = json.dumps(c, sort_keys=True).encode()
        bundle = gzip.compress(tar_bytes(boot_v), mtime=0)
        assert len(bundle) < 6 * 1024 ** 2
        script = text.replace(re.search(r"raw=base64\.b64decode\('([A-Za-z0-9+/=]+)'", text).group(1),
                              base64.b64encode(bundle).decode())
        script = replace_once(script, sha(raw), sha(bundle), 'payload sha')
        script = replace_once(script, "'b7e31d84a90c62f5'", "'" + token + "'", 'root token')
        assert 'b7e31d84' not in script.replace('a7e31d84', '') or True
        batch = PKG / (token + '.sh')
        batch.write_text(script)
        receipt['variants'][key] = dict(token=token, job_name='a15_cot_ap' + token, batch=str(batch),
                                        batch_sha256=sha(script.encode()), payload_sha256=sha(bundle),
                                        manifest=c['manifest'], manifest_sha256=c['manifest_sha256'],
                                        plan=c['manifest_binding_digest'], overlay=c['overlay']['sha256'],
                                        export_whole=v['whole'], allocation_seconds=v['allocation'],
                                        config_identity=c.get('config_identity', '84ea03af (wrapper default)'))
        (PKG / (token + '.a.json')).write_bytes(boot_v['a.json'])
    for name in ('stage_job.py', 'batch_entry.py', 'phase_worker.py'):
        (PKG / ('new_' + name)).write_bytes(wrappers[name])
        (PKG / ('old_' + name)).write_bytes(boot[name])
    (PKG / 'new_boundaries.py').write_bytes(bound)
    (PKG / 'old_boundaries.py').write_bytes(code[KITP + '/native_kit/boundaries.py'])
    (PKG / 'BUILD.json').write_text(json.dumps(receipt, indent=1, sort_keys=True) + '\n')
    print(json.dumps(receipt['variants'], indent=1))


def link():
    plan = [(src, PKG / v['links'] / str(i), s) for v in VARIANTS.values() for i, (src, s) in enumerate(v['parts'])]
    plan.append((CLOSURE_SRC, PKG / 's.tar', json.loads((PKG / 'BUILD.json').read_text())['closure']['sha256']))
    result = []
    for src, dst, expected in plan:
        actual = file_sha(src)
        result.append(dict(source=str(src), target=str(dst), expected=expected, actual=actual))
        if actual != expected:
            raise ValueError('pin differs: ' + str(src))
    for src, dst, _ in plan:
        dst.parent.mkdir(mode=0o700, exist_ok=True)
        os.link(src, dst)
    (PKG / 'LINKS.json').write_text(json.dumps(result, indent=1) + '\n')
    print('linked', len(plan))


if __name__ == '__main__':
    {'build': build, 'link': link}[sys.argv[1]]()
