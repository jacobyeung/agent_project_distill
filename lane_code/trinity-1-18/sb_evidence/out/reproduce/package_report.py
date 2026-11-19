"""Validate deliverables and create the evidence archive with an external checksum footer."""
import hashlib
import json
import sys
import tarfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from survey import ROOT,W,K,N,OUT,TREE,read,pin,save,sha
from student_pilot import r2_policy as P

decisions=read(OUT/'RECORD_DECISIONS.json')
survey=read(OUT/'SURVEY.json')
checks=read(OUT/'SELF_CHECK.json')
intersections=read(OUT/'INTERSECTIONS.json')
assert len(list((OUT/'gaps').glob('*.json')))==9
assert not list((OUT/'records').glob('*.json'))
assert read(OUT/'kit/registry.json')==read(N/'registry.json')
assert all(checks['individual_slots'][s]['status']=='REFUSE' for s in decisions['slots'])
assert all(r['status']=='REFUSE' for r in checks['component_phases'].values())
assert all(r['result']['status']=='REFUSE' and r['result']['reason']=='Missing component evidence: init_m544' for r in checks['official_gateway_synthetic_checks'].values())

# Include reproducible code and small audit inputs, not multi-gigabyte row stores.
for name in ('survey.py','intersections.py','build_gaps.py','self_check.py','package_report.py','run_python.sh'):
    p=ROOT/'work'/name;q=OUT/'reproduce'/name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
for name in ('source_paths.txt','tree_paths.txt','w12_paths.txt'):
    p=ROOT/name;q=OUT/'audit_inputs'/name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
for name in ('json_index_full.json','extracted_index.json','sqlite_index.json','tar_inventory.json'):
    p=ROOT/'work'/name
    save(OUT/'audit_inputs'/name,dict(schema='sb-captured-survey-index-v1',inputs=[pin(p)],entries=read(p)))
save(OUT/'REPRODUCTION.json',dict(schema='sb-evidence-reproduction-v1',inputs=[pin(ROOT/'work'/n) for n in ('survey.py','intersections.py','build_gaps.py','self_check.py','package_report.py','run_python.sh')],
    environment='trinity-1-18; CPU only; local p1cpu Python; two BLAS threads; process virtual memory limit below 40 GiB.',
    commands=['bash work/run_python.sh work/survey.py','bash work/run_python.sh work/intersections.py',
              'bash work/run_python.sh work/build_gaps.py','bash work/run_python.sh work/self_check.py',
              'bash work/run_python.sh work/package_report.py'],
    checksum_method='hashlib.sha256 of exact bytes in 8 MiB blocks; sha256sum FILE independently reproduces each number.',
    registry_note='The registry retains the exact r2_policy slot schema, so its source hashes are in REGISTRY_PROVENANCE.json instead of adding invalid registry fields.',
    archive_note='The tar excludes itself and its checksum sidecar. Its report omits only the final archive-checksum footer, which is appended to the external report after tar creation.',
    data_dependencies='Absolute source paths are intentional provenance. Reproduction requires those source bytes and the captured work indexes; the archive does not include training databases or model weights.'))

lines=['# Component evidence report','',
       '**No production component record is justified. All nine slots remain MISSING.**',
       'The bundle contains nine gap files, a copied registry, a source survey and CPU gate checks. W was not edited.',
       '', '| Slot | Status / record SHA256 or gap | Evidence basis | Overlaps found |', '|---|---|---|---|']
for s in (*P.LINEAGE,*P.EXTERNAL,*P.NEW):
    d=decisions['slots'][s]
    overlap='Unknown: complete parent membership missing.' if s in P.LINEAGE else 'No complete component-level conclusion.'
    if s=='data_rows_r2':overlap='0 in resolved populations; 119,375 v7 rows unknown.'
    lines.append(f'| {s} | MISSING; [gap](gaps/{s}.json); no record | {d["rests_on"]} | {overlap} |')
