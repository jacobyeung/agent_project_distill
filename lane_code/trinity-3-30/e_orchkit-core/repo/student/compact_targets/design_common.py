import argparse
import copy
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from . import compact_control as control
from . import compact_counted_v1 as compact


P = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918')
S = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
D = P / 'claude_target_design_astra_20260923T0820Z'
H = P / 'claude_iteration_harness_20260923T0830Z'
TRAINER = P / 'claude_onethinker_v241_launch_20260921T0015Z/work_checkout_b084aaf'
TRAINER_COMMIT = 'b084aafe6605a18112160773d6e7436677f3947d'
PYTHON = S / 'venv/bin/python'
REFERENCE = P / 'claude_student_launch_20260922T0515Z/onethinker_armc_answeronly'
EVAL_SHA = '38ccb7aa999e894bd96ef1ae79d3037d3b67e12a46d1b06727b7568403677f87'
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'
QUOTAS = {'object_rel_direction_medium': 300, 'object_counting': 100, 'obj_appearance_order': 100,
          'gtm_object_count': 100, 'gtm_object_size': 100, 'gtm_room_size': 100,
          'gtm_object_distance': 100, 'gtm_camera_object_distance': 100}
VARIANTS = {'a0': 'a0_design_v1_s17', 'c0': 'c0_design_v1_s17'}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def input_digest(inputs):
    return digest(json.dumps(inputs, sort_keys=True, separators=(',', ':')))


def input_fingerprint(inputs):
    projected = {**inputs, 'frames': [frame['sha256'] for frame in inputs['frames']]}
    return input_digest(projected)


def check_target(target, answer, count_tokens, bounded=True):
    control.require(isinstance(answer, str) and answer and answer == answer.strip()
                    and '\n' not in answer and '\r' not in answer, 'common_answer_schema')
    control.require(isinstance(target, str) and target.count(compact.MARKER) == 1, 'closing_marker')
    control.require(target.endswith('\n' + compact.MARKER + '\n' + answer)
                    and target.splitlines()[-2:] == [compact.MARKER, answer], 'terminal_answer')
    tokens = count_tokens(target)
    control.require(type(tokens) is int and tokens > 0, 'target_token_count')
    control.require(not bounded or tokens <= compact.MAX_TOKENS, 'target_token_limit')
    return tokens


def admit_identity(record, row, answer, corrected_row=None, corrected_answer=None, count_tokens=None):
    for key in ('qid', 'scene', 'dataset'):
        control.require(record[key] == row[key], f'common_identity: {key}')
    category = record.get('category', record['family'])
    control.require(category == row['category'], 'common_identity: category')
    control.require(record['answer'] == answer, 'common_answer: proposed')
    if corrected_row is not None:
        control.require(corrected_answer == answer, 'common_answer: corrected')
        control.require(all(corrected_row[key] == row[key] for key in ('qid', 'scene', 'dataset', 'category')),
                        'common_identity: corrected')
        control.require(corrected_row['student_input'] == row['student_input'], 'common_input: corrected')
        check_target(corrected_row['target'], answer, count_tokens, bounded=False)
    else:
        control.require(row.get('source') == 'gtmeasure_v1' and row.get('family') == record['family'],
                        'gtm_source_schema')
        control.require(row['ground_truth']['answer'] == answer, 'common_answer: gtmeasure')
        control.require(all(row['checks'].get(key) is True for key in ('counted_layout', 'numeric_tokens', 'terminal_answer')),
                        'gtm_source_checks')
    control.require(record['input_sha256'] == input_digest(row['student_input']), 'common_input_sha256')
    control.validate_rgb(row['student_input'])
    return check_target(row['target'], answer, count_tokens)


def duplicate_refusals(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['input_fingerprint']].append(row)
    refused = {}
    for members in groups.values():
        if len({row['answer'] for row in members}) > 1:
            refused.update({row['qid']: 'duplicate_answer_conflict' for row in members})
        else:
            refused.update({row['qid']: 'duplicate_input' for row in members[1:]})
    return refused


