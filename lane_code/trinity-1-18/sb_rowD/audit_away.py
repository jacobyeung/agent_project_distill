#!/usr/bin/env python3
"""Audit existing ReVSI-worded away traces; never generate training rows."""
import collections
import hashlib
import json
from pathlib import Path
import random
import re
import sqlite3

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
MIRROR = STORE.parent.parent
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
SEED = 20261118
EXPECTED = {'object_rel_direction_easy': 3664,
            'object_rel_direction_medium': 2665,
            'object_rel_direction_hard': 2182}
PHRASE = 'facing in the opposite direction of'
TURN = ('That is a half turn: what was ahead is now behind me, '
        'what was behind is now ahead, and left and right swap.')
FORMS = ['separate_half_turn_step', 'half_turn_merged_or_out_of_order',
         'keeps_toward_heading', 'no_explicit_half_turn']


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def classify(row):
    text = row['target'].replace('\\n', '\n')
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    relation = [i for i, x in enumerate(lines)
                if re.fullmatch(r'If I stood at the .+ facing the .+, the .+ would be .+\.', x)]
    turn = [i for i, x in enumerate(lines)
            if re.fullmatch(r'The question has me facing in the opposite direction of the .+\. '
                            + re.escape(TURN), x)]
    result = [i for i, x in enumerate(lines) if x.startswith('So I find ')]
    if (len(relation) == len(turn) == len(result) == 1
            and relation[0] + 1 == turn[0] and turn[0] + 1 == result[0]
            and lines[-2:] == ['</think>', row['answer']]):
        return FORMS[0]
    if 'half turn' in text.lower():
        return FORMS[1]
    if re.search(r'(keep|keeps) that heading', text):
        return FORMS[2]
    return FORMS[3]


def entry(i, row, number):
    text = row['target'].replace('\\n', '\n')
    return (f'### Sample {number}: {row["qid"]}\n\n'
            f'Store index: {i}. Family: {row["question_type"]}. '
            f'Form: {classify(row)}.\n\n'
            f'Question: {row["student_input"]["question"]}\n\n'
            f'Options: {" | ".join(row["student_input"]["options"])}\n\n'
            f'Answer: {row["answer"]}\n\n```text\n{text}\n```\n\n')


