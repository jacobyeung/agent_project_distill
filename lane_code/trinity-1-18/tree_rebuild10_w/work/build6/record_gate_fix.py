"""Record the standalone identity repair without changing packet manifests."""
import difflib
import hashlib
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
B = L / 'work/build6'
name = 'launch_s1/b/i.py'
before = (L / 'work/contracts_r6/tree_copy' / name).read_bytes()
after = (L / 'work/tree_r1' / name).read_bytes()
sha = lambda value: hashlib.sha256(value).hexdigest()
prior = json.loads((L / 'work/build5/proofs/suite_tree/source_hashes.json').read_text())
assert sha(before) == prior[name]
patch = ''.join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                                    fromfile='build5/' + name, tofile='build6/' + name))
(B / 'GATE_IDENTITY_FIX.diff').write_text(patch)
test = 'tests.test_s1_launch_kit.LaunchKitTests.test_all_eight_ranks_and_native_configuration_binding_are_required'
test_file = 'tests/test_s1_launch_kit.py'
proof = B / 'proofs/final_targeted'
validated = False
if (proof / 'results.json').exists() and (proof / 'source_hashes.json').exists():
    result = json.loads((proof / 'results.json').read_text())
    hashes = json.loads((proof / 'source_hashes.json').read_text())
    validated = (test in result['passed'] and result['complete']
                 and result.get('coverage_code_filter') == 'compiled-source fingerprint'
                 and hashes.get(name) == sha(after)
                 and hashes.get(test_file) == sha((L / 'work/tree_r1' / test_file).read_bytes()))
reason = ('The standalone gate runs before private training modules are staged and must '
          'match native configuration identity in both contract epochs.')
value = dict(file=name, route='additional integration repair', before=sha(before), after=sha(after),
             manifest_patched_hash=None, native_source='student_pilot/carrier_c1_run.py',
             threshold_source='trace_format/contracts.py',
             before_source='work/build5/proofs/suite_tree/source_hashes.json',
             diff='work/build6/GATE_IDENTITY_FIX.diff', test=test,
             proof='work/build6/proofs/final_targeted/results.json', validated=validated,
             hunks=[dict(header=line, disposition='adapted', reason=reason)
                    for line in patch.splitlines() if line.startswith('@@')])
(B / 'GATE_IDENTITY_FIX.json').write_text(json.dumps(value, indent=2) + '\n')
report = L / 'out/CONTRACTS_INTEGRATION.md'
marker = '\n## Standalone gate identity\n'
body = report.read_text().split(marker, 1)[0].rstrip()
lines = [marker.rstrip(), '',
         '`launch_s1/b/i.py` is an additional integration repair outside the packet manifest. '
         'Its standalone configuration identity now matches the accepted native heading-threshold rule. '
         'The existing native-parity assertion remains, with explicit epoch and invalid-threshold cases.', '',
         f"Before: `{value['before']}`. After: `{value['after']}`. Manifest patched hash: not listed.", '',
         '| Hunk | Disposition | Reason |', '|---|---|---|']
lines.extend('| ' + row['header'] + ' | adapted | ' + reason + ' |' for row in value['hunks'])
lines += ['', 'The exact adaptation is in `work/build6/GATE_IDENTITY_FIX.diff`. '
          'Hashes, native rule sources and validation state are in `work/build6/GATE_IDENTITY_FIX.json`.']
report.write_text(body + '\n' + '\n'.join(lines) + '\n')
print(json.dumps(dict(file=name, validated=validated, hunks=len(value['hunks']))))
