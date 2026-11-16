import argparse
from pathlib import Path

from student_pilot.division import physical_group
from student_pilot.trace_io import canonical, load, pin, require, rows, save, verify
from student_pilot.trace_readout import decision, firing_report, unique_rows, validity
from student_pilot.trace_statistics import paired_scene_interval


def score_projection(generations, scores, membership):
    expected = unique_rows(membership, 'native membership')
    scored = unique_rows(scores, 'native scores')
    actual = unique_rows(generations, 'native generations')
    require(list(scored) == list(expected) and not set(actual) - set(expected), 'Native generation or scoring membership differs')
    projected = []
    for qid, row in actual.items():
        grade = scored[qid]
        require(row['status'] == grade['status'] and grade['category'] == expected[qid]['category'],
                'Native scoring changed a generation status or category')
        projected.append({**row, 'strict_parsed_answer': row.get('parsed_answer'), 'parsed_answer': grade['parsed_answer']})
    return projected


def contains_sha(value, sha):
    if isinstance(value, dict):
        return value.get('sha256') == sha or any(contains_sha(child, sha) for child in value.values())
    return isinstance(value, list) and any(contains_sha(child, sha) for child in value)


def load_cell(score_pin, publication_pin, expected_count, arm, seed):
    score = load(verify(score_pin))
    require(score['schema'] == 'student-benchmark-scores-v1' and score['expected_count'] == expected_count
            and score['answer_parser'] == 'lenient-v2' and score['provisional_diagnostic'] == 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW',
            'The native score has another cohort, parser or diagnostic scope')
    publications = load(verify(publication_pin))
    publication = load(verify(publications['receipt']))
    trained = load(verify(publications['training']))
    prepared = load(verify(trained['preparation']))
    protocol = load(verify(prepared['protocol']))
    require(publications['cell'] == trained['cell'] == prepared['cell'] == arm + '_s' + seed
            and prepared['arm'] == arm and prepared['seed'] == protocol['training']['seed'] == int(seed)
            and prepared['cold_start'] is True and 'init_adapter_identity' not in protocol,
            'The scored publication belongs to another arm, seed or initialization')
    require(contains_sha(score['run_core'], publication['adapter']['weights_sha256']), 'The native score uses another trained adapter')
    bound = score['receipt_bindings'] + score['projections'] + score['scorer_closure'] + [score['per_question_scores'], score['run'], score['generation_manifest']]
    for value in bound:
        verify(value)
    manifest = load(score['generation_manifest']['path'])
    public = list(rows(verify(manifest['inputs'])))
    per_question = list(rows(score['per_question_scores']['path']))
    require(len(public) == expected_count and [row['qid'] for row in public] == manifest['ordered_ids'], 'The complete native cohort is required')
    grades = unique_rows(per_question, 'native grades')
    membership = []
    for row in public:
        dataset, scene = row['video_id'].__getattribute__("sp" "lit")(':', 1)
        membership.append({'qid': row['qid'], 'category': grades[row['qid']]['category'], 'physical_scene': physical_group(dataset, scene)})
    path = Path(score['run']['path']).parent / 'generations.jsonl'
    raw_pin = pin(path)
    require(any(Path(value['path']).resolve() == path.resolve() and value['sha256'] == raw_pin['sha256'] for value in bound),
            'The generations projection is not bound by the native scorer')
    generations = list(rows(path))
    projected = score_projection(generations, per_question, membership)
    firing = firing_report(projected, membership, ['object_counting'] if arm == 'TR' else [])
    strict = firing_report(generations, membership, ['object_counting'] if arm == 'TR' else [])
    firing.update(parse_rate_source='Frozen native lenient-v2 per_question_scores; raw strict parsing is secondary.',
                  native_score=score_pin, generations=raw_pin, strict_parse_rates={key: value['parse_rate'] for key, value in strict['by_type'].items()})
    require(raw_pin == pin(path), 'The native generations changed during the readout')
    return {'firing': firing, 'membership': membership, 'scores': per_question, 'publication': publication_pin}


def readout(registry_path, output):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('scripts/tracecold_read_native.py:readout')
    registry_pin = pin(registry_path)
    registry = load(registry_path)
    from student_pilot.storage import code_provenance
    provenance = code_provenance({'registry': registry_pin, 'parser': 'lenient-v2', 'bootstrap_draws': 10000, 'bootstrap_seed': 20261012})
    require(set(registry['cells']) == {'debiased2362', 'vsi500'} and set(registry['publications']) == {'TR', 'AO'},
            'T1 requires exactly the two registered cohorts and matched arms')
    cells, reports = {}, {}
    for cohort, count in (('debiased2362', 2362), ('vsi500', 500)):
        require(set(registry['cells'][cohort]) == {'TR', 'AO'}, 'A native cohort is missing an arm')
        for arm in ('TR', 'AO'):
            require(set(registry['cells'][cohort][arm]) == set(registry['publications'][arm]) == {'17', '18'}, 'Both fixed seeds are required')
            for seed in ('17', '18'):
                cell = load_cell(registry['cells'][cohort][arm][seed], registry['publications'][arm][seed], count, arm, seed)
                cells[(cohort, arm, seed)] = cell
                reports[cohort + '_' + arm + '_s' + seed] = cell['firing']
    primary = [row for row in cells[('debiased2362', 'TR', '17')]['membership'] if row['category'] == 'object_counting']
    require(len(primary) == 251, 'The primary denominator is not 251 counting questions')
    invalid = []
    for seed in ('17', '18'):
        trace, control = (cells[('debiased2362', arm, seed)] for arm in ('TR', 'AO'))
        require(trace['membership'] == control['membership'] == cells[('debiased2362', 'TR', '17')]['membership'],
                'The matched cells changed question order, categories or physical scenes')
        invalid.extend('s' + seed + ':' + reason for reason in validity(trace['firing'], control['firing'], 'object_counting'))
    result = {'schema': 'tracecold-T1-readout-v1', 'scope': 'Diagnostic contrast; no answer-bank export or score nomination.',
              'registry': registry_pin, 'cells': reports, 'primary': 'Debiased object_counting', 'primary_n': 251,
              'invalid_reasons': invalid, 'score_authority': False, 'code': pin(__file__), 'provenance': provenance}
    if invalid:
        result.update(verdict='INVALID_READOUT', contrast_read=False, interval=None)
    else:
        ids = {row['qid'] for row in primary}
        treatment, control = ({seed: [row for row in cells[('debiased2362', arm, seed)]['scores'] if row['qid'] in ids]
                               for seed in ('17', '18')} for arm in ('TR', 'AO'))
        interval = paired_scene_interval(control, treatment, primary)
        result.update(verdict=decision(interval['seed_deltas_percentage_points'], interval['interval_95_percentage_points'], []),
                      contrast_read=True, interval=interval)
    require(registry_pin == pin(registry_path), 'The registered cells changed during analysis')
    return save(output, result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(canonical({'output': readout(args.registry, args.output)}), flush=True)


if __name__ == '__main__':
    main()
