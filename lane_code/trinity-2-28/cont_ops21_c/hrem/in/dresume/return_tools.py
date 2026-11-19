"""Authenticate published D returns without importing model libraries (Python 3.6)."""
import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
import fetch_validation as fetch
import score_base as base


def read(path):
    return json.loads(Path(path).read_text())


def package_info(path):
    path = Path(path)
    trusted = base.package_identity(path)
    if path.is_dir():
        public = read(path/'0.json')
        delivery = read(path/'PACKAGE.json')
        if (delivery['token'] != public['token'] or
                delivery['files']['a/6.py'] != trusted['operator_sha256']):
            raise ValueError('Operator differs from sealed delivery')
        with tarfile.open(str(path/'0.tgz')) as t:
            raw = t.extractfile('items/dist580.json').read()
            trusted['evaluator_files'] = {m.name[len('h1eval/'):]:hashlib.sha256(t.extractfile(m).read()).hexdigest()
                for m in t if m.isfile() and m.name.startswith('h1eval/')
                and '__pycache__' not in m.name.split('/') and not m.name.endswith('.pyc')}
        trusted.update(token=public['token'], items_sha256=hashlib.sha256(raw).hexdigest())
    else:
        b = read(path)
        b = b.get('D', b)
        trusted.update(token=b['token'], items_sha256=b['items_sha256'])
        if 'evaluator_files' in b:
            trusted['evaluator_files'] = b['evaluator_files']
    return trusted


def validate_manifest(items, package):
    expected = package_info(package)
    if fetch.digest(items) != expected['items_sha256']:
        raise ValueError('Manifest differs from trusted package')
    return read(items), expected


def unpack(archive, exit_path, receipt_path, package, dest):
    """Receipts bind archive bytes before any member is written."""
    expected = package_info(package)
    ex = read(exit_path)
    token = ex.get('token', '')
    if not re.fullmatch(re.escape(expected['token'])+'[0-9a-f]{8}', token):
        raise ValueError('Return package token differs')
    if str(ex.get('job')) != str(int(token[-8:], 16)):
        raise ValueError('Return job differs')
    fetch.validate_exit(ex, archive, expected['plan'], token)
    fetch.validate_receipt(read(receipt_path), ex, exit_path, archive, expected['plan'], token)
    if ex.get('archive_complete') is not True or ex.get('conflicting_terminal_markers') is not False:
        raise ValueError('Return archive was not completely published')
    dest = Path(dest)
    with tarfile.open(str(archive)) as tar:
        members = tar.getmembers()
        seen = set()
        total = 0
        for m in members:
            p = PurePosixPath(m.name)
            total += m.size
            if (not m.isfile() or p.is_absolute() or '..' in p.parts or
                    str(p) != m.name or m.name in seen or total > 512*1024**2):
                raise ValueError('Unsafe return member')
            seen.add(m.name)
        dest.mkdir(parents=True, exist_ok=False)
        for m in members:
            target = dest/m.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as out:
                out.write(tar.extractfile(m).read())
    rid = read(dest/'metadata/RETURN_ID.json')
    if rid.get('token') != token or str(rid.get('job')) != str(ex['job']):
        raise ValueError('Inner return identity differs')
    return ex


def load(root, items, package):
    manifest, expected = validate_manifest(items, package)
    previous = base.EXPECTED_COUNT
    base.EXPECTED_COUNT = manifest['count']
    try:
        rows, meta = base.load_return(root, manifest, items, package)
    finally:
        base.EXPECTED_COUNT = previous
    if 'evaluator_files' in expected:
        want = base.canonical(sorted(expected['evaluator_files'].items()))
        if meta['binding']['evaluator_code_sha256'] != want:
            raise ValueError('Evaluator code differs from trusted package')
    root = Path(root)
    outer = read(root/'metadata/IDENTITY.json')
    inputs = read(root/'metadata/INPUTS.json')
    if outer.get('inputs') != base.canonical({k:v for k,v in inputs.items() if k != 'resume'}):
        raise ValueError('Input identity differs')
    journals = list((root/'metadata/reads').glob('*/metadata/journals/*/*/items.jsonl'))
    if [p.relative_to(root).as_posix() for p in journals] != ['metadata/reads/0/metadata/journals/3/0/items.jsonl']:
        raise ValueError('Unexpected journal layout')
    summary = read(root/'SUMMARY.json')
    if (summary.get('expected') != manifest['count'] or summary.get('completed') != len(rows)
            or summary.get('complete') != (len(rows) == manifest['count'])):
        raise ValueError('Summary and committed journals differ')
    return rows, meta
