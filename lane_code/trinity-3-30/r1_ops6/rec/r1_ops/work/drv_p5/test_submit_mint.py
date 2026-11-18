"""Exercise wrapper idempotency and export absence checks with local stubs."""
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import urllib.error
from packet_config import MEMBERS, PINS, fixture

W = Path(__file__).resolve().parent
T = Path(tempfile.mkdtemp(prefix='submit_p5_', dir=W))
mock = T/'bin'
mock.mkdir()
commands = {
    'squeue': '[[ "$TZ" == UTC ]] || exit 9\n[[ "$QUEUE_ERROR" == 0 ]] || exit 8\nif [[ " $* " == *" -p advanced "* ]]; then printf "%s" "$QUEUED"; fi',
    'sacct': 'printf "%s" "$HISTORY"',
    'bash': '[[ "$1" == s.sh ]] || exit 8\nprintf "%s\\n" "$PROOF_JOB" >> "$CALLED"',
}
for name, body in commands.items():
    p = mock/name
    p.write_text('#!/bin/bash\n'+body+'\n')
    p.chmod(0o700)
root = T/'remote'
root.mkdir()
b, k = root/'i_69d2930d', root/'x_69d2930d'
b.mkdir()
k.mkdir()
for name in MEMBERS:
    p = b/name
    p.parent.mkdir(parents=True, exist_ok=True)
    os.link(fixture()/name, p)
(b/'p.tar').write_bytes(__import__('packet_config').ARCHIVE)
(k/'SHA256SUMS.txt').write_text('LOCAL TEST MANIFEST\n')
body = (W/'go_submit_9dd2fbb7.sh').read_text().replace('/project/community/jjyeung/okh7', str(root))
script = T/'submit.sh'
script.write_text(body)
called = T/'called'
env = dict(os.environ, PATH=str(mock)+':'+str(Path(sys.executable).parent)+':/usr/bin:/bin',
           USER='localtest', QUEUE_ERROR='0', QUEUED='', HISTORY='', CALLED=str(called))
def run(args, okay, **changes):
    result = subprocess.run(['/bin/bash', str(script)]+args, env=dict(env, **changes), capture_output=True, text=True)
    assert (result.returncode == 0) == okay, result.stdout+result.stderr
    return result
args = ['170999', 'a'*64]
run(args, True)
raw = (b/'go.json').read_bytes()
assert (b/'go.json').stat().st_mode & 0o777 == 0o600
assert 'byte-equal' in run(args, True).stdout
assert (b/'go.json').read_bytes() == raw
assert called.read_text().splitlines() == ['170999', '170999']
run(['170999', 'b'*64], False)
run(['not-a-job', 'a'*64], False)
run(['170999', 'not-a-sha'], False)
run(args, False, QUEUED='180000|PENDING')
run(args, False, HISTORY='180000|COMPLETED')
run(args, False, QUEUE_ERROR='1')
assert called.read_text().splitlines() == ['170999', '170999']
assert (b/'go.json').read_bytes() == raw
print('PASS training wrapper: exact member pins; two arguments; byte-equal GO reuse; changed GO, invalid arguments, queue/history and queue errors refused')
assert '-p advanced' in MEMBERS['s.sh'].decode() and '--gres=gpu:4' in MEMBERS['s.sh'].decode()
cfg = json.loads(MEMBERS['config.json'])
assert cfg['h1']['stop_after_step'] == 200
assert all(m in MEMBERS['jb.sh'].decode() for m in ('m100', 'm200', 'mstop', 'mstopB', 'mstopC'))
print('PASS sealed training behavior: advanced; 4 GPUs; stop_after_step=200; five export slots')

spec = importlib.util.spec_from_file_location('mint_fresh', W/'mint_fresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for label in ('absent', 'exists', 'auth_error', 'fallback_exists'):
    calls = []
    minted = []
    def install(helper):
        helper.BUCKET = 'local-test'
        helper.token = lambda: 'LOCAL_FAKE_TOKEN'
        helper.mint = lambda *a: minted.append(a)
    fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=install))
    def request(req, timeout):
        calls.append(req.full_url)
        if '/o?' in req.full_url:
            if label == 'auth_error':
                raise urllib.error.HTTPError(req.full_url, 403, 'refused', {}, None)
            return io.BytesIO(b'{"items":[{"name":"occupied"}]}' if label == 'fallback_exists' else b'{}')
        if label == 'absent':
            raise urllib.error.HTTPError(req.full_url, 404, 'absent', {}, None)
        if label == 'auth_error':
            raise urllib.error.HTTPError(req.full_url, 403, 'refused', {}, None)
        return SimpleNamespaceContext()
    class SimpleNamespaceContext:
        def __enter__(self): return self
        def __exit__(self, *args): return False
    argv = ['mint_fresh.py', str(T/(label+'.json')), '8865619b', '673bc60f', 'm100', 'm200', 'mstop', 'mstopB', 'mstopC']
    with patch.object(sys, 'argv', argv), patch.object(module.importlib.util, 'spec_from_file_location', return_value=fake_spec), patch.object(module.importlib.util, 'module_from_spec', return_value=SimpleNamespace()), patch.object(module.urllib.request, 'urlopen', side_effect=request):
        try:
            module.main()
        except SystemExit:
            assert label != 'absent'
        else:
            assert label == 'absent'
    assert len(minted) == (1 if label == 'absent' else 0)
    assert len(calls) == (21 if label == 'absent' else 2 if label == 'exists' else 1)
    print('PASS mint export check', label)
print('No Slurm, GCS, or real session calls occurred')
