#!/usr/bin/env python3
"""The one job driver and return path: stage, run the entry, and always return what the job made.

    python3 -E -s -B -m <package>.ret job --bundle BUNDLE --root ROOT [--expect-gpus N]

BUNDLE holds kit/ (PINS.json, CONFIG.json, code) and JOB.json ({token, job_name, sessions}). ROOT is
the node-local job directory. The driver stages CONFIG.stage into ROOT, runs CONFIG.entry with
{root}, {kit} and {out} substituted, and then, whatever happened, packs ROOT/out and ROOT/logs into
one tar bounded by CONFIG.budgets.return.max_bytes and publishes it independently to the pool
(CONFIG.return.pool/<token>/) and to GCS through resumable session uploads (JOB.json sessions, one
per object name). A staging fault or an entry that fails still returns its log and traceback; a
return above its budget is refused before any upload and replaced by a tail-only return that lists
the refused members.

Receipt (RECEIPT.json, also returned): {schema, utc, token, job_id, state, rc, error,
kit_pins_sha256, config_sha256, members: [{path, bytes, sha256}], archive: {name, bytes, sha256},
refused: [{path, bytes}], pool: {dir, verified, error}, gcs: {uri, generation, verified, error}}.

Python 3.6-safe, standard library only. Nothing here removes a file.
"""
import argparse
import base64
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import tarfile
import time
import traceback

try:
    import http.client as httplib
    from urllib.parse import urlsplit
except ImportError:  # pragma: no cover
    raise

if __package__ in (None, ''):
    import importlib
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))  # noqa: A001
    importlib.import_module(__package__)
from . import stage, util  # noqa: E402

ARCHIVE = 'result.tar.gz'
RECEIPT = 'RECEIPT.json'
RETURN_DIRS = ('out', 'logs')
TAIL_BYTES = 64 * 1024
POOL_RESERVE = 1 << 20
UPLOAD_CHUNK = 8 << 20
QUANTUM = 256 * 1024
RETRY_STATUS = (408, 429, 500, 502, 503, 504)
STATES = ('complete', 'failed', 'staging_failed', 'interrupted', 'no_gpu', 'over_budget')


class BudgetError(ValueError):
    def __init__(self, message, members):
        ValueError.__init__(self, message)
        self.members = members


class UploadError(IOError):
    pass


# ---------------------------------------------------------------- archive

def collect(root, dirs=RETURN_DIRS):
    """[(arcname, path, bytes)] of every regular file under ROOT/<dir>; symlinks are skipped."""
    rows = []
    for top in dirs:
        base = os.path.join(root, top)
        for current, subdirs, files in os.walk(base):
            subdirs.sort()
            for name in sorted(files):
                path = os.path.join(current, name)
                if os.path.islink(path) or not os.path.isfile(path):
                    continue
                rows.append((os.path.relpath(path, root), path, os.path.getsize(path)))
    return rows