def balanced_order(rows, prefix):
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        groups[row.get('stratum', row.get('category', ''))][row['scene']].append(row)
    ordered = {}
    for key, scenes in groups.items():
        queues = [sorted(scenes[scene], key=lambda row: digest(prefix + '|qid|' + row['qid']))
                  for scene in sorted(scenes, key=lambda scene: digest(prefix + '|scene|' + scene))]
        merged = []
        while any(queues):
            for queue in queues:
                if queue:
                    merged.append(queue.pop(0))
        ordered[key] = merged
    result = []
    while any(ordered.values()):
        for key in sorted(ordered):
            if ordered[key]:
                result.append(ordered[key].pop(0))
    return result


def replacement_order(failed, pool, unavailable):
    candidates = [row for row in pool if row['family'] == failed['family'] and row['qid'] not in unavailable]
    ordered = balanced_order(candidates, 'train-design-v1|' + failed['family'])
    stratum = failed.get('stratum', failed.get('category', ''))
    return sorted(ordered, key=lambda row: row.get('stratum', row.get('category', '')) != stratum)


def check_native_manifest(manifest, qids):
    control.require(not manifest['pre_evaluation_drops'], 'native_token_drops')
    expected = sorted(qids)
    control.require([row['qid'] for row in manifest['rows']] == expected
                    and manifest['accepted_before_token_limits'] == len(qids), 'native_training_membership')
    control.require([audit['qid'] for audit in manifest['input_audits']] == expected, 'native_audit_membership')
    control.require(all(audit['assistant_tokens_including_eos'] > 0 for audit in manifest['input_audits']),
                    'native_assistant_eos')


def gtm_entry(row):
    return {'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
            'question_type': row['category'], 'answer': str(row['ground_truth']['answer']),
            'pool': row['source'], 'family': row['family'], 'config_sha256': row['config_sha256'],
            'generation_commit': row['generation_commit'], 'validation_commit': row['generation_commit']}


def read_gt(path):
    rows, raw = {}, {}
    with compact.safe_path(path).open('rb') as stream:
        for line in stream:
            if not line.strip():
                continue
            row = compact.decode_json(line)
            qid = compact.safe_qid(row['qid'])
            control.require(qid not in rows, f'duplicate_qid: {qid}')
            rows[qid], raw[qid] = row, line
    return rows, raw


def evaluation_contract():
    evaluation_pin = compact.binding(D / 'EVAL_QIDS.json')
    control.require(evaluation_pin['sha256'] == EVAL_SHA, 'design_evaluation_sha256')
    evaluation = compact.load_json(evaluation_pin['path'])
    qids, groups, pins = control.evaluation_exclusions([
        H / 'eval_subsets/vsibench_answerable500_s20260923_200.json',
        H / 'eval_subsets/vstibench_repr450_v2_s20260923_150.json',
    ])
    for benchmark, size in (('vsibench_answerable500', 200), ('vstibench_repr450_v2', 150)):
        rows = evaluation['benchmarks'][benchmark]
        control.require(len(rows) == len({row['qid'] for row in rows}) == size, 'design_evaluation_size')
        control.require({row['qid'] for row in rows} <= qids, 'design_evaluation_membership')
        for row in rows:
            control.require(control.scene_group(*row['scene'].split('/', 1)) in groups, 'design_evaluation_scene')
    return evaluation_pin, qids, groups, pins


