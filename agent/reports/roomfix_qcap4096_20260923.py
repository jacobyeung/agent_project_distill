"""Copy the corrected Set B mix with a Qwen assistant-token cap on training rows."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

WT = Path(__file__).resolve().parents[2]
RUN = WT.parents[1]
OUT = RUN / 'out_qcap'
TMP = RUN / 'tmp_qcap'
PILOT = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
SOURCE = PILOT / 'mix_v25_uncapped_gtm2_r050_roomfix_20260923'
SOURCE_TRAINER = PILOT / (SOURCE.name + '_trainer')
MIX = PILOT / 'mix_v25_uncapped_gtm2_r050_roomfix_qcap4096_20260923'
TRAINER = PILOT / (MIX.name + '_trainer')
CHECKOUT = RUN.parent / 'claude_orchard_setup_20260922T0700Z/work/dep_trainer_433d8a1'
SNAPSHOT = Path('/data2/jjyeung/cache/huggingface/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a')
CAP = 4096
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'
sys.path[:0] = [str(CHECKOUT), str(WT)]

from tools.gtmeasure.io import digest, pin, read_json, read_jsonl, sha, verify_pin


def write_json(path, value):
    with path.open('x') as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def write_jsonl(path, rows):
    with path.open('x') as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')


def step(number, text):
    with (OUT / f'STEP_{number}.md').open('x') as handle:
        handle.write(text + '\n')


def counts(rows):
    return {'rows': len(rows), 'by_family': dict(Counter(r.get('family', r['category']) for r in rows)),
            'by_source': dict(Counter(r.get('source', 'compact') for r in rows)),
            'by_dataset': dict(Counter(r['dataset'] for r in rows))}


def main():
    assert Path(os.environ['TMPDIR']).resolve() == TMP
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert os.environ.get('HF_HUB_OFFLINE') == '1'
    if MIX.exists() or TRAINER.exists():
        raise FileExistsError('Destination must be new; source and completed outputs are immutable')
    source_pins = [pin(p) for root in (SOURCE, SOURCE_TRAINER) for p in root.iterdir() if p.is_file()]
    before = {side: list(read_jsonl(SOURCE / (side + '.jsonl'))) for side in ('train', 'heldout')}
    original = {r['qid']: r for rows in before.values() for r in rows}
    assert len(original) == sum(map(len, before.values()))
    source_manifest = read_json(SOURCE / 'MANIFEST.json')
    source_materialization = read_json(SOURCE_TRAINER / 'MATERIALIZATION.json')
    for manifest in (source_manifest, source_materialization):
        for spec in manifest['artifacts'].values():
            verify_pin(spec)
    entries = list(read_jsonl(SOURCE_TRAINER / 'candidate_index.jsonl'))
    assert len(entries) == len(original) and {e['qid'] for e in entries} == set(original)
    print('Loading the offline Qwen processor and trainer formatter.', flush=True)
    from transformers import AutoProcessor
    import transformers
    from student_pilot.batches import training_text
    processor = AutoProcessor.from_pretrained(str(SNAPSHOT), local_files_only=True)
    token_records = []
    for side, rows in before.items():
        for position, row in enumerate(rows):
            inputs = row['student_input']
            prompt, suffix = training_text(processor, inputs['question'], inputs['options'], row['target'])
            ids = processor.tokenizer.encode(suffix, add_special_tokens=False)
            assert ids[-1] == processor.tokenizer.eos_token_id
            assert processor.tokenizer.decode(ids, skip_special_tokens=False) == suffix
            token_records.append({'qid': row['qid'], 'side': side, 'source_row_index': position,
                                  'type': row.get('family', row['category']), 'category': row['category'],
                                  'source': row.get('source', 'compact'), 'target_tokens_including_eos': len(ids),
                                  'target_sha256': hashlib.sha256(row['target'].encode()).hexdigest(),
                                  'assistant_suffix_sha256': hashlib.sha256(suffix.encode()).hexdigest(),
                                  'dropped': side == 'train' and len(ids) > CAP})
            if len(token_records) % 1000 == 0:
                print(f'Counted {len(token_records)}/{len(original)} targets.', flush=True)
    dropped = [r for r in token_records if r['dropped']]
    drop_qids = {r['qid'] for r in dropped}
    after = {'train': [r for r in before['train'] if r['qid'] not in drop_qids], 'heldout': before['heldout']}
    kept_records = [r for r in token_records if r['side'] == 'train' and not r['dropped']]
    policy = {'cap': CAP, 'comparison': 'drop training rows iff assistant tokens including EOS > cap',
              'formatter': pin(CHECKOUT / 'student_pilot/batches.py'), 'function': 'training_text',
              'encoding': 'processor.tokenizer.encode(suffix, add_special_tokens=False)',
              'scope': 'Training candidates only; held-out rows and both inherited split records retain their bytes.',
              'snapshot': str(SNAPSHOT), 'transformers_version': transformers.__version__,
              'processor_class': type(processor).__name__, 'tokenizer_class': type(processor.tokenizer).__name__,
              'eos_token': processor.tokenizer.eos_token, 'eos_token_id': processor.tokenizer.eos_token_id,
              'tokenizer_files': [pin(SNAPSHOT / name) for name in ('tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt', 'chat_template.jinja')],
              'training_rows_before': len(before['train']), 'training_rows_after': len(after['train']),
              'dropped_rows': len(dropped), 'dropped_by_type': dict(Counter(r['type'] for r in dropped)),
              'dropped_by_category': dict(Counter(r['category'] for r in dropped)),
              'dropped_by_source': dict(Counter(r['source'] for r in dropped)),
              'maximum_source_training_tokens': max(r['target_tokens_including_eos'] for r in token_records if r['side'] == 'train'),
              'maximum_remaining_training_tokens': max(r['target_tokens_including_eos'] for r in kept_records),
              'maximum_heldout_tokens': max(r['target_tokens_including_eos'] for r in token_records if r['side'] == 'heldout')}
    write_jsonl(OUT / 'TOKEN_COUNTS.jsonl', token_records)
    write_jsonl(OUT / 'DROPPED_ROWS.jsonl', dropped)
    write_json(OUT / 'CAP_POLICY.json', policy)
    step(2, f"The trainer formatter counted {len(token_records)} targets with the offline Qwen3.5-9B processor.\n"
         f"The cap removes {len(dropped)} training rows: {policy['dropped_by_type']}.\n"
         f"The remaining {len(after['train'])} training rows have at most {policy['maximum_remaining_training_tokens']} assistant tokens including EOS.\n"
         'TOKEN_COUNTS.jsonl records every source row; DROPPED_ROWS.jsonl records all exclusions; CAP_POLICY.json pins the formatter and tokenizer.')
    print(f"Dropping {len(dropped)} rows: {policy['dropped_by_type']}", flush=True)
    MIX.mkdir()
    TRAINER.mkdir()
    with (SOURCE / 'train.jsonl').open('rb') as source, (MIX / 'train.jsonl').open('xb') as dest:
        for raw in source:
            if json.loads(raw)['qid'] not in drop_qids:
                dest.write(raw)
    for name in ('heldout.jsonl', 'split.json', 'split_trainer.json'):
        shutil.copyfile(SOURCE / name, MIX / name)
    for root in (MIX, TRAINER):
        for name in ('TOKEN_COUNTS.jsonl', 'DROPPED_ROWS.jsonl', 'CAP_POLICY.json'):
            shutil.copyfile(OUT / name, root / name)
    for name in ('split.json', 'split_trainer.json'):
        shutil.copyfile(SOURCE / name, TRAINER / name)
    target_root = TRAINER / 'targets'
    target_root.mkdir()

    def copy_entry(entry):
        qid = entry['qid']
        new = dict(entry)
        directory = target_root / qid
        directory.mkdir()
        for key, hash_key, filename in [('row_path', 'row_sha256', 'row.json'), ('target_path', 'sha256', 'target.txt')]:
            path = Path(entry[key])
            assert path == SOURCE_TRAINER / 'targets' / qid / filename and not path.is_symlink()
            assert sha(path) == entry[hash_key]
            shutil.copyfile(path, directory / filename)
            assert sha(directory / filename) == entry[hash_key]
            new[key] = str(directory / filename)
        assert read_json(directory / 'row.json') == original[qid]
        assert (directory / 'target.txt').read_bytes() == original[qid]['target'].encode()
        return new

    retained_entries = [e for e in entries if e['qid'] not in drop_qids]
    with ThreadPoolExecutor(max_workers=8) as executor:
        new_entries = list(executor.map(copy_entry, retained_entries))
    write_jsonl(TRAINER / 'candidate_index.jsonl', new_entries)
    tree = digest(sorted((str(Path(e[key]).relative_to(TRAINER)), e[hash_key]) for e in new_entries
                         for key, hash_key in [('row_path', 'row_sha256'), ('target_path', 'sha256')]))
    new_manifest = dict(source_manifest)
    new_manifest.update({'parent_manifest': pin(SOURCE / 'MANIFEST.json'), 'length_cap': policy,
                         'counts': {side: counts(rows) for side, rows in after.items()},
                         'source_selection': source_manifest['selection'],
                         'selection': {'rule': 'retain source training rows in order iff formatted assistant tokens including EOS <= 4096',
                                       'selected': counts(after['train'])['by_source'],
                                       'excluded_by_length_cap': policy['dropped_by_source'],
                                       'actual_gt_fraction': sum(r.get('source') == 'gtmeasure_v1' for r in after['train']) / len(after['train'])},
                         'config': {**source_manifest['config'], 'length_cap': policy},
                         'split_record_semantics': 'Inherited membership authority, not a list of post-cap training rows; use train.jsonl and the filtered candidate index.'})
    new_manifest['config_sha256'] = digest(new_manifest['config'])
    new_manifest['split_census'] = {**source_manifest['split_census'], 'train_rows': len(after['train'])}
    new_manifest['artifacts'] = {name: pin(MIX / name) for name in ('train.jsonl', 'heldout.jsonl', 'split.json', 'split_trainer.json', 'TOKEN_COUNTS.jsonl', 'DROPPED_ROWS.jsonl', 'CAP_POLICY.json')}
    for side in after:
        new_manifest['artifacts'][side + '.jsonl']['rows'] = len(after[side])
    write_json(MIX / 'MANIFEST.json', new_manifest)
    materialization = {**source_materialization, 'set': 'uncapped-B-recipe-roomfix-qcap4096', 'source_mix': str(MIX),
                       'parent_materialization': pin(SOURCE_TRAINER / 'MATERIALIZATION.json'), 'length_cap': policy,
                       'counts': {'train': len(after['train']), 'heldout': len(after['heldout']), 'candidate_index': len(new_entries),
                                  'targets': dict(Counter('gtmeasure' if original[e['qid']].get('source') == 'gtmeasure_v1' else 'compact' for e in new_entries))},
                       'reconciliation': {'index_rows': len(new_entries), 'target_directories': len(new_entries),
                                          'train_plus_heldout': sum(map(len, after.values()))},
                       'artifacts': {name: pin(TRAINER / name) for name in ('candidate_index.jsonl', 'split.json', 'split_trainer.json', 'TOKEN_COUNTS.jsonl', 'DROPPED_ROWS.jsonl', 'CAP_POLICY.json')},
                       'targets_tree_sha256': tree, 'split_record_semantics': new_manifest['split_record_semantics']}
    materialization['artifacts']['candidate_index.jsonl']['rows'] = len(new_entries)
    write_json(TRAINER / 'MATERIALIZATION.json', materialization)
    step(3, f"The capped mix is {MIX}.\nThe capped trainer layout is {TRAINER}.\n"
         f"The layout contains {len(new_entries)} candidates: {len(after['train'])} training and {len(after['heldout'])} held-out rows.\n"
         'Each copied row and target matches its source hash. Both split records retain their source bytes.\n'
         f"The candidate index SHA-256 is {sha(TRAINER / 'candidate_index.jsonl')}.\nThe targets-tree SHA-256 is {tree}.")
    print('Copies complete; verifying the trainer loader and split stability.', flush=True)
    verify(after, before, entries, new_entries, token_records, drop_qids, source_pins, policy, tree)


def verify(after, before, entries, new_entries, token_records, drop_qids, source_pins, policy, tree):
    from student_pilot.provisional import load_provisional_candidates, load_inherited_record
    from student_pilot.split import make_inherited_split, physical_group
    for root in (MIX, TRAINER):
        for name in ('split.json', 'split_trainer.json'):
            assert (root / name).read_bytes() == (SOURCE / name).read_bytes()
    assert (MIX / 'heldout.jsonl').read_bytes() == (SOURCE / 'heldout.jsonl').read_bytes()
    with (SOURCE / 'train.jsonl').open('rb') as handle:
        expected_bytes = b''.join(raw for raw in handle if json.loads(raw)['qid'] not in drop_qids)
    assert (MIX / 'train.jsonl').read_bytes() == expected_bytes
    assert [e['qid'] for e in new_entries] == [e['qid'] for e in entries if e['qid'] not in drop_qids]
    assert {p.name for p in (TRAINER / 'targets').iterdir()} == {e['qid'] for e in new_entries}
    for root, filename in ((MIX, 'MANIFEST.json'), (TRAINER, 'MATERIALIZATION.json')):
        for spec in read_json(root / filename)['artifacts'].values():
            verify_pin(spec)
    print('Calling load_provisional_candidates with all original RGB hash checks enabled.', flush=True)
    loaded = load_provisional_candidates(TRAINER / 'candidate_index.jsonl', LABEL)
    assert len(loaded) == len(new_entries)
    expected = {r['qid']: r for rows in after.values() for r in rows}
    assert {r['qid'] for r in loaded} == set(expected)
    for row in loaded:
        assert row['target'] == expected[row['qid']]['target']
        assert row['student_input'] == expected[row['qid']]['student_input']
    inherited = load_inherited_record({'path': str(MIX / 'split_trainer.json'), 'sha256': sha(MIX / 'split_trainer.json')})
    derived = make_inherited_split(loaded, loaded, inherited, seed=17, heldout_fraction=0.1)
    assert derived['train_candidate_qids'] == sorted(r['qid'] for r in after['train'])
    assert derived['heldout_qids'] == sorted(r['qid'] for r in after['heldout'])
    assert derived['hashed_group_count'] == 0
    old_sides = {(r['dataset'], r['scene']): side for side, rows in before.items() for r in rows}
    assert all(old_sides[r['dataset'], r['scene']] == side for side, rows in after.items() for r in rows)
    source_groups = {physical_group(r['dataset'], r['scene']) for rows in before.values() for r in rows}
    assert derived['donor_group_count'] == len(source_groups)
    lengths = {r['qid']: r['target_tokens_including_eos'] for r in token_records}
    assert all(lengths[qid] <= CAP for qid in derived['train_candidate_qids'])
    assert not set(derived['train_candidate_qids']) & drop_qids
    for spec in source_pins:
        verify_pin(spec)
    receipt = {'verdict': 'PASS', 'paths': {name: str(path) for name, path in {
        'source_mix': SOURCE, 'source_trainer': SOURCE_TRAINER, 'mix': MIX, 'trainer': TRAINER,
        'trainer_checkout': CHECKOUT, 'tokenizer_snapshot': SNAPSHOT, 'out': OUT, 'tmp': TMP,
        'script': Path(__file__).resolve()}.items()},
        'cap': policy, 'counts_before': {side: counts(rows) for side, rows in before.items()},
        'counts_after': {side: counts(rows) for side, rows in after.items()},
        'loader': {'function': 'load_provisional_candidates', 'rows': len(loaded), 'rgb_hash_checks': 'unmodified',
                   'code': pin(CHECKOUT / 'student_pilot/provisional.py'), 'label': LABEL},
        'split_stability': {'scenes_checked': len(old_sides), 'physical_groups': len(source_groups), 'moved_scenes': 0,
                            'hashed_group_count': 0, 'split_files_byte_identical': True,
                            'code': pin(CHECKOUT / 'student_pilot/split.py')},
        'preservation': {'heldout_byte_identical': True, 'retained_train_bytes_and_order_identical': True,
                         'retained_candidate_order_identical': True, 'row_and_target_hashes_identical': True,
                         'source_top_level_pins_unchanged': source_pins},
        'candidate_index_sha256': sha(TRAINER / 'candidate_index.jsonl'), 'targets_tree_sha256': tree,
        'artifacts': {str(root): {p.name: pin(p) for p in root.iterdir() if p.is_file()} for root in (MIX, TRAINER)},
        'script': pin(Path(__file__).resolve()), 'training_launched': False}
    write_json(OUT / 'VERIFICATION.json', receipt)
    write_json(WT / 'agent/reports/roomfix_qcap4096_20260923_manifest.json', receipt)
    step(4, f"PASS: the unmodified trainer loader accepted all {len(loaded)} candidates and checked their RGB hashes.\n"
         f"The inherited split yields exactly {len(after['train'])} training and {len(after['heldout'])} held-out qids.\n"
         f"All {len(old_sides)} scenes and {len(source_groups)} physical groups preserve their sides, with zero newly hashed groups.\n"
         'Every retained row and target is byte-identical; both split records are byte-identical; source pins are unchanged.\n'
         'VERIFICATION.json and agent/reports/roomfix_qcap4096_20260923_manifest.json record the paths and artifact hashes.\n'
         'No training was launched. No borderline historical prose was retained.')
    print(json.dumps({'verdict': 'PASS', 'train': len(after['train']), 'heldout': len(after['heldout']),
                      'dropped': len(drop_qids), 'max_tokens': policy['maximum_remaining_training_tokens'],
                      'index_sha256': receipt['candidate_index_sha256'], 'targets_tree_sha256': tree}), flush=True)


if __name__ == '__main__':
    main()
