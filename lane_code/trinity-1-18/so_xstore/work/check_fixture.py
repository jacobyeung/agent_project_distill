from pathlib import Path
import json
import os
import subprocess
import sys

L = Path(__file__).resolve().parent.parent
results = []
for name in ('a', 'b'):
    temporary = L / 'work/tmp' / ('cold_final_' + name)
    temporary.mkdir(exist_ok=True)
    output = L / 'out/evidence' / ('cold_final_' + name)
    env = {**os.environ, 'TK_XSTORE_EXPERIMENT': '1', 'HOSTNAME': 'cold-node-' + name, 'TMPDIR': str(temporary)}
    command = [sys.executable, '-I', '-s', '-B', str(L / 'work/fixture_cold.py'), str(output)]
    p = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    (L / 'out/tests' / ('cold_final_' + name + '.txt')).write_text(p.stdout)
    results.append(json.loads(p.stdout))
assert results[0]['key'] == results[1]['key']
command = [sys.executable, '-I', '-s', '-B', str(L / 'work/tree/scripts/compare_preparation_stores.py'),
           '--left', results[0]['store'], '--left-root', results[0]['root_digest'],
           '--right', results[1]['store'], '--right-root', results[1]['root_digest'], '--key', results[0]['key']]
p = subprocess.run(command, env={**os.environ, 'TK_XSTORE_EXPERIMENT': '1'}, text=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
(L / 'out/tests/cold_compare.txt').write_text(p.stdout)
(L / 'out/evidence/cold_fixture.json').write_text(json.dumps(dict(
    scope='protocol fixture only; no native preparation or two-node execution', results=results,
    compare_command=command, compare_stdout=p.stdout), indent=2) + '\n')
print(p.stdout, end='')
