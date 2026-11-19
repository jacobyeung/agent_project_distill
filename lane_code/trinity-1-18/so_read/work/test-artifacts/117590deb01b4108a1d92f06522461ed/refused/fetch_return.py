"""Authenticate return provenance before copying any return; Python 3.6 stdlib."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_exit(receipt, archive, plan, token):
    if receipt.get('plan_sha256') != plan:
        raise ValueError('Return plan differs')
    if receipt.get('token') != token:
        raise ValueError('Return token differs')
    if receipt.get('synthetic') is not False:
        raise ValueError('Synthetic return refused')
    size = receipt.get('archive_bytes')
    if type(size) is not int or not 0 < size < 90000000 or Path(archive).stat().st_size != size:
        raise ValueError('Return byte count differs')
    if receipt.get('archive_sha256') != digest(archive):
        raise ValueError('Return archive digest differs')
    if type(receipt.get('complete')) is not bool or receipt.get('status') != ('COMPLETE' if receipt['complete'] else 'FAILED'):
        raise ValueError('Return completion status differs')


def validate_receipt(receipt, exit_value, exit_path, archive, plan, token):
    if receipt.get('plan_sha256') != plan or receipt.get('token') != token:
        raise ValueError('Return receipt provenance differs')
    if receipt.get('job') != exit_value.get('job') or receipt.get('returned') is not True:
        raise ValueError('Return receipt job/status differs')
    pool = receipt.get('channels', {}).get('pool', {})
    if pool.get('verified') is not True:
        raise ValueError('Return pool is unverified')
    for name, path in [('EXIT.json', exit_path), ('result.tar.gz', archive)]:
        pin = pool.get('files', {}).get(name, {})
        if pin.get('sha256') != digest(path) or pin.get('bytes') != Path(path).stat().st_size:
            raise ValueError('Return receipt file differs: '+name)


def fetch(package, token, destination):
    package = Path(package).resolve()
    public = json.loads((package/'0.json').read_text())
    manifest = json.loads((package/'PACKAGE.json').read_text())
    for name, expected in manifest['files'].items():
        if digest(package/name) != expected:
            raise ValueError('Delivery member differs: '+name)
    if digest(package/'0.tgz') != public['payload_sha256']:
        raise ValueError('Payload differs')
    with tarfile.open(package/'0.tgz') as t:
        cfg = json.load(t.extractfile('9.json'))
    plan = hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if plan != public['plan_sha256'] or cfg['token'] != public['token']:
        raise ValueError('Package plan/token differs')
    if not re.fullmatch(re.escape(cfg['token'])+'[0-9a-f]{8}', token):
        raise ValueError('Requested return token differs')
    source = Path(cfg['pool'])/token
    raw = source/'result.tar.gz'
    exit_path = source/'EXIT.json'
    exit_raw = exit_path.read_bytes()
    exit_value = json.loads(exit_raw.decode())
    receipt_raw = (source/'RETURN_RECEIPT.json').read_bytes()
    receipt = json.loads(receipt_raw.decode())
    validate_exit(exit_value, raw, plan, token)
    if str(exit_value.get('job')) != str(int(token[-8:],16)):
        raise ValueError('Return job differs')
    validate_receipt(receipt, exit_value, exit_path, raw, plan, token)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    with raw.open('rb') as src, (destination/'0.tgz').open('xb') as dst:
        shutil.copyfileobj(src, dst, 1024**2)
    # Authenticate the copied bytes against the exact receipts already read.
    validate_exit(exit_value, destination/'0.tgz', plan, token)
    (destination/'EXIT.json').write_bytes(exit_raw)
    (destination/'RETURN_RECEIPT.json').write_bytes(receipt_raw)
    print(json.dumps(dict(destination=str(destination), complete=exit_value['complete'],
                          sha256=exit_value['archive_sha256'])))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', required=True)
    p.add_argument('--return-token', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    fetch(a.package, a.return_token, a.out)


if __name__ == '__main__':
    main()

