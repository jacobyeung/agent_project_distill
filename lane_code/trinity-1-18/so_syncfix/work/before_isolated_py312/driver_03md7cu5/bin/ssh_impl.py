import json, os, shlex, signal, subprocess, sys, time
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['FAKE_SSH_LOG'], 'a') as f: f.write(json.dumps(args) + '\n')
while args and args[0] == '-o': args = args[2:]
host, command = args[0], ' '.join(args[1:])
root = Path(os.environ['FAKE_ROOT'])
if host == 'trinity-3-30.ib':
    if os.environ.get('FAKE_RECEIVER_HANG') == '1':
        signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(5)
    rc = subprocess.call(['bash', '-c', command])
    if os.environ.get('FAKE_STAGE_FIFO') == '1' and os.environ.get('FAKE_ACTIVE_HOST') == 'trinity-1-18':
        import tarfile
        writer = shlex.split(command)[-1]
        if writer.startswith('cat > '):
            archive = shlex.split(writer)[-1]
            with tarfile.open(archive, 'a') as stream:
                member = tarfile.TarInfo('aaa_raced.json')
                member.type = tarfile.FIFOTYPE
                stream.addfile(member)
        else:
            dest = shlex.split(command)[-1]
            os.mkfifo(str(Path(dest) / 'aaa_raced.json'))
    sys.exit(rc)
mode = os.environ.get('FAKE_' + host.replace('-', '_'), 'success')
if mode == 'unreachable':
    assert 'ConnectTimeout=20' in sys.argv
    time.sleep(0.10)
    print('ssh: connect to host ' + host + ': Connection timed out', flush=True)
    sys.exit(255)
if mode.startswith('held'):
    (root / 'ssh.pid').write_text(str(os.getpid()))
    code = ('import os,time; os.setsid(); '
            'open(' + repr(str(root / 'holder.pid')) + ', "w").write(str(os.getpid())); '
            'time.sleep(' + ('1.2' if mode == 'held_exit' else '4') + ')')
    subprocess.Popen([sys.executable, '-I', '-s', '-B', '-c', code],
                     stdin=subprocess.DEVNULL, close_fds=False)
    print('held stdout fixture', flush=True)
    if mode == 'held_exit': sys.exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(5)
    sys.exit(99)
script = sys.stdin.read()
source = str(root / 'sources' / host)
if mode == 'missing': source += '_absent'
script = script.replace(shlex.quote(os.environ['LCS_LANES_ROOT']), shlex.quote(source), 1)
if mode == 'scanner_hang':
    script = script.replace('python3 - ', 'python3 -c "import time; time.sleep(5)" ', 1)
result = subprocess.run(['bash', '-c', command], input=script.encode(),
                        env=dict(os.environ, FAKE_ACTIVE_HOST=host))
sys.exit(23 if mode == 'partial' else result.returncode)
