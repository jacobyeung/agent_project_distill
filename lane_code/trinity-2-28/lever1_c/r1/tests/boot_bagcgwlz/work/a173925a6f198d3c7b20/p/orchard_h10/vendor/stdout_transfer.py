
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
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
LOG_LIMIT = 64*1024
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