def tar_bound(members):
    """Upper bound of the uncompressed tar size of members (headers, long names, padding)."""
    total = 1024
    for name, _, size in members:
        total += 512 + -(-size // 512) * 512
        if len(name.encode('utf-8')) > 99:
            total += 1024 + -(-len(name.encode('utf-8')) // 512) * 512
    return -(-total // 10240) * 10240


class LimitedWriter(object):
    def __init__(self, stream, limit):
        self.stream = stream
        self.limit = limit
        self.written = 0

    def write(self, data):
        if self.written + len(data) > self.limit:
            raise BudgetError('the archive grew past %d bytes while writing' % self.limit, [])
        self.written += len(data)
        return self.stream.write(data)

    def flush(self):
        return self.stream.flush()


def build_archive(members, target, max_bytes):
    """Write members into a gzip tar at target. Refuses, before writing a byte, when their
    uncompressed bound exceeds max_bytes; the error lists every member, largest first."""
    bound = tar_bound(members)
    if max_bytes is None or bound > max_bytes:
        listed = [{'path': name, 'bytes': size}
                  for name, _, size in sorted(members, key=lambda row: (-row[2], row[0]))]
        raise BudgetError('return needs up to %d bytes; its budget is %d' % (bound, max_bytes),
                          listed)
    rows = []
    with open(target, 'xb') as raw:
        limited = LimitedWriter(raw, max_bytes)
        with tarfile.open(fileobj=limited, mode='w:gz', compresslevel=6) as archive:
            for name, path, _ in members:
                digest, count = util.sha256_file(path)
                info = archive.gettarinfo(path, arcname=name)
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                with open(path, 'rb') as handle:
                    archive.addfile(info, handle)
                rows.append({'path': name, 'bytes': count, 'sha256': digest})
        raw.flush()
        os.fsync(raw.fileno())
    digest, count = util.sha256_file(target)
    return {'name': os.path.basename(target), 'bytes': count, 'sha256': digest}, rows


def tails(members, into, limit=TAIL_BYTES):
    """Copy the last limit bytes of every log member into a fresh directory; return member rows."""
    rows = []
    for name, path, size in members:
        if not name.startswith('logs/'):
            continue
        target = os.path.join(into, name)
        parent = os.path.dirname(target)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, 'rb') as handle:
            handle.seek(max(0, size - limit))
            data = handle.read(limit)
        with open(target, 'xb') as out:
            out.write(data)
        rows.append((name, target, len(data)))
    return rows


# ---------------------------------------------------------------- pool

def publish_pool(pool, token, paths, max_bytes=None):
    """Copy files into POOL/<token>/ through .partial names, then check each copy's sha256."""
    if not pool or not os.path.isabs(pool) or os.path.islink(pool):
        raise ValueError('pool must be an absolute directory, not a link: %r' % (pool,))
    dest = os.path.join(pool, token)
    if not os.path.isdir(dest):
        os.makedirs(dest, 0o700)
    incoming = sum(os.path.getsize(path) for path in paths)
    held = sum(os.path.getsize(os.path.join(dest, name)) for name in os.listdir(dest)
               if os.path.isfile(os.path.join(dest, name)))
    if max_bytes is not None and held + incoming > max_bytes:
        raise ValueError('pool budget: %d held + %d incoming > %d' % (held, incoming, max_bytes))
    vfs = os.statvfs(dest)
    if vfs.f_bavail * vfs.f_frsize < incoming + POOL_RESERVE:
        raise ValueError('pool has %d bytes free; %d needed' % (vfs.f_bavail * vfs.f_frsize,
                                                                  incoming + POOL_RESERVE))
    files = {}
    for path in paths:
        name = os.path.basename(path)
        partial = os.path.join(dest, '%s.partial.%d' % (name, int(time.time() * 1e6)))
        with open(path, 'rb') as src, open(partial, 'xb') as out:
            while True:
                block = src.read(1 << 20)
                if not block:
                    break
                out.write(block)
            out.flush()
            os.fsync(out.fileno())
        if util.sha256_file(partial) != util.sha256_file(path):
            raise ValueError('pool copy of %s differs' % name)
        os.rename(partial, os.path.join(dest, name))
        files[name] = os.path.getsize(os.path.join(dest, name))
    return {'dir': dest, 'verified': True, 'files': files}


# ---------------------------------------------------------------- GCS resumable session upload

def _connect(uri, timeout):
    parts = urlsplit(uri)
    kind = httplib.HTTPSConnection if parts.scheme == 'https' else httplib.HTTPConnection
    return kind(parts.netloc, timeout=timeout), parts.path + ('?' + parts.query if parts.query else '')


def _persisted(reply):
    value = reply.getheader('Range')
    if not value:
        return 0
    return int(value.split('-')[-1]) + 1


def upload_session(uri, path, chunk=UPLOAD_CHUNK, attempts=8, sleep=time.sleep, timeout=300):
    """Upload a file to a GCS resumable session URI. After a reset or a retryable status the
    session is queried and the upload reopens at the first byte GCS has not persisted.
    Returns the object metadata {size, md5Hash, generation, ...} after checking size and md5."""
    if chunk % QUANTUM:
        raise ValueError('chunk must be a multiple of 256 KiB')
    total = os.path.getsize(path)
    md5 = hashlib.md5()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            md5.update(block)
    want_md5 = base64.b64encode(md5.digest()).decode('ascii')
    offset = 0
    failures = 0
    query = False
    meta = None
    while meta is None:
        conn = None
        try:
            conn, target = _connect(uri, timeout)
            if query:
                conn.putrequest('PUT', target)
                conn.putheader('Content-Length', '0')
                conn.putheader('Content-Range', 'bytes */%d' % total)
                conn.endheaders()
                body = b''
            else:
                end = min(offset + chunk, total)
                with open(path, 'rb') as handle:
                    handle.seek(offset)
                    body = handle.read(end - offset)
                conn.putrequest('PUT', target)
                conn.putheader('Content-Length', str(len(body)))
                conn.putheader('Content-Type', 'application/octet-stream')
                conn.putheader('Content-Range', 'bytes %d-%d/%d' % (offset, end - 1, total)
                               if total else 'bytes */0')
                conn.endheaders()
                conn.send(body)
            reply = conn.getresponse()
            data = reply.read()
            if reply.status in (200, 201):
                meta = json.loads(data.decode('utf-8'))
            elif reply.status == 308:
                offset = _persisted(reply)
                query = False
            elif reply.status in RETRY_STATUS:
                raise UploadError('HTTP %d' % reply.status)
            else:
                raise UploadError('HTTP %d: %r (not retried)' % (reply.status, data[:300]))
        except (socket.error, httplib.HTTPException, UploadError) as err:
            if isinstance(err, UploadError) and 'not retried' in str(err):
                raise
            failures += 1
            if failures >= attempts:
                raise UploadError('upload failed after %d attempts: %s' % (failures, err))
            sleep(min(60, 2 ** failures))
            query = True
        finally:
            if conn is not None:
                conn.close()
    if int(meta.get('size', -1)) != total or meta.get('md5Hash', want_md5) != want_md5:
        raise UploadError('GCS size or md5 differs: %s %s' % (meta.get('size'), meta.get('md5Hash')))
    meta['resets'] = failures
    return meta


# ---------------------------------------------------------------- return

def do_return(config, job, root, state, rc=None, error=None, uploader=None, job_id=None):
    """Pack, publish and receipt. Never raises for a channel fault; the receipt records it."""
    uploader = uploader or upload_session
    token = job['token']
    local = os.path.join(root, 'ret')
    serial = 0
    while os.path.lexists(local):
        serial += 1
        local = os.path.join(root, 'ret.%d' % serial)
    os.makedirs(local)
    budgets = config.get('budgets') or {}
    max_bytes = (budgets.get('return') or {}).get('max_bytes')
    members = collect(root)
    refused = []
    try:
        archive, rows = build_archive(members, os.path.join(local, ARCHIVE), max_bytes)
    except BudgetError as err:
        refused = err.members
        error = (error + ' | ' if error else '') + str(err)
        state = 'over_budget'
        small = tails(members, os.path.join(local, 'tails'))
        archive, rows = build_archive(small, os.path.join(local, ARCHIVE),
                                      max(max_bytes or 0, tar_bound(small)))
    kit_config = os.path.join(job.get('kit', ''), 'CONFIG.json')
    receipt = {'schema': 'return-receipt-v1', 'utc': util.utc_iso(), 'token': token,
               'job_id': job_id, 'state': state, 'rc': rc, 'error': error,
               'kit_pins_sha256': config.get('kit_pins_sha256'),
               'config_sha256': util.sha256_file(kit_config)[0] if os.path.isfile(kit_config)
               else None,
               'members': rows, 'archive': archive, 'refused': refused,
               'pool': None, 'gcs': None}
    target = config.get('return') or {}
    archive_path = os.path.join(local, ARCHIVE)
    if target.get('pool'):
        try:
            receipt['pool'] = publish_pool(target['pool'], token, [archive_path],
                                           (budgets.get('pool') or {}).get('max_bytes'))
        except Exception as err:  # noqa: BLE001 -- recorded in the receipt
            receipt['pool'] = {'dir': os.path.join(target['pool'], token), 'verified': False,
                               'error': '%s: %s' % (type(err).__name__, err)}
    sessions = job.get('sessions') or {}
    if sessions.get(ARCHIVE):
        uri = '%s/%s/%s' % ((target.get('gcs_prefix') or '').rstrip('/'), token, ARCHIVE)
        try:
            meta = uploader(sessions[ARCHIVE], archive_path)
            receipt['gcs'] = {'uri': uri, 'generation': str(meta.get('generation')),
                              'verified': True, 'resets': meta.get('resets', 0)}
        except Exception as err:  # noqa: BLE001 -- recorded in the receipt
            receipt['gcs'] = {'uri': uri, 'generation': None, 'verified': False,
                              'error': '%s: %s' % (type(err).__name__, err)}
    receipt['returned'] = any(bool(channel and channel.get('verified'))
                              for channel in (receipt['pool'], receipt['gcs']))
    receipt_path = os.path.join(local, RECEIPT)
    util.write_json(receipt_path, receipt)
    if target.get('pool'):
        try:
            publish_pool(target['pool'], token, [receipt_path])
        except Exception:  # noqa: BLE001 -- the archive channel result already stands
            pass
    if sessions.get(RECEIPT):
        try:
            uploader(sessions[RECEIPT], receipt_path)
        except Exception:  # noqa: BLE001
            pass
    return receipt


# ---------------------------------------------------------------- job driver

def substitute(argv, mapping):
    out = []
    for value in argv:
        value = str(value)
        for key, replacement in mapping.items():
            value = value.replace('{%s}' % key, replacement)
        out.append(value)
    return out


def gpu_guard(expect_gpus, env):
    """None when the visible devices fit the job, else the reason."""
    visible = env.get('CUDA_VISIBLE_DEVICES')
    if expect_gpus == 0:
        return None
    count = len([part for part in (visible or '').split(',') if part.strip()])
    if count < expect_gpus:
        return 'expected %d GPUs, %d visible' % (expect_gpus, count)
    return None


def run_job(bundle, root, expect_gpus=0, uploader=None, gcs_fetch=None, grace=None):
    bundle, root = os.path.abspath(bundle), os.path.abspath(root)
    kit = os.path.join(bundle, 'kit')
    config = util.read_json(os.path.join(kit, 'CONFIG.json'))
    job = util.read_json(os.path.join(bundle, 'JOB.json'))
    job['kit'] = kit
    out, logs = os.path.join(root, 'out'), os.path.join(root, 'logs')
    for path in (out, logs):
        if not os.path.isdir(path):
            os.makedirs(path)
    flags = {'signal': None, 'at': None}
    child = []

    def interrupted(number, frame):
        flags['signal'], flags['at'] = number, time.time()
        if child and child[0].poll() is None:
            try:
                os.killpg(child[0].pid, signal.SIGTERM)
            except OSError:
                pass

    previous = dict((number, signal.signal(number, interrupted))
                    for number in (signal.SIGUSR1, signal.SIGTERM, signal.SIGINT))
    if grace is None:
        grace = max(10, int((config.get('job') or {}).get('signal_s', 120)) // 3)
    state, rc, error, phase = 'complete', None, None, 'guard'
    try:
        reason = gpu_guard(expect_gpus, os.environ)
        if reason:
            state, error = 'no_gpu', reason
        else:
            phase = 'stage'
            with open(os.path.join(logs, 'stage.log'), 'ab') as log:
                stage.run(kit, root, config, gcs_fetch=gcs_fetch, log=log,
                          gcs_env=(config.get('return') or {}).get('gcs_env'))
            phase = 'entry'
            argv = substitute(config['entry'], {'root': root, 'kit': kit, 'out': out})
            env = dict(os.environ)
            env.update(JOB_ROOT=root, JOB_OUT=out, JOB_KIT=kit, JOB_TOKEN=job['token'])
            if expect_gpus == 0:
                env['CUDA_VISIBLE_DEVICES'] = ''
            with open(os.path.join(logs, 'entry.log'), 'ab') as log:
                child.append(subprocess.Popen(argv, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                              env=env, start_new_session=True))
                while rc is None:
                    try:
                        rc = child[0].wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        if flags['at'] is not None and time.time() - flags['at'] > grace:
                            try:
                                os.killpg(child[0].pid, signal.SIGKILL)
                            except OSError:
                                pass
            if rc != 0:
                state = 'failed'
                with open(os.path.join(logs, 'entry.log'), 'rb') as handle:
                    handle.seek(max(0, os.path.getsize(handle.name) - 400))
                    error = 'entry exited %s: %s' % (rc, handle.read().decode('utf-8', 'replace')
                                                     .strip().splitlines()[-1:])
    except Exception as err:  # noqa: BLE001 -- every fault is returned, never lost
        text = traceback.format_exc()
        with open(os.path.join(logs, 'TRACEBACK.txt'), 'ab') as handle:
            handle.write(text.encode('utf-8'))
        state = 'staging_failed' if phase == 'stage' else 'failed'
        error = '%s: %s' % (type(err).__name__, err)
    if flags['signal'] is not None:
        state = 'interrupted'
        error = (error + ' | ' if error else '') + 'signal %d' % flags['signal']
    for number, handler in previous.items():
        signal.signal(number, handler)
    job_id = os.environ.get('SLURM_JOB_ID')
    receipt = do_return(config, job, root, state, rc, error, uploader,
                        int(job_id) if job_id and job_id.isdigit() else None)
    sys.stdout.write(json.dumps({'state': receipt['state'], 'returned': receipt['returned']},
                                sort_keys=True) + '\n')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')
    p_job = sub.add_parser('job')
    p_job.add_argument('--bundle', required=True)
    p_job.add_argument('--root', required=True)
    p_job.add_argument('--expect-gpus', type=int, default=0)
    args = parser.parse_args(argv)
    if args.command != 'job':
        parser.print_help()
        return 2
    receipt = run_job(args.bundle, args.root, args.expect_gpus)
    return 0 if receipt['state'] == 'complete' and receipt['returned'] else 1


if __name__ == '__main__':
    sys.exit(main())
