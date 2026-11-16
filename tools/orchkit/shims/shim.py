#!/usr/bin/python3 -I
"""Transport shim for a dry run: serves pinned objects from local files and logs every call.

dryrun.py copies this file once per command name (gcloud, gsutil, sbatch, squeue, sacct, scontrol,
nvidia-smi, ssh, curl) into OUTDIR/shims/ and bakes in the plan path below, so the shim needs no
environment variable a kit could scrub. The command is chosen by the name it was invoked as.

A call is served only when the plan has a fixture for it: an exact-argv fixture, a pinned object
(URI and generation honoured), or an upload under an allowed prefix. Any other call is logged with
planned=false and exits 97, and the dry run fails with fail_reason unplanned_call.

Standard library only; Python 3.6-safe.
"""
import json
import os
import re
import shutil
import sys
import time

PLAN_PATH = ''  # baked by dryrun.py
ORCHKIT_DIR = ''  # baked by dryrun.py
UNPLANNED_RC = 97

GCS_HTTP = (
    re.compile(r'^https?://storage\.googleapis\.com/download/storage/v1/b/([^/]+)/o/([^?]+)\?(.*)$'),
    re.compile(r'^https?://storage\.googleapis\.com/([^/?]+)/([^?]+)(?:\?(.*))?$'),
    re.compile(r'^https?://([^./]+)\.storage\.googleapis\.com/([^?]+)(?:\?(.*))?$'),
)


class Unplanned(Exception):
    pass


def load_plan():
    with open(PLAN_PATH, 'rb') as handle:
        return json.loads(handle.read().decode('utf-8'))


def log(plan, row):
    sys.path.insert(0, os.path.dirname(ORCHKIT_DIR))
    from orchkit import util
    row['utc'] = util.utc_iso()
    row['argv'] = [a if len(a) <= 300 else a[:300] + '...' for a in row['argv']][:40]
    util.append_jsonl_locked(plan['log'], row, max_bytes=16384)


def split_uri(uri):
    """gs://b/o#gen -> ('gs://b/o', 'gen' or None)."""
    if '#' in uri:
        base, gen = uri.rsplit('#', 1)
        return base, gen
    return uri, None


def lookup(plan, uri, generation=None):
    base, gen = split_uri(uri)
    gen = gen if gen is not None else generation
    row = plan.get('objects', {}).get(base)
    if row is None:
        raise Unplanned('no pinned object for ' + base)
    if gen is not None and row.get('generation') is not None and str(gen) != str(row['generation']):
        raise Unplanned('generation %s requested, pinned %s' % (gen, row['generation']))
    return base, row


def upload_ok(plan, uri):
    return any(uri.startswith(p) for p in plan.get('uploads', []))


def store_upload(plan, src, uri):
    name = re.sub(r'[^A-Za-z0-9._-]', '_', uri[len('gs://'):])
    dest = os.path.join(plan['upload_dir'], '%d_%s' % (int(time.time() * 1e6), name))
    if src == '-':
        with open(dest, 'wb') as out:
            shutil.copyfileobj(sys.stdin.buffer, out)
    else:
        shutil.copyfile(src, dest)
    return dest


def emit(path, dest):
    if dest is None or dest == '-':
        with open(path, 'rb') as handle:
            shutil.copyfileobj(handle, sys.stdout.buffer)
        sys.stdout.buffer.flush()
    else:
        if os.path.isdir(dest):
            raise Unplanned('copy into a directory is not planned: ' + dest)
        shutil.copyfile(path, dest)


def strip_opts(args, with_value, flags):
    """Drop leading global options; return the rest. Unknown option -> Unplanned."""
    out = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in with_value:
            i += 2
            continue
        if a in flags or any(a.startswith(v + '=') for v in with_value if v.startswith('--')):
            i += 1
            continue
        if a.startswith('-') and a != '-':
            raise Unplanned('option not planned: ' + a)
        out.append(a)
        i += 1
    return out


def gsutil(plan, args, row):
    args = list(args)
    while args and args[0] in ('-m', '-q', '-o', '-h', '-u'):
        args = args[2:] if args[0] in ('-o', '-h', '-u') else args[1:]
    if not args:
        raise Unplanned('no subcommand')
    sub, rest = args[0], args[1:]
    rest = strip_opts(rest, ('-h',), ('-n', '-v', '-q', '-c', '-L', '-l', '-e'))
    return gcs_op(plan, sub, rest, row)


def gcloud(plan, args, row):
    args = strip_opts(list(args), ('--billing-project', '--project', '--verbosity', '--format',
                                   '--configuration', '--account'),
                      ('--quiet', '-q', '--no-user-output-enabled', '--log-http', '--no-clobber',
                       '--recursive', '--long', '-l'))
    if '--recursive' in args:
        raise Unplanned('recursive copy is not planned')
    if len(args) >= 2 and args[0] == 'storage':
        sub = args[1]
        if sub == 'objects' and len(args) >= 4 and args[2] == 'describe':
            return gcs_op(plan, 'describe', args[3:], row)
        return gcs_op(plan, sub, args[2:], row)
    raise Unplanned('gcloud command not planned')


