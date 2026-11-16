import argparse
import base64
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time


SCHEMA = 'evalx-stdout-transfer-v1'
BEGIN = b'EVALX_TRANSFER_BEGIN '
DATA = b'EVALX_TRANSFER_DATA '
END = b'EVALX_TRANSFER_END '
LIMIT = 900000000
MAX_RATE = 8000000
LINE_LIMIT = 128*1024
LOG_LIMIT = 8*1024**2
CHUNK = 64*1024


def digest_string(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('Invalid transfer digest')
    return value


def validate(header, plan):
    if (set(header) != {'schema', 'plan_sha256', 'sha256', 'bytes', 'outcome'}
            or header['schema'] != SCHEMA or header['plan_sha256'] != digest_string(plan)
            or type(header['bytes']) is not int or not 0 < header['bytes'] <= LIMIT
            or header['outcome'] not in ('complete', 'failed')):
        raise ValueError('Invalid transfer header, plan or size')
    digest_string(header['sha256'])


def emit(source, output, plan, outcome, rate=MAX_RATE):
    source = Path(source)
    digest_string(plan)
    if type(rate) is not int or not 0 < rate <= MAX_RATE:
        raise ValueError('Transfer rate exceeds the allowed limit')
    if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode):
        raise ValueError('Only a regular result archive can be sent')
    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= LIMIT:
            raise ValueError('Result archive exceeds the transfer limit')
        hashed = hashlib.sha256()
        for raw in iter(lambda: stream.read(1024**2), b''):
            hashed.update(raw)
        header = dict(schema=SCHEMA, plan_sha256=plan, sha256=hashed.hexdigest(),
                      bytes=before.st_size, outcome=outcome)
        validate(header, plan)
        started = time.monotonic()
        written = 0

        def send(raw):
            nonlocal written
            written += len(raw)
            delay = written/rate-(time.monotonic()-started)
            if delay > 0:
                time.sleep(delay)
            output.write(raw)
            output.flush()

        send(BEGIN+json.dumps(header, sort_keys=True, separators=(',', ':')).encode()+b'\n')
        stream.seek(0)
        for raw in iter(lambda: stream.read(CHUNK), b''):
            send(DATA+base64.b64encode(raw)+b'\n')
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('Result archive changed during transfer')
        send(END+header['sha256'].encode()+b'\n')
    return header


def receive(source, destination, plan, log):
    digest_string(plan)
    destination = Path(destination)
    parent = destination.parent.resolve()
    if not parent.is_dir() or parent.parts[1:2] == ('home',) or (
            len(parent.parts) > 1 and parent.parts[1].startswith('data')):
        raise ValueError('Return artifacts require an existing node-local directory')
    partial = Path(str(destination)+'.partial')
    receipt = Path(str(destination)+'.receipt.json')
    for path in (destination, partial, receipt):
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
    header = None
    stream = None
    ended = False
    received = logged = 0
    hashed = hashlib.sha256()
    with ExitStack() as stack:
        while True:
            line = source.readline(LINE_LIMIT+1)
            if not line:
                break
            if len(line) > LINE_LIMIT:
                raise ValueError('Transfer line exceeds the bounded line limit')
            protocol = line.startswith((BEGIN, DATA, END))
            if protocol and (ended or not line.endswith(b'\n')):
                raise ValueError('Duplicate or truncated transfer record')
            if line.startswith(BEGIN):
                if header is not None:
                    raise ValueError('Duplicate transfer header')
                header = json.loads(line[len(BEGIN):])
                if not isinstance(header, dict):
                    raise ValueError('Invalid transfer header')
                validate(header, plan)
                stream = stack.enter_context(partial.open('xb'))
            elif line.startswith(DATA):
                if stream is None:
                    raise ValueError('Payload precedes its transfer header')
                raw = base64.b64decode(line[len(DATA):-1], validate=True)
                if not raw or len(raw) > CHUNK or received+len(raw) > header['bytes']:
                    raise ValueError('Transfer payload exceeds its declared size')
                stream.write(raw)
                hashed.update(raw)
                received += len(raw)
            elif line.startswith(END):
                if (header is None or received != header['bytes']
                        or hashed.hexdigest() != header['sha256']
                        or line[len(END):-1].decode('ascii') != header['sha256']):
                    raise ValueError('Transfer size or digest differs')
                stream.flush()
                os.fsync(stream.fileno())
                ended = True
            else:
                logged += len(line)
                if logged > LOG_LIMIT:
                    raise ValueError('Unframed transfer log exceeds its limit')
                log.write(line)
                log.flush()
        if not ended:
            raise ValueError('Transfer is incomplete; no final archive is published')
    os.link(partial, destination, follow_symlinks=False)
    value = dict(schema=SCHEMA, path=str(destination.resolve()), bytes=received,
                 sha256=header['sha256'], plan_sha256=plan, sender_outcome=header['outcome'],
                 transport_verified=True, experiment_integrity_checked=False,
                 partial_retained=True)
    with receipt.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    return value


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    emit_parser = sub.add_parser('emit')
    emit_parser.add_argument('--source', required=True)
    emit_parser.add_argument('--plan', required=True)
    emit_parser.add_argument('--outcome', choices=('complete', 'failed'), required=True)
    emit_parser.add_argument('--rate', type=int, default=MAX_RATE)
    receive_parser = sub.add_parser('receive')
    receive_parser.add_argument('--destination', required=True)
    receive_parser.add_argument('--plan', required=True)
    args = parser.parse_args()
    if args.command == 'emit':
        emit(args.source, sys.stdout.buffer, args.plan, args.outcome, args.rate)
    else:
        with Path(args.destination+'.stream.log').open('xb') as log:
            value = receive(sys.stdin.buffer, args.destination, args.plan, log)
        print(json.dumps(value, sort_keys=True), file=sys.stderr)


if __name__ == '__main__':
    main()
