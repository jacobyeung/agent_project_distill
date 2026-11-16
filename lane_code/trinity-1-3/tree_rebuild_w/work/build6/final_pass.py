"""Freeze and qualify the final snapshot with sequential bounded proofs."""
import json
import subprocess
import sys
from pathlib import Path

L = Path(__file__).resolve().parents[2]
B = L / 'work/build6'
steps = [('restage', 'restage_kits.py'), ('kit_readcheck', 'kit_readcheck.py'),
         ('kit_protocols', 'protocol_check.py'), ('packet', 'PACKET_TEST.sh'),
         ('qualification', 'qualify.py'), ('coverage', 'coverage_all.py'),
         ('comparison', 'compare.py')]
record = []
for name, script in steps:
    with (B / 'STATUS.md').open('a') as stream:
        stream.write('\nFinal snapshot step running: `' + name + '`. Log: `work/build6/final_' + name + '.log`.\n')
    command = (['bash', str(B / script)] if script.endswith('.sh') else
               [sys.executable, '-I', '-s', '-B', str(B / script)])
    with (B / ('final_' + name + '.log')).open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    record.append(dict(step=name, returncode=result.returncode,
                       log='work/build6/final_' + name + '.log'))
    (B / 'FINAL_PASS.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode < 0:
        raise RuntimeError('Final snapshot process was killed; stop without retry')
    if result.returncode:
        raise RuntimeError(name + ' failed; inspect its log')
    with (B / 'STATUS.md').open('a') as stream:
        stream.write('\nFinal snapshot step complete: `' + name + '` (`work/build6/FINAL_PASS.json`).\n')
    print(name + ' complete', flush=True)
