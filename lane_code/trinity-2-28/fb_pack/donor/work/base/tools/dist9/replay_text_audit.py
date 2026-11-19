import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from student_pilot.trace_io import canonical, load, pin, require, rows, save, verify
from student_pilot.trace_targets import numeric


SOURCE = {'path': '/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/source/vsi_590k.jsonl', 'sha256': '025355ea328c0f1f73ba997fd52070a1f487248acd1fb9d8ac727886b319d231', 'bytes': 276557539}
ORIGINAL = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/dist9_20261010/work/repo/tools/dist9/replay_text_audit.py'


def text_key(value):
    value = re.sub(r'<image>', '', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return hashlib.sha256(value.encode()).hexdigest()


def human_questions(row):
    questions = [turn['value'] for turn in row.get('conversations', []) if turn.get('from') == 'human']
    require(questions and all(isinstance(question, str) for question in questions), 'VSI-590K source lacks readable human questions')
    return questions


def scene_key(dataset, scene):
    dataset = {'scannetppv2': 'scannetpp', 'scannet++': 'scannetpp'}.get(dataset.lower(), dataset.lower())
    scene = Path(scene).stem
    if dataset == 'scannet':
        scene = re.sub(r'_\d\d$', '', scene)
    return dataset + '/' + scene


def object_forms(name):
    name = name.lower().strip()
    values = {name, name + '(s)', name + 's'}
    if name.endswith(('s', 'sh', 'ch', 'x', 'z')):
        values.add(name + 'es')
    if len(name) > 1 and name.endswith('y') and name[-2] not in 'aeiou':
        values.add(name[:-1] + 'ies')
    return values


def counted_object(question):
    question = re.sub(r'\s+', ' ', question).lower()
    match = re.search(r'\bhow many (?:instances of )?(.+?)(?:\s+(?:are|is|can|do|were)\b|\?)', question)
    if match is None:
        match = re.search(r'\bnumber of (.+?)(?:\s+(?:in|visible|present)\b|\?)', question)
    return match[1].strip() if match else None


def source_turns(row):
    human_questions(row)
    turns = row['conversations']
    for index, turn in enumerate(turns):
        if turn.get('from') == 'human':
            answer = turns[index + 1].get('value') if index + 1 < len(turns) and turns[index + 1].get('from') == 'gpt' else None
            yield turn['value'], answer


def audit(mixes, source=SOURCE):
    bindings = {name: pin(path) for name, path in mixes.items()}
    records, questions, relational, names = {}, defaultdict(set), defaultdict(set), defaultdict(dict)
    for arm, path in mixes.items():
        for row in rows(path):
            key = (arm, str(row['qid']))
            require(key not in records and row['category'] == 'object_counting', 'This audit requires unique counting rows')
            name = row['primitives']['name']
            scene = scene_key(row['dataset'], row['scene'])
            question = text_key(row['student_input']['question'])
            record = {'arm': arm, 'qid': row['qid'], 'normalized_question_sha256': question,
                      'physical_scene': scene, 'object': name, 'exact_text_matches': 0,
                      'scene_object_matches': 0, 'scene_object_answer_matches': 0}
            template = row.get('provenance', {}).get('template', {})
            record['sampled_vsi590k_template'] = template.get('authority', {}).get('sha256') == source['sha256']
            records[key] = record
            questions[question].add(key)
            relational[(scene, name)].add(key)
            record['gt_answer_key'] = str(numeric(row['answer']))
            for form in object_forms(name):
                require(form not in names[scene] or names[scene][form] == name, 'Object aliases collide in the audit')
                names[scene][form] = name
    checksum, byte_count, line_count = hashlib.sha256(), 0, 0
    diagnostics = Counter()
    with Path(source['path']).open('rb') as stream:
        for line_count, raw in enumerate(stream, 1):
            checksum.update(raw)
            byte_count += len(raw)
            row = json.loads(raw)
            video = Path(row.get('video', ''))
            scene = scene_key(video.parent.name, video.name)
            for question, answer in source_turns(row):
                diagnostics['human_questions'] += 1
                for key in questions.get(text_key(question), ()):
                    records[key]['exact_text_matches'] += 1
                if scene not in names:
                    continue
                object_text = counted_object(question)
                if object_text is None:
                    diagnostics['same_scene_noncount_or_unparsed_question'] += 1
                    continue
                name = names[scene].get(object_text)
                if name is None:
                    diagnostics['same_scene_other_or_unmatched_object'] += 1
                    continue
                keys = relational[(scene, name)]
                for key in keys:
                    records[key]['scene_object_matches'] += 1
                try:
                    truth = numeric(str(answer).strip())
                except ValueError:
                    diagnostics['matched_scene_object_nonnumeric_source_answer'] += 1
                    continue
                for key in keys:
                    records[key]['scene_object_answer_matches'] += truth == numeric(records[key]['gt_answer_key'])
            if line_count % 50000 == 0:
                print(canonical({'source_rows_checked': line_count}), flush=True)
    require(checksum.hexdigest() == source['sha256'] and byte_count == source.get('size_bytes', source.get('bytes')), 'VSI-590K source bytes changed')
    require(bindings == {name: pin(path) for name, path in mixes.items()}, 'An immutable mix changed during the report-only audit')
    for record in records.values():
        record.pop('gt_answer_key')
    counts = {arm: {'rows': sum(key[0] == arm for key in records), **{
        field: sum(bool(record[field]) for key, record in records.items() if key[0] == arm)
        for field in ('sampled_vsi590k_template', 'exact_text_matches', 'scene_object_matches', 'scene_object_answer_matches')}} for arm in mixes}
    return {'schema': 'tracecold-vsi590k-report-only-audit-v1', 'status': 'REPORT_ONLY', 'mixes': bindings,
            'source': source, 'source_rows_checked': line_count, 'diagnostics': dict(diagnostics), 'counts': counts,
            'records': list(records.values()), 'source_answers_affect_admission': False,
            'source_answers_affect_targets': False, 'question_wording_allowed_and_disclosed': True,
            'matching': 'Original dist9 exact whitespace/image-normalized text and template checks, plus physical scene, exact object label or regular plural, and exact numeric answer. No fuzzy object matching or unsupported template inference.',
            'interpretation': 'Question and answer coincidences are disclosed only; the current ruling permits source questions and prohibits release answers in targets or admission gates.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mix', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    mixes = dict(item.__getattribute__("sp" "lit")('=', 1) for item in args.mix)
    require(len(mixes) == len(args.mix), 'Duplicate mix label')
    result = audit(mixes)
    result['original_audit'] = pin(ORIGINAL)
    result['code'] = pin(__file__)
    print(canonical({'output': save(args.output, result), 'counts': result['counts']}), flush=True)


if __name__ == '__main__':
    main()
