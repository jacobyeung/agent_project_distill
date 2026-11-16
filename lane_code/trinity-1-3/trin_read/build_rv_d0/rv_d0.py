"""Receipt-gated D0 identity overlay; the reviewed payload stays immutable."""
import hashlib
import os
from pathlib import Path
import re
import stat

import trinity_read as T

ADAPTER_SHA = 'a10f34f4b6d240e0e366e56c9928f1c7d9cd080a91886d6a3a1d6c1381b35109'
EXPORT_SHA = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
CHECKER_PINS = {
    'export_check.py': '0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2',
    'common.py': '1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4',
}
TARGET = '/scratch/jjyeung/rvkit/reader/official_adapter.py'
OVERLAY = 'adapter_overlay/official_adapter.py'
RECEIPT = 'ADAPTER_OVERLAY.json'


def regular(path):
    path = Path(path).absolute()
    if '..' in path.parts or path.resolve() != path or not path.is_file():
        raise ValueError('Require a regular file without symlinks: '+str(path))
    return path


def admit(root, artifact):
    """Authenticate stage-export evidence before any GPU admission."""
    logical = artifact['path']
    match = re.fullmatch(re.escape(str(T.FSW)) + r'/ap/8865619b/runs/359fcc3c/m([1-9][0-9]*)/artifact.json', logical)
    if not match: raise ValueError('D0 requires lineage 8865619b, run 359fcc3c and a positive step')
    step = int(match.group(1))
    path = regular(T.physical(root, logical))
    # The checker resolves paths; reject links and special files before it runs.
    for directory, dirs, files in os.walk(str(path.parent), followlinks=False):
        for name in dirs + files:
            p = Path(directory)/name
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError('Symlink or special file in D0 export: '+str(p))
    receipt_dir = root/'exports'/('359fcc3c_m'+str(step))
    receipt_path = regular(receipt_dir/'RECEIPT.json')
    receipt = T.load(receipt_path)
    digest = receipt.get('artifact_sha256')
    if (receipt.get('schema') != 1 or receipt.get('status') != 'complete' or
            receipt.get('run') != '359fcc3c' or type(receipt.get('step')) is not int or receipt['step'] != step or
            receipt.get('artifact') != logical or not isinstance(digest, str) or
            not re.fullmatch('[0-9a-f]{64}', digest) or digest != artifact['sha256'] or T.sha(path) != digest):
        raise ValueError('D0 stage-export receipt identity/hash differs')
    a = T.load(path)
    if a.get('schema') != 'carrier-c1-artifact-v1' or type(a.get('step')) is not int or a['step'] != step:
        raise ValueError('D0 artifact schema/step differs from receipt')
    checker = T.load(regular(receipt_dir/'CHECK.json'))
    command = T.load(regular(receipt_dir/'COMMAND.json'))
    status = {'full': 'VERIFIED', 'header-only': 'HEADER_ONLY_NOT_VERIFIED'}.get(receipt.get('checker_mode'))
    if (status is None or receipt.get('checker') != checker or checker.get('status') != status or
            checker.get('scope') != 'direct' or type(checker.get('step')) is not int or checker['step'] != step or
            checker.get('artifact') != dict(path=logical, sha256=digest) or
            command.get('gpu') is not False or command.get('source_sha256') != CHECKER_PINS):
        raise ValueError('D0 stage-export checker evidence differs')
    return dict(schema='revsi-d0-admission-v1', step=receipt['step'], artifact=dict(artifact),
                stage_receipt_path=str(receipt_path), stage_receipt_sha256=T.sha(receipt_path),
                stage_receipt=receipt, stage_check_sha256=T.sha(receipt_dir/'CHECK.json'),
                stage_command_sha256=T.sha(receipt_dir/'COMMAND.json'))