def main():
    OUT.mkdir(exist_ok=True)
    (ROOT / 'STATUS.md').write_text(
        'The store and family index are located. The audit samples 60 rows with seed '
        '20261118 and classifies the full ReVSI-worded away population before deciding '
        'whether rebuilding is warranted. All work runs on local disk with CPU only.\n')
    paths = [STORE / 'vqa/rows.sqlite', STORE / 'vqa/receipt.json',
             STORE / 'BUILD_MANIFEST.json', STORE / 'FAMILY_INDEX_RANGES.json',
             MIRROR / 'out/ADMISSION_PACKET_V7.md', MIRROR / 'out/ROWS_READ_V7.md',
             MIRROR / 'STATUS.md', W / 'inputs/records/n.json',
             W / 'w19/work/build19/seal.log', Path(__file__).resolve()]
    paths += [STORE / f'FAMILY_QIDS/{family}.txt' for family in EXPECTED]
    inputs = {str(p): sha(p) for p in paths}
    receipt = json.loads((STORE / 'vqa/receipt.json').read_text())
    assert inputs[str(STORE / 'vqa/rows.sqlite')] == receipt['database']['sha256']
    assert inputs[str(STORE / 'vqa/rows.sqlite')].startswith('210b2534')
    index = json.loads((STORE / 'FAMILY_INDEX_RANGES.json').read_text())['families']
    membership = {}
    qids = {}
    for family in EXPECTED:
        qids[family] = set((STORE / f'FAMILY_QIDS/{family}.txt').read_text().splitlines())
        for start, end in index[family]:
            for i in range(start, end + 1):
                assert i not in membership
                membership[i] = family
    db = sqlite3.connect(f'file:{STORE}/vqa/rows.sqlite?mode=ro&immutable=1', uri=True)
    assert db.execute('SELECT COUNT(*) FROM rows').fetchone()[0] == 204413
    population = []
    # Read all indexed direction rows so the sample frame does not depend on a suffix assumption.
    for i, raw in db.execute('SELECT i,row FROM rows ORDER BY i'):
        if i not in membership:
            continue
        row = json.loads(raw)
        assert row['question_type'] == membership[i]
        assert row['qid'] in qids[membership[i]]
        if PHRASE in row['student_input']['question']:
            population.append((i, row))
    db.close()
    family_counts = collections.Counter(r['question_type'] for _, r in population)
    assert dict(family_counts) == EXPECTED, dict(family_counts)
    assert len({r['qid'] for _, r in population}) == 8511
    census = collections.Counter(classify(r) for _, r in population)
    sample = random.Random(SEED).sample(population, 60)
    sample_counts = collections.Counter(classify(r) for _, r in sample)
    sample_families = collections.Counter(r['question_type'] for _, r in sample)
    assert len({r['qid'] for _, r in sample}) == 60
    assert census[FORMS[0]] == 8511, 'Audit-only branch requires all rows to pass.'
    header = ('# Away-row trace audit\n\n'
              'Seed: `20261118`; Python `random.Random(seed).sample`, without replacement, '
              'from all 8,511 matching rows ordered by store index.\n\n'
              'A separate step is a standalone trace line after the toward relation and before '
              'the derived away relation and answer. A numbered `Step 3` label is not required.\n\n'
              '| Form | Sample | Full population |\n|---|---:|---:|\n')
    for form in FORMS:
        header += f'| {form} | {sample_counts[form]} | {census[form]} |\n'
    header += '\nAll 60 complete questions, options and target traces appear below.\n\n'
    body = header + '## Ten examples per observed form\n\n'
    shown = set()
    for form in FORMS:
        matches = [(n, i, r) for n, (i, r) in enumerate(sample, 1) if classify(r) == form]
        if not matches:
            body += f'`{form}`: no examples exist in the sample or census.\n\n'
            continue
        for n, i, r in matches[:10]:
            shown.add(n)
            body += entry(i, r, n)
    body += '## Remaining sampled rows\n\n'
    for n, (i, r) in enumerate(sample, 1):
        if n not in shown:
            body += entry(i, r, n)
    (OUT / 'READ60.md').write_text(body)
    read30 = ('# Thirty complete source rows\n\n'
              'These are unchanged audit inputs, not replacement training rows. '
              'The first 30 rows of the seeded sample are printed in full.\n\n')
    for n, (i, r) in enumerate(sample[:30], 1):
        read30 += entry(i, r, n) + '```json\n' + json.dumps(r, ensure_ascii=False, indent=2) + '\n```\n\n'
    (OUT / 'READ30.md').write_text(read30)
    # n.json is JSONL despite its suffix. An empty stream means zero removals.
    with (W / 'inputs/records/n.json').open() as f:
        removal_schema = sorted(json.loads(next(f)))
    assert removal_schema == ['pool', 'question_type', 'reason', 'row_key', 'scene']
    (OUT / 'REMOVE.json').write_text('')
    checks = {
        'schema': 'sb_rowD_audit_v1', 'status': 'PASS_AUDIT_ONLY', 'input_sha256': inputs,
        'command': 'python -B audit_away.py', 'seed': SEED,
        'population': len(population), 'population_by_family': dict(family_counts),
        'sample_size': len(sample), 'sample_by_family': dict(sample_families),
        'forms_sample': {k: sample_counts[k] for k in FORMS},
        'forms_population': {k: census[k] for k in FORMS},
        'sample': [{'i': i, 'qid': r['qid'], 'form': classify(r)} for i, r in sample],
        'checks': {'store_sha256_matches_receipt_and_task': True, 'exact_family_counts': True,
                   'family_index_and_qid_membership': True, 'unique_population_qids': True,
                   'sample_source_use_maximum': 1, 'ordered_separate_half_turn_all_8511': True},
        'manual_review': 'PENDING: agent must read all 60 target traces before finalization',
        'build': {'replacement_rows': 0, 'toward_twins_generated': 0, 'removals': 0,
                  'reason': 'All rows already state the half turn as a separate step.'},
        'removal_format': {'encoding': 'JSONL', 'keys': removal_schema, 'records': 0},
        'not_applicable': {
            'pack_validate_new_rows_and_sources': 'No build; no new rows or build sources.',
            'candidate_id_recomputation_and_field_diff': 'No edited rows.',
            'independent_gt_geometry_recomputation': 'No rebuilt answers; this audit checks trace form only.',
            'room_rule': 'No admission or generation; existing room checks are not recertified.',
            'benchmark_edit_distance_filter': 'No new wording; threshold not applied; removed 0.'},
        'tree': {'path': str(W / 'w19/work/build19/proofs/final/frozen/work/tree_r1'),
                 'seal': str(W / 'w19/work/build19/seal.log'),
                 'used_for_build': False, 'reason': 'Newer sealed w19 found; no build required.'},
        'output_sha256': {name: sha(OUT / name) for name in ['READ60.md', 'READ30.md', 'REMOVE.json']}
    }
    (OUT / 'CHECKS.json').write_text(json.dumps(checks, indent=2) + '\n')
    (ROOT / 'STATUS.md').write_text(
        'The seeded sample contains 60/60 traces with a separate half-turn step. '
        'The full census confirms the same form in 8,511/8,511 rows. READ60.md and READ30.md '
        'are ready for direct review. The task takes the audit-only branch; REMOVE.json is '
        'an empty JSONL stream, and no replacement rows or twins are generated.\n')
    print(json.dumps({k: checks[k] for k in ['status', 'population_by_family', 'sample_by_family',
                                           'forms_sample', 'forms_population']}, indent=2))


if __name__ == '__main__':
    main()