class Sources:
    def __init__(self, proposed, count_tokens):
        self.proposed = proposed
        self.count_tokens = count_tokens
        arm_pin, corrected_pin, gt_pin, split_pin = proposed['sources']
        for pin in proposed['sources']:
            control.checked_bytes(pin)
        self.arm = control.identities(compact.load_jsonl(arm_pin['path']))
        self.corrected = control.identities(compact.load_jsonl(corrected_pin['path']))
        self.gt, self.gt_raw = read_gt(gt_pin['path'])
        self.gt_pin = gt_pin
        self.split = control.checked_json(split_pin)
        manifest_path = Path(gt_pin['path']).parent / 'MANIFEST.json'
        gt_manifest = compact.load_json(manifest_path)
        self.gt_manifest_pin = compact.binding(manifest_path)
        control.require(gt_manifest['artifacts']['train.jsonl']['sha256'] == gt_pin['sha256'], 'gtm_train_manifest')
        heldout_pin = gt_manifest['artifacts']['heldout.jsonl']
        control.checked_bytes(heldout_pin)
        self.gt_heldout, self.gt_heldout_raw = read_gt(heldout_pin['path'])
        self.gt_heldout_pin = heldout_pin
        self.heldout = set(self.split['heldout_qids']) | set(self.gt_heldout)
        self.train_groups = control.normalized_groups(self.split['train_group_ids'])
        self.heldout_groups = control.normalized_groups(self.split['heldout_group_ids'])
        control.require(not self.train_groups & self.heldout_groups, 'published_scene_sides_conflict')
        self.eval_pin, self.eval_qids, self.eval_groups, self.eval_pins = evaluation_contract()
        self.frames = set()
        self.cache = {}

    def teacher_record(self, qid):
        entry = self.arm[qid]
        corrected = self.corrected[qid]
        row, _, _ = control.bundle(corrected)
        options, answer = row['student_input']['options'], corrected['answer']
        semantic = options[ord(answer) - 65] if options and len(answer) == 1 else answer
        return {'qid': qid, 'scene': entry['scene'], 'dataset': entry['dataset'],
                'family': entry['question_type'], 'stratum': f'{len(options)}|{semantic}' if options else 'count',
                'v25_row_path': corrected['row_path'], 'v1c_row_path': entry['row_path'],
                'answer': answer, 'input_sha256': input_digest(row['student_input']),
                'trace25': int(digest('trace25-v1|' + qid), 16) % 4 == 0}

    def pool(self):
        rows = []
        for qid in sorted(set(self.arm) & set(self.corrected) & set(self.split['train_candidate_qids'])):
            if self.arm[qid]['question_type'] in QUOTAS:
                rows.append(self.teacher_record(qid))
        for row in self.gt.values():
            if self.count_tokens(row['target']) <= compact.MAX_TOKENS:
                qid = row['qid']
                rows.append({'qid': qid, 'scene': row['scene'], 'dataset': row['dataset'], 'family': row['family'],
                             'category': row['category'], 'answer': row['ground_truth']['answer'],
                             'gtm_source_path': self.gt_pin['path'], 'input_sha256': input_digest(row['student_input']),
                             'trace25': int(digest('trace25-v1|' + qid), 16) % 4 == 0})
        return rows

    def admit(self, record):
        qid = record['qid']
        if qid in self.cache:
            return self.cache[qid]
        group = control.scene_group(record['dataset'], record['scene'])
        control.require(qid not in self.heldout, f'heldout_qid: {qid}')
        control.require(qid not in self.eval_qids, f'evaluation_qid: {qid}')
        control.require(group not in self.heldout_groups and group in self.train_groups, f'published_train_scene: {qid}')
        control.require(group not in self.eval_groups, f'evaluation_scene: {qid}: {group}')
        if 'v1c_row_path' in record:
            entry, corrected = self.arm[qid], self.corrected[qid]
            control.require(qid in self.split['train_candidate_qids'], f'teacher_not_published_train: {qid}')
            control.require(entry['row_path'] == record['v1c_row_path'] and corrected['row_path'] == record['v25_row_path'],
                            f'proposed_row_path: {qid}')
            row, row_bytes, target_bytes = control.bundle(entry)
            corrected_row, _, _ = control.bundle(corrected)
            for source in (entry, corrected):
                control.require(source['tier_i']['all_deterministic_checks_satisfied'] is True,
                                f'reviewed_source_checks: {qid}')
                for row_key, entry_key in compact.ROW_ALIGNED_FIELDS:
                    bound_row = row if source is entry else corrected_row
                    control.require(bound_row.get(row_key) == source.get(entry_key), f'source_row_identity: {qid}: {row_key}')
            tokens = admit_identity(record, row, entry['answer'], corrected_row, corrected['answer'], self.count_tokens)
            pins = {'v1c_row': {'path': entry['row_path'], 'sha256': entry['row_sha256']},
                    'v1c_target': {'path': entry['target_path'], 'sha256': entry['sha256']},
                    'v25_row': {'path': corrected['row_path'], 'sha256': corrected['row_sha256']},
                    'v25_target': {'path': corrected['target_path'], 'sha256': corrected['sha256']}}
        else:
            control.require(record['gtm_source_path'] == self.gt_pin['path'], f'gtm_source_path: {qid}')
            row, row_bytes = self.gt[qid], self.gt_raw[qid]
            entry, target_bytes = gtm_entry(row), row['target'].encode('utf-8')
            tokens = admit_identity(record, row, entry['answer'], count_tokens=self.count_tokens)
            pins = {'gtm_jsonl': self.gt_pin, 'gtm_row_sha256': compact.sha256_bytes(row_bytes)}
        control.require(target_bytes in (row['target'].encode('utf-8'), (row['target'] + '\n').encode('utf-8')),
                        f'target_row_bytes: {qid}')
        for frame in row['student_input']['frames']:
            control.frame_check(frame, self.frames)
        details = {'qid': qid, 'family': record['family'], 'question_type': row['category'],
                   'answer': entry['answer'], 'input_sha256': input_digest(row['student_input']),
                   'input_fingerprint': input_fingerprint(row['student_input']), 'physical_scene_group': group,
                   'target_tokens': tokens, 'answer_tokens': self.count_tokens(entry['answer']),
                   'source_pins': pins, 'semantic_status': control.SEMANTIC_STATUS, 'claims_new_derivation': False}
        self.cache[qid] = (row, row_bytes, target_bytes, entry, details)
        return self.cache[qid]

    def context(self):
        result, groups = [], set()
        for qid, entry in sorted(self.corrected.items()):
            group = control.scene_group(entry['dataset'], entry['scene'])
            if group in self.heldout_groups and group not in groups:
                row, row_bytes, target_bytes = control.bundle(entry)
                result.append((row, row_bytes, target_bytes, entry))
                groups.add(group)
        for qid, row in sorted(self.gt_heldout.items()):
            group = control.scene_group(row['dataset'], row['scene'])
            if group in self.heldout_groups and group not in groups:
                result.append((row, self.gt_heldout_raw[qid], row['target'].encode('utf-8'), gtm_entry(row)))
                groups.add(group)
        control.require(groups == self.heldout_groups, 'heldout_context_group_coverage')
        return result


