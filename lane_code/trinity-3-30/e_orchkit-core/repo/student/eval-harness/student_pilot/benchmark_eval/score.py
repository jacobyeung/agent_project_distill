import contextlib
import csv
import importlib.util
import io
import json
import math
import os
import subprocess
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

from .answers import parse_answer
from .contracts import (VARIANTS, binding, canonical_bytes, digest, jsonl_bytes, load_generation, load_json,
                        load_jsonl, new_directory, require_pair, safe_id, validate_receipt, verify_pin,
                        write_bytes_once, write_once)
from .prepare import COMPOSITE_SHA, DSI_SCORER_SHA, SCORER_SHA


OFFICIAL_BRIDGE = '''import contextlib, importlib.util, io, json, sys
import pandas
spec = importlib.util.spec_from_file_location("student_official_dsi", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.META_BASE_PATH, module.OUTPUT_BASE_PATH, module.VLM_MODEL = sys.argv[2], sys.argv[3], "student"
original = module.print_metrics
values = []
def capture(categories, overall):
    values.append({"categories": {str(key): float(value) for key, value in categories.items()}, "overall": float(overall)})
    original(categories, overall)
module.print_metrics = capture
output = io.StringIO()
with contextlib.redirect_stdout(output):
    module.sample_wise_evaluation()
    module.group_wise_evaluation(n=3)
    for variant in module.VIDEO_AUGS:
        module.single_evaluation(variant)
print(json.dumps({"values": values, "printed": output.getvalue(), "pandas_version": pandas.__version__}, allow_nan=False))
'''


