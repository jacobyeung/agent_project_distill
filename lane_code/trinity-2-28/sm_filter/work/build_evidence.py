import collections
import gzip
import importlib.util
import json
from pathlib import Path
import re
spec = importlib.util.spec_from_file_location('simulate', 'out/tests/simulate.py')
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)
patterns = [
 ('test_runs / test-artifacts', r'(?i)/(?:test_runs|test-artifacts)/'),
 ('LANE_TEST_OUTPUT / B2_TEST_OUTPUT / TMPDIR / R2_PROOFS', r'(?i)/(?:lane_test_output|b2_test_output|tmpdir|r2_proofs)/'),
 ('32 hexadecimal characters in a directory', r'/[^/]*[a-fA-F0-9]{32}[^/]*/'),
 ('Mixed letter/digit eight-character suffix', r'/[^/]*_(?=[a-z0-9_]{0,7}[a-z])(?=[a-z0-9_]{0,7}[0-9])[a-z0-9_]{8}/'),
 ('Known tempfile families', r'/(?:sam_r10|finetune_gate_test|provisional|driver)_[a-z0-9_]{8}/'),
 ('Nested orch_n30 tree', r'/orch_n30/'),
 ('Nested scratch/jjyeung tree', r'/scratch/jjyeung/'),
 ('Vendored Python library', r'/lib/python'),
 ('Conda metadata', r'/conda-meta/'),
 ('Staged interpreter environment', r'/payload/environment/'),
 ('Extracted work archives', r'/work/extract/'),
 ('Rehearsals', r'(?i)/rehearsal[0-9]*/'),
 ('Attics', r'(?i)/attic/'),
 ('Nested build work', r'/work/build[^/]*/work/'),
 ('Generated build review tests', r'/work/build[^/]*/review_tests/'),
 ('Generated build integration tests', r'/work/build[^/]*/integration[0-9]*/'),
 ('patch_validation_*', r'(?i)/patch_validation_[^/]*/'),
 ('fixtry', r'(?i)/fixtry/'),
 ('sandbox / sandboxes', r'(?i)/(?:sandbox|sandboxes)/'),
 ('Existing cache rules', r'/[^/]*cache[^/]*/'),
]
patterns = [(name, re.compile(pattern)) for name, pattern in patterns]
evidence = {name: dict(files=0, bytes=0, examples=[]) for name, _ in patterns}
manifest_counts = collections.defaultdict(lambda: [0,0])
for source in sorted(Path('in/commits').glob('*.gz')):
 commit=source.name.split('_')[1]
 with gzip.open(str(source),'rt') as stream:
  for line in stream:
   size,label,path=sim.parse(line)
   if label == 'repository': continue
   if path.startswith('code_sync/meta/DEDUP_') and path.endswith('.tsv.gz'):
    manifest_counts[commit][0]+=1;manifest_counts[commit][1]+=size
   # Only directories for basename predicates; interpreter /lib/python is also a substring.
   q='/'+'/'.join(path.split('/')[:-1])+'/'
   for name, pattern in patterns:
    if pattern.search(q):
     e=evidence[name];e['files']+=1;e['bytes']+=size
     if len(e['examples'])<2 and label+'/'+path not in e['examples']:e['examples'].append(label+'/'+path)
Path('work/rule-evidence.json').write_text(json.dumps(dict(rules=evidence,manifests=manifest_counts),indent=2,sort_keys=True)+'\n')
for name,_ in patterns:
 e=evidence[name];print('%s\t%d\t%d'%(name,e['files'],e['bytes']))
