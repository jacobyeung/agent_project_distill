#!/usr/bin/python3
"""Local-only transport and command recorder; never opens a network connection."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

name = Path(sys.argv[1]).name
args = sys.argv[2:]
root = Path(os.environ['TEST_ROOT'])
if name in ('git', 'ssh', 'sleep') or (name == 'bash' and args and args[0].endswith('/tssh.sh')):
    with (root / 'commands.jsonl').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps([name, args], separators=(',', ':')) + '\n')

if name == 'hostname':
    print(os.environ.get('FAKE_HOST', 'trinity-3-30'))
    sys.exit(int(os.environ.get('FAKE_HOSTNAME_RC', '0')))
elif name == 'date' and os.environ.get('FAKE_DATE'):
    now = datetime.datetime.strptime(os.environ['FAKE_DATE'], '%Y-%m-%dT%H:%M:%SZ')
    print(now.strftime(args[-1][1:]))
elif name == 'sleep':
    sys.exit(int(os.environ.get('FAKE_SLEEP_RC', '0')))
elif name == 'ssh':
    pos = 0
    while args[pos] == '-o':
        pos += 2
    host = args[pos]
    command = args[pos + 1:]
    if host.endswith('.ib'):
        if len(command) != 1 or str(root) not in command[0]:
            raise ValueError('receiver escaped test root')
        os.execv('/bin/bash', ['bash', '-c', command[0]])
    modes = json.loads(os.environ.get('FAKE_REMOTE_MODES', '{}'))
    script = sys.stdin.buffer.read()
    (root / ('ssh-program-' + host)).write_bytes(script)
    mode = modes.get(host, 'ok')
    if mode == 'missing':
        print('SKIP %s no orch_n30/source' % host)
        sys.exit(66)
    if mode == 'silent':
        sys.exit(255)
    if mode == 'badpipe':
        print('PIPE 1 0 0')
        sys.exit(4)
    source = str(root / 'lanes').encode()
    remote = str(root / 'remote' / host).encode()
    script = script.replace(b'cd ' + source + b' ', b'cd ' + remote + b' ', 1)
    proc = subprocess.run(['/bin/bash', '-s'], input=script)
    sys.exit(proc.returncode)
elif name == 'git':
    # The test harness also restricts Git transports to local filesystem paths.
    repo = Path(args[1]).resolve() if args[:1] == ['-C'] else Path.cwd().resolve()
    repo.relative_to(Path(os.environ['TEST_SUITE_ROOT']).resolve())
    os.execv('/usr/bin/git', ['git'] + args)
elif name == 'bash':
    os.execv('/bin/bash', ['bash'] + args)
elif name == 'date':
    os.execv('/bin/date', ['date'] + args)
else:
    raise ValueError('unexpected fake command: ' + name)
