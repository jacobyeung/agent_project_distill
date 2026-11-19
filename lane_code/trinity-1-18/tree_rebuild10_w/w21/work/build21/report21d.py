from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d'
def read(p):return json.loads(p.read_text())
d=read(D/'DELIVERY.json');tests=read(D/'TESTS.json');coverage=read(D/'COVERAGE.json')
scan=read(D/'SCAN.json');mutations=read(D/'MUTATIONS.json');kit=read(D/'KIT_CHECK.json')
assert d['status']=='PASS' and scan['status']=='PASS' and kit['byte_identical']
text='''PASS: both review-21c scanner gaps are closed. GO remains false; nothing was submitted.

`work/build21/naming21.py` checks every decoded map key and string value, including nested
payloads, and Python environment assignments, updates and passed `env=` maps without a path filter.
It follows environment aliases, local value bindings and mapping updates, checks concatenated
literal strings, and checks shell assignment/export tokens and scheduler export arguments.
Every exception has an exact field selector and fixed identity or inventory seal.
No decoded payload subtree is skipped. `work/build21d/FIX.diff` contains the scanner diff.

`work/build21/joblib.py` is unchanged: its staging-map traversal already checks nested keys and
values without the defective payload/path filter. Its runtime guards remain covered by the regressions.
The new tests are `work/build21/naming_test21d.py`; the `*21d.py` scan, tracing, suite, metadata,
packaging and report helpers make the evidence reproducible. `work/build21d/CHANGES.json`
records their hashes. `OPERATOR.md`, `STATUS.md`, `FINAL_KITS.json` and `PACKAGE_MANIFEST.json`
under `work/build21/` describe the final delivery; upload entries are unchanged.

The small named allowlist is defined in `work/build21/naming21.py` and exported in
`work/build21d/ALLOWLIST.json`. Each listed exception is authenticated file content only;
none supplies a wrapper name, job path, argument, environment entry or log line:

- `k/{7,c0}.json:{files,sources,operation_sources}` retains source identity keys because the
  frozen source verifier requires the exact inventory. Fixed canonical SHA-256 seals authenticate
  each complete inventory; every key/value is visited. Added inventory entries refuse.
- `k/{c,n}.json:benchmark_scene_exclusions`, `geometry_connector`, `trace_program_version`,
  `r1_training/room_authority/split`, and `route_table/{object_size_estimation,room_size_estimation}`
  retain exact schema keys because frozen content readers require them. All values are scanned.
- `k/l.json:staged_inputs/{archives,files,packages,directories}/<index>/destination` retains
  the exact reader schema key; its spelling contains the bound substring `sti`. Its value is scanned.
- `k/n.json:{benchmark_scene_exclusions,dev_scene_exclusions,r1_training/wording_exclusion}/path`
  and `s1_routing/catalog/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`
  retain exact original identity text to preserve authenticated config content. Each consumer
  resolves its pinned hash through the checked opaque `pin_paths` map; unknown identities refuse.
- `k/s.json:entries/u/a4509d8c159f71f81d0f82adad8e85ef8135d17363084e7281fadddea04c9c5c/@content/room_rule`
  retains the exact admission annotation to preserve the pinned card content. Changing its text
  or copying it to another field does not receive the exception; all sibling fields are scanned.
- `k/g.json:payload` retains the exact bound `WORDS` list because the refusal filter needs those
  identifiers to recognize forbidden names. A changed list refuses.

The two reviewer controls use patched in-memory reads. The decoded-map control adds
`{"BeNcHmArK":"DaTaSeT"}` to the first `k/s.json` entry and recomputes both capsule hashes.
The environment control appends `os.environ["BeNcHmArK"]="q"` to `b/o.py`.
Both pass the saved old scanner and refuse by name in the final scanner. Additional controls
cover a nested forbidden value, shell `export BeNcHmArK=1`, and a Python `env=` dictionary key.
`work/build21d/MUTATIONS.json` records each old result and exact refusal.

Tests (overlapping suites are reported separately; source paths contain the counts):

'''
for row in tests:
    text+=f"- `{row['name']}`: {row['tests']} tests, {row['failures']} failures, {row['errors']} errors; `{row['source']}`.\n"
text+=f'''
The new suite records {len(mutations)} refusal cases, including
{sum(x.get('old')=='PASS' for x in mutations)} old-PASS/new-REFUSE controls (`work/build21d/MUTATIONS.json`).
Changed-statement coverage is {coverage['observed']}/{coverage['total']} AST statement heads;
exact source hashes, observed lines and uncovered guards are in `work/build21d/COVERAGE.json`.

The final scan passes {scan['checked_strings']} checked strings across {len(scan['decoded_maps'])} JSON maps
(`work/build21d/SCAN.json`). It found no forbidden job-visible name requiring a kit edit.
The kit has {kit['files']} byte-identical files (`work/build21d/KIT_CHECK.json`):
- Kit seal before: `{d['kit_seal_before']}`.
- Kit seal after: `{d['kit_seal_after']}`.

The tree seal stays `{d['tree_seal']}`
({d['tree_files']} files; `out/TREE_SEAL.json` and `work/build21/FINAL_KITS.json`).
P's opener rows, the step-544 lineage path, admission, legality and DEFERRED boundary are unchanged.
Neither the tree nor staging path changed, so no capacity restaging or q preview was needed.
The static scanner checks source literals and their local bindings; it does not execute dynamic
runtime inputs or evaluate inherited ambient environment values. Host-only inputs remain
subject to the unchanged runtime guards. Production, GPU and scheduler execution were not run.
The focused suites retain the unbundled prerequisites listed in `work/build21c/DEPENDENCIES.json`.

Delivery (all numbers below come from `work/build21d/DELIVERY.json`):

- Package: `{d['package']}` (gzip).
- SHA-256: `{d['sha256']}`.
- Package bytes: {d['bytes']}; manifest-verified members: {d['members']}.
- Content seal: `{d['package_seal']}`.
- Upload inventory: {d['upload_bytes']} bytes in {d['upload_files']} files; actual uploads: none.
- Workspace growth: {d['workspace_growth_bytes']} bytes, below the 2 GB limit.
- Build-21c package unchanged: `{d['base']['path']}`.
- Build-21c SHA-256: `{d['base']['sha256']}`.
- Completion: {d['timestamp']}.

Every archive member was streamed back and matched against the updated manifest.
The package checksum and this report remain outside the archive to avoid a circular checksum.
The required old/new control comparisons are retained as test evidence, not revision narrative.
'''
assert len(text.splitlines())<120,len(text.splitlines())
(L/'out/BUILD21D_REPORT.md').write_text(text)
print(text)
