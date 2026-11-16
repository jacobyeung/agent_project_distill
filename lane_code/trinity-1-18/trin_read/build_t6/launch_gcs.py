#!/usr/bin/env python3
"""Governed four-part GCS pull. Usage: launch_gcs.py LANE DONE_FILE OUT; PRIO from env. Never retries."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from done_record import parse_done

GCLOUD = '/home/jjyeung/google-cloud-sdk/bin/gcloud'
GOVERNOR = Path('/scratch/jjyeung/io_governor')
STREAMS = Path('/data3/jjyeung/orch_n13_20261026/io_governor/streams')


def launch(lane, done_file, output, gcloud=GCLOUD, governor=GOVERNOR, streams=STREAMS,
           identity_fn=None, ratelimit_comm=None):
    """Dependency arguments permit CPU fixtures; CLI always uses the governed production paths."""
    if not re.fullmatch('[A-Za-z0-9_-]+', lane): raise ValueError('Invalid lane')
    done = parse_done(done_file)
    out = Path(output).absolute(); part = out.with_name(out.name+'.part')
    receipt_path = out.with_name(out.name+'.RECEIPT.json')
    if out.resolve() != out or not str(out).startswith('/scratch/'):
        raise ValueError('Require a local /scratch output without symlinks')
    if out.exists() or part.exists() or receipt_path.exists(): raise ValueError('Output exists; no overwrite or retry')
    if identity_fn is None:
        sys.path.insert(0, str(governor))
        from signal_helper import identity, COMM
        identity_fn, ratelimit_comm = identity, COMM['ratelimit']
    objects = ['gs://cmu-gpucloud-jjyeung/'+done['object']+'.part%02d-of-04'%i for i in range(4)]
    # The reader root stays bash for the governor's identity checks. Never exec it.
    reader = ['bash', '-c', 'kill -STOP $$; timeout 14400 "$@"; exit $?',
              'gcs-reader', str(gcloud), 'storage', 'cat']+objects
    rate = ['/usr/bin/python3', '-s', str(governor/'ratelimit.py'), '-q', '-L', '1000', '-B', '65536']
    with part.open('xb') as sink, open('/dev/null', 'rb') as source:
        src = subprocess.Popen(reader, stdin=source, stdout=subprocess.PIPE)
        rl = subprocess.Popen(rate, stdin=src.stdout, stdout=sink)
    src.stdout.close()
    for _ in range(1000):
        if identity_fn(src.pid)['state'] == 'T' and identity_fn(rl.pid)['comm'] == ratelimit_comm: break
        time.sleep(.01)
    else:
        raise RuntimeError('reader did not reach gate or ratelimit did not start; inspect, do not retry')
    register = ['/usr/bin/python3', '-s', str(governor/'register.py'), '--lane', lane, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(done['bytes']),
                '--tier', '3', '--kind', 'pull', '--io-weight', '1', '--nominal-mbps', '8',
                '--allow-resume', '--priority', os.environ.get('PRIO', '50')]
    subprocess.run(register, check=True)
    print('registered', lane, 'reader', src.pid, 'ratelimit', rl.pid, 'bytes', done['bytes'], flush=True)
    src.wait(); rl.wait()
    if src.returncode or rl.returncode:
        raise RuntimeError('stream failed: reader=%d ratelimit=%d; no restart'%(src.returncode, rl.returncode))
    digest = hashlib.sha256(); size = 0
    with part.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk); size += len(chunk)
    rec = streams/(lane+'.json')
    if rec.exists(): rec.rename(streams/('%s.done.%d'%(lane, int(time.time()))))
    receipt = dict(lane=lane, out=str(out), bytes=size, sha256=digest.hexdigest(), expected_bytes=done['bytes'],
                   expected_sha256=done['sha256'], done=done, done_file=str(done_file),
                   done_sha256=hashlib.sha256(Path(done_file).read_bytes()).hexdigest(),
                   reader_argv=reader, ratelimit_argv=rate, register_argv=register,
                   utc=time.strftime('%FT%TZ', time.gmtime()))
    receipt['verified'] = size == done['bytes'] and digest.hexdigest() == done['sha256']
    with receipt_path.open('x') as stream: json.dump(receipt, stream, indent=2)
    if not receipt['verified']: raise ValueError('verify failed; retain .part; no retry')
    if out.exists(): raise ValueError('Output appeared during transfer; retain .part')
    part.rename(out)
    print('complete', out, size, digest.hexdigest(), flush=True)
    return receipt


def main():
    if len(sys.argv) != 4: raise ValueError(__doc__)
    launch(*sys.argv[1:])


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print('REFUSED: '+str(error), file=sys.stderr); sys.exit(2)