lines += ['', 'The policy accepts only hash-bound `r2-component-evidence-v1` records. Lineage needs explicit overlap lists and all three checked banks. Frozen exemptions need actual frozen weights; new training needs complete exclusions.',
          'The policy permits the disclosed venue `381879` exception. No overlap was suppressed or assigned that exception.',
          'N sets `geometry_connector=none`; the strict component policy still requires `heads_gf1_connector`. No clean claim is inferred from that setting.',
          '', 'The [survey](SURVEY.json) lists '+str(len(survey['sources']))+' source files with hashes, what each proves and what each lacks. The readable version is [SURVEY.md](SURVEY.md).',
          'The local b01 source tree matches all 792 entries in the sealed code inventory. The two other named source archives were copied once each; they do not supply parent scene manifests.',
          '', 'Fresh scene checks use the unchanged `r1_rooms.Rooms.canonical` and `Rooms.room`, including ScanNet room grouping, ScanNet++ aliases and ARKit visits.',
          'The bank membership source is `benchmark_scene_exclusions.json` / BENCH v2, SHA256 `3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.',
          '[BENCHMARK_SCENES.json](BENCHMARK_SCENES.json) preserves the bank-specific lists and input pins. [INTERSECTIONS.json](INTERSECTIONS.json) records every observed intersection and unresolved count.',
          '', '| Observed population | Rows | Resolved | Unresolved | VSI-Bench / VSTI / ReVSI intersections |', '|---|---:|---:|---:|---|']
for r in intersections['observable_populations']:
    c=r['counts'];hits=' / '.join(str(len(r['overlaps'][b])) for b in P.SCOPE)
    lines.append(f'| {r["label"]} | {c["rows"]:,} | {c.get("resolved",0):,} | {c.get("unresolved",0):,} | {hits} |')
lines += ['', 'These are raw surviving populations before N-side removals. The dev set is not a training manifest; the routing slices do not cover all production families. No lineage intersection is claimed.',
          '', 'CPU self-check ([full output](SELF_CHECK.json)):',
          '- `components(registry, "training")`: REFUSE — `Missing component evidence: init_m544`.',
          '- `components(registry, "native_evaluation")`: REFUSE — the same reason.',
          '- Each of the nine requested slots: REFUSE — `Missing component evidence: <slot>`.',
          '- Unchanged `read_bank` gateway, synthetic fixtures labeled VSI-Bench, VSTI and ReVSI: REFUSE — `Missing component evidence: init_m544`.',
          '- Existing `tests.test_r2_policy`: 5 tests passed; [test log](policy_tests.log). The local policy and test bytes match W.',
          'No official benchmark items were read. Native evaluation also requires five program-choice records outside this task; those remain null.',
          '', 'Missing named sources (full expected paths, hashes and referencing records are in [PIN_RESOLUTION.json](PIN_RESOLUTION.json) and the gap files):']
gap=read(OUT/'gaps/init_m544.json')
for m in gap['missing_sources']:
    lines.append('- `'+m['expected_path']+'` — SHA256 `'+m['expected_sha256']+'`.')
