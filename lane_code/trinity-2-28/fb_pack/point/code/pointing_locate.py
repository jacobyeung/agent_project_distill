"""Transform only stored pointing target text; verify with the supplied native reader."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path('/scratch/jjyeung/orch_n30/fb_pack/point')
TREE = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
SOURCE = Path('/scratch/jjyeung/orch_n30/fb_pack/in/pointing/rows_c09bb5ca.sqlite')
SOURCE_SHA = 'c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938'
OLD_RECEIPT = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/ext/preceipts/rc3/pool_7c9f2d84_receipt.json')
OLD_RECEIPT_SHA = '93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a'
OUT = ROOT / 'out'
DB = OUT / 'rows_pointing_locate.sqlite'
EMPTY = '<think>\n\n</think>\n\n'
# The review's forty SQL indices, printed in the task's named evidence file.
SAMPLE = [101,200,677,899,1648,1807,1918,2008,5471,5972,7099,7102,7398,7592,8321,9005,9273,9816,10357,10825,11861,12697,14536,15668,15760,15943,16621,16924,18079,18394,18536,19868,19930,19995,21822,22217,22702,23106,23413,23739]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def pin(path):
    return {'path': str(path), 'sha256': sha(path)}


def write_json(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def status(text):
    (ROOT / 'STATUS.md').write_text(text + '\n')


def connect(path):
    return sqlite3.connect(Path(path).as_uri() + '?mode=ro', uri=True)


def parameters(row):
    p = row['pointing']
    q = row['student_input']['question']
    m = re.match(r'Point to the (.+?) in frame ([0-9]+)\.', q)
    assert m and m[1] == p['label'] and int(m[2]) == p['frame'], row['qid']
    assert f'If there is no {p["label"]} in frame {p["frame"]}, output ' in q
    assert type(p['frame']) is int and 1 <= p['frame'] <= len(row['student_input']['frames'])
    assert p['label'] and not any(c in p['label'] for c in '\r\n<>')
    return p['label'], p['frame']


def transformed(row):
    label, frame = parameters(row)
    target = row['target']
    assert target.startswith(EMPTY) and target.count('</think>') == 1, row['qid']
    answer = target[len(EMPTY):]
    value = json.loads(answer)
    assert set(value) == {'point_2d'}
    absent = value['point_2d'] is None
    assert absent == (row['pointing']['kind'] == 'gt_absent'), row['qid']
    body = f'Locate the {label} in frame {frame}'
    body += ': it is not visible in that frame.' if absent else '.'
    return f'<think>\n{body}\n</think>\n\n{answer}', answer, body


def build():
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(OLD_RECEIPT) == OLD_RECEIPT_SHA
    if DB.exists():
        raise FileExistsError(DB)
    src = connect(SOURCE)
    dst = sqlite3.connect(DB)
    src.backup(dst)
    changed = 0
    for i, raw, auxiliary in src.execute('SELECT i,row,target FROM rows ORDER BY i'):
        row = json.loads(raw)
        target, _, _ = transformed(row)
        before = '"target": ' + json.dumps(row['target'])
        after = '"target": ' + json.dumps(target)
        assert raw.count(before) == 1, (i, 'target serialization')
        updated = raw.replace(before, after, 1)
        assert json.loads(updated) == {**row, 'target': target}
        dst.execute('UPDATE rows SET row=? WHERE i=?', (updated, i))
        changed += 1
    assert changed == 25020
    dst.commit()
    dst.close()
    src.close()
    (OUT / 'rows_pointing_locate.sqlite.sha256').write_text(f'{sha(DB)}  rows_pointing_locate.sqlite\n')
    status('Stage 2: The replacement SQLite store contains one Locate line in each of 25,020 targets. The transform preserves each exact label, frame, and JSON answer. Seven labels contain digits, so their exact labels conflict with the strict no-extra-digit check. Full native-reader validation is pending.')
    print(json.dumps({'stage': 'build', 'rows': changed, 'bytes': DB.stat().st_size, 'sha256': sha(DB)}), flush=True)


def native_imports():
    sys.path.insert(0, str(TREE))
    import torch
    torch.set_num_threads(16)
    from student_pilot import carrier_c1_run, carrier_c1_data, r2_contract, r1_training, trace_grammar, r1_handover
    return carrier_c1_run, carrier_c1_data, r2_contract, r1_training, trace_grammar, r1_handover


def verify():
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(OLD_RECEIPT) == OLD_RECEIPT_SHA
    run, data, contract, training, grammar, handover = native_imports()
    receipt = json.loads(OLD_RECEIPT.read_text())
    assert receipt['database']['sha256'] == SOURCE_SHA
    before_reader = run.Rows({'streams': {'pointing': {'database': pin(SOURCE), 'count': receipt['count']}}}, None)
    after_reader = run.Rows({'streams': {'pointing': {'database': pin(DB), 'count': receipt['count']}}}, None)
    old_db, new_db = connect(SOURCE), connect(DB)
    assert old_db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master').fetchall() == new_db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master').fetchall()
    assert new_db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    old_counts, new_counts, old_types, new_types = Counter(), Counter(), Counter(), Counter()
    failures, shared_errors, shared_examples = [], Counter(), {}
    strict_digit_failures, samples, scenes = [], {}, set()
    tallies = Counter()
    ids = set()
    for (i, old_raw, old_aux), (j, new_raw, new_aux) in zip(old_db.execute('SELECT * FROM rows ORDER BY i'), new_db.execute('SELECT * FROM rows ORDER BY i'), strict=True):
        assert i == j == tallies['rows']
        old, old_record = before_reader.row('pointing', i)
        new, new_record = after_reader.row('pointing', i)
        assert old_aux == new_aux and old_record == new_record
        expected, answer, body = transformed(old)
        assert new['target'] == expected
        assert new == {**old, 'target': expected}
        assert new_raw == old_raw.replace('"target": ' + json.dumps(old['target']), '"target": ' + json.dumps(expected), 1)
        assert new['target'].split('</think>\n\n', 1)[1].encode() == answer.encode()
        label, frame = parameters(new)
        assert len(body.splitlines()) == 1
        assert body == f'Locate the {label} in frame {frame}' + (': it is not visible in that frame.' if json.loads(answer)['point_2d'] is None else '.')
        if re.findall(r'\d+', body) != [str(frame)]:
            strict_digit_failures.append({'i': i, 'qid': new['qid'], 'label': label, 'frame': frame, 'think': body})
        # Every digit must belong to the exact source label or the frame index.
        assert re.findall(r'\d+', body) == re.findall(r'\d+', label) + [str(frame)]
        assert new['qid'] not in ids
        ids.add(new['qid'])
        scenes.add(new['dataset'] + '/' + new['scene'])
        assert data.single_image_row(new, 'pointing') is False
        for row, counts, types in ((old, old_counts, old_types), (new, new_counts, new_types)):
            contract.validate(row, 'pointing', require_frames=False)
            contract.perception(row, 'pointing', {})
            training.row_check(row, 'pointing')
            counts[row['dataset'] + '/' + row['pointing']['kind']] += 1
            types[row['question_type']] += 1
        tallies['native_validator_pass'] += 1
        # Diagnostic only: pointing does not invoke the shared VQA direct grammar.
        errors = grammar.validate_row({**new, 'answer': answer, 'form': 'direct'})
        if errors:
            for rule in {e.rule_id for e in errors}:
                shared_errors[rule] += 1
                shared_examples.setdefault(rule, {'i': i, 'qid': new['qid'], 'think': body, 'errors': [e._asdict() for e in errors]})
        else:
            tallies['shared_grammar_pass_diagnostic'] += 1
        if i in SAMPLE or any(v['i'] == i for v in strict_digit_failures):
            samples[i] = (old, new)
        tallies['rows'] += 1
    assert tallies['rows'] == receipt['count'] == before_reader.count('pointing') == after_reader.count('pointing') == 25020
    assert old_counts == new_counts and old_types == new_types
    assert len(scenes) == receipt['scenes']
    for reader in (before_reader, after_reader):
        for c in reader.connections.values(): c.close()
    old_db.close(); new_db.close()
    # Hash all tree modules loaded by the actual reader/validators, plus static evidence.
    sources = {Path(m.__file__).resolve() for m in tuple(sys.modules.values()) if getattr(m, '__file__', None) and Path(m.__file__).resolve().is_relative_to(TREE)}
    for name in ('student_pilot/pose_samples.py', 'student_pilot/batches.py', 'student_pilot/r2_grammar.py', 'launch_r2/build.py', 'launch_r2/staging.py', 'launch_r2/staging_sources.json', 'trace_format/box_v313.py', 'generator/derivgen_v7/derivgen/box_v313.py'):
        sources.add(TREE / name)
    inputs = [pin(SOURCE), pin(OLD_RECEIPT), pin(Path(__file__).resolve()), pin(ROOT / 'code/run.sh')] + [pin(p) for p in sorted(sources)]
    rule = {
        'schema': 'pointing-locate-transform-v1', 'inputs': inputs,
        'source_store': pin(SOURCE), 'source_receipt': pin(OLD_RECEIPT),
        'target_rule': '<think>\nLocate the <exact pointing.label> in frame <pointing.frame>.\n</think>\n\n<unchanged answer bytes>',
        'null_target_rule': '<think>\nLocate the <exact pointing.label> in frame <pointing.frame>: it is not visible in that frame.\n</think>\n\n<unchanged answer bytes>',
        'label_frame_authority': 'pointing.label and pointing.frame, checked against both clauses of student_input.question',
        'edits': 'Only the JSON-serialized row.target value in the rows.row SQLite column; rows.target auxiliary column stays byte-identical.',
        'digit_conflict': 'Exact source labels take precedence over removing label digits; strict failures are enumerated in CHECKS.json.',
        'command': 'bash code/run.sh build; bash code/run.sh verify',
        'builder': {'native_build_stream_can_preserve_target': False, 'reason': 'carrier_c1_data.py:650-654 recomputes mask answers and writes READOUT_TARGET + target, erasing Locate text.'},
    }
    write_json(OUT / 'TRANSFORM.json', rule)
    from student_pilot.p3_provenance import write, file_pin
    # A derived receipt preserves inherited division/GT assertions; it does not re-prove masks or splits.
    derived = {**receipt, 'database': file_pin(DB), 'source': file_pin(OUT / 'TRANSFORM.json'),
               'source_receipt': pin(OLD_RECEIPT), 'inputs': inputs + [pin(DB), pin(OUT / 'TRANSFORM.json')],
               'provenance_scope': 'Target-only derivative; count/scenes verified here; division and GT-mask evidence inherited unchanged.'}
    write(OUT / 'receipt_pointing_locate.json', derived)
    assert handover.stream_identity(derived, 'pointing') == sha(DB)
    assert handover.prepared_stream_identity(derived, {'database': pin(DB)}, 'pointing') == (sha(DB), 25020)
    with data._source_lines(pin(OUT / 'receipt_pointing_locate.json'), True, 'pointing') as rows:
        source_rows = sum(1 for _ in rows)
    assert source_rows == 25020
    lines = ['# Forty pointing targets before and after', '', 'These are the forty SQL indices listed in the named review evidence. The source store and transform hashes are in CHECKS.json. The command is `bash code/run.sh verify`.', '']
    for i in SAMPLE:
        old, new = samples[i]
        lines += [f'## Row {i}: {old["qid"]}', '', f'Type: {old["pointing"]["kind"]}. Label: `{old["pointing"]["label"]}`. Frame: {old["pointing"]["frame"]}.', '', old['student_input']['question'], '', 'Before:', '```text', old['target'], '```', '', 'After:', '```text', new['target'], '```', '']
    lines += ['# Exact source labels with digits', '', 'These seven additional rows fail the strict no-extra-digit condition. Their labels and JSON answers remain unchanged.', '']
    for v in strict_digit_failures:
        lines += [f'- Row {v["i"]}, `{v["qid"]}`: `{v["think"]}`']
    (OUT / 'READ40.md').write_text('\n'.join(lines) + '\n')
    checks = {
        'schema': 'fbp-point-checks-v1', 'status': 'QUALIFIED: seven exact source labels conflict with the strict digit rule',
        'command': 'bash code/run.sh verify', 'inputs': inputs + [pin(DB), pin(OUT / 'TRANSFORM.json'), pin(OUT / 'receipt_pointing_locate.json')],
        'source_sha256_verified': True, 'sqlite_integrity': 'ok', 'schema_identical': True,
        'rows': tallies['rows'], 'scenes': len(scenes), 'unique_qids': len(ids),
        'old_counts': dict(old_counts), 'new_counts': dict(new_counts), 'old_question_types': dict(old_types), 'new_question_types': dict(new_types),
        'row_order_ids_identical': True, 'only_serialized_target_changed': True,
        'json_answer_bytes_unchanged': tallies['rows'], 'question_label_frame_match': tallies['rows'],
        'one_locate_line': tallies['rows'], 'no_coordinate_digits_in_trace': tallies['rows'],
        'strict_no_digits_except_frame': {'pass': not strict_digit_failures, 'pass_rows': tallies['rows'] - len(strict_digit_failures), 'fail_rows': len(strict_digit_failures), 'failures': strict_digit_failures},
        'native_reader': {'entry': 'student_pilot.carrier_c1_run.Rows.__init__/row/count', 'old_rows': tallies['rows'], 'new_rows': tallies['rows'], 'receipt_source_iterator_rows': source_rows, 'scope': 'Real database reader with minimal stream receipt, without sealed membership, frame reads, model, or processor.'},
        'native_validator': {'pass_rows': tallies['native_validator_pass'], 'entries': ['student_pilot.r2_contract.validate(require_frames=False)', 'student_pilot.r2_contract.perception', 'student_pilot.r1_training.row_check', 'student_pilot.row_text_audit.check via Rows.row']},
        'shared_grammar_diagnostic': {'required_by_pointing_stream': False, 'pass_rows': tallies['shared_grammar_pass_diagnostic'], 'per_rule_failing_rows': dict(shared_errors), 'examples': shared_examples, 'note': 'Applied without rewriting the grammar or changing the null wording; absence is forbidden for direct VQA traces.'},
        'read40_count': len(SAMPLE), 'read40_indices': SAMPLE,
        'new_database': {**pin(DB), 'bytes': DB.stat().st_size}, 'new_receipt': pin(OUT / 'receipt_pointing_locate.json'),
        'stream_identity': handover.stream_identity(derived, 'pointing'),
        'native_build_stream_receipt': 'NOT RUN: it would regenerate targets and erase Locate text; also requires the original division, masks, RGB, and source selection.',
        'derived_receipt': 'Produced on CPU using native p3_provenance.write/file_pin; authenticates a target-only derivative, not a mask rebuild.',
        'not_executed': ['RGB/mask revalidation', 'full prepared membership admission', 'tokenizer/image encoding', 'training'],
    }
    write_json(OUT / 'CHECKS.json', checks)
    for p in (OUT / 'TRANSFORM.json', OUT / 'receipt_pointing_locate.json', OUT / 'CHECKS.json'):
        p.with_name(p.name + '.sha256').write_text(f'{sha(p)}  {p.name}\n')
    status(f'Stage 3: All {tallies["rows"]:,} transformed rows pass the supplied native pointing validators and open through the real Rows reader. Schema, IDs, row order, auxiliary targets, other row bytes, JSON answer bytes, and type counts match. Seven exact source labels fail the strict digit rule; CHECKS.json lists them. The derived receipt and forty before/after examples are complete. Pin instructions and packaging remain.')
    print(json.dumps({'stage': 'verify', 'rows': tallies['rows'], 'counts': dict(new_counts), 'native_pass': tallies['native_validator_pass'], 'digit_failures': len(strict_digit_failures), 'shared_errors': dict(shared_errors), 'new_sha256': sha(DB)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('build', 'verify'))
    args = parser.parse_args()
    {'build': build, 'verify': verify}[args.stage]()
