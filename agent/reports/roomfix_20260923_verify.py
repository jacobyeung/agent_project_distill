"""Audit Set B room repair, source bytes, label ratios, splits, and exact trainer materialization."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics
import os
import sys
import time

WT = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_roomfix_fullset_20260923T1152Z/work/repo')
sys.path.insert(0, str(WT))
from tools.gtmeasure.io import canonical, digest, pin, read_json, read_jsonl, sha, verify_pin
from tools.gtmeasure.mix import mix_rows
from tools.gtmeasure.split import load_split
from tools.gtmeasure.generate import counts

S = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
OUT = WT.parents[1] / 'out'
OLD_GT = S / 'gtmeasure_v2_20260922_full'
NEW_GT = S / 'gtmeasure_v2_roomfix_20260923'
OLD_MIX = S / 'mix_v25_uncapped_gtm2_r050_20260923'
NEW_MIX = S / 'mix_v25_uncapped_gtm2_r050_roomfix_20260923'
OLD_TRAINER = S / 'mix_v25_uncapped_gtm2_r050_20260923_trainer'
NEW_TRAINER = S / 'mix_v25_uncapped_gtm2_r050_roomfix_20260923_trainer'


def rows(root):
    return {side: list(read_jsonl(root / (side + '.jsonl'))) for side in ('train', 'heldout')}


def assert_pins(manifest):
    for spec in manifest['artifacts'].values():
        verify_pin(spec)


def nonroom(root, side):
    with (root / (side + '.jsonl')).open('rb') as handle:
        return {json.loads(raw)['qid']: raw for raw in handle if json.loads(raw)['family'] != 'gtm_room_size'}


def trainer(root, expected):
    while root == NEW_TRAINER and not (root / 'MATERIALIZATION.json').exists():
        print('Waiting for the trainer materialization receipt.', flush=True)
        time.sleep(10)
    print('Checking trainer files: ' + str(root), flush=True)
    manifest = read_json(root / 'MATERIALIZATION.json')
    assert_pins(manifest)
    entries = list(read_jsonl(root / 'candidate_index.jsonl'))
    assert len(entries) == len(expected) == len(set(e['qid'] for e in entries))
    assert [e['qid'] for e in entries] == sorted(expected)
    def check_entry(entry):
        qid = entry['qid']
        row_path, target_path = Path(entry['row_path']), Path(entry['target_path'])
        assert row_path == root / 'targets' / qid / 'row.json'
        assert target_path == root / 'targets' / qid / 'target.txt'
        assert {item.name for item in os.scandir(row_path.parent)} == {'row.json', 'target.txt'}
        assert not row_path.is_symlink() and not target_path.is_symlink()
        row_raw, target_raw = row_path.read_bytes(), target_path.read_bytes()
        row_sha, target_sha = hashlib.sha256(row_raw).hexdigest(), hashlib.sha256(target_raw).hexdigest()
        assert row_sha == entry['row_sha256'] and target_sha == entry['sha256']
        row = json.loads(row_raw)
        assert row == expected[qid]
        assert target_raw == row['target'].encode()
        for key in ('qid', 'dataset', 'scene', 'generation_commit', 'config_sha256'):
            assert entry[key] == row[key]
        assert entry['question_type'] == row['category']
        if row.get('source') == 'gtmeasure_v1':
            assert entry['answer'] == str(row['ground_truth']['answer'])
            assert entry['validation_commit'] == row['generation_commit']
        return [(str(row_path.relative_to(root)), row_sha), (str(target_path.relative_to(root)), target_sha)]
    with ThreadPoolExecutor(max_workers=8) as executor:
        tree = [item for pair in executor.map(check_entry, entries) for item in pair]
    print('Verified every row and target hash: ' + str(root), flush=True)
    assert digest(sorted(tree)) == manifest['targets_tree_sha256']
    assert not (root / 'targets').is_symlink()
    actual_dirs = list(os.scandir(root / 'targets'))
    assert all(p.is_dir(follow_symlinks=False) for p in actual_dirs)
    assert {p.name for p in actual_dirs} == set(expected)
    assert (root / 'split.json').read_bytes() == (Path(manifest['source_mix']) / 'split.json').read_bytes()
    return {'index_sha256': sha(root / 'candidate_index.jsonl'), 'targets_tree_sha256': manifest['targets_tree_sha256'], 'rows': len(entries)}


def main():
    gt_before, gt_after, before, after = rows(OLD_GT), rows(NEW_GT), rows(OLD_MIX), rows(NEW_MIX)
    for root in (OLD_GT, NEW_GT, OLD_MIX, NEW_MIX):
        assert_pins(read_json(root / 'MANIFEST.json'))
    preserved = {}
    for side in ('train', 'heldout'):
        old, new = nonroom(OLD_GT, side), nonroom(NEW_GT, side)
        assert old == new
        assert list(old) == list(new)
        preserved[side] = {'rows': len(old), 'sha256': hashlib.sha256(b''.join(old.values())).hexdigest()}
    old_by_qid = {r['qid']: r for group in gt_before.values() for r in group}
    room = [r for group in gt_after.values() for r in group if r['family'] == 'gtm_room_size']
    wanted = {r['provenance']['room_label']['source_line'] for r in room}
    authority = read_json(NEW_GT / 'CONVENTIONS.json')['authorities']['vsi']
    verify_pin(authority)
    label_lines = {}
    with Path(authority['path']).open('rb') as handle:
        for number, raw in enumerate(handle, 1):
            if number in wanted:
                label_lines[number] = (json.loads(raw), hashlib.sha256(raw).hexdigest())
    ratios, changed, scalars = [], 0, []
    factors = {'square meters': Decimal(1), 'square feet': Decimal('0.09290304')}
    for row in room:
        parent = old_by_qid[row['qid']]
        assert all(row[k] == parent[k] for k in ('qid', 'dataset', 'scene', 'student_input', 'frame_index'))
        label = row['provenance']['room_label']
        source, source_sha = label_lines[label['source_line']]
        assert source_sha == label['source_line_sha256']
        assert source['video'] == row['dataset'] + '/' + row['scene'] + '.mp4'
        assert label['split_side'] == 'train'
        answer = next(t['value'] for t in source['conversations'] if t['from'] == 'gpt')
        question = next(t['value'] for t in source['conversations'] if t['from'] == 'human')
        unit, = [u for u in factors if u in question]
        value_si = Decimal(answer) * factors[unit]
        assert value_si == Decimal(label['value_si_decimal'])
        target_si = Decimal(row['ground_truth']['answer']) * factors[row['ground_truth']['units']]
        ratios.append(float(target_si / value_si))
        scalars.append(float(Decimal(str(row['ground_truth']['measurements'][0]['value_si'])) / value_si))
        changed += row['ground_truth']['answer'] != parent['ground_truth']['answer']
    policy = load_split(OLD_MIX / 'split.json')
    scene_sides = {}
    for side, group in before.items():
        for row in group:
            scene_sides[row['dataset'], row['scene']] = side
    for side, group in after.items():
        for row in group:
            assert scene_sides[row['dataset'], row['scene']] == side == policy.side(row['dataset'], row['scene'])
    compact = [r for group in before.values() for r in group if r.get('source') != 'gtmeasure_v1']
    replay_train, replay_heldout, replay_split, selection = mix_rows(compact, gt_after['train'] + gt_after['heldout'], policy, .5, 17)
    assert replay_train == after['train'] and replay_heldout == after['heldout']
    assert replay_split == read_json(NEW_MIX / 'split.json')
    assert selection == read_json(NEW_MIX / 'MANIFEST.json')['selection']
    assert [r['qid'] for r in before['train']] == [r['qid'] for r in after['train']]
    deferred = read_json(NEW_GT / 'ROOM_REPAIR.json')['deferred']
    removed = {r['qid'] for group in gt_before.values() for r in group} - {r['qid'] for group in gt_after.values() for r in group}
    assert removed == {r['qid'] for r in deferred}
    report = {'verdict': 'PASS', 'paths': {k: str(v) for k, v in {'old_corpus': OLD_GT, 'corpus': NEW_GT, 'old_mix': OLD_MIX, 'mix': NEW_MIX, 'old_trainer': OLD_TRAINER, 'trainer': NEW_TRAINER}.items()},
              'corpus_counts_before': {k: counts(v) for k, v in gt_before.items()},
              'corpus_counts_after': {k: counts(v) for k, v in gt_after.items()},
              'mix_counts_before': {k: counts(v) for k, v in before.items()},
              'mix_counts_after': {k: counts(v) for k, v in after.items()},
              'room_rows_corrected': len(room), 'room_answers_changed': changed,
              'room_rows_deferred': len(deferred), 'deferrals_by_reason': dict(Counter(r['reason'] for r in deferred)),
              'target_label_ratio_median': statistics.median(ratios), 'target_label_ratio_min': min(ratios), 'target_label_ratio_max': max(ratios),
              'scalar_label_ratio_median': statistics.median(scalars), 'nonroom_preservation': preserved,
              'split_stability': {'scenes_checked': len(scene_sides), 'moved_scenes': 0, 'train_qids_and_order_unchanged': True},
              'mix_replay': 'exact rows, order, split and selection', 'selection': selection,
              'trainer_before': trainer(OLD_TRAINER, {r['qid']: r for group in before.values() for r in group}),
              'trainer_after': trainer(NEW_TRAINER, {r['qid']: r for group in after.values() for r in group})}
    (OUT / 'VERIFICATION.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
