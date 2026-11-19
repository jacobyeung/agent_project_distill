from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23c';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
kit=J.load(D/'KIT.json');scan=J.load(D/'SCAN.json');tests=J.load(D/'GUARD_TESTS.json');suites=J.load(D/'SUITES.json');look=J.load(D/'LOOKAHEAD.json');start=J.load(D/'START.json')
assert J.seal(K)==kit['kit_seal']==scan['kit_seal']==look['kit_seal']
assert inventory(L/'work/tree_r1')==start['tree']
assert tests['successful'] and not tests['missing']
assert len(suites)==5 and all(r['returncode']==0 and r['successful'] for r in suites)
assert look['result']['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED' and look['config_unchanged']
assert scan['status']=='PASS'
for name,v in start['packages'].items():assert (L/name).stat().st_size==v['bytes'] and J.sha(L/name)==v['sha256']
uploads=J.load(L/'out/UPLOADS_NEW_23C.json')
for row in J.load(B/'UPLOADS.json')['files']:
 p=Path(row['local_path']);assert p.stat().st_size==row['bytes'] and J.sha(p)==row['sha256']
counts=dict(guard=tests['tests'],regression=sum(x['tests'] for x in suites),groups=suites)
counts['total']=counts['guard']+counts['regression'];J.write(D/'TEST_COUNTS.json',counts)
J.write(B/'FINAL_KITS.json',dict(status='PASS',GO=False,tree_seal=kit['tree_seal'],kits={'q':J.load(K/'BUILD.json')},decoded_scan=scan,upload_bytes=J.load(B/'UPLOADS.json')['total_bytes'],upload_files=len(J.load(B/'UPLOADS.json')['files']),scope='Kit-only E42 repair; source and config unchanged.'))
lines=[
'PASS: kit-only GPU guard repair validated. Production GO=false.',
'The in-view guard prints one flushed JSON diagnostic, accepts at least 75 GiB, and refuses missing CUDA, zero devices or failed property queries with E42.',
'The diagnostic records torch version, CUDA availability/count, CUDA_VISIBLE_DEVICES, device name/memory bytes, and /dev/nvidia0 plus /dev/nvidiactl existence.',
'Opaque key meanings and the exact build-24 generator patch are in out/GUARD_PATCH.md; out/GUARD_PATCH.diff contains the two generator hunks.',
'Source: work/build21/kit.py; emitted guard: work/build21/kits/q/b/g.py. Resource metadata also declares 75 GiB.',
'',
'The guard runs inside bwrap, after tk_bwrap constructs BW; q/job.sh reaches it through bootstrap and decoded k/j.json.',
'The view matches P: --dev-bind /dev /dev exposes host NVIDIA nodes; top-level read-only binds/symlinks preserve host driver-library paths.',
'No bind change was needed. Source audit: work/build23c/VIEW_AUDIT.json; P reference: ext/pwrap/b/c.sh:339-366.',
'Job 173076 did not record its cause; this CPU check cannot establish its CUDA visibility or device-memory value.',
'',
'Before/after: 85,520,809,984 bytes refuses/passes; no CUDA refuses/refuses; 70 GiB refuses/refuses.',
f"Guard tests: {tests['tests']} passed, including exact/below threshold, zero count, property failure and missing-node diagnostics; all {len(tests['changed_statement_lines'])} guard statement lines covered (work/build23c/GUARD_TESTS.json).",
f"Regression tests: {counts['regression']} passed across kit, naming and resolver suites; {counts['total']} tests total (work/build23c/TEST_COUNTS.json, SUITES.json).",
f"Decoded scan: PASS, {scan['checked_strings']} strings (work/build23c/SCAN.json).",
'Look-ahead: view PASS; CPU guard E42 with diagnostic; stubbed 80 GB-class guard PASS; native entry reaches R1_PROOF_FRAME_HOST_REQUIRED.',
'The look-ahead uses the kit own decoded config unchanged. Only the guard uses stubbed torch; the native entry uses real CPU torch and the inherited empty/prefixed mounts.',
'That refusal remains the frame-host boundary; no production proof or capacity rerun is claimed (work/build23c/LOOKAHEAD.json).',
'',
f"Tree seal unchanged: {kit['tree_seal']} (out/TREE_SEAL.json; work/build23c/INTEGRITY.json).",
f"Kit q seal: {kit['kit_seal']} (work/build21/kits/q/SHA256SUMS.txt).",
f"Upload diff versus 67ce92f6: {len(uploads)} files, {sum(v['bytes'] for v in uploads)} bytes: q/b/g.py, q/SHA256SUMS.txt and q/BUILD.json (out/UPLOADS_NEW_23C.json).",
'All sealed-tree bytes, config, resolver identities, admission, legality, removals, P opener rows, step-544 lineage and DEFERRED behavior remain unchanged.',
'Existing packages are byte-identical; superseded generator, guard and metadata are retained in attic/build23c (work/build23c/START.json).',
'Package seal, byte count, SHA-256 and stream verification: work/build23c/DELIVERY.json, external to avoid circular hashing.',
'The requested before/after comparison is retained as regression evidence. No upload, submission, network or GPU execution occurred.',
]
assert len(lines)<40
(L/'out/BUILD23C_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='PASS',tests=counts['total'],report_lines=len(lines),kit_seal=kit['kit_seal'])))