def emit_pair(source, output):
    row, row_bytes, target_bytes, entry, _ = source
    compact_entry = control.copy_entry(entry, row_bytes, target_bytes, output / VARIANTS['c0'])
    answer_row = {**row, 'target': entry['answer']}
    answer_entry = control.copy_entry(entry, compact.canonical_bytes(answer_row),
                                     (entry['answer'] + '\n').encode('utf-8'), output / VARIANTS['a0'])
    return answer_entry, compact_entry


def restricted_split(published, qids, source_split, source_proposed, code):
    result = copy.deepcopy(published)
    result.update(schema='provisional-whole-scene-split-v1', train_candidate_qids=qids,
                  source_split=source_split, source_proposed=source_proposed)
    split_content = {key: value for key, value in result.items()
                     if key not in ('provenance', 'PROVISIONAL_SPLIT_SHA', 'SPLIT_SHA')}
    for key in ('PROVISIONAL_SPLIT_SHA', 'SPLIT_SHA'):
        if key in result:
            result[key] = compact.digest_json(split_content)
    content = {key: value for key, value in result.items() if key != 'provenance'}
    result['provenance'] = {'config_sha256': compact.digest_json(content),
                            'emitted_by': 'student/compact_targets/design_common.py',
                            'git_commit': code['commit'], 'source_provenance': published.get('provenance')}
    return result