def gcs_op(plan, sub, rest, row):
    if sub == 'cat' and len(rest) == 1:
        base, obj = lookup(plan, rest[0])
        row.update(uri=base, served=obj['path'], standin=bool(obj.get('standin')))
        emit(obj['path'], None)
        return 0
    if sub == 'cp' and len(rest) == 2:
        src, dst = rest
        if src.startswith('gs://') and not dst.startswith('gs://'):
            base, obj = lookup(plan, src)
            row.update(uri=base, served=obj['path'], standin=bool(obj.get('standin')))
            emit(obj['path'], dst)
            return 0
        if dst.startswith('gs://') and not src.startswith('gs://'):
            if not upload_ok(plan, dst):
                raise Unplanned('upload outside the allowed prefixes: ' + dst)
            row.update(uri=dst, uploaded=store_upload(plan, src, dst))
            return 0
        raise Unplanned('copy form not planned')
    if sub in ('stat', 'describe') and len(rest) == 1:
        base, obj = lookup(plan, rest[0])
        size = os.path.getsize(obj['path'])
        row.update(uri=base, served=obj['path'], standin=bool(obj.get('standin')))
        if sub == 'describe':
            bucket, name = base[len('gs://'):].split('/', 1)
            sys.stdout.write(json.dumps({'bucket': bucket, 'name': name, 'size': str(size),
                                         'generation': obj.get('generation')}) + '\n')
        else:
            sys.stdout.write('%s:\n    Content-Length:         %d\n    Generation:             %s\n'
                             % (base, size, obj.get('generation')))
        return 0
    if sub == 'ls' and len(rest) == 1:
        prefix = split_uri(rest[0])[0]
        hits = sorted(u for u in plan.get('objects', {}) if u == prefix or u.startswith(prefix.rstrip('/') + '/'))
        if not hits:
            raise Unplanned('no pinned object under ' + prefix)
        row.update(uri=prefix, listed=len(hits))
        sys.stdout.write(''.join(h + '\n' for h in hits))
        return 0
    raise Unplanned('storage operation not planned: ' + sub)


def curl(plan, args, row):
    out, url = None, None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('-o', '--output'):
            out = args[i + 1]
            i += 2
            continue
        if a in ('-H', '--header', '--limit-rate', '--retry', '--connect-timeout', '--max-time'):
            i += 2
            continue
        if re.match(r'^-[LsSfk]+$', a) or a in ('--fail', '--silent', '--location', '--show-error'):
            i += 1
            continue
        if a.startswith('-'):
            raise Unplanned('curl option not planned: ' + a)
        if url is not None:
            raise Unplanned('two URLs')
        url = a
        i += 1
    if url is None:
        raise Unplanned('no URL')
    for pattern in GCS_HTTP:
        m = pattern.match(url)
        if m:
            bucket, name, query = m.group(1), m.group(2), m.group(3) or ''
            gen = None
            q = re.search(r'(?:^|&)generation=([0-9]+)', query)
            if q:
                gen = q.group(1)
            try:
                from urllib.parse import unquote
            except ImportError:
                from urllib import unquote
            base, obj = lookup(plan, 'gs://%s/%s' % (bucket, unquote(name)), gen)
            row.update(uri=base, served=obj['path'], standin=bool(obj.get('standin')))
            emit(obj['path'], out)
            return 0
    raise Unplanned('URL is not a pinned storage object')


HANDLERS = {'gsutil': gsutil, 'gcloud': gcloud, 'curl': curl}


def main(argv):
    name = os.path.basename(argv[0])
    plan = load_plan()
    row = {'cmd': name, 'argv': [name] + list(argv[1:]), 'planned': False, 'rc': UNPLANNED_RC}
    try:
        for fixture in plan.get('calls', []):
            if fixture['argv'] == [name] + list(argv[1:]):
                sys.stdout.write(fixture.get('stdout', ''))
                sys.stderr.write(fixture.get('stderr', ''))
                row.update(planned=True, rc=int(fixture.get('rc', 0)), fixture=True)
                return row['rc']
        handler = HANDLERS.get(name)
        if handler is None:
            raise Unplanned('no fixture for this command')
        rc = handler(plan, list(argv[1:]), row)
        row.update(planned=True, rc=rc)
        return rc
    except Unplanned as err:
        row['reason'] = str(err)
        sys.stderr.write('dry-run shim: unplanned call (%s): %s\n' % (name, err))
        return UNPLANNED_RC
    finally:
        log(plan, row)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
