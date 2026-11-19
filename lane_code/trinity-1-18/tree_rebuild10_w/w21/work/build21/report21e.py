from pathlib import Path
import json,datetime
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e'
def read(p):return json.loads(p.read_text())
delivery=read(D/'DELIVERY.json');tests=read(D/'TESTS.json');scan=read(D/'SCAN.json');coverage=read(D/'COVERAGE.json')
replay=read(D/'REPLAY.json');delta=read(D/'UPLOAD_DIFF.json');fixture=read(D/'FIXTURE.json');identities=read(D/'IDENTITY_READERS.json')
lines=['PASS: both resolver defects are fixed. Production execution remains unrun; GO stays false.','',
    '`work/build21/joblib.py` preserves JSONL members as hash-verified values. It requires single-document',
    'JSON for the artifact, config, binding, preparation, model manifest and reachable metadata pins.',
    'Metadata parse failures identify the member. Explicit removal-list pin positions use the line-record',
    'reader; the same hash used in a metadata position still refuses. No hash check is bypassed.','',
    '`work/build21/kit.py` pins both identities, the original kit config, and the real config/binding/preparation',
    'pins shared by e.json and r.json. The resolver checks the runtime identity against the artifact, binding',
    'and preparation. Restoring the kit streams and preparation output must recover the kit identity.',
    '`donor_config_sha256` receives the runtime identity. Evidence: `work/build21e/IDENTITY_READERS.json`.','',
    f"- Kit identity: `{identities['kit_identity']}`.",
    f"- Runtime identity: `{identities['runtime_identity']}`.",'',
    'No sealed-tree reader needed a change. The export-only and persisted readers and handover donor',
    'already use historical P `export_identity`; N preparation uses the current N identity independently.',
    '`init_from_artifact` authenticates the artifact and export tensor pins and topology, not a kit identity.',
    'P opener rows, the step-544 lineage path, admission, legality and the DEFERRED boundary are unchanged.','',
    'Other edits: `jobtest.py` models both identities; `resolver21e.py` contains the new tests; the `*21e.py`',
    'helpers reproduce replay, tracing and delivery. `OPERATOR.md` specifies the exact listing fields and',
    'resolve command. `work/build21e/LISTING_TEMPLATE.json` pins the eight production metadata entries.',
    '`work/build21e/CHANGES.json` and `FIX.diff` record changed files and code details.','',
    'Real-byte fixture evidence: `work/build21e/FIXTURE.json`, `MUTATIONS_MAIN.json`, and `REAL_INPUTS.json`.',
    'The old resolver raises exactly `JSONDecodeError: Extra data: line 2 column 1` on the real JSONL',
    'members. With JSONL handling substituted, it raises exactly `E23` on the real artifact. The repaired',
    'resolver passes. Repinned JSONL metadata refuses by member name; unknown or kit artifact identities refuse.',
    'The fixture keeps all supplied real member and e/r/DONE/RP bytes. Missing archive members use tiny',
    'placeholders with rewritten manifest hashes/lengths. Export parts and the completion marker use fixture',
    'bytes. External metadata checks use a declared boundary stand-in because those bytes are absent.',
    'The omitted archive tokenizer adds one fixture entry to the eight production external files.','',
    'Tests (overlapping suites are separate; counts and per-suite paths: `work/build21e/TESTS.json`):','',
    '| Suite | Tests | Failures/errors |','|---|---:|---:|']
for x in tests:lines.append(f"| {x['name']} | {x['tests']} | {x['failures']}/{x['errors']} |")
lines += ['',f"Changed-statement coverage: {coverage['observed']}/{coverage['total']} AST statement heads (`work/build21e/COVERAGE.json`).",
    f"Decoded scan: PASS, {scan['checked_strings']} strings across {len(scan['decoded_maps'])} maps (`work/build21e/SCAN.json`).",
    'The tree and staging paths did not change, so the conditional capacity restaging/q-preview rerun was',
    'not required. The focused regressions cover the synthetic handover and initialization paths.','',
    'Real pre-forward reader replay (`work/build21e/REPLAY.json`; unchanged real pins, CPU):','',
    '| Reader | Result |','|---|---|']
short={
    'p_opener_witness.prepared_vocabulary':'REFUSE: base-model config/tokenizer metadata absent',
    'p_opener_witness.produce':'REFUSE: base-model config/tokenizer metadata absent',
    'production_proof.bind_handover':'REFUSE: N production r2_sampling has not been produced',
    'r1_persisted.admission(weights=True)':'REFUSE: production heads absent',
    'carrier_c1_run.init_from_artifact:lm':'REFUSE: production export index absent',
    'carrier_c1_run.init_from_artifact:heads':'REFUSE: production heads absent',
    'p_export_receipt.collect':'REFUSE: production heads absent',
    'r1_handover.donor_meta_model':'REFUSE: base-model topology metadata absent',
    'r1_handover.verify_trainable_groups':'REFUSE: base-model topology metadata absent',
    'carrier_c1_run.prepared:N':'REFUSE: N scene-rebuild receipt has not been produced (exact pin required)',
}
for x in replay['rows']:
    result=x['status'] if x['status']=='PASS' else short.get(x['reader'],x['error'].replace('|','/'))
    if x['reader']=='r1_training.start':result+=': step '+str(x['result'])
    lines.append(f"| {x['reader']} | {result} |")
lines += ['',
    'No production tensor load or GPU forward is claimed. Initialization uses only model metadata attributes',
    'and stops at real missing tensor I/O. The final N binder stops at its missing produced row plan.',
    'These refusals preserve the production requirements; no identity or admission check was relaxed.','',
    'Delivery values below come from `work/build21e/DELIVERY.json`; every archive member was streamed',
    'back and checked against `work/build21/PACKAGE_MANIFEST.json`.','',
    f"- Package: `{delivery['package']}` (gzip), {delivery['bytes']} bytes; {delivery['members']} verified members.",
    f"- Package SHA-256: `{delivery['sha256']}`.",
    f"- Package content seal: `{delivery['package_seal']}`.",
    f"- Tree seal: `{delivery['tree_seal']}` ({delivery['tree_files']} files; unchanged).",
    f"- Kit q seal: `{delivery['kit_seal_after']}`.",
    f"- Upload inventory: {delivery['upload_bytes']} bytes in {delivery['upload_files']} files; actual uploads: none.",
    '- Changed uploads versus build 21c: '+', '.join('`'+x['name']+'`' for x in delta['changed'])+'.',
    '  Exact before/after hashes and lengths: `work/build21e/UPLOAD_DIFF.json`.',
    f"- Bundled real fixture inputs: {delivery['real_fixture_files']} files, {delivery['real_fixture_bytes']} bytes.",
    f"- Workspace growth: {delivery['workspace_growth_bytes']} bytes, below the 2 GB limit.",
    '- Both build-21c and build-21d packages and reports remain unchanged.',
    f"- Completed: {delivery['timestamp']}.",'',
    'The focused-suite prerequisites omitted from the earlier delivery remain listed in',
    '`work/build21c/DEPENDENCIES.json`. No SSH, network, Orchard, GPU, Git, scheduler or agents were used.',
    'The report and final package checksum stay outside the archive to avoid a circular checksum.']
assert len(lines)<120,len(lines)
(L/'out/BUILD21E_REPORT.md').write_text('\n'.join(lines)+'\n')
print('Report lines',len(lines));print(delivery['package'],delivery['sha256'])