def save_split(args, split):
    path = args.common / 'split_trainer.json'
    if path.exists() and path.read_bytes() != compact.canonical_bytes(split):
        control.require(args.repair_unfrozen_split and not (args.common / 'COMMON_DONE').exists(),
                        'common_split_already_exists')
        previous = compact.load_json(path)
        old_content = {key: value for key, value in previous.items() if key != 'provenance'}
        new_content = {key: value for key, value in split.items() if key != 'provenance'}
        control.require(old_content == new_content, 'split_repair_may_only_reseal_provenance')
        control.require(previous['provenance']['config_sha256'] != compact.digest_json(old_content),
                        'split_repair_requires_reproduced_stale_hash')
        archived = args.stage / 'previous_unfrozen_split.json'
        control.require(not archived.exists(), 'split_repair_archive_exists')
        before = compact.binding(path)
        path.rename(archived)
        compact.save(args.stage / 'SPLIT_REPAIR.json', {'reason': 'native gate rejected stale embedded content hash',
                     'before': before, 'preserved_at': compact.binding(archived),
                     'membership_and_scene_sides_unchanged': True})
    compact.save(path, split)


def build(args):
    code = {**control.provenance(), 'common_module': compact.binding(__file__)}
    proposed = compact.load_json(args.proposed)
    control.require(len(proposed['rows']) == len({row['qid'] for row in proposed['rows']}) == 1000, 'proposed_membership_size')
    control.require(dict(Counter(row['family'] for row in proposed['rows'])) == QUOTAS, 'proposed_family_quotas')
    count_tokens, tokenizer_pins = compact.tokenizer_counter(compact.TOKENIZER)
    sources = Sources(proposed, count_tokens)
    selected = copy.deepcopy(proposed['rows'])
    refused, replacements, unavailable = [], [], {row['qid'] for row in selected}
    external_refusals = compact.load_json(args.refusals) if args.refusals else {}
    pool = None
    while True:
        failures, audits = {}, []
        for record in selected:
            qid = record['qid']
            try:
                control.require(qid not in external_refusals, f'native_sequence_refusal: {external_refusals.get(qid)}')
                audits.append(sources.admit(record)[-1])
            except (ValueError, KeyError, OSError, compact.Deferral) as error:
                failures[qid] = str(error)
        failures.update(duplicate_refusals(audits))
        if not failures:
            break
        if pool is None:
            pool = sources.pool()
        fingerprints = {row['input_fingerprint'] for row in audits
                        if row['qid'] not in failures or failures[row['qid']] == 'duplicate_answer_conflict'}
        for index, record in enumerate(selected):
            if record['qid'] not in failures:
                continue
            refused.append({'qid': record['qid'], 'reason': failures[record['qid']], 'family': record['family']})
            for candidate in replacement_order(record, pool, unavailable):
                unavailable.add(candidate['qid'])
                try:
                    audit = sources.admit(candidate)[-1]
                    control.require(audit['input_fingerprint'] not in fingerprints, 'replacement_duplicate_input')
                    control.require(candidate['qid'] not in external_refusals, 'replacement_native_refusal')
                except (ValueError, KeyError, OSError, compact.Deferral) as error:
                    refused.append({'qid': candidate['qid'], 'reason': str(error), 'family': candidate['family']})
                    continue
                selected[index] = candidate
                fingerprints.add(audit['input_fingerprint'])
                replacements.append({'old_qid': record['qid'], 'new_qid': candidate['qid'],
                                     'family': record['family'], 'reason': failures[record['qid']]})
                break
            else:
                compact.save(args.stage / 'REFUSALS.jsonl', control.jsonl(refused))
                raise ValueError(f'common_stratum_exhausted: {record["qid"]}')
    control.require(dict(Counter(row['family'] for row in selected)) == QUOTAS, 'final_family_quotas')
    qids = [record['qid'] for record in selected]
    control.require(len(qids) == len(set(qids)) == 1000, 'final_common_membership')
    a0, c0, audit = [], [], []
    for index, record in enumerate(selected, 1):
        source = sources.admit(record)
        answer_entry, compact_entry = emit_pair(source, args.sets)
        a0.append(answer_entry)
        c0.append(compact_entry)
        audit.append({**source[-1], 'a0_row': {'path': answer_entry['row_path'], 'sha256': answer_entry['row_sha256']},
                      'a0_target': {'path': answer_entry['target_path'], 'sha256': answer_entry['sha256']},
                      'c0_row': {'path': compact_entry['row_path'], 'sha256': compact_entry['row_sha256']},
                      'c0_target': {'path': compact_entry['target_path'], 'sha256': compact_entry['sha256']}})
        if index % 100 == 0:
            print(json.dumps({'materialized': index, 'replacements': len(replacements)}), flush=True)
    context = []
    for row, row_bytes, target_bytes, entry in sources.context():
        context.append(control.copy_entry(entry, row_bytes, target_bytes, args.stage / 'heldout_context'))
    split = restricted_split(sources.split, qids, proposed['sources'][3], compact.binding(args.proposed), code)
    save_split(args, split)
    candidate_pins = {}
    for variant, entries in (('a0', a0), ('c0', c0)):
        root = args.sets / VARIANTS[variant]
        candidate_pins[variant] = compact.save(root / 'candidate_index.jsonl', control.jsonl(entries))
        compact.save(root / 'split_trainer.json', split)
        compact.save(args.stage / variant / 'protocol_context/candidate_index.jsonl', control.jsonl(entries + context))
    compact.save(args.stage / 'SOURCE_AUDIT.jsonl', control.jsonl(audit))
    compact.save(args.stage / 'REFUSALS.jsonl', control.jsonl(refused))
    compact.save(args.stage / 'REPLACEMENTS.json', replacements)
    chosen = []
    for family in QUOTAS:
        chosen.append(next(row['qid'] for row in selected if row['family'] == family))
    for stratum in ('2|left', '2|right', '3|back', '4|front-left', '4|back-right'):
        match = next((row['qid'] for row in selected if row.get('stratum') == stratum), None)
        if match and match not in chosen:
            chosen.append(match)
    for item in sorted(audit, key=lambda row: (-row['target_tokens'], row['qid'])):
        if item['qid'] not in chosen and len(chosen) < 16:
            chosen.append(item['qid'])
    samples = []
    for qid in chosen:
        record = next(row for row in selected if row['qid'] == qid)
        row, _, _, entry, details = sources.admit(record)
        samples.append({'qid': qid, 'family': record['family'], 'record': record,
                        'question': row['student_input']['question'], 'options': row['student_input']['options'],
                        'answer': entry['answer'], 'c0_target': row['target'], 'a0_target': entry['answer'],
                        'audit': details})
    compact.save(args.stage / 'HANDCHECK_SAMPLE.json', samples)
    report = {'source_admitted': 1000, 'source_refusals': len(refused), 'replacements': len(replacements),
              'counts_by_family': dict(Counter(row['family'] for row in selected)),
              'control_target_tokens': {'p50': control.percentile([row['target_tokens'] for row in audit], .5),
                                        'p95': control.percentile([row['target_tokens'] for row in audit], .95),
                                        'max': max(row['target_tokens'] for row in audit)},
              'answer_target_tokens': {'p50': control.percentile([row['answer_tokens'] for row in audit], .5),
                                       'p95': control.percentile([row['answer_tokens'] for row in audit], .95),
                                       'max': max(row['answer_tokens'] for row in audit)},
              'unique_frame_files_verified': len(sources.frames), 'heldout_context_rows': len(context),
              'heldout_context_qids': [row['qid'] for row in context],
              'source_hashes_verified': True, 'answer_agreement': True, 'duplicate_inputs': 0,
              'evaluation_qid_overlap': 0, 'evaluation_scene_overlap': 0, 'heldout_overlap': 0,
              'semantic_status': control.SEMANTIC_STATUS, 'gemini_tokens': 0,
              'native_sequence_admission': 'pending; COMMON_DONE has not been published'}
    compact.save(args.stage / 'SOURCE_ADMISSION.json', report)
    common = {**proposed, 'schema': 'swarm-common-training-v1', 'status': 'FROZEN_AFTER_COMMON_ADMISSION',
              'pool_id': 'design_v1', 'n': 1000, 'rows': selected, 'qids': qids,
              'native_training_qid_order': sorted(qids), 'proposed': compact.binding(args.proposed),
              'evaluation': sources.eval_pin, 'candidate_indices': candidate_pins,
              'split': compact.binding(args.common / 'split_trainer.json'),
              'source_audit': compact.binding(args.stage / 'SOURCE_AUDIT.jsonl'),
              'source_admission': compact.binding(args.stage / 'SOURCE_ADMISSION.json'),
              'replacements': compact.binding(args.stage / 'REPLACEMENTS.json'),
              'code': code, 'tokenizer': tokenizer_pins,
              'gtm_manifest': sources.gt_manifest_pin, 'gtm_heldout': sources.gt_heldout_pin,
              'evaluation_exclusion_sources': sources.eval_pins}
    compact.save(args.stage / 'TRAIN_1000.pending.json', common)
    compact.save(args.stage / 'BUILD.json', {'common': str(args.common), 'sets': str(args.sets),
                 'candidates': candidate_pins, 'proposed': compact.binding(args.proposed), 'code': code})
    print(json.dumps(report, indent=2), flush=True)
    return 0