lines += [
    '- Complete inherited scene manifests and parent membership receipts for `49becb79/m200` and `b19c1200/train/step_400`. Their exact manifest filenames are not recoverable from surviving metadata; none was invented.',
    '- Geometry tower release, weights/config identity and actual frozen optimizer inventory bound to N. The joint receipt filename is unknown.',
    '- Actual frozen SAM3 inventory bound to N and the checkpoint in `SAM3_RECEIPT.json` (`9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`). Its inventory filename is unknown.',
    '- Complete independent scene mapping for the 119,375 unresolved v7 rows, complete post-filter family manifests, and frame-host membership. The current `component_rows.json` explicitly leaves these unresolved.',
    '- GF1 connector parameter inventory and complete clean training/exclusion receipt. Its original filename is unknown.',
    '', 'Commands that produce the reported numbers:',
    '- Source hashes, source count and 792-file archive check: `bash work/run_python.sh work/survey.py`.',
    '- Population counts and bank intersections: `bash work/run_python.sh work/intersections.py`.',
    '- Nine gap decisions and copied registry: `bash work/run_python.sh work/build_gaps.py`.',
    '- Phase, slot and official gateway results: `bash work/run_python.sh work/self_check.py`; this also records the exact unittest command that produced the five-test result.',
    '- Any individual file checksum: `sha256sum FILE`. SQLite candidates were hashed sequentially in 8 MiB blocks; their exact digests are retained in `audit_inputs/sqlite_index.json`.',
    '- Archive and validation: `bash work/run_python.sh work/package_report.py`; independently verify with `sha256sum out/sb_evidence_records.tar`.',
    '', 'The archive includes this report without the final archive-checksum footer. It excludes the tar itself and its checksum sidecar. Source paths remain provenance references; the archive contains no training databases.',
    'The no-archaeology skill governs report wording. No historical-process sentence requires an exception.'
]
report=OUT/'EVIDENCE_REPORT.md'
assert len(lines)+3 <= 120,len(lines)
report.write_text('\n'.join(lines)+'\n')
snapshot=OUT/'REPORT_CONTENT.md'
snapshot.write_bytes(report.read_bytes())

# Verify referenced inputs once per digest, including the recorded source survey.
verified={};errors=[]
def verify_pin(p):
    key=(p['path'],p['sha256'])
    if key in verified:return
    path=Path(p['path'])
    if not path.is_file():errors.append('missing '+str(path));return
    actual=sha(path)
    if actual!=p['sha256']:errors.append('changed '+str(path))
    verified[key]=actual
for p in OUT.rglob('*.json'):
    if p.name=='VALIDATION.json':continue
    d=read(p)
    if isinstance(d,dict):
        for v in d.get('inputs',[]):verify_pin(v)
for r in survey['sources']:
    # Large SQLite hashes were established immediately before the read-only census.
    if not r['path'].endswith('.sqlite'):verify_pin(r)
    if 'archive_input' in r:verify_pin(r['archive_input'])
assert not errors,errors
save(OUT/'VALIDATION.json',dict(schema='sb-deliverable-validation-v1',inputs=[pin(OUT/'RECORD_DECISIONS.json'),pin(OUT/'SELF_CHECK.json'),pin(OUT/'SURVEY.json'),pin(snapshot),pin(__file__)],
    status='PASS',records=0,gaps=9,registry_unchanged=True,verified_pins=len(verified),errors=[],
    report_pin_scope='Report before the archive-checksum footer; exact bytes are retained in the tar.',
    source_verification=[dict(path=k[0],sha256=k[1]) for k in sorted(verified)],
    large_store_check=pin(ROOT/'work/sqlite_index.json')))

archive=OUT/'sb_evidence_records.tar'
with tarfile.open(archive,'w') as tar:
    # The member list is fixed before opening/adding the archive itself.
    for p in sorted(OUT.rglob('*')):
        if p==archive or p.name=='sb_evidence_records.tar.sha256':continue
        if p.is_dir():continue
        tar.add(p,arcname='out/'+str(p.relative_to(OUT)),recursive=False)
checksum=sha(archive)
(OUT/'sb_evidence_records.tar.sha256').write_text(checksum+'  sb_evidence_records.tar\n')
with report.open('a') as f:f.write('\nArchive SHA256: `'+checksum+'`\n')
(ROOT/'STATUS.md').write_text('Stage 4 complete. The evidence archive and report are ready. All nine slots remain MISSING because the surviving sources cannot support complete lineage, frozen inventory or clean new-training claims. The copied registry refuses both policy phases and all three synthetic official gateway checks; the five existing policy tests pass. The report gives exact missing pins, partial intersection counts and archive SHA256. W and all other lanes remain unchanged.\n')
print('report lines',len(report.read_text().splitlines()))
print('archive',archive)
print('sha256',checksum)
print('verified source pins',len(verified))
