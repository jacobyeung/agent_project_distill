import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tarfile
import time
import uuid

import chain_save as S


AUTHORIZED_POOL = Path('/home/jjyeung/okit/evalx_results')
READ_LIMIT = 256*1024**2
POOL_LIMIT = 1024**3
EXIT_RESERVE = 16*1024
ARCHIVE_LIMIT = READ_LIMIT-EXIT_RESERVE


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def usage(path):
    return sum(p.stat().st_size for p in S.regular_files(path))


def publish(source, pool, token, plan_sha256, returncode, synthetic=False, rate=4*1024**2):
    source, pool = Path(source), Path(pool)
    if not synthetic and (pool.resolve() != AUTHORIZED_POOL.resolve() or rate > 4*1024**2):
        raise ValueError('Results require the authorized Orchard home destination and rate')
    if synthetic and not pool.resolve().is_relative_to(Path(__file__).resolve().parent/'test_runs'):
        raise ValueError('Synthetic results require the private test directory')
    if (not re.fullmatch('[a-z][0-9a-f]{8,32}', token) or rate <= 0
            or not re.fullmatch('[0-9a-f]{64}', plan_sha256)):
        raise ValueError('Invalid return identity or rate')
    if pool.is_symlink():
        raise ValueError('Result pool must not be a symlink')
    pool.mkdir(mode=0o700, exist_ok=True)
    directory_fd = os.open(pool, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        if usage(pool)+EXIT_RESERVE > POOL_LIMIT:
            raise S.BudgetError('No room for an exit receipt within the 1 GiB result pool')
        dest = pool/token
        dest.mkdir(mode=0o700)
        complete, failed = (source/'COMPLETE.json').is_file(), (source/'FAILED.json').is_file()
        value = dict(schema='evalx-orchard-result-return-v1', token=token,
                     plan_sha256=plan_sha256, job=os.environ.get('SLURM_JOB_ID'),
                     returncode=returncode, synthetic=synthetic, archive=None,
                     archive_bytes=None, archive_complete=False,
                     conflicting_terminal_markers=complete and failed,
                     complete=complete and not failed and returncode == 0,
                     status='FAILED' if failed or returncode else 'INCOMPLETE')
        if value['complete']:
            marker = json.loads((source/'COMPLETE.json').read_text())
            value['complete'] = marker.get('plan_sha256') == plan_sha256 and marker.get('synthetic') is synthetic
            if value['complete']:
                value['status'] = 'COMPLETE'
        initial = dict(value, status='INCOMPLETE', complete=False)
        S.atomic_json(dest/'EXIT.json', initial)
        log = json.dumps(dict(job=value['job'], token=token, returncode=returncode,
                              status=value['status'], plan_sha256=plan_sha256), sort_keys=True)+'\n'
        with (dest/'JOB.log').open('x') as stream:
            stream.write(log[:4096])
            stream.flush()
            os.fsync(stream.fileno())
        local = source.parent/('.return_'+token+'_'+uuid.uuid4().hex+'.tar.gz.partial')
        try:
            paths = S.members(source)
            with local.open('xb') as raw:
                with tarfile.open(fileobj=S.LimitedWriter(raw, S.ARCHIVE_LIMIT),
                                  mode='w:gz', compresslevel=6) as archive:
                    for name, path in sorted(paths.items()):
                        archive.add(path, arcname=name, recursive=False)
                raw.flush()
                os.fsync(raw.fileno())
            size, digest = local.stat().st_size, sha(local)
            value.update(archive_bytes=size, archive_complete=True, archive_sha256=digest)
            if size > ARCHIVE_LIMIT:
                raise S.BudgetError('The compressed archive exceeds the 256 MiB per-read allowance')
            if usage(pool)+size+EXIT_RESERVE > POOL_LIMIT:
                raise S.BudgetError('The archive would exceed the 1 GiB result pool')
            partial = dest/'result.tar.gz.partial'
            started, copied = time.monotonic(), 0
            with local.open('rb') as stream, partial.open('xb') as output:
                for chunk in iter(lambda:stream.read(256*1024), b''):
                    written = output.write(chunk)
                    if written != len(chunk):
                        raise OSError('Short result write')
                    copied += written
                    time.sleep(max(0, copied/rate-(time.monotonic()-started)))
                output.flush()
                os.fsync(output.fileno())
            if copied != size or sha(partial) != digest:
                raise ValueError('Persisted result differs from the node-local archive')
            target = dest/'result.tar.gz'
            os.replace(partial, target)
            value['archive'] = dict(name=target.name, bytes=size, sha256=digest)
        except Exception as error:
            value.update(status='INCOMPLETE', complete=False, error=str(error)[:2048])
            if value['archive_bytes'] is None and local.exists():
                value.update(archive_bytes=local.stat().st_size, archive_complete=False,
                             archive_size_is_lower_bound=True)
        if (len(json.dumps(value).encode())+1024 > EXIT_RESERVE
                or usage(dest)+EXIT_RESERVE > READ_LIMIT
                or usage(pool)+EXIT_RESERVE > POOL_LIMIT):
            raise S.BudgetError('No room for the bounded exit receipt')
        S.atomic_json(dest/'EXIT.json', value)
        return value
    finally:
        os.close(directory_fd)


def verify(receipt, archive, expected_plan):
    if receipt.get('synthetic') is not False:
        raise ValueError('A synthetic return cannot admit an empirical read')
    if (receipt.get('schema') != 'evalx-orchard-result-return-v1'
            or receipt.get('plan_sha256') != expected_plan
            or receipt.get('status') != 'COMPLETE' or receipt.get('complete') is not True
            or receipt.get('conflicting_terminal_markers') is not False
            or receipt.get('returncode') != 0):
        raise ValueError('The returned read is incomplete or failed')
    archive = Path(archive)
    pin = receipt.get('archive', {})
    if (archive.is_symlink() or archive.stat().st_size != pin.get('bytes')
            or archive.stat().st_size > ARCHIVE_LIMIT or sha(archive) != pin.get('sha256')):
        raise ValueError('The returned archive identity differs')
    with tarfile.open(archive) as stream:
        names, total = set(), 0
        for entry in stream:
            total += entry.size
            if entry.name in names or len(names) >= 10000 or entry.size < 0 or total > 512*1024**2:
                raise ValueError('Invalid or oversized result inventory')
            names.add(entry.name)
            path = PurePosixPath(entry.name)
            if (not entry.isfile() or path.is_absolute() or '..' in path.parts
                    or path.suffix in ('.pt', '.safetensors', '.png', '.jpg', '.jpeg')):
                raise ValueError('Unsafe result archive member')
        if 'FAILED.json' in names or 'COMPLETE.json' not in names:
            raise ValueError('Conflicting or missing terminal markers')
        marker = json.load(stream.extractfile('COMPLETE.json'))
        if marker.get('plan_sha256') != expected_plan or marker.get('synthetic') is not False:
            raise ValueError('The chain completion identity differs')
    return receipt
