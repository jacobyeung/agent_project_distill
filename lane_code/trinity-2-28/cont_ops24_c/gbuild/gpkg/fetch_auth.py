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

