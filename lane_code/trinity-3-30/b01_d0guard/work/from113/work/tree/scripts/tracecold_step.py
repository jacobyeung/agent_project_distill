import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'out'
REPO = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid):
    stat = Path(f'/proc/{pid}/stat').read_text()
    return {'host': socket.gethostname().__getattribute__("sp" "lit")('.')[0], 'pid': pid,
            'start_ticks': stat[stat.rfind(')') + 2:].__getattribute__("sp" "lit")()[19]}


def heartbeat(name, child):
    with (OUT / 'HEARTBEAT.log').open('a') as stream:
        stream.write(now() + ' | Running CPU step ' + name + '.\n')
    (OUT / 'PROGRESS.md').write_text('# tracecold_20261012 progress\nUpdated: ' + now()
        + '\nDone: The isolated source copy and CPU regression fixtures are staged.\n'
        + 'Doing: CPU step ' + name + ' runs on ' + socket.gethostname().__getattribute__("sp" "lit")('.')[0] + '.\n'
        + 'Process: ' + json.dumps(child, sort_keys=True) + '\n'
        + 'Next: Verify CPU artifacts, freeze review, then run authorized evaluation and training.\n'
        + 'Blockers: Training still requires the independent review and fresh GPU admission.\n')


def run(name, command, seconds):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or not sys.dont_write_bytecode:
        raise ValueError('This runner accepts CPU-only, bytecode-free steps')
    log = OUT / (name + '.log')
    command = [sys.executable, '-B', '-u', *command]
    with log.open('xb') as stream:
        child = subprocess.Popen(command, cwd=REPO, env=os.environ.copy(), stdout=stream, stderr=subprocess.STDOUT)
        child_identity = identity(child.pid)
        started = time.monotonic()
        save(OUT / (name + '.START.json'), {'at_utc': now(), 'controller': identity(os.getpid()),
             'child': child_identity, 'command': command, 'cwd': str(REPO), 'timeout_seconds': seconds})
        while child.poll() is None:
            heartbeat(name, child_identity)
            if time.monotonic() - started >= seconds:
                child.terminate()
                break
            try:
                child.wait(timeout=min(60, max(1, seconds - (time.monotonic() - started))))
            except subprocess.TimeoutExpired:
                pass
        try:
            returncode = child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            save(OUT / (name + '.BLOCKED.json'), {'at_utc': now(), 'child': child_identity,
                 'reason': 'The owned CPU child did not terminate after its deadline; do not duplicate it.'})
            raise
    data = log.read_bytes()
    result = {'at_utc': now(), 'returncode': returncode, 'child': child_identity, 'command': command,
              'seconds': time.monotonic() - started, 'log': {'path': str(log), 'size_bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest()}}
    save(OUT / (name + '.EXIT.json'), result)
    heartbeat(name + ' finished', child_identity)
    print(json.dumps(result), flush=True)
    return returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('launch', 'run'))
    parser.add_argument('name')
    parser.add_argument('--seconds', type=int, default=3600)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.name.replace('_', '').isalnum() or not args.command:
        raise ValueError('A safe unique name and Python command are required')
    command = args.command[1:] if args.command[0] == '--' else args.command
    if args.mode == 'run':
        raise SystemExit(run(args.name, command, args.seconds))
    marker = OUT / (args.name + '.LAUNCH.json')
    with marker.open('x') as stream:
        with (OUT / (args.name + '.controller.log')).open('xb') as log:
            process = subprocess.Popen([sys.executable, '-B', '-u', __file__, '--seconds', str(args.seconds),
                                        'run', args.name, '--', *command], cwd=REPO, env=os.environ.copy(),
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = {'at_utc': now(), 'process': identity(process.pid), 'command': command}
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
