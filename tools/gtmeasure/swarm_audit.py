import argparse
from collections import Counter, defaultdict
from pathlib import Path
import statistics
import subprocess
import sys

from .io import canonical, pin, read_json, read_jsonl, sha
from .swarm import LABEL, require, write_new


def trace_audit(paths):
    records = []
    for path in paths:
        raw = read_json(path)
        calls = []
        roles = Counter()
        messages = raw.get('trace', [])
        require(isinstance(messages, list) and messages, 'trace_message_list')
        for message in messages:
            roles[str(message.get('role', message.get('type', 'unknown')))] += 1
            for call in message.get('tool_calls') or []:
                function = call.get('function', call)
                calls.append({'name': function.get('name'),
                              'arguments_excerpt': str(function.get('args', function.get('arguments', '')))[:500]})
        content = messages[-1].get('content', '')
        final_text = content if isinstance(content, str) else '\n'.join(item.get('text', '') for item in content if item.get('type') == 'text')
        responses = raw.get('tool_vlm_responses', [])
        records.append({'source': pin(path), 'qid': raw.get('question_id'), 'question': raw.get('question'),
                        'prediction': raw.get('pred'), 'trace_entry_count': len(messages), 'message_roles': dict(roles),
                        'tool_calls': calls, 'tool_call_count': len(calls), 'tool_vlm_response_count': len(responses),
                        'final_text': final_text})
    return {'schema': 'h05-source-trace-inspection-v1', 'traces': records, 'used_for_training': False,
            'gemini': {'calls': 0, 'input_tokens': 0, 'output_tokens': 0}}


def layout_audit(directory, trainer, tokenizer, trainer_commit):
    actual_commit = subprocess.check_output(['git', '-C', str(trainer), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(trainer), '--no-optional-locks', 'status', '--porcelain'], text=True)
    require(actual_commit == trainer_commit and not status.strip(), 'trainer_source_pin')
    sys.path.insert(0, str(Path(trainer).resolve()))
    from student_pilot.provisional import load_inherited_record, load_provisional_candidates
    from student_pilot.split import make_inherited_split
    from transformers import AutoTokenizer

    directory = Path(directory).resolve()
    train_entries = list(read_jsonl(directory / 'candidate_index.jsonl'))
    heldout_entries = list(read_jsonl(directory / 'heldout_context/candidate_index.jsonl'))
    context = list(read_jsonl(directory / 'protocol_context/candidate_index.jsonl'))
    require(context == sorted(train_entries + heldout_entries, key=lambda row: row['qid']), 'audit_context')
    loaded = load_provisional_candidates(str(directory / 'protocol_context/candidate_index.jsonl'), LABEL)
    split_pin = {'path': str(directory / 'split_trainer.json'), 'sha256': sha(directory / 'split_trainer.json')}
    published = load_inherited_record(split_pin)
    split = make_inherited_split(loaded, loaded, published, seed=17, heldout_fraction=0.1)
    train_qids = {row['qid'] for row in train_entries}
    heldout_qids = {row['qid'] for row in heldout_entries}
    require(set(split['train_candidate_qids']) == train_qids and set(split['heldout_qids']) == heldout_qids
            and split['hashed_group_count'] == 0 and not train_qids & heldout_qids, 'trainer_split_replay')
    encoder = AutoTokenizer.from_pretrained(str(tokenizer), local_files_only=True, trust_remote_code=False)
    require(encoder.eos_token_id is not None, 'tokenizer_eos')
    training = [row for row in loaded if row['qid'] in train_qids]
    tokens = [len(encoder.encode(row['target'], add_special_tokens=False)) for row in training]
    require(max(tokens) + 1 <= 1536, 'target_token_bound')
    groups = defaultdict(list)
    for entry in train_entries:
        if entry['qid'].startswith('gtmeasure_'):
            family = {'object_counting': 'count', 'object_size_estimation': 'size', 'room_size_estimation': 'room',
                      'object_abs_distance': 'distance', 'object_rel_distance': 'distance',
                      'camera_obj_abs_dist': 'camera_distance'}[entry['question_type']]
            groups[family].append(entry)
    chosen = []
    per_family = 2 if len(train_entries) == 1000 else 1
    for family in sorted(groups):
        candidates = groups[family]
        chosen.extend(candidates[:per_family])
        if family == 'distance' and per_family == 2:
            relative = next((entry for entry in candidates if entry['question_type'] == 'object_rel_distance'), None)
            if relative is not None and relative not in chosen:
                chosen[-1] = relative
    if len(train_entries) > 1000:
        seen = set()
        for entry in train_entries:
            if entry['qid'].startswith('vsi590k_') and entry['question_type'] not in seen:
                chosen.append(entry)
                seen.add(entry['question_type'])
                if len(chosen) == 10:
                    break
    samples = []
    for entry in chosen:
        row = read_json(entry['row_path'])
        samples.append({'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                        'family': row.get('family', 'answeronly:' + row['category']),
                        'question': row['student_input']['question'], 'options': row['student_input']['options'],
                        'target': row['target'], 'answer': entry['answer'], 'ground_truth': row.get('ground_truth'),
                        'object_ids': row.get('object_ids'), 'frame_count': len(row['student_input']['frames']),
                        'target_tokens': len(encoder.encode(row['target'], add_special_tokens=False)),
                        'row_path': entry['row_path'], 'target_path': entry['target_path']})
    return {
        'schema': 'h05-trainer-layout-audit-v1', 'verdict': 'PASS', 'directory': str(directory),
        'trainer_root': str(trainer), 'trainer_commit': actual_commit, 'audit_source': pin(__file__),
        'loader': 'student_pilot.provisional.load_provisional_candidates',
        'context_rows_accepted': len(loaded), 'training_rows_accepted': len(training),
        'heldout_context_rows': len(heldout_qids), 'heldout_in_train': 0, 'hashed_group_count': 0,
        'split': split_pin, 'tokenizer': str(tokenizer), 'eos_token_id': encoder.eos_token_id,
        'target_tokens_excluding_eos': {'total': sum(tokens), 'minimum': min(tokens), 'maximum': max(tokens),
                                        'median': statistics.median(tokens), 'mean': statistics.mean(tokens)},
        'family_counts': dict(Counter(row['category'] for row in training)),
        'handcheck_samples': samples, 'independent_review': 'not performed by this audit',
    }


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    traces = commands.add_parser('traces')
    traces.add_argument('--paths', nargs=3, required=True)
    layout = commands.add_parser('layout')
    layout.add_argument('--directory', required=True)
    layout.add_argument('--trainer', required=True)
    layout.add_argument('--trainer-commit', required=True)
    layout.add_argument('--tokenizer', required=True)
    for command in (traces, layout):
        command.add_argument('--output', required=True)
    args = parser.parse_args()
    result = trace_audit(args.paths) if args.command == 'traces' else layout_audit(args.directory, args.trainer, args.tokenizer, args.trainer_commit)
    write_new(args.output, result)
    print(canonical({key: value for key, value in result.items() if key not in ('traces', 'handcheck_samples')}))


if __name__ == '__main__':
    main()
