The kit remains GO=false. Nothing was submitted. Run the commands below only after reviewing the delivery and supplying the missing pinned inputs.

Before submission, the operator creates these opaque links. The job authenticates the linked metadata archive and model archive against `k/p.json` before staging.

```bash
ln -s /project/community/jjyeung/distill/okit /project/community/jjyeung/okh7/l_94a76bda
ln -s /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/l_3d48eea0
```

If a link already exists, check its target and pinned content. The delivery does not replace it.

The upload inventory is `UPLOADS.json`. Its entries specify every local file, opaque destination, SHA-256 and byte count. From the extracted delivery, the supplied `upload.py` checks every file before writing to N's new pool folder. It never writes into P's kit or run.

```bash
python3 work/build21/upload.py "$PWD" /project/community/jjyeung/okh7/x_22c714e1
```

The resolver reads a JSON object with two arrays. `objects` contains exactly four entries in part order,
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
(pool / 'x_22c714e1' / 'l.json').write_text(json.dumps(listing, indent=2) + '\n')
```

Resolve the staged input with the uploaded kit:

```bash
python3 -I -s -B /project/community/jjyeung/okh7/x_22c714e1/q/b/resolve.py \
  --pool /project/community/jjyeung/okh7 \
  --listing /project/community/jjyeung/okh7/x_22c714e1/l.json \
  --output /project/community/jjyeung/okh7/x_22c714e1/r.json
```

The kit pins P's kit identity `774503e2…`, runtime identity `9459724f…`, original kit config,
and the config/binding/preparation pins shared by `e.json` and `r.json`. The resolver authenticates
their relation and gives `donor_config_sha256` the runtime identity. JSONL removal files remain
hash-verified data; required metadata must parse as one JSON document and refuses by member name.
Native export files stage together under their manifest sibling names.

Mode q also requires authenticated host envelopes for all bound routing slices, with exact row membership, RGB joins, scene coverage and extent receipt. A missing input must remain a refusal. `proofs/receipts/RESULT.json` lists absent dependencies by SHA-256 and original path. The local capacity proof does not supply production RGB, model shards or host envelopes.

The scanner checks every decoded key/string value, all literal environment contributions, and unresolved environment operations. Only the whole unmodified host environment may be inherited through a spread or copy; every added key is checked. Runtime Python values require one of the five explicit path names in `environment21f.py`. Complex shell programs require their exact reviewed source hash and the literal-name runtime allowlist in `environment_shell21g.json`; any edit invalidates that proof. The authenticated content exceptions remain in `../build21d/ALLOWLIST.json`. Final scan and upload differences: `../build21g/SCAN.json` and `../build21g/UPLOAD_DIFF.json`.

The view mounts a private writable `/tmp`, restores the node-local job root at its original path, then applies the remaining binds and `/tmp/q_22c714e1` alias. It creates no pool mount point. AS, AL and P must already exist wherever their host ancestor is read-only; an absent top-level prefix can instead be created under the namespace root. Those earlier binds succeeded in job 173051. Their values and every ordered destination are in `../build21g/MOUNTS.json`. The CPU stand-in view passes; the production GPU/model/store proof remains required.

The result archive contains the proof result and a separate room census. The census cannot admit a failed proof.

The exclusion payload stages as `k/3119aa4a.json`. Its SHA-256 remains
`3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.
The authenticated `p_sources` map reads the same bytes from N's `u/<sha256>` upload.
Configuration pins and hash-keyed catalogs use the pinned opaque map. P's original files remain unchanged.

Upload total: 137108151 bytes in 164 files (source: `UPLOADS.json`).

The focused test fixture closure would add 202336662 bytes.
The delivery includes 22066639 bytes of smaller fixture inputs; the remaining prerequisites,
their hashes and paths are listed in `../build21c/DEPENDENCIES.json` under `omissions`.
The full focused suite therefore requires those listed inputs after unpacking.
No checkpoint, database or frame set is bundled for test replay.
The source tree remains sealed as `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`.

To replay the focused suites once the listed prerequisites are available, use the supplied environment
and run `nice -n 10 bash work/build21/run.sh work/build21/focused.py` from the delivery root.
The test helpers and the small baseline source/inputs are included. The original path identities in
authenticated records remain pinned; `B21C_PORTABLE=1` redirects bundled prerequisite reads by the
explicit dependency map without changing their bytes.