def canonical_scorer(pins):
    source, core = verify_pin(pins['implementation']), verify_pin(pins['composite'])
    binding(source, SCORER_SHA)
    binding(core, COMPOSITE_SHA)
    package_name = '_student_pinned_evaluation'
    package = types.ModuleType(package_name)
    package.__path__ = [str(source.parent)]
    sys.modules[package_name] = package
    modules = []
    for name, path in (('scoring', source), ('score_record_core', core)):
        spec = importlib.util.spec_from_file_location(f'{package_name}.{name}', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        modules.append(module)
    return modules


def aggregate_categories(category_values, benchmark, scorer, core, counts=None, paper=True):
    schema = 'vsibench-official-8task-v1' if benchmark == 'vsibench_answerable500' else 'vstibench-official-5subtask-v1'
    formula = core.AGGREGATION_FORMULAS[schema]
    expected = set(formula['categories'])
    if set(category_values) - expected:
        raise ValueError('Unknown scoring categories')
    missing = sorted(expected - set(category_values))
    if paper and missing:
        raise ValueError(f'Paper score lacks mandatory categories: {missing}')
    if not category_values:
        raise ValueError('Cannot score an empty cohort')
    if not missing:
        dataset = {'synthetic_category_projection': True}
        records = {category: {'record_type': 'category', 'record_id': 'sha256:' + digest([category, value]),
                               'scorer_id': 'student-pinned-scorer', 'dataset': dataset,
                               'scope': {'category': category, 'question_count': (counts or {}).get(category, 1)},
                               'score': {'value': value}} for category, value in category_values.items()}
        composite = core.build_composite_record(schema, records, scorer_id='student-pinned-scorer')
        official, raw = composite['score']['official'], composite['score']['raw_category_macro']
    else:
        groups, collapsed = [], set()
        for group in formula['collapse_groups']:
            present = set(group) & set(category_values)
            if present:
                groups.append(scorer.canonical_mean(category_values[name] for name in sorted(present)))
                collapsed.update(present)
        groups.extend(value for category, value in category_values.items() if category not in collapsed)
        official, raw = scorer.canonical_mean(groups), scorer.canonical_mean(category_values.values())
    return {'metric': schema if not missing else 'synthetic-partial-observed-task-macro',
            'primary_score': official, 'raw_category_macro': raw, 'category_scores': category_values,
            'missing_categories': missing, 'official_aggregation_complete': not missing}


def dsi_metrics(labels, answers):
    ids = [row['id'] for row in labels]
    if not ids or len(set(ids)) != len(ids) or set(answers) - set(ids):
        raise ValueError('DSI prediction/label id census mismatch')
    grouped, categories, variants, per_question = defaultdict(list), defaultdict(list), defaultdict(list), []
    for label in labels:
        variant, group = label['variant'], label['group_id']
        if variant not in VARIANTS or type(group) is not int or group < 0 or label['id'] != f'dsibench:{variant}:{group}':
            raise ValueError('DSI variant/group identity mismatch')
        if str(label['question_type']) not in {str(i) for i in range(6)}:
            raise ValueError('Unknown DSI category')
        answer = answers.get(label['id'])
        credit = int(answer in ('A', 'B', 'C', 'D') and answer == label['ground_truth'])
        grouped[group].append((variant, str(label['question_type']), label['relative_path'], credit))
        categories[str(label['question_type'])].append(credit)
        variants[variant].append(credit)
        per_question.append({'qid': label['id'], 'credit': float(credit), 'category': str(label['question_type']),
                             'group_id': group, 'variant': variant})
    if sorted(grouped) != list(range(len(grouped))):
        raise ValueError('DSI groups must retain consecutive original row ordinals')
    robust, robust_categories = {}, defaultdict(list)
    for group, rows in sorted(grouped.items()):
        if len(rows) != 4 or {row[0] for row in rows} != set(VARIANTS) or len({(row[1], row[2]) for row in rows}) != 1:
            raise ValueError('DSI group lost a variant or changed category/video identity')
        robust[group] = int(sum(row[3] for row in rows) >= 3)
        robust_categories[rows[0][1]].append(robust[group])
    mean = lambda values: sum(values) / len(values)
    return {'metric': 'dsibench-sample-wise-all4-v1', 'primary_score': mean([row['credit'] for row in per_question]),
            'group_wise_accuracy': mean(list(robust.values())),
            'category_scores': {key: mean(value) for key, value in sorted(categories.items())},
            'group_category_scores': {key: mean(value) for key, value in sorted(robust_categories.items())},
            'variant_scores': {key: mean(variants[key]) for key in VARIANTS},
            'group_credits': {str(key): value for key, value in robust.items()},
            'question_groups': len(grouped), 'evaluation_rows': len(labels)}, per_question


def csv_bytes(fields, rows):
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return text.getvalue().encode('utf-8')


def official_dsi(labels, answers, scorer_pin, output, artifact_root, paper, official_python):
    scorer_path = verify_pin(scorer_pin)
    binding(scorer_path, DSI_SCORER_SHA)
    pins = []
    for variant in VARIANTS:
        subset = sorted((row for row in labels if row['variant'] == variant), key=lambda row: row['group_id'])
        if [row['group_id'] for row in subset] != list(range(len(subset))):
            raise ValueError('DSI projection is not in original row order')
        meta = [{'cate': row['question_type'], 'relative_path': row['relative_path'], 'video_type': '',
                 'question': row['question'], 'options': row['options'], 'GT': row['ground_truth'], 'others': ''} for row in subset]
        predictions = [{'qid': row['id'], 'final_answer': answers.get(row['id']) if answers.get(row['id']) in ('A', 'B', 'C', 'D') else 'E'} for row in subset]
        pins.append(write_bytes_once(output / f'dsi_metadata/{variant}.csv',
                                     csv_bytes(['cate', 'relative_path', 'video_type', 'question', 'options', 'GT', 'others'], meta), artifact_root, paper))
        pins.append(write_bytes_once(output / f'dsi_predictions/{variant}/student.csv',
                                     csv_bytes(['qid', 'final_answer'], predictions), artifact_root, paper))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    result = subprocess.run([str(official_python), '-B', '-c', OFFICIAL_BRIDGE, str(scorer_path),
                             str(output / 'dsi_metadata'), str(output / 'dsi_predictions')],
                            check=True, capture_output=True, text=True, timeout=120, env=env)
    observed = json.loads(result.stdout)
    if len(observed['values']) != 6:
        raise ValueError('Official DSI scorer did not produce sample/group/four-variant outputs')
    expected, _ = dsi_metrics(labels, answers)
    pairs = [(expected['primary_score'], expected['category_scores']),
             (expected['group_wise_accuracy'], expected['group_category_scores'])]
    for variant in VARIANTS:
        sublabels = [row for row in labels if row['variant'] == variant]
        cats = defaultdict(list)
        for row in sublabels:
            cats[str(row['question_type'])].append(int(answers.get(row['id']) == row['ground_truth']))
        pairs.append((expected['variant_scores'][variant], {key: sum(value) / len(value) for key, value in cats.items()}))
    for actual, (overall, categories) in zip(observed['values'], pairs):
        if not math.isclose(actual['overall'], overall, abs_tol=1e-14) or actual['categories'] != categories:
            raise ValueError('Wrapper and pinned official DSI scorer disagree')
        if f'Overall Acc = {overall:.2%}' not in observed['printed']:
            raise ValueError('Official printed DSI score differs from full-precision result')
    pins.append(write_bytes_once(output / 'official_dsi_stdout.txt', observed['printed'].encode(), artifact_root, paper))
    pins.append(write_once(output / 'official_dsi_metrics.json', observed, artifact_root, paper))
    return observed, pins


def _read_run(run, manifest, rows):
    run = Path(run)
    header = load_json(run / 'run.json')
    if header.get('schema') != 'student-generation-run-v1' or header['core']['generation_manifest'] != manifest['generation']:
        raise ValueError('Run belongs to a different generation package')
    ids = [row['qid'] for row in rows]
    if header['core']['ordered_ids'] != ids:
        raise ValueError('Run membership differs from the scoring cohort')
    verify_pin(header['preflight'])
    preflight = load_json(header['preflight']['path'])
    verify_pin(preflight['input_audits'])
    audits = {row['qid']: row for row in load_jsonl(preflight['input_audits']['path'])}
    if set(audits) != set(ids) or preflight['input_audits']['sha256'] != header['core']['input_audits_sha256']:
        raise ValueError('Run input audit binding changed')
    attempts_path = run / 'attempts.jsonl'
    attempts = load_jsonl(attempts_path) if attempts_path.exists() else []
    if len({row['qid'] for row in attempts}) != len(attempts):
        raise ValueError('More than one attempt started for a question')
    for start in attempts:
        if start['qid'] not in ids or start['attempt_index'] != 1 or start['run_header_sha256'] != digest(header):
            raise ValueError('Invalid or foreign generation attempt')
    started = {row['qid'] for row in attempts}
    receipts, pins = {}, []
    for path in sorted((run / 'questions').glob('*.json')):
        receipt = validate_receipt(load_json(path), header)
        qid = receipt['qid']
        if qid in receipts or path.name != f'{safe_id(qid)}.json':
            raise ValueError('Duplicate or misnamed question receipt')
        if (receipt['attempt_index'] == 1) != (qid in started):
            raise ValueError('Question receipt and attempt ledger disagree')
        if receipt['status'] == 'ok':
            if receipt['input_audit'] != audits[qid]:
                raise ValueError('Question prompt/pixels differ from preflight')
            for name in ('frame_hashes', 'frame_indices', 'source_pts_seconds', 'effective_timestamps_seconds',
                         'pixel_tensor_sha256', 'prompt_token_sha256', 'video_grid_thw', 'prompt_tokens', 'video_sha256'):
                if receipt[name] != audits[qid][name]:
                    raise ValueError(f'Question provenance mismatch: {name}')
        receipts[qid] = receipt
        pins.append(binding(path))
    if (run / 'generations.jsonl').exists():
        projection = load_jsonl(run / 'generations.jsonl')
        if projection != [receipts[qid] for qid in ids if qid in receipts] or len(projection) != len(ids):
            raise ValueError('Native JSONL does not exactly census immutable question receipts')
        pins.append(binding(run / 'generations.jsonl'))
    if (run / 'completion.json').exists():
        completion = load_json(run / 'completion.json')
        if (completion['scheduled_ids'] != ids or completion['expected_count'] != len(ids)
                or completion['terminal_count'] != len(receipts) or completion['started_count'] != len(started)
                or completion['run'] != binding(run / 'run.json')
                or completion['outcomes'] != {qid: receipts[qid]['status'] for qid in ids if qid in receipts}):
            raise ValueError('Completion marker disagrees with actual integrity evidence')
        verify_pin(completion['generations'])
        pins.append(binding(run / 'completion.json'))
    if attempts_path.exists():
        pins.append(binding(attempts_path))
    return header, receipts, pins, len(started)


def score_run(run, scoring_manifest, output, artifact_root, official_python=None):
    manifest = load_json(scoring_manifest)
    if manifest.get('schema') != 'student-scoring-manifest-v1':
        raise ValueError('Invalid offline scoring manifest')
    for pin in [manifest['generation'], manifest['labels']] + manifest['source_bindings']:
        verify_pin(pin)
    public, rows, config = load_generation(manifest['generation']['path'])
    labels = load_jsonl(manifest['labels']['path'])
    ids = public['ordered_ids']
    if [row['id'] for row in labels] != ids or manifest['ordered_ids'] != ids or manifest['expected_count'] != len(ids):
        raise ValueError('Scoring labels must match the exact ordered generation cohort')
    if public['benchmark'] != manifest['benchmark'] or public['paper_cell'] != manifest['paper_cell']:
        raise ValueError('Scoring and inference scopes differ')
    for row, label in zip(rows, labels):
        if row['student_input']['question'] != label['question'] or row['student_input']['options'] != label['options']:
            raise ValueError('Scoring question/options differ from inference inputs')
    header, receipts, receipt_pins, started = _read_run(run, manifest, rows)
    if header['core']['config'] != config:
        raise ValueError('Scoring run settings differ from the shared manifest')
    paper = public['paper_cell']
    output = new_directory(output, artifact_root, paper)
    answers, statuses, parser_counts, projections = {}, {}, Counter(), []
    projection_pins = []
    for row in rows:
        qid, receipt = row['qid'], receipts.get(row['qid'])
        parsed = parse_answer(receipt['raw_generation'] if receipt else '', row['student_input']['options'])
        if receipt and (parsed['answer'] != receipt['parsed_answer'] or parsed['parser'] != receipt['parser']):
            raise ValueError('Stored parser output differs from deterministic raw-text replay')
        answer = parsed['answer'] if receipt and receipt['status'] == 'ok' else None
        answers[qid] = answer
        statuses[qid] = receipt['status'] if receipt else 'missing'
        parser_counts[parsed['parser']['branch']] += 1
        projections.append({'question_id': qid, 'trace': {'messages': [
            {'role': 'ai', 'content': f'<ANSWER>{answer}</ANSWER>' if answer is not None else '', 'tool_calls': []}]},
            'provenance': 'deterministic_parser_projection_not_raw_generation'})
    if manifest['benchmark'] == 'dsibench_all4':
        metrics, question_scores = dsi_metrics(labels, answers)
        if paper and set(metrics['category_scores']) != {str(index) for index in range(6)}:
            raise ValueError('A full DSI paper cell must include all six categories')
        official, projection_pins = official_dsi(labels, answers, manifest['scorer']['official'], output,
                                                artifact_root, paper, official_python or sys.executable)
        scorer_environment = {'pandas_version': official['pandas_version']}
    else:
        scorer, core = canonical_scorer(manifest['scorer'])
        category_credits, counts, question_scores = defaultdict(list), Counter(), []
        for label, projection in zip(labels, projections):
            record, details = scorer._score_entry(projection, label, strict=True)
            credit = record['accuracy'] if 'accuracy' in record else record['MRA']
            category = label['question_type']
            category_credits[category].append(credit)
            counts[category] += 1
            question_scores.append({'qid': label['id'], 'credit': credit, 'category': category,
                                    'group_id': None, 'variant': None, 'canonical_metrics': details})
            projection_pins.append(write_once(output / f'compatibility/trace_{label["id"]}.json', projection, artifact_root, paper))
        values = {name: scorer.canonical_mean(credits) for name, credits in sorted(category_credits.items())}
        metrics = aggregate_categories(values, manifest['benchmark'], scorer, core, counts, paper)
        scorer_environment = {'aggregation': scorer.SCORING_CONTRACT['aggregation']}
    for row in question_scores:
        row.update(parsed_answer=answers[row['qid']], status=statuses[row['qid']])
    projection_pins.append(write_bytes_once(output / 'compatibility_projection.jsonl', jsonl_bytes(projections), artifact_root, paper))
    per_question = write_bytes_once(output / 'per_question_scores.jsonl', jsonl_bytes(question_scores), artifact_root, paper)
    closure = [binding(Path(__file__).parent / name) for name in ('__init__.py', 'score.py', 'prepare.py', 'answers.py', 'contracts.py', 'frames.py')]
    closure += list(manifest['scorer'].values())
    cap_count = sum(row['finish_reason'] == 'max_new_tokens' for row in receipts.values())
    result = {'schema': 'student-benchmark-scores-v1', 'benchmark': manifest['benchmark'], 'paper_cell': paper,
              'publication_ready': False, 'run': binding(Path(run) / 'run.json'), 'run_core': header['core'],
              'scoring_manifest': binding(scoring_manifest), 'generation_manifest': manifest['generation'],
              'scorer_closure': closure, 'scorer_environment': scorer_environment, 'receipt_bindings': receipt_pins,
              'projections': projection_pins, 'per_question_scores': per_question, 'expected_count': len(ids),
              'terminal_count': len(receipts), 'started_count': started, 'missing_count': len(ids) - len(receipts),
              'coverage_complete': len(receipts) == len(ids), 'native_success_count': sum(status == 'ok' for status in statuses.values()),
              'parse_failures': parser_counts.get('failure', 0), 'parser_branches': dict(parser_counts),
              'cap_count': cap_count, 'cap_without_answer_count': sum(row['finish_reason'] == 'max_new_tokens' and row['parsed_answer'] is None for row in receipts.values()),
              'failure_counts': dict(Counter(statuses.values())), **metrics}
    write_once(output / 'scores.json', result, artifact_root, paper)
    return result


def compare_scores(base_path, distilled_path, output, artifact_root):
    base, distilled = load_json(base_path), load_json(distilled_path)
    if base.get('schema') != 'student-benchmark-scores-v1' or distilled.get('schema') != base['schema']:
        raise ValueError('Comparison requires two benchmark score receipts')
    for score in (base, distilled):
        for pin in [score['run'], score['scoring_manifest'], score['generation_manifest'], score['per_question_scores']] + score['receipt_bindings'] + score['projections'] + score['scorer_closure']:
            verify_pin(pin)
    require_pair(base['run_core'], distilled['run_core'])
    for field in ('benchmark', 'scoring_manifest', 'generation_manifest', 'scorer_closure', 'scorer_environment', 'metric', 'expected_count'):
        if base[field] != distilled[field]:
            raise ValueError(f'Comparison changed {field}')
    for field in ('category_scores',):
        if set(base[field]) != set(distilled[field]):
            raise ValueError('Comparison changed category membership')
    result = {'schema': 'student-paired-comparison-v1', 'base': binding(base_path), 'distilled': binding(distilled_path),
              'benchmark': base['benchmark'], 'metric': base['metric'],
              'base_score': base['primary_score'], 'distilled_score': distilled['primary_score'],
              'delta_percentage_points': 100 * (distilled['primary_score'] - base['primary_score']),
              'category_deltas_percentage_points': {name: 100 * (distilled['category_scores'][name] - value) for name, value in base['category_scores'].items()},
              'coverage_complete': base['coverage_complete'] and distilled['coverage_complete'],
              'publication_ready': False, 'single_seed': 17}
    output = new_directory(output, artifact_root, base['paper_cell'])
    write_once(output / 'comparison.json', result, artifact_root, base['paper_cell'])
    return result


def export_bank(run, score_path, bank_id, output, artifact_root):
    safe_id(bank_id)
    score = load_json(score_path)
    if score.get('schema') != 'student-benchmark-scores-v1' or score['run'] != binding(Path(run) / 'run.json'):
        raise ValueError('Answer bank run/score identity mismatch')
    for pin in score['receipt_bindings'] + score['projections'] + score['scorer_closure'] + [score['per_question_scores']]:
        verify_pin(pin)
    output = new_directory(output, artifact_root, score['paper_cell'])
    copied, sources = {}, {}

    def copy(path, relative):
        path = Path(path)
        source = binding(path)
        destination = write_bytes_once(output / relative, path.read_bytes(), artifact_root, score['paper_cell'])
        if destination['sha256'] != source['sha256']:
            raise ValueError('Bank copy hash mismatch')
        copied[relative] = destination['sha256']
        sources[str(path.absolute())] = relative

    run = Path(run)
    for name in ('run.json', 'attempts.jsonl', 'generations.jsonl', 'completion.json', 'adapter_reload.json'):
        if (run / name).is_file():
            copy(run / name, f'run/{name}')
    for path in sorted((run / 'questions').glob('*.json')):
        copy(path, f'run/questions/{path.name}')
    copy(score_path, 'score/scores.json')
    scoring_root = Path(score_path).parent
    for pin in score['projections'] + [score['per_question_scores']]:
        path = verify_pin(pin)
        if not path.resolve().is_relative_to(scoring_root.resolve()):
            raise ValueError('Score artifact escapes its package')
        copy(path, 'score/' + str(path.relative_to(scoring_root)))
    scoring_manifest = load_json(verify_pin(score['scoring_manifest']))
    copy(score['scoring_manifest']['path'], 'scoring/manifest.json')
    copy(verify_pin(scoring_manifest['labels']), 'scoring/labels.jsonl')
    public, rows, _ = load_generation(score['generation_manifest']['path'])
    copy(score['generation_manifest']['path'], 'generation/manifest.json')
    for name in ('config', 'inputs', 'media', 'membership', 'admission_input'):
        copy(verify_pin(public[name]), 'generation/' + Path(public[name]['path']).name)
    seen = set()
    for media in load_json(public['media']['path']).values():
        receipt_path = verify_pin(media['frame_receipt'])
        receipt = load_json(receipt_path)
        if receipt['cache_id'] in seen:
            continue
        seen.add(receipt['cache_id'])
        prefix = 'generation/frames/' + receipt['cache_id']
        copy(receipt_path, prefix + '/selection.json')
        for row in receipt['frames']:
            copy(verify_pin(row['png']), prefix + '/' + Path(row['png']['path']).name)
    header = load_json(run / 'run.json')
    preflight = load_json(verify_pin(header['preflight']))
    copy(header['preflight']['path'], 'preflight/preflight.json')
    copy(verify_pin(preflight['input_audits']), 'preflight/input_audits.jsonl')
    for index, pin in enumerate(header['core']['runtime'] + score['scorer_closure']):
        copy(verify_pin(pin), f'code/{index:03d}_{Path(pin["path"]).name}')
    for index, pin in enumerate(scoring_manifest['source_bindings']):
        copy(verify_pin(pin), f'sources/{index:03d}_{Path(pin["path"]).name}')
    provenance = {'model': header['core']['model_snapshot'], 'adapter': header['core']['adapter'],
                  'source_path_to_archive': sources}
    pin = write_once(output / 'provenance.json', provenance, artifact_root, score['paper_cell'])
    copied['provenance.json'] = pin['sha256']
    receipt = {'schema': 'student-answer-bank-export-v1', 'bank_id': bank_id, 'paper_cell': score['paper_cell'],
               'expected_count': score['expected_count'], 'terminal_count': score['terminal_count'],
               'source_run': binding(run / 'run.json'), 'source_score': binding(score_path),
               'shared_registry_status': 'pending', 'publication_ready': False,
               'raw_native_outputs_preserved': True, 'coverage_complete': score['coverage_complete'],
               'registration_handoff': 'Campaign archiver must copy this immutable bank, update the locked registry/hash authority, and mirror metadata shards <=100 KB.'}
    pin = write_once(output / 'export_receipt.json', receipt, artifact_root, score['paper_cell'])
    copied['export_receipt.json'] = pin['sha256']
    for relative, expected in copied.items():
        binding(output / relative, expected)
    manifest_pin = write_once(output / 'SHA256_MANIFEST.json', copied, artifact_root, score['paper_cell'])
    return {**receipt, 'archive': str(output), 'sha_manifest': manifest_pin}
