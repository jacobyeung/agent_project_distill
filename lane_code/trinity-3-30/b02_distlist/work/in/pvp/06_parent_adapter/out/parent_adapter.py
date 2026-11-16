#!/usr/bin/env python3
"""Build a score-only parent direct input and run the pinned analysis, using stdlib."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

BUILD = Path(__file__).resolve().parents[1]
ROOT = BUILD.parents[1]
OUT = BUILD / 'out'
RESULT = ROOT / 'builds/05_analysis_fix/out/real_parent'
SCRIPT = ROOT / 'builds/05_analysis_fix/out/native_vs_direct.py'
SCRIPT_SHA = '44468e7201200d611eddef7449ead57ccb7c3be32ed2230a2bc747801070c8d8'
PYTHON = ROOT / 'env312/bin/python3.12'
TYPES = ('object_abs_distance', 'room_size_estimation')
PATHS = {
    'bundle': ROOT / 'work/full_c8r/x/native/R1.json',
    'admission': ROOT / 'work/full_c8r/x/native/paired/IN_JOB_ADMISSION.json',
    'config': ROOT / 'work/full_c8r/x/metadata/CONFIG.json',
    'compact': ROOT / 'work/direct/DIRECT_B2048_COMPACT.json',
    'raw_main': ROOT / 'builds/05_analysis_fix/in/direct_raw/items_leg_m544_main.jsonl',
    'raw_camera': ROOT / 'builds/05_analysis_fix/in/direct_raw/items_leg_m544_camera.jsonl',
    'parent': ROOT / 'work/parent/r5/merge_results/B2048.json',
    'kit': ROOT / 'work/parent/r5/merge_results/B2048_kit_summary.json',
    'merge_inputs': ROOT / 'work/parent/r5/merge_results/MERGE_INPUTS.json',
    'merge_complete': ROOT / 'work/parent/r5/merge_results/MERGE_COMPLETE.json',
    'tasks': ROOT / 'work/parent/r3/TASKS.jsonl',
    'frames': ROOT / 'work/parent/r3/FRAMES.json',
    'strata': ROOT / 'work/parent/r3/STRATA.jsonl',
    'native_tasks': ROOT / 'work/meta/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl',
    'native_frames': ROOT / 'work/meta/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json',
}
PINS = {
    'bundle': '75669a6300aeeaf1ec98ef1dbd2b5276a7607422d92d9624af0d64a9c82154c0',
    'admission': '5d9e50107ab957ce330737b20d88bf0604f7e2a2514fb44d3373748da12ed7ac',
    'compact': '0ece1ea5e9f04c50fad3060ee94b9867fc789dfcbf765d2f6040cff24ce98428',
    'parent': '53a382bb1c3ae9db4bfee5efb8ea4efaaa9b0d9b30d046ac00692bcd19cd8d05',
    'kit': '577e939785b4f5d95958c3bc36b4e338dc28c83e01592d175411ca21a413a16a',
    'tasks': 'a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e',
    'frames': 'c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439',
}


class Refusal(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Refusal(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_script(path=SCRIPT):
    observed = sha(path)
    require(observed == SCRIPT_SHA, 'script sha mismatch: ' + str(path))
    return observed


def analysis_module():
    verify_script()
    spec = importlib.util.spec_from_file_location('confirmed_analysis', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.label({'stratum': 'primary'}) == 'released_answer'
            and module.label({'stratum': 'other'}) == 'answer', 'script label rule changed')
    return module


def read(path):
    return json.loads(Path(path).read_bytes())


def lines(path):
    return [json.loads(b) for b in Path(path).read_bytes().splitlines() if b.strip()]


def write(path, data):
    path = Path(path).resolve()
    require(path.is_relative_to(BUILD) or path.is_relative_to(RESULT), 'write outside permitted roots')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def index(rows, field='key'):
    result = {}
    for row in rows:
        key = row[field]
        require(key not in result, 'duplicate ' + field + ': ' + key)
        result[key] = row
    return result


def array_spans(text):
    """Return exact object spans; preserve every byte outside substituted objects."""
    decoder = json.JSONDecoder()
    pos = 0
    while text[pos].isspace():
        pos += 1
    require(text[pos] == '[', 'compact input must be an array')
    pos += 1
    while True:
        while text[pos].isspace():
            pos += 1
        if text[pos] == ']':
            require(not text[pos + 1:].strip(), 'compact trailing data')
            return
        start = pos
        row, pos = decoder.raw_decode(text, pos)
        require(isinstance(row, dict), 'compact row must be an object')
        yield start, pos, row
        while text[pos].isspace():
            pos += 1
        require(text[pos] in ',]', 'invalid compact separator')
        if text[pos] == ',':
            pos += 1


def validate(bundle, parent, kit, tasks, frames, config, compact, raw, strata=None, full=True):
    """Validate identity independently of file pins, so mutation tests reach each guard."""
    n = analysis_module()
    keys = set(bundle['expected_keys'])
    require(len(keys) == len(bundle['expected_keys']), 'duplicate native expected key')
    arms = {a: index(bundle['arms'][a]) for a in n.ARMS}
    require(all(set(x) == keys for x in arms.values()), 'native key mismatch')
    parents = index(parent['rows'])
    taskmap = index([dict(t, key='devrows:' + t['id']) for t in tasks])
    captures = index(frames['captures'], 'native')
    ci, ri = index(compact), index(raw)
    target = {k for k in keys if arms['unflagged'][k]['question_type'] in TYPES}
    require(keys & set(parents) == target, 'parent key mismatch or unexpected camera coverage')
    require(target and target <= set(taskmap) & set(ci) & set(ri), 'missing paired key')
    counts = Counter(arms['unflagged'][k]['question_type'] for k in target)
    if full:
        require(counts == dict(zip(TYPES, (150, 36))), 'paired type count mismatch')
        require(len(keys - target) == 450, 'camera count mismatch')
    require(parent['model'] == kit['model'] == 'cp1m200', 'parent model mismatch')
    budget = kit['budget_arm']
    require(parent['arm'] == budget['arm'] == 'B2048', 'parent arm mismatch')
    require(kit['layout'] == budget['layout'] == 'duplicate', 'parent layout mismatch')
    require(kit['frames'] == budget['frames'] == 32, 'parent frame count mismatch')
    require(budget['budget'] == 2048 and budget['answer_cap'] == 64, 'parent decode budget mismatch')
    benchmark = kit['benchmarks']['devrows']
    require(benchmark['expected'] == benchmark['completed'] == len(parents), 'incomplete parent summary')
    require(kit['derivation']['total'] == len(parents), 'derivation denominator mismatch')
    require(kit['parity_pass'] is True and benchmark['errors'] == 0, 'parent admission failed')
    audit = config['full_projection']['parity']['P3']['trainer_audit']
    indices = audit['original_frame_indices']
    stamps = audit['original_timestamps_seconds']
    require(audit['frame_count'] == len(indices) == len(stamps) == 64, 'native duplicated frame count mismatch')
    require(audit['do_sample_frames'] is False and indices[::2] == indices[1::2]
            and stamps[::2] == stamps[1::2], 'native duplicate layout mismatch')
    require(audit['temporal_patch_timestamps_seconds'] == stamps[::2], 'native processor timestamps mismatch')
    require(all(math.isclose(t, i / audit['fps'], abs_tol=1e-8) for i, t in zip(indices, stamps)),
            'native timestamp fps mismatch')
    require(any(c['anchor_indices'] == indices[::2] and math.isclose(c['fps'], audit['fps'])
                for c in captures.values()), 'native processor audit lacks matching capture')
    records, decode_counts = [], Counter()
    si = index(strata) if strata is not None else None
    for typ, count in counts.items():
        d = kit['derivation']['per_type'][typ]
        require(all(d[k] == 0 for k in ('forced_close', 'stopped_unclosed', 'derivation_error')),
                'nonzero derivation count: ' + typ)
        require({k for k, p in parents.items() if p['question_type'] == typ} ==
                {k for k in target if parents[k]['question_type'] == typ}, 'parent type coverage mismatch')
        values = [parents[k]['scores'][n.label(taskmap[k])] for k in target if parents[k]['question_type'] == typ]
        reported = benchmark['per_type'][typ]
        require(reported['count'] == count and math.isclose(sum(values) / count, reported['score'], abs_tol=1e-12),
                'parent per-type mean mismatch: ' + typ)
    for key in sorted(target):
        t, p, dr = taskmap[key], parents[key], ri[key]
        typ = t['question_type']
        for field in ('key', 'question_type', 'room', 'stratum'):
            require(p[field] == t[field], 'parent ' + field + ' mismatch: ' + key)
            require(ci[key][field] == t[field] and dr[field] == t[field], 'student ' + field + ' mismatch: ' + key)
            for arm in n.ARMS:
                require(arms[arm][key][field] == t[field], 'native ' + field + ' mismatch: ' + key)
        for field in ('question', 'options', 'released_answer', 'ground_truth', 'answer', 'native', 'id', 'scorer'):
            require(dr[field] == t[field], 'TASKS ' + field + ' mismatch: ' + key)
        require(str(t['ground_truth']).strip() == str(t[n.label(t)]).strip(), 'TASKS ground truth mismatch: ' + key)
        require(t['scorer'] == 'official_vsi_mra' and t['stratum'] == 'primary', 'paired scorer or label mismatch')
        if si is not None:
            for field in ('question_type', 'room', 'stratum', 'answer', 'released_answer'):
                require(si[key][field] == t[field], 'STRATA ' + field + ' mismatch: ' + key)
        frame = captures[t['native']]
        anchors = kit['anchor_indices'][key]
        require(anchors == t['source_frame_indices'] == frame['anchor_indices'], 'anchor mismatch: ' + key)
        require(anchors == [f['index'] for f in frame['frames']] and len(anchors) == kit['frames'], 'frame index mismatch: ' + key)
        require(frame['scene'] == t['scene'] and frame['fps'] == t['fps'], 'capture metadata mismatch: ' + key)
        require(all(math.isclose(a / frame['fps'], s, abs_tol=1e-8) for a, s in zip(anchors, frame['timestamps']))
                and len(frame['timestamps']) == len(anchors), 'capture timestamp mismatch: ' + key)
        if 'anchor_indices' in benchmark:
            require(benchmark['anchor_indices'][t['id']] == anchors, 'benchmark anchor mismatch: ' + key)
        for arm in n.ARMS:
            row = arms[arm][key]
            require(row['perception']['frame_indices'] == anchors, 'native anchor mismatch: ' + key)
            require(row['perception']['frame_sha256'] == [f['sha256'] for f in frame['frames']], 'frame-sha mismatch: ' + key)
            if arm == 'unflagged':
                if row.get('geometry_refusal'):
                    require(not row.get('decode') and row['no_answer'], 'refused item unexpectedly decoded')
                    decode_counts['geometry_refused_without_decode'] += 1
                else:
                    db = row['decode']['decode_budget']
                    require(db['thinking_tokens'] == budget['budget'] and db['answer_tokens'] == budget['answer_cap'],
                            'native decode budget mismatch: ' + key)
                    decode_counts['decoded_budget_checked'] += 1
        for flag in ('capped', 'unparsed', 'unanswered'):
            require(isinstance(p[flag], bool), 'parent flag is not boolean: ' + key)
        score = p['scores'][n.label(t)]
        require(isinstance(score, (float, int)) and math.isfinite(score) and 0 <= score <= 1, 'invalid parent score')
        require(not any(p[f] for f in ('capped', 'unparsed', 'unanswered')) or score == 0, 'flagged parent score is nonzero')
        records.append(dict(key=key, question_type=typ, room=t['room'], stratum=t['stratum'],
                            capture=t['native'], question=t['question'], options=t['options'],
                            released_answer=t['released_answer'], ground_truth=t['ground_truth'],
                            anchor_indices=anchors, frame_sha256=row['perception']['frame_sha256'],
                            parent_score=score, label=n.label(t), review_status='pending one reader'))
    flag_counts = {typ: {f: sum(parents[k][f] for k in target if parents[k]['question_type'] == typ)
                         for f in ('capped', 'unparsed', 'unanswered')} for typ in counts}
    require(all(benchmark[f] == 0 for f in ('cap_hits', 'parse_failures', 'unanswered')),
            'parent benchmark flag count is nonzero')
    require(all(v == 0 for d in flag_counts.values() for v in d.values()), 'parent paired flag count is nonzero')
    return dict(status='PASS', paired_counts=dict(counts), unpaired_camera_keys=sorted(keys - target),
                decode_checks=dict(decode_counts), parent_flags=flag_counts, items=records,
                native_layout_evidence='CONFIG full_projection.parity.P3 trainer_audit; representative processor audit',
                question_label_evidence='Shared TASKS bytes; CONFIG input hashes; student raw TASKS fields; parent STRATA binding',
                model_identity='cp1m200 from kit summary and request binding; no parent artifact digest checked')


def substitute(compact_text, raw_bytes, parents, kit, taskmap, selected):
    """Retain uncovered object slices and complete raw lines verbatim."""
    replacements, fields = {}, {}
    for _, _, row in array_spans(compact_text):
        key = row['key']
        if key not in selected:
            continue
        p, t = parents[key], taskmap[key]
        label = 'released_answer' if t['stratum'] == 'primary' else 'answer'
        changed = dict(row, score=p['scores'][label], hit_token_cap=p['capped'],
                       parse_failed=p['unparsed'] or p['unanswered'], forced_close=False,
                       stopped_unclosed=False, derivation_error=False, producer_error=False,
                       finish_reason='length' if p['capped'] else 'stop', model=kit['model'],
                       binding=kit['request_binding'],
                       adapter_evidence='parent summary; no raw generation',
                       finish_reason_evidence='normalized from flags; original unavailable')
        changed['kit_binding'] = kit['binding']
        replacements[key] = changed
    parts, cursor = [], 0
    for start, end, row in array_spans(compact_text):
        if row['key'] in replacements:
            parts.extend((compact_text[cursor:start], json.dumps(replacements[row['key']], ensure_ascii=True)))
            cursor = end
    parts.append(compact_text[cursor:])
    raw_out, seen = [], set()
    for line in raw_bytes.splitlines(keepends=True):
        if not line.strip():
            raw_out.append(line)
            continue
        old = json.loads(line)
        key = old['key']
        if key not in selected:
            raw_out.append(line)
            continue
        require(key not in seen, 'duplicate selected raw key')
        seen.add(key)
        new = dict(taskmap[key], **replacements[key])
        new.update(arm=kit['budget_arm']['arm'], status='complete', frames=kit['frames'], layout=kit['layout'],
                   anchor_indices=kit['anchor_indices'][key], answer_cap=kit['budget_arm']['answer_cap'])
        fields[key] = dict(set_fields=sorted(new), unavailable_student_fields=sorted(set(old) - set(new)))
        raw_out.append((json.dumps(new, ensure_ascii=True) + '\n').encode())
    require(seen == selected, 'raw selected key mismatch')
    return ''.join(parts).encode(), b''.join(raw_out), fields


def build_inputs():
    before = verify_script()
    sources = {k: dict(path=str(p), sha256=sha(p), bytes=p.stat().st_size) for k, p in PATHS.items()}
    for k, digest in PINS.items():
        require(sources[k]['sha256'] == digest, 'input sha mismatch: ' + k)
    for kind in ('tasks', 'frames'):
        require(PATHS[kind].read_bytes() == PATHS['native_' + kind].read_bytes(), 'shared ' + kind + ' byte mismatch')
    bundle, parent, kit, config = (read(PATHS[k]) for k in ('bundle', 'parent', 'kit', 'config'))
    merge, complete = read(PATHS['merge_inputs']), read(PATHS['merge_complete'])
    require(complete['export_sha256']['B2048'] == sources['parent']['sha256'], 'merge export digest mismatch')
    require(complete['receipt_sha256'] == sources['merge_inputs']['sha256'], 'merge receipt digest mismatch')
    require(complete['original_request_binding_unchanged'] is True and complete['journals_byte_identical'] is True,
            'merge completion not admitted')
    require(parent['request_binding'] == merge['request_binding'] and parent['source_sha256'] == merge['source_sha256'],
            'parent request binding mismatch')
    require(parent['strata_sha256'] == sources['strata']['sha256'], 'parent STRATA binding mismatch')
    for kind in ('tasks', 'frames'):
        require(config['worker']['inputs'][kind]['sha256'] == sources[kind]['sha256'], 'native CONFIG input mismatch')
    require(config['worker']['expected_keys'] == bundle['expected_keys'], 'native CONFIG keys mismatch')
    tasks, frames, strata = lines(PATHS['tasks']), read(PATHS['frames']), lines(PATHS['strata'])
    compact_text = PATHS['compact'].read_bytes().decode('utf-8')
    raw_bytes = PATHS['raw_main'].read_bytes()
    identity = validate(bundle, parent, kit, tasks, frames, config, json.loads(compact_text),
                        [json.loads(x) for x in raw_bytes.splitlines() if x.strip()], strata)
    selected = {x['key'] for x in identity['items']}
    taskmap = {('devrows:' + t['id']): t for t in tasks}
    adapted, raw, field_manifest = substitute(compact_text, raw_bytes, index(parent['rows']),
                                             dict(kit, request_binding=parent['request_binding']), taskmap, selected)
    require(len(adapted) + len(raw) < 20_000_000, 'adapted inputs exceed reserved space')
    compact_path, raw_path = OUT / 'DIRECT_PARENT_COMPACT.json', OUT / 'items_parent_main.jsonl'
    compact_path.write_bytes(adapted)
    raw_path.write_bytes(raw)
    identity.update(sources=sources, script_sha_before=before, script_sha_after=verify_script(),
                    parent_request_binding=parent['request_binding'], parent_kit_binding=kit['binding'])
    write(OUT / 'IDENTITY_CHECKS.json', identity)
    write(OUT / 'FIELD_MANIFEST.json', field_manifest)
    write(OUT / 'ADAPTED_INPUTS.json', dict(review_status='pending one reader', selected_keys=sorted(selected),
          direct=dict(path=str(compact_path), sha256=sha(compact_path)),
          direct_raw_main=dict(path=str(raw_path), sha256=sha(raw_path)),
          direct_raw_camera=sources['raw_camera'], sources=sources))
    return identity


def run_analysis():
    before = verify_script()
    cmd = [str(PYTHON), '-I', '-s', '-B', str(SCRIPT), '--bundle', str(PATHS['bundle']),
           '--admission', str(PATHS['admission']), '--direct', str(OUT / 'DIRECT_PARENT_COMPACT.json'),
           '--direct-raw', str(OUT / 'items_parent_main.jsonl'), str(PATHS['raw_camera']), '--output', str(RESULT)]
    (BUILD / 'STATUS.md').write_text('Status: identity checks passed; confirmed analysis CLI is running.\nEvidence: out/IDENTITY_CHECKS.json. All model results remain pending one reader.\n')
    with (OUT / 'analysis_cli.log').open('w') as log:
        completed = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=False)
    after = verify_script()
    write(OUT / 'CLI_RECEIPT.json', dict(command=cmd, returncode=completed.returncode,
          script_path=str(SCRIPT), script_sha_before=before, script_sha_after=after,
          log_path=str(OUT / 'analysis_cli.log')))
    require(completed.returncode == 0, 'confirmed analysis failed; see analysis_cli.log')


def reports():
    result = read(RESULT / 'NATIVE_VS_DIRECT.json')
    identity = read(OUT / 'IDENTITY_CHECKS.json')
    groups = {k: v for k, v in result['groups'].items() if k.split('/')[-1] in TYPES}
    note = ('The direct arm is cp1m200 by the parent kit summary and request binding. '
            'The confirmed script hashes the student EXPORT_ARTIFACT; that check does not identify the parent. '
            'No parent artifact digest is checked. Camera types do not pair: parent camera reads are not in this folder. '
            'The comparison crosses GPU types (parent on a Trinity card, native on an Orchard H100) '
            'and prompts (direct versus routed) by design; hardware provenance is supplied context.')
    unchecked = ['Parent raw generations, extracted answers, original finish reasons, token IDs, scorer execution and checkpoint bytes are unavailable or not rechecked.',
                 'Question text is absent from parent score rows and native R1 rows; equality is established through shared TASKS bytes and metadata bindings, not independently observed prompts.',
                 'Frame digest strings and anchor indices match; PNG bytes and per-item processor tensors were not reread. CONFIG supplies a representative duplicated-frame processor audit.',
                 'Geometry-refused native items have no decode receipt. Scripted rows have no thinking-budget receipt; the budget comparison applies to decoded native unflagged rows.',
                 'GPU identity, original parent request contents, original generation journals, upstream model training, room/venue ground truth, and gravity mathematics were not independently audited.',
                 'No independent reader has reviewed this comparison. All model numbers are pending one reader.']
    obj = dict(review_status='pending one reader', source=str(RESULT / 'NATIVE_VS_DIRECT.json'),
               identity_source=str(OUT / 'IDENTITY_CHECKS.json'), provenance=note, groups=groups,
               method=result['method'], claims={k:v for k,v in result['claims'].items() if k in groups},
               unit_scores={t: result['unit_scores_with_direct'][t] for t in TYPES},
               not_checked=unchecked, mixed_output_warning='Other script groups mix parent and student direct rows; they are not parent comparisons.')
    write(OUT / 'PAIRED_VS_PARENT.json', obj)
    source = str(RESULT / 'NATIVE_VS_DIRECT.json')
    md = ['# Native versus parent direct', '', 'All model numbers in this report are **pending one reader**.', '',
          note, '', 'Every table value comes from `' + source + '`; group and selection names identify its JSON location.',
          'The native column is the script\'s unflagged routed arm. Intervals are paired physical-room bootstrap intervals in percentage points.', '',
          '| Group | Primary: items / rooms; native / scripted / parent %; native−parent [CI]; scripted−parent [CI] | Capped zeroed: same fields |',
          '|---|---|---|']
    def fmt(x):
        return 'NA' if x is None else f'{x:.2f}'
    def cell(v):
        ds = []
        for a in ('unflagged', 'scripted'):
            d = v['differences'][a]
            interval = d['paired95_rooms']
            ds.append(fmt(d['points']) + (' [' + ', '.join(map(fmt, interval)) + ']' if interval else ' [NA]'))
        return f"{v['items']} / {v['rooms']}; " + ' / '.join(fmt(v[k]) for k in ('native_pct','scripted_pct','direct_pct')) + '; ' + '; '.join(ds)
    for name in [*TYPES, *(g+'/'+t for g in ('d1','d2','d3') for t in TYPES)]:
        md.append('| ' + name + ' | ' + cell(groups[name]['all_items']) + ' | ' + cell(groups[name]['capped_zeroed']) + ' |')
    md += ['', 'Sensitivity values also come from `' + source + '`; all model numbers remain **pending one reader**.', '',
           '| Group | Selection | Items / rooms; native / scripted / parent %; native−parent [CI]; scripted−parent [CI] |', '|---|---|---|']
    for name, selections in groups.items():
        for selection in ('metre_only', 'passed_geometry', 'no_producer_error'):
            md.append('| ' + name + ' | ' + selection + ' | ' + cell(selections[selection]) + ' |')
    md += ['', 'Unit summaries from `' + source + '` under `unit_scores_with_direct`; all model numbers are **pending one reader**.', '',
           '| Type | Unit group | All items / geometry-passed items | All-item native / scripted / parent % | Geometry-passed native / scripted / parent % |',
           '|---|---|---|---|---|']
    for typ in TYPES:
        units = result['unit_scores_with_direct'][typ]
        for name, value in [*units['groups'].items(), *[("exact: " + k, v) for k, v in units['exact_units'].items()]]:
            all_scores = ' / '.join(fmt(value['all_item_scores_pct'][a]) for a in ('unflagged','scripted','direct'))
            passed_scores = ' / '.join(fmt(value['scores_pct'][a]) for a in ('unflagged','scripted','direct'))
            md.append(f"| {typ} | {name} | {value['all_items']} / {value['items']} | {all_scores} | {passed_scores} |")
    md += ['', 'The JSON companion preserves the full precision of these unit summaries. The script supplies paired intervals for the metre-only sensitivity above, but not for each exact-unit summary.',
           'Other script groups mix parent and student direct rows. They must not be cited as parent comparisons.', '',
           'The method, seed, draw count and confidence level are recorded in `' + source + '` under `method`. '
           'Intervals are marginal, with no multiple-comparison adjustment; this is a descriptive dev comparison.', '',
           'Identity evidence: `' + str(OUT / 'IDENTITY_CHECKS.json') + '`. Field provenance and defaults: `' + str(OUT / 'DECISIONS.md') + '`.', '',
           'What was not checked:', ''] + ['- ' + x for x in unchecked]
    (OUT / 'PAIRED_VS_PARENT.md').write_text('\n'.join(md) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.report_only:
            reports()
        else:
            build_inputs()
            if not args.prepare_only:
                run_analysis()
                reports()
        print('PASS; evidence in ' + str(OUT))
    except (Refusal, KeyError, TypeError, OSError, ValueError) as exc:
        (BUILD / 'STATUS.md').write_text('Status: REFUSED. ' + str(exc) + '\n')
        print('REFUSED: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
