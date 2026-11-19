"""Show that the native parity harness rejects a one-frame fixture."""
from pathlib import Path
import json, os, subprocess, sys

L = Path(__file__).resolve().parents[1]
source = L/'work/fixture_modules/modep_native_fixture.py'
old = "frame_pins.append(dict(file_pin(path),path='/data2/'+path.name))"
text = source.read_text()
assert text.count(old) == 1
variant = source.with_name('modep_native_fixture_degenerate.py')
variant.write_text(text.replace(old, 'frame_pins.append(fp)'))
env = {**os.environ, 'MODEP_TREE': str(L/'work/delivery_tree'),
       'MODEP_NATIVE_LABEL': 'review1_parity_degenerate',
       'MODEP_FIXTURE_MODULE': 'modep_native_fixture_degenerate'}
command = [sys.executable, '-I', '-s', '-B', str(L/'work/native_parity.py')]
log = L/'out/tests/review1_parity_degenerate.log'
with log.open('w') as handle:
    process = subprocess.run(command, env=env, stdout=handle, stderr=subprocess.STDOUT)
output = log.read_text()
assert process.returncode == 1 and "assert all(value['unique_frames'] > 1" in output, output[-3000:]
result = dict(mutation='all fixture frame pins refer to one physical file', returncode=process.returncode,
              caught_by='native parity unique_frames > 1 assertion', log=str(log), command=command)
(L/'out/tests/review1_parity_mutation.json').write_text(json.dumps(result, indent=2)+'\n')
print('MUTATION_CAUGHT '+json.dumps(result, sort_keys=True), flush=True)