def trainer_checkout():
    require_commit = subprocess.check_output(['git', '-C', str(TRAINER), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(TRAINER), 'status', '--short'], text=True).strip()
    control.require(require_commit == TRAINER_COMMIT and not dirty, 'native_trainer_checkout')


def native(args):
    trainer_checkout()
    stage = args.stage
    config = compact.load_json(stage / 'BUILD.json')
    recipe = compact.load_json(REFERENCE / 'work/training_config_armc_answeronly.json')
    control.require(recipe['seed'] == 17 and recipe['world_size'] == 2, 'matched_training_recipe')
    root = stage / args.variant
    compact.save(root / 'training_config.json', recipe)
    protocol, training = root / 'protocol.json', root / 'training.json'
    commands = [
        (protocol, ['prepare-protocol', '--candidate-index', root / 'protocol_context/candidate_index.jsonl',
                    '--student', 'onethinker', '--holdout-fraction', '0.1', '--inherit-split',
                    Path(config['common']) / 'split_trainer.json', '--training-config', root / 'training_config.json',
                    '--output', protocol]),
        (training, ['prepare-training', '--protocol', protocol, '--output', training]),
    ]
    env = {**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1',
           'TOKENIZERS_PARALLELISM': 'false', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    for destination, arguments in commands:
        if destination.exists():
            continue
        log = root / (destination.stem + '.log')
        with log.open('ab') as stream:
            subprocess.run([str(PYTHON), '-B', '-m', 'student_pilot.cli', 'diagnostic', *map(str, arguments),
                            '--provisional-diagnostic', LABEL], cwd=TRAINER, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
    common = compact.load_json(stage / 'TRAIN_1000.pending.json')
    manifest = compact.load_json(training)
    check_native_manifest(manifest, common['qids'])
    frozen = compact.load_json(protocol)
    control.require(frozen['split']['train_candidate_qids'] == sorted(common['qids'])
                    and frozen['split']['hashed_group_count'] == 0, 'native_split_inheritance')
    compact.save(root / 'NATIVE_ADMISSION.json', {'passed': True, 'rows': len(common['qids']),
                 'protocol': compact.binding(protocol), 'training': compact.binding(training),
                 'trainer_commit': TRAINER_COMMIT, 'token_limit_drops': 0, 'hashed_scene_groups': 0})
    print(json.dumps({'variant': args.variant, 'native_admitted': len(common['qids']), 'drops': 0}), flush=True)
    return 0


def freeze(args):
    common = compact.load_json(args.stage / 'TRAIN_1000.pending.json')
    native_pins, models = {}, {}
    for variant in VARIANTS:
        path = args.stage / variant / 'NATIVE_ADMISSION.json'
        receipt = compact.load_json(path)
        control.require(receipt['passed'] is True and receipt['trainer_commit'] == TRAINER_COMMIT, 'native_admission_receipt')
        manifest = control.checked_json(receipt['training'])
        check_native_manifest(manifest, common['qids'])
        protocol = control.checked_json(receipt['protocol'])
        control.require(protocol['split']['inherited_from'] == common['split'], 'native_published_split_pin')
        native_pins[variant] = compact.binding(path)
        models[variant] = (manifest, protocol)
    a0, c0 = models['a0'][0], models['c0'][0]
    control.require([row['student_input'] for row in a0['rows']] == [row['student_input'] for row in c0['rows']],
                    'native_control_input_equality')
    control.require([row['answer'] for row in a0['rows']] == [row['answer'] for row in c0['rows']],
                    'native_control_answer_equality')
    control.require(models['a0'][1]['training'] == models['c0'][1]['training'], 'native_control_recipe_equality')
    control.require(args.handcheck and args.handcheck.is_file(), 'common_handcheck_required')
    for pin in [common['proposed'], common['split'], common['source_audit'], common['source_admission'],
                common['replacements'], *common['candidate_indices'].values(), *common['sources']]:
        control.checked_bytes(pin)
    common['native_admission'] = native_pins
    common['handcheck'] = compact.binding(args.handcheck)
    manifest_pin = compact.save(args.common / 'TRAIN_1000.json', common)
    compact.save(args.common / 'SOURCE_ADMISSION.json', control.checked_bytes(common['source_admission']))
    compact.save(args.common / 'HANDCHECK_QIDS.json', [row['qid'] for row in compact.load_json(args.stage / 'HANDCHECK_SAMPLE.json')])
    done = {'schema': 'swarm-common-admission-done-v1', 'passed': True, 'rows': 1000,
            'membership': manifest_pin, 'split': compact.binding(args.common / 'split_trainer.json'),
            'native_admission': native_pins, 'handcheck': common['handcheck'], 'code': common['code']}
    compact.save(args.common / 'COMMON_DONE', done)
    print(json.dumps(done, indent=2), flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('build', 'native', 'freeze'))
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--common', type=Path, required=True)
    parser.add_argument('--sets', type=Path)
    parser.add_argument('--proposed', type=Path, default=D / 'TRAIN_1000_PROPOSED.json')
    parser.add_argument('--variant', choices=VARIANTS)
    parser.add_argument('--refusals', type=Path)
    parser.add_argument('--handcheck', type=Path)
    parser.add_argument('--repair-unfrozen-split', action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'build':
        control.require(args.sets is not None, 'sets_directory_required')
    if args.command == 'native':
        control.require(args.variant is not None, 'variant_required')
    return {'build': build, 'native': native, 'freeze': freeze}[args.command](args)


if __name__ == '__main__':
    raise SystemExit(main())
