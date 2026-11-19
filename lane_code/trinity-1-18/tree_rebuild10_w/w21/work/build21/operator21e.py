from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e';E=L.parent/'ext/m400real'
sys.path.insert(0,str(B));import joblib as J
f=J.load(D/'FIXTURE.json');original={x['sha256'] for x in J.load(E/'MANIFEST.json')['files']}
external=[x for x in f['external_metadata'] if x['sha256'] not in original]
assert len(external)==8
template=dict(objects=[dict(name=f'q8/8865619b/6ed2c7aa_m400.tar.part{i:02d}-of-04',pool_path=None,bytes=None) for i in range(4)],
    metadata=[dict(name=x['name'],sha256=x['sha256'],pool_path=None,bytes=None) for x in external])
J.write(D/'LISTING_TEMPLATE.json',template)
text=(L/'attic/build21e/OPERATOR.md').read_text()
start=text.index('The resolver requires');end=text.index('\n\n',start)
paragraph='''The resolver reads a JSON object with two arrays. `objects` contains exactly four entries in part order,
each with `name`, an absolute `pool_path` inside the pool, and integer `bytes`; an individual `sha256`
is optional. The names are exactly `q8/8865619b/6ed2c7aa_m400.tar.part00-of-04` through
`q8/8865619b/6ed2c7aa_m400.tar.part03-of-04`. It checks each length and the combined SHA-256
and length against P's completion marker.

`metadata` contains one entry for each base-model metadata file absent from P's small archive,
with `name`, `sha256`, an absolute `pool_path` inside the pool, and integer `bytes`.
Use the names and hashes from the pinned model manifest, including JSON/TXT/Jinja files and
`model.safetensors.index.json` (and `.model` tokenizer files if listed). These are base-model
metadata, distinct from the trained export index. All metadata files remain content-hash verified.
The production step-400 input requires eight such entries. `../build21e/LISTING_TEMPLATE.json`
contains their exact names and hashes and the four exact object names; replace every `null`
with the actual staged path or byte count. For example, one completed entry has this shape:

```json
{"name":"config.json","sha256":"<64 hex from the pinned model manifest>","pool_path":"/project/community/jjyeung/okh7/m/<sha256>","bytes":1234}
```

The displayed hash/path and 1234 bytes are examples, not production values. To fill the template
without estimating sizes, stage the parts as `p0` through `p3` and the eight metadata files as
`m/<sha256>` under the pool, then run this on the login host:

```python
import json
from pathlib import Path
pool = Path('/project/community/jjyeung/okh7')
listing = json.loads(Path('work/build21e/LISTING_TEMPLATE.json').read_text())
for i, entry in enumerate(listing['objects']):
    path = pool / f'p{i}'
    entry.update(pool_path=str(path), bytes=path.stat().st_size)
for entry in listing['metadata']:
    path = pool / 'm' / entry['sha256']
    entry.update(pool_path=str(path), bytes=path.stat().st_size)
(pool / 'x_22c714e1' / 'l.json').write_text(json.dumps(listing, indent=2) + '\\n')
```

Resolve the staged input with the uploaded kit:

```bash
python3 -I -s -B /project/community/jjyeung/okh7/x_22c714e1/q/b/resolve.py \\
  --pool /project/community/jjyeung/okh7 \\
  --listing /project/community/jjyeung/okh7/x_22c714e1/l.json \\
  --output /project/community/jjyeung/okh7/x_22c714e1/r.json
```

The kit pins P's kit identity `774503e2…`, runtime identity `9459724f…`, original kit config,
and the config/binding/preparation pins shared by `e.json` and `r.json`. The resolver authenticates
their relation and gives `donor_config_sha256` the runtime identity. JSONL removal files remain
hash-verified data; required metadata must parse as one JSON document and refuses by member name.
Native export files stage together under their manifest sibling names.'''
text=text[:start]+paragraph+text[end:]
text=text.replace('The scan and unchanged kit proof are in `../build21d/SCAN.json` and `../build21d/KIT_CHECK.json`.',
    'The final scan is in `../build21e/SCAN.json`; `../build21e/UPLOAD_DIFF.json` identifies changed uploads.')
uploads=J.load(B/'UPLOADS.json')
text=text.replace('Upload total: 137103557 bytes in 164 files',f"Upload total: {uploads['total_bytes']} bytes in {len(uploads['files'])} files")
(B/'OPERATOR.md').write_text(text)
spec=J.load(B/'kits/q/k/p.json')
readers=[
    dict(reader='joblib.identities',identity='both',checks='Pinned kit config, runtime config, e/r run pins, artifact, binding, preparation; project prepared streams/output back to kit identity.'),
    dict(reader='launch_r1.p_export_receipt.collect',identity='runtime export_identity',checks='Artifact/binding/preparation against P runtime config.'),
    dict(reader='student_pilot.r1_persisted.verify/admission',identity='runtime export_identity',checks='Real e/r closure, milestone and preparation; training start checks continuation.'),
    dict(reader='student_pilot.r1_handover._donor/donor',identity='runtime export_identity',checks='donor_config_sha256 equals runtime config and artifact; binding/preparation and prepared streams authenticate.'),
    dict(reader='student_pilot.r1_handover.bind_target/progress; launch_r1.production_proof.bind_handover',identity='donor runtime; N target/continuation',checks='Donor reader authenticates P; each binder derives N target identity independently.'),
    dict(reader='student_pilot.carrier_c1_run.init_from_artifact',identity='artifact content pin, topology, named tensor hashes',checks='No p_identity or donor_config_sha256 comparison. Caller admission authenticates donor identity; full export and heads verify their own pins.'),
    dict(reader='student_pilot.carrier_c1_run.identity/prepared',identity='current N config',checks='N preparation uses the current contract identity; it must not replace historical P export_identity.')]
J.write(D/'IDENTITY_READERS.json',dict(kit_identity=spec['p_kit_identity'],runtime_identity=spec['p_runtime_identity'],
    p_run=spec['p_run'],kit_config=spec['p_kit_config'],sealed_tree_changed=False,readers=readers))
