"""Consolidate verified results, document admission limits, and package the kit."""
import collections, hashlib, json, re, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
I = ROOT / 'inputs'

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4194304), b''): digest.update(block)
    return digest.hexdigest()

def load(path): return json.loads(Path(path).read_text())
def dump(path, value): Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
def rows(path):
    with Path(path).open() as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def main():
    a = load(OUT / 'formA/CHECKS.json'); b = load(OUT / 'CHECKS.json')
    for form, folder, checks in [('B', OUT, b), ('A', OUT / 'formA', a)]:
        audit = load(folder / 'INDEPENDENT_CHECKS.json'); review = load(folder / 'READ30_REVIEW.json')
        assert audit['status'] == review['status'] == 'PASS'
        assert audit['rows'] == checks['emitted_rows'] == 17737
        assert sha(folder / 'READ30.md') == review['input_sha256'][str((folder / 'READ30.md').relative_to(ROOT))]
        for filename, digest in audit['input_sha256'].items(): assert sha(folder / filename) == digest
        for filename in ['build_rows.py', 'count_forms.py', 'source_contract.py', 'prepare_inputs.py', 'ned_filter.c', 'ned_filter.so']:
            assert sha(ROOT / filename) == checks['input_sha256'][filename], filename
        checks['independent_audit'] = {'status': 'PASS', 'rows': audit['rows'], 'sha256': sha(folder / 'INDEPENDENT_CHECKS.json')}
        checks['read30_review'] = {'status': 'PASS', 'rows': 30, 'sha256': sha(folder / 'READ30_REVIEW.json')}
        checks['contract_tests'] = {'status': load(OUT / 'CONTRACT_TESTS.json')['status'], 'sha256': sha(OUT / 'CONTRACT_TESTS.json')}
        checks['input_sha256']['finalize_kit.py'] = sha(__file__)
        dump(folder / 'CHECKS.json', checks)
    maps_b = list(rows(OUT / 'QID_MAP.jsonl')); maps_a = list(rows(OUT / 'formA/QID_MAP.jsonl'))
    assert {r['old_qid'] for r in maps_a} == {r['old_qid'] for r in maps_b}
    assert not {r['new_qid'] for r in maps_a} & {r['new_qid'] for r in maps_b}
    assert not {r['candidate_id'] for r in maps_a} & {r['candidate_id'] for r in maps_b}
    n = {r['row_key']: r for r in rows(I / 'n.json')}
    z = {r['row_key']: r for r in rows(I / 'z.json')}
    native_excluded = [{'old_qid': m['old_qid'], 'new_qid_B': m['new_qid'], 'source_removal': n[m['old_qid']]}
                       for m in maps_b if m['old_qid'] in n and m['old_qid'] not in z]
    assert len(native_excluded) == 173
    admission = {'input_sha256': {'n.json': sha(I / 'n.json'), 'z.json': sha(I / 'z.json'),
                 'QID_MAP_B.jsonl': sha(OUT / 'QID_MAP.jsonl'), 'QID_MAP_A.jsonl': sha(OUT / 'formA/QID_MAP.jsonl'),
                 'finalize_kit.py': sha(__file__)},
                 'status': 'KIT_ONLY_NOT_ADMITTED', 'alternatives': 'Choose one form; do not mix both by default.',
                 'converted_z_list_rows': len(maps_b) - len(native_excluded),
                 'converted_additional_n_removed_rows': len(native_excluded),
                 'n_reason_counts': dict(collections.Counter(r['source_removal']['reason'] for r in native_excluded)),
                 'additional_n_removed_rows': native_excluded,
                 'required_decision': 'Preserve outside_native_training_division exclusions when considering new qids; a new qid does not authorize admission.',
                 'cross_form_unique_qids_and_candidate_ids': 2 * len(maps_b)}
    dump(OUT / 'ADMISSION_SCOPE.json', admission)
    amendment = '''Both requested forms need an explicit trace-rule amendment before training admission.

Form B permits one Step per category that announces N and contains exactly N entries of the form "i of N, frame f". The ordinals must be 1..N without gaps or repetitions, all denominators must equal N, and every f must be an integer sampled-frame index in 1..32. Equal frames and equal region tags are valid for different instances; equal ordinals are not. A single category must total the answer. Multiple categories require a subsequent addition of their exact totals. Optional source region tags remain unchanged. This category Step replaces separate Locate lines and licenses the announced count only when the complete numbered inventory validates.

Form A permits one Step per category containing one positive integer increment per first-seen frame, in strictly increasing frame order, followed by its total. A category contains at most 32 frame entries. The increments must sum to the category total; region subtotals, when present, must sum to the frame increment. Category totals must sum to the answer. This grouped evidence replaces one Locate line per instance and licenses the increments and totals from the annotated instance inventory.

Both forms permit their final count conclusion inside the trace. Zero categories use an empty inventory and total zero, although no zero-truth source rows occur in this build. The generator preserves source category names and questions. Numbering is an output index, not a newly invented object identity; the source annotation IDs remain in provenance. Frames are indices, never seconds.

The local count_forms.py validator implements these proposed invariants. It is not installed in N. N's trace_grammar.py rejects every new row; r2_grammar.py pins that shared grammar by SHA256. Adoption requires the orchestrator to review and reseal the shared grammar and update the explicit counting admission policy. r1_counting.py currently refuses list forms and all totals. The kit does not weaken those gates or fabricate a passing native check.

ground_rows.pack is a routed ground-record API. Every source and new direct counting row fails it because suffix/events/spec_version are absent. A direct-row packing contract or an explicit scope correction is required; fabricating routed events would misrepresent these sources. Student-input and direct row-schema checks pass, and every original source passes native direct validation.

ADMISSION_SCOPE.json lists 173 converted sources that n.json excludes as outside_native_training_division. Those exclusions must survive any qid remapping. This kit builds both alternatives for review; it grants no training admission and reports no new checkpoint measurements. Form A remains unmeasured.
'''
    (OUT / 'TRACE_RULE_AMENDMENT.md').write_text(amendment)
    histogram = load(OUT / 'TRUTH_HISTOGRAM.json')['converted']
    census = load(OUT / 'CENSUS.json')
    lines = [
        'sb_rowF builds 17,737 counting rows per alternative: B is the default; --form A emits tallies.',
        'The kit is complete for review, but the required unchanged-N validation gate FAILS. No training admission is claimed.',
        '',
        'The generator uses W/w19 sealed tree_r1, 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa.',
        'Store v7 matches 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443 (204,413 rows).',
        'The census finds 20,669 counting rows: 18,052 first-seen sources and 2,617 outside this scope.',
        'All 18,052 sources convert mechanically; 17,737 pass the independent-annotation and room checks.',
        'The source union includes all 17,879 z.json list rows and 173 additional lists already removed by n.json.',
        'Of the converted rows, 17,564 come from z.json; 173 carry outside_native_training_division exclusions.',
        'ADMISSION_SCOPE.json lists those 173 rows. New qids do not override their native-division exclusions.',
        '',
        '| Source cell | Mechanical | Emitted per form | Refused |',
        '|---|---:|---:|---:|',
    ]
    for cell in sorted(census['mechanical_cells']):
        label = cell.replace('|', ' / ')
        lines.append(f"| {label} | {census['mechanical_cells'][cell]} | {census['eligible_cells'].get(cell, 0)} | {census['refusal_cells'].get(cell, 0)} |")
    lines += [
        '',
        'REFUSALS.jsonl lists 315 refusals: 228 K1-held-out rooms, 84 MISSING independent instance annotations, and 3 MISSING canonical-room mappings.',
        'Each missing-input refusal names its qid and the exact expected structured field or mapping key. No mapping or GT was invented.',
        'REMOVE.json is empty JSONL in n.json format: every emitted source is already removed by n.json or z.json.',
        'REMOVE_RECEIPT.json binds the empty file hash and the exact set difference.',
        '',
        '| Truth | ' + ' | '.join(str(i) if i < 10 else '10+' for i in range(11)) + ' |',
        '|---|' + '---:|' * 11,
        '| Rows per form | ' + ' | '.join(str(histogram[str(i) if i < 10 else '10+']) for i in range(11)) + ' |',
        '',
        'Exact source and emitted cell counts are asserted against inputs/EXPECTED_CELLS.json; no cell is sampled or silently shortened.',
        'Every source is used once per alternative. The two alternatives have disjoint qids and candidate_ids; kit formulas bind the new qid and unchanged question.',
        'Full field diffs permit only qid, candidate_id, target, and provenance.sb_rowF. All 82,716 instance entries per form match independent annotated IDs and frames.',
        'The independent audit verifies every row, region multiplicity, category sum, final answer, histogram, removal, and K1/R0/withheld-80/dev-S1/BENCH-v2 room exclusion.',
        'All 18,052 original sources pass student-input, row-schema, native-direct, and shared-grammar validation.',
        'All 17,737 new rows per form pass student-input, row-schema, and proposed-form validation; all FAIL unchanged N native-direct, shared-grammar, and counting admission.',
        'N ground_rows.pack fails on all 18,052 sources and 17,737 new rows per form: these direct rows lack routed ground-record fields. CHECKS.json retains the failures.',
        'Contract tests pass 12 positive cases and 33 malformed variants, including repeated/skipped ordinals, frame range/order, wrong totals, and region sums.',
        'READ30.md prints 30 full rows per form. The assistant reviewed every selected question and complete trace against its annotations; independent checks compare all JSON fields.',
        '',
        'New questions: 0. New trace bodies and individual lines are screened against 1,017 kit/fixture/R0-item wordings at normalized Levenshtein distance <=0.10; removed: 0 in each form.',
        'The screen covers all available question/prompt fields in W/w19 kit/fixtures and the mirrored R0 VSTI item file. Full external evaluation corpora are not supplied in this kit.',
        'TRACE_RULE_AMENDMENT.md specifies both Locate-line exceptions, numeric provenance, native gate changes, and the direct-packing limitation.',
        'Form B follows the requested count-first numbered pattern; form A is unmeasured. No checkpoint evaluation, images, training, GPU, network, SSH, or external writes were used.',
        'The orchestrator must decide trace-rule changes, native-division eligibility, and admission. The kit does not meet an all-native-checks-pass requirement.',
        '',
        'Commands below produce all reported counts and checks from this workspace:',
        '`PY=/scratch/jjyeung/envs/p1cpu/bin/python`; use `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`.',
        '`$PY -B prepare_inputs.py` produces the store census, source union, input hashes, source skips, and wording corpus.',
        '`cc -O2 -shared -fPIC ned_filter.c -o ned_filter.so` builds the bounded edit-distance helper.',
        '`$PY -B build_rows.py --census-only` fixes expected mechanical, eligible, and refusal counts.',
        '`$PY -B build_rows.py` produces form B; `$PY -B build_rows.py --form A --out out/formA` produces form A and both histograms/native checks.',
        '`$PY -B test_forms.py` produces the contract-test results.',
        '`$PY -B audit_rows.py` and `$PY -B audit_rows.py --form A --out out/formA` independently recount identities, truth, cells, rooms, and removals.',
        '`$PY -B finalize_kit.py` checks review receipts, cross-form IDs, native exclusions, and packages code, pinned inputs, rows, and reports.',
        '`sha256sum out/sb_rowF.tar` reproduces the digest in out/sb_rowF.tar.sha256 and out/PACKAGE_RECEIPT.json.',
        'The report contains no project-revision narrative; no borderline history sentences were retained.',
    ]
    assert len(lines) <= 80
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    scripts = ['prepare_inputs.py', 'source_contract.py', 'build_rows.py', 'count_forms.py', 'audit_rows.py',
               'test_forms.py', 'finalize_kit.py', 'ned_filter.c', 'ned_filter.so']
    members = [ROOT / p for p in scripts] + sorted(I.iterdir())
    names = ['rows.jsonl', 'QID_MAP.jsonl', 'REFUSALS.jsonl', 'REMOVE.json', 'REMOVE_RECEIPT.json',
             'CENSUS.json', 'CHECKS.json', 'TRUTH_HISTOGRAM.json', 'READ30.md', 'READ30_REVIEW.json', 'INDEPENDENT_CHECKS.json']
    members += [folder / name for folder in [OUT, OUT / 'formA'] for name in names]
    members += [OUT / name for name in ['CONTRACT_TESTS.json', 'ADMISSION_SCOPE.json', 'TRACE_RULE_AMENDMENT.md', 'REPORT.md']]
    manifest = {'input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in members},
                'schema': 'sb-rowF-kit-v1', 'default_form': 'B', 'rows_per_form': 17737,
                'status': 'KIT_ONLY_BLOCKED_BY_UNCHANGED_N_VALIDATORS',
                'external_dependency': {'tree': b['tree'], 'tree_sha256': b['tree_sha256']}}
    dump(OUT / 'ARTIFACT_MANIFEST.json', manifest); members.append(OUT / 'ARTIFACT_MANIFEST.json')
    archive = OUT / 'sb_rowF.tar'
    with tarfile.open(archive, 'w') as tar:
        for path in members: tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    expected_members = dict(manifest['input_sha256'])
    expected_members['out/ARTIFACT_MANIFEST.json'] = sha(OUT / 'ARTIFACT_MANIFEST.json')
    with tarfile.open(archive, 'r:') as tar:
        assert set(tar.getnames()) == set(expected_members)
        for member in tar:
            stream = tar.extractfile(member); checksum = hashlib.sha256()
            for block in iter(lambda: stream.read(4194304), b''): checksum.update(block)
            assert checksum.hexdigest() == expected_members[member.name], member.name
    digest = sha(archive)
    (OUT / 'sb_rowF.tar.sha256').write_text(digest + '  sb_rowF.tar\n')
    dump(OUT / 'PACKAGE_RECEIPT.json', {'input_sha256': {'ARTIFACT_MANIFEST.json': sha(OUT / 'ARTIFACT_MANIFEST.json'), 'finalize_kit.py': sha(__file__)},
         'archive': str(archive), 'sha256': digest, 'bytes': archive.stat().st_size, 'members': len(members),
         'archive_member_hash_verification': 'PASS',
         'status': 'KIT_ONLY_BLOCKED_BY_UNCHANGED_N_VALIDATORS'})
    (ROOT / 'STATUS.md').write_text('Kit complete: 17,737 rows in each alternative, with B as default, 315 explicit refusals, old/new qid maps, truth histograms, and an empty additional-removal delta. Independent audits and 30-row reviews pass for both forms. All new rows fail N\'s unchanged grammar and counting admission; the routed pack API also rejects these direct rows. The report and trace-rule amendment document those blockers and the 173 native-division exclusions. No training was run. The archive and SHA256 receipt are in out.\n')
    print(json.dumps({'archive': str(archive), 'sha256': digest, 'bytes': archive.stat().st_size,
                      'report_lines': len(lines), 'members': len(members)}))

if __name__ == '__main__': main()