def render(kit, identity):
    source = regular(kit/'reader/official_adapter.py').read_bytes()
    if hashlib.sha256(source).hexdigest() != ADAPTER_SHA:
        raise ValueError('Adapter source pin differs')
    for name, digest in CHECKER_PINS.items():
        if T.sha(regular(kit/'reader/out'/name)) != digest:
            raise ValueError('Export checker source pin differs')
    step = identity['step']; digest = identity['artifact']['sha256']
    if type(step) is not int or step <= 0 or not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('Invalid overlay identity')
    replacements = [
        ('EXPORT_SHA', "EXPORT_SHA='"+EXPORT_SHA+"'", "EXPORT_SHA='"+digest+"'"),
        ('bind.check_export.step', "models['base']['path'],544)", "models['base']['path'],"+str(step)+")"),
        ('bind.reader.step', 'reader=dict(step=544,', 'reader=dict(step='+str(step)+','),
        ('launch.check_export.step', "cfg['models']['base']['path'],544)", "cfg['models']['base']['path'],"+str(step)+")"),
    ]
    changes = []
    for site, old, new in replacements:
        if source.count(old.encode()) != 1: raise ValueError('Overlay replacement count differs: '+site)
        source = source.replace(old.encode(), new.encode(), 1)
        changes.append(dict(site=site, old=old, new=new))
    return source, changes


def write_overlay(out, kit, identity):
    raw, changes = render(kit, identity)
    target = out/OVERLAY
    target.parent.mkdir(exist_ok=False)
    with target.open('xb') as stream: stream.write(raw)
    evidence = dict(identity, target=TARGET, file=OVERLAY, source_sha256=ADAPTER_SHA,
                    sha256=hashlib.sha256(raw).hexdigest(), replacements=changes,
                    checker_source_sha256=CHECKER_PINS)
    T.dump(out/RECEIPT, evidence)
    return evidence


def verify_overlay(out, kit, evidence):
    raw, changes = render(kit, evidence)
    if (evidence.get('target') != TARGET or evidence.get('file') != OVERLAY or
            evidence.get('source_sha256') != ADAPTER_SHA or evidence.get('replacements') != changes or
            evidence.get('checker_source_sha256') != CHECKER_PINS or
            evidence.get('sha256') != hashlib.sha256(raw).hexdigest() or
            regular(out/OVERLAY).read_bytes() != raw):
        raise ValueError('Adapter overlay SHA256 or replacement contract differs')


def proof_scope(identity):
    return dict(schema='revsi-d0-proof-scope-v1', artifact=identity['artifact'], step=identity['step'],
        model_independent=[
            'p0/a1/a2: pinned videos, tier-32 decode and frame-plan checks',
            'p1: unchanged dry step-544 bind, serialized prompt pins, accepted 20 prompt bytes with pinned base processor',
            'a4/a5: unchanged scorer and membership checks on 10 synthetic generation items'],
        model_dependent=[
            'a0/a3: selected artifact, full shard hashes, native tensor names/dtypes/shapes checked by unchanged check_export',
            'a3: selected weights staged; tokenizer, processor and model metadata copied from pinned base',
            'a3: synthetic engine uses selected model metadata for processor parity; it does not evaluate learned weights'],
        not_established=['D0 generated-token parity', 'D0 model accuracy', 'real engine execution or GPU memory fit'],
        identity_records=['CONFIG.spec', 'ADAPTER_OVERLAY.json', 'a0/request.json.reader'],
        kit_authorization_step='AUTHORIZATION.json.step remains the unchanged kit protocol label 544; use identity_records for the selected optimizer step')


def audit_bound(out, evidence):
    request = T.load(out/'a0/request.json')
    reader = request['reader']; checked = reader['export_verification']
    if (request['models']['cp1m200'] != evidence['artifact'] or reader['step'] != evidence['step'] or
            checked.get('status') != 'VERIFIED' or checked.get('step') != evidence['step'] or
            checked.get('artifact') != {k: evidence['artifact'][k] for k in ('path', 'sha256')} or
            reader['code_pins'].get('official_adapter.py') != evidence['sha256'] or
            T.load(out/'a0/CODE_PINS.json') != reader['code_pins']):
        raise ValueError('Bound D0 model, full export verification or adapter SHA256 differs')
