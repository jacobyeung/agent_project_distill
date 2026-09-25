import argparse
import ast
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import copy
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import re
import time

import numpy as np

from . import answer_fullpool as full
from . import compact_control as control
from tools.gtmeasure import assets, geometry
from tools.gtmeasure.conventions import box_corners
from tools.gtmeasure.formats import format_observation_value as format_number
from tools.gtmeasure.io import canonical, digest, read_json, sha, source_commit

INDEX_SHA = 'b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446'
SPLIT_SHA = '46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checked_json(binding):
    payload = Path(binding['path']).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == binding['sha256'], 'sha256_mismatch: ' + binding['path'])
    return json.loads(payload)


def write_json(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')


def v3_sources(layout, counting_entries=None):
    layout = Path(layout)
    require(sha(layout / 'candidate_index.jsonl') == INDEX_SHA, 'v3_index_pin')
    require(sha(layout / 'split_trainer.json') == SPLIT_SHA, 'v3_split_pin')
    split = read_json(layout / 'split_trainer.json')
    manifest = read_json(Path(str(layout).removesuffix('_trainer')) / 'MANIFEST.json')
    inputs = checked_json(manifest['artifacts']['BUILD_INPUTS.json'])
    forbidden_qids, forbidden_groups = full.benchmark_groups(inputs)
    heldout_qids = set(split['heldout_qids'])
    heldout_groups = control.normalized_groups(split['heldout_group_ids'])
    heldout_scenes = set(split['heldout_scenes'])
    train_groups = control.normalized_groups(split['train_group_ids'])
    train_scenes = set(split['train_scenes'])
    selected, drops = [], Counter()
    with (layout / 'candidate_index.jsonl').open() as stream:
        for line in stream:
            entry = json.loads(line)
            qid = entry['qid']
            group = control.scene_group(entry['dataset'], entry['scene'])
            scene = entry['dataset'] + '/' + entry['scene']
            if qid in heldout_qids or group in heldout_groups or scene in heldout_scenes:
                drops['heldout_side'] += 1
            elif qid in forbidden_qids or group in forbidden_groups:
                drops['benchmark_overlap'] += 1
            elif group not in train_groups or scene not in train_scenes:
                drops['not_v3_train_scene'] += 1
            else:
                if counting_entries is not None and entry['question_type'] == 'object_counting':
                    counting_entries.append(entry)
                if not entry.get('strict_accepted_trace') and not qid.startswith('vsi590k_'):
                    drops['no_teacher_trace'] += 1
                else:
                    selected.append(entry)
    return selected, drops


def counting_category_matches(question, label):
    text = question.lower()
    prefix = r'\b(?:how many|(?:number|quantity|count) (?:of|for)|count(?: the)?)\s+'
    match = re.search(prefix + r'(.+?)\((?:s|es)\)', text)
    if not match:
        match = re.search(prefix + r'(.+?)(?:\s+(?:are|is|do|does|can|have|exist|present|located|in|here)\b|[?.!\n])', text)
    if not match:
        return False
    noun = re.sub(r'^(?:(?:the|distinct|different)\s+)+', '', match[1].strip())
    variants = {label, label + 's', label + 'es'}
    if label.endswith('y'):
        variants.add(label[:-1] + 'ies')
    if label.endswith('f'):
        variants.add(label[:-1] + 'ves')
    if label.endswith('fe'):
        variants.add(label[:-2] + 'ves')
    return noun in variants


def counting_catalog(entries):
    result = []
    for entry in entries:
        require(entry['question_type'] == 'object_counting', 'count_catalog_question_type')
        source = {key: entry[key] for key in ('qid', 'dataset', 'scene', 'question_type', 'row_path', 'row_sha256')}
        row = checked_json({'path': entry['row_path'], 'sha256': entry['row_sha256']})
        require(all(row[key] == entry[key] for key in ('qid', 'dataset', 'scene')), 'count_catalog_identity')
        result.append({'entry': source, 'question': row['student_input']['question'], 'label': row['target'],
                       'frames_sha256': digest(row['student_input']['frames'])})
    return result


def count_label_checks(entry, source_row, label, count, catalog):
    records = list(catalog or [])
    if entry['question_type'] == 'object_counting' and not any(item['entry']['qid'] == entry['qid'] for item in records):
        records += counting_catalog([entry])
    frame_sha = digest(source_row['student_input']['frames'])
    checks, sources = [], []
    for record in records:
        other = record['entry']
        if (other['dataset'], other['scene'], record['frames_sha256']) != (entry['dataset'], entry['scene'], frame_sha):
            continue
        if not counting_category_matches(record['question'], label):
            continue
        value = str(record['label']).strip()
        require(bool(re.fullmatch(r'\d+(?:\.0+)?', value)), 'count_v3_label_not_integer')
        checks.append({'v3_qid': other['qid'], 'v3_label': record['label'], 'gt_count': count,
                       'agree': int(value.split('.')[0]) == count})
        sources.append(other)
    checks.sort(key=lambda item: (item['agree'], item['v3_qid'] != entry['qid'], item['v3_qid']))
    return checks, sorted(sources, key=lambda item: item['qid'])


def stratified(entries, limit, seed):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for entry in entries:
        groups[entry['question_type']].append(entry)
    for group in groups.values():
        rng.shuffle(group)
    result = []
    while groups and len(result) < limit:
        for key in sorted(list(groups)):
            result.append(groups[key].pop())
            if not groups[key]:
                del groups[key]
            if len(result) == limit:
                break
    return result


def source_trace(entry):
    row_pin = {'path': entry['row_path'], 'sha256': entry['row_sha256']}
    row = checked_json(row_pin)
    binding = entry.get('strict_accepted_trace') or row.get('sources', {}).get('raw')
    require(bool(binding), 'missing_raw_trace')
    trace = checked_json(binding)
    require(trace['question_id'] == entry['qid'] == row['qid'], 'trace_qid_mismatch')
    receipt_pin = trace['run_receipt']['scene_receipt']
    receipt = checked_json(receipt_pin)
    frame_mapping(receipt, row['student_input'])
    return row, binding, trace, receipt_pin, receipt


def frame_mapping(receipt, student_input):
    frames = receipt['frames']
    require(len(frames) == len(student_input['frames']) == 32, 'frame_count')
    # Content identity: the v3 row may name the same bytes through a content-addressed reference path, so compare SHA-256 in order.
    require([frame['sha256'] for frame in frames] == [frame['sha256'] for frame in student_input['frames']], 'frame_sha_mismatch')
    require([frame['ordinal'] for frame in frames] == student_input['frame_indices'], 'frame_ordinal_mismatch')
    return {i: student_input['frames'][i - 1] for i in range(1, 33)}


def decode_content(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def tool_pairs(trace):
    pending, result = {}, []
    for raw in trace['trace']:
        message = raw.get('data', raw)
        for call in message.get('tool_calls') or []:
            call_id = call.get('id')
            require(bool(call_id) and call_id not in pending, 'missing_or_duplicate_call_id')
            pending[call_id] = {'name': call['name'], 'args': call['args'], 'call_id': call_id}
        if message.get('tool_call_id') is not None:
            call_id = message['tool_call_id']
            require(call_id in pending, 'unmatched_tool_response')
            call = pending.pop(call_id)
            require(not message.get('name') or message['name'] == call['name'], 'tool_name_mismatch')
            result.append({**call, 'response': decode_content(message.get('content'))})
    return result


def inventory(args):
    started = time.monotonic()
    entries, drops = v3_sources(args.v3_layout)
    sample = stratified(entries, args.limit or 25, args.seed)
    example = next((entry for entry in entries if entry['qid'] == 'vsi590k_135758'), None)
    if example and example not in sample:
        sample.insert(0, example)
    stats = {'eligible_traces': len(entries), 'eligible_by_type': dict(Counter(e['question_type'] for e in entries)),
             'excluded': dict(drops), 'checked': [], 'mismatches': [], 'tool_names': Counter(),
             'frame_modes': Counter(), 'message_schema': {}, 'examples': {}}
    for entry in sample:
        try:
            row, binding, trace, receipt_pin, receipt = source_trace(entry)
            calls = tool_pairs(trace)
            schemas = [{key: type(value).__name__ for key, value in msg.items()} for msg in trace['trace'][:8]]
            if not stats['message_schema']:
                stats['message_schema'] = schemas
            record = {'qid': entry['qid'], 'question_type': entry['question_type'], 'scene': entry['scene'],
                      'trace': binding, 'scene_receipt': receipt_pin, 'frame_pairs_checked': 32,
                      'calls': [], 'question': trace['question']}
            for call in calls:
                stats['tool_names'][call['name']] += 1
                if call['name'] == 'find_frames_with_object':
                    stats['frame_modes'][str(call['args'].get('num_frames'))] += 1
                response = canonical(call['response'])
                record['calls'].append({**call, 'response': call['response'] if len(response) < 2500 else response[:2500],
                                        'response_bytes': len(response), 'has_instance_id': 'instance_id' in response})
                if call['name'] not in stats['examples'] or entry['qid'] == 'vsi590k_135758':
                    stats['examples'][call['name']] = {**call, 'qid': entry['qid']}
            stats['checked'].append(record)
            print(f"checked {entry['qid']} {entry['question_type']} {len(calls)} calls", flush=True)
        except (ValueError, KeyError, OSError, TypeError) as error:
            stats['mismatches'].append({'qid': entry['qid'], 'error': str(error)})
            print(f"deferred {entry['qid']}: {error}", flush=True)
    stats['seconds'] = time.monotonic() - started
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / 'INVENTORY.json', stats)
    print(json.dumps({key: value for key, value in stats.items() if key not in ('checked', 'examples')}, indent=2), flush=True)


KINDS = ('traceev_count_list', 'traceev_abs_distance', 'traceev_size', 'traceev_frames_all',
         'traceev_frames_first', 'traceev_frames_some', 'traceev_rel_quadrant')
SUPPORTS = {'traceev_count_list': ['object_counting'], 'traceev_abs_distance': ['object_abs_distance'],
            'traceev_size': ['object_size_estimation'], 'traceev_frames_all': ['obj_appearance_order', 'object_counting'],
            'traceev_frames_first': ['obj_appearance_order'], 'traceev_frames_some': ['grounding'],
            'traceev_rel_quadrant': ['object_rel_direction_hard']}
PREFIX = 'These are frames of a video.\n'
FRAME_PREFIX = 'The video has 32 frames, numbered 1 to 32 in order.\n'
COUNT_INSTRUCTION = 'Answer with one line per instance in order of first appearance, then a final line with the count.'
LEAKAGE = re.compile(r'\(|\bx\s*=|camera|pose|centroid|instance|world|[/\\\\]|mask|find_frames|predict_2d|get_3d|execute_python', re.I)


def valid_label(label):
    require(isinstance(label, str) and label == label.lower().strip() and
            bool(re.fullmatch(r'[a-z][a-z -]*', label)) and not LEAKAGE.search(label) and
            label not in assets.EXCLUDED, 'unsafe_or_excluded_label')
    return label


def frame_numbers(values):
    require(isinstance(values, list) and bool(values) and
            all(type(i) is int and 1 <= i <= 32 for i in values) and len(values) == len(set(values)), 'invalid_frame_numbers')
    return sorted(values)


def validate_text(question, target):
    require(question.startswith(PREFIX), 'question_prefix')
    tail = question[len(PREFIX):].replace(COUNT_INSTRUCTION, '')
    require(not LEAKAGE.search(tail) and not LEAKAGE.search(target), 'student_text_leakage')
    require(not re.search(r'\d+\.\d{3,}', question + '\n' + target), 'excess_numeric_precision')
    require(not any(token in question + target for token in ('<|', '|>', '<answer>', '<ANSWER>')), 'student_control_token')


def render(kind, labels, values):
    require(kind in KINDS, 'unknown_kind')
    labels = [valid_label(label) for label in labels]
    question = PREFIX
    if kind.startswith('traceev_frames_'):
        frames = frame_numbers(values['frames'])
        label, = labels
        obj = ('the ' if values['unique'] else 'at least one ') + label
        question += FRAME_PREFIX
        if kind == 'traceev_frames_all':
            question += f'In which frames is {obj} visible?\nAnswer with the frame numbers in increasing order, separated by commas.'
        elif kind == 'traceev_frames_first':
            require(len(frames) == 1, 'first_frame_cardinality')
            question += f'In which frame does {obj} first appear?\nAnswer with a single frame number.'
        else:
            require(len(frames) <= 5, 'some_frames_cardinality')
            question += f'Name {len(frames)} frames in which {obj} is clearly visible.\nAnswer with the frame numbers in increasing order, separated by commas.'
        target = ', '.join(map(str, frames))
    elif kind == 'traceev_size':
        label, = labels
        dims = values['dimensions']
        require(len(dims) == 3 and all(math.isfinite(x) and x > 0 for x in dims), 'invalid_dimensions')
        question += f'What are the dimensions of the {label}, from longest to shortest, in meters?\nAnswer with three numbers separated by commas.'
        target = ', '.join(format_number(value) for value in sorted(dims, reverse=True))
    elif kind == 'traceev_abs_distance':
        a, b = labels
        value = values['distance']
        require(math.isfinite(value) and value >= 0, 'invalid_distance')
        question += f'What is the distance between the {a} and the {b} in meters, measured between their closest points?\nAnswer with a single number.'
        target = format_number(value)
    elif kind == 'traceev_count_list':
        label, = labels
        first = sorted(values['first_frames'], key=lambda pair: (pair[1], pair[0]))
        require(values['count'] == len(first) > 0 and len({pair[0] for pair in first}) == len(first), 'invalid_count_census')
        require(all(type(pair[1]) is int and 1 <= pair[1] <= 32 for pair in first), 'invalid_count_frame')
        question += FRAME_PREFIX + f'List each {label} in the video with the frame where it first appears, then give the total count.\n' + COUNT_INSTRUCTION
        target = '\n'.join(f'{label} {i}: frame {pair[1]}' for i, pair in enumerate(first, 1)) + f'\ncount: {len(first)}'
    else:
        a, b, c = labels
        target = values['quadrant']
        require(target in ('front-left', 'front-right', 'back-left', 'back-right'), 'invalid_quadrant')
        question += (f'If I am standing by the {a} and facing the {b}, is the {c} to my front-left, front-right, back-left, or back-right?\n'
                     'Answer with one of: front-left, front-right, back-left, back-right.')
    validate_text(question, target)
    return question, target


def unique_ids(objects, grounded):
    counts = Counter(obj['label'] for obj in objects.values())
    return sorted(iid for iid in grounded if iid in objects and counts[objects[iid]['label']] == 1)


class SceneCache:
    def __init__(self, receipt_pin, receipt):
        require(receipt['coordinate_frame'] == 'source_world_meters_opencv_camera_to_world' and receipt['gravity_up'] == [0, 0, 1], 'unsupported_gt_coordinates')
        self.receipt_pin, self.receipt = receipt_pin, receipt
        groups = checked_json(receipt['instances'])['segGroups']
        annotations = checked_json(receipt['annotations'])['instances']
        annotation_labels = {row['instance_id']: row['label'].lower().strip() for row in annotations}
        self.objects = {}
        self.labels = defaultdict(list)
        for group in groups:
            iid = group.get('objectId', group['id'])
            label = group['label'].lower().strip()
            require(type(iid) is int and iid >= 0 and iid not in self.objects, 'invalid_gt_instance_census')
            require(annotation_labels.get(iid) == label, 'gt_annotation_label_mismatch')
            self.objects[iid] = {'id': iid, 'label': label, 'obb': group['obb']}
            self.labels[label].append(iid)
        require(set(self.objects) == set(annotation_labels) and len(annotations) == len(annotation_labels), 'incomplete_gt_instance_census')
        self.loaded = None
        self.load_error = None
        self.first = None
        self.visible_frames = None
        self.distances = {}

    def scene(self):
        if self.load_error:
            raise ValueError(self.load_error)
        if self.loaded is None:
            try:
                self.loaded = assets.load_scene(self.receipt_pin['path'])
                self.mesh_objects = {obj['id']: obj for obj in self.loaded.objects}
            except (ValueError, OSError, KeyError) as error:
                self.load_error = 'gt_scene_unavailable: ' + str(error)
                raise ValueError(self.load_error) from error
        return self.loaded

    def visibility(self):
        if self.first is None:
            scene = self.scene()
            first, visible_frames = {}, defaultdict(list)
            for slot in range(1, 33):
                for observation in scene.observations(slot):
                    iid = observation['id']
                    first.setdefault(iid, slot)
                    visible_frames[iid].append(slot)
            self.first, self.visible_frames = first, visible_frames
        return self.first

    def distance(self, left, right):
        key = tuple(sorted((left, right)))
        if key not in self.distances:
            self.scene()
            require(all(iid in self.mesh_objects for iid in key), 'distance_instance_without_surface')
            self.distances[key] = geometry.object_distance(*(self.mesh_objects[iid] for iid in key))
        return self.distances[key]


def response_instances(value):
    if isinstance(value, dict):
        if type(value.get('instance_id')) is int:
            yield value
        for nested in value.values():
            yield from response_instances(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from response_instances(nested)


def grounding(calls, objects, scene_id):
    grounded, labels, lifts, handles = {}, {}, defaultdict(list), {}
    all_labels = {obj['label'] for obj in objects.values()}
    for call in calls:
        args, name = call['args'], call['name']
        if 'scene_id' in args:
            require(args['scene_id'] == scene_id, 'tool_scene_mismatch')
        if name == 'find_frames_with_object':
            label = str(args.get('object_label', '')).strip().lower()
            if label in all_labels and isinstance(call['response'], list) and call['response']:
                frame_numbers(call['response'])
                labels.setdefault(label, call)
        if name not in ('predict_2d_segmentation_masks', 'predict_2d_segmentation_masks_video'):
            continue
        slots = args.get('frame_indices') if name.endswith('_video') else [args.get('frame_index')]
        frame_numbers(slots)
        for item in response_instances(call['response']):
            iid = item['instance_id']
            require(iid in objects, 'trace_instance_not_in_gt')
            grounded.setdefault(iid, call)
            labels.setdefault(objects[iid]['label'], call)
            for key in ('mask_dense_handle', 'mask_handle'):
                if isinstance(item.get(key), str):
                    require(item[key] not in handles or handles[item[key]] == iid, 'mask_instance_conflict')
                    handles[item[key]] = iid
    for call in calls:
        if call['name'] != 'get_3d_points_in_mask' or not isinstance(call['response'], dict):
            continue
        handle = call['args'].get('mask_dense_handle', call['args'].get('mask_handle'))
        iid = handles.get(handle)
        if iid is not None:
            value = {key: call['response'][key] for key in ('centroid', 'extent_xyz_p90') if key in call['response']}
            if value:
                lifts[iid].append({**value, 'call': call})
    return grounded, labels, dict(lifts)


def complete_tool_visibility(calls, objects, label):
    slots, witnesses = {}, []
    for call in calls:
        if str(call['args'].get('object_label', '')).strip().lower() != label:
            continue
        name, response = call['name'], call['response']
        observations = {}
        if name == 'find_frames_with_object' and str(call['args'].get('num_frames')) == 'all':
            if not isinstance(response, list):
                continue
            present = frame_numbers(response) if response else []
            observations = {slot: set() for slot in range(1, 33) if slot not in present}
        elif name in ('predict_2d_segmentation_masks', 'predict_2d_segmentation_masks_video'):
            requested = call['args'].get('frame_indices') if name.endswith('_video') else [call['args'].get('frame_index')]
            frame_numbers(requested)
            frames = response.get('frames', {}) if name.endswith('_video') and isinstance(response, dict) else {}
            if not name.endswith('_video'):
                frames = {str(requested[0]): response}
            for slot in requested:
                items = frames.get(str(slot))
                if not isinstance(items, list) or not all(isinstance(item, dict) and type(item.get('instance_id')) is int for item in items):
                    continue
                ids = {item['instance_id'] for item in items}
                require(all(iid in objects and objects[iid]['label'] == label for iid in ids), 'count_tool_category_mismatch')
                observations[slot] = ids
        if observations:
            witnesses.append(call)
        for slot, ids in observations.items():
            require(slot not in slots or slots[slot] == ids, 'count_tool_visibility_conflict')
            slots[slot] = ids
    if set(slots) != set(range(1, 33)):
        return None
    first = {}
    for slot in range(1, 33):
        for iid in sorted(slots[slot]):
            first.setdefault(iid, slot)
    return first, witnesses


def program_viewpoint(calls, lifts):
    def match_point(values):
        if not isinstance(values, list) or len(values) not in (2, 3) or not all(type(v) in (int, float) for v in values):
            return values
        matches = {iid for iid, items in lifts.items() for item in items if 'centroid' in item and
                   len(item['centroid']) == 3 and np.allclose(values, item['centroid'][:len(values)], rtol=0, atol=.001)}
        return ('object', next(iter(matches))) if len(matches) == 1 else values

    def tagged(value, name):
        return isinstance(value, tuple) and bool(value) and value[0] == name

    for call in reversed(calls):
        if call['name'] != 'execute_python_code' or not isinstance(call['response'], str):
            continue
        sides = set(re.findall(r'\b(left|right)\b', call['response'].lower()))
        if len(sides) != 1:
            continue
        try:
            tree = ast.parse(call['args'].get('code', ''))
        except (SyntaxError, ValueError):
            continue
        names, crosses = {}, []

        def evaluate(node):
            if isinstance(node, ast.Name):
                return names.get(node.id)
            if isinstance(node, ast.Constant):
                return node.value if type(node.value) in (int, float, str) else None
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
                value = evaluate(node.operand)
                return (-value if isinstance(node.op, ast.USub) else value) if type(value) in (int, float) else None
            if isinstance(node, (ast.List, ast.Tuple)):
                values = [evaluate(item) for item in node.elts]
                if len(values) == 2 and all(tagged(v, 'delta') for v in values):
                    if values[0][1:3] == values[1][1:3] and [v[3] for v in values] == [0, 1]:
                        return ('vector', *values[0][1:3])
                return match_point(values)
            if isinstance(node, ast.Dict):
                keys = [evaluate(key) for key in node.keys]
                if all(isinstance(key, str) for key in keys):
                    return dict(zip(keys, (evaluate(v) for v in node.values)))
            if isinstance(node, ast.Subscript):
                base = evaluate(node.value)
                if isinstance(node.slice, ast.Slice):
                    lower = evaluate(node.slice.lower) if node.slice.lower else 0
                    upper = evaluate(node.slice.upper) if node.slice.upper else None
                    if lower == 0 and upper in (None, 2, 3) and node.slice.step is None:
                        return base
                    return None
                index = evaluate(node.slice)
                if isinstance(base, dict) and isinstance(index, str):
                    return base.get(index)
                if tagged(base, 'object') or tagged(base, 'vector'):
                    return ('component', base, index) if type(index) is int and index in (0, 1) else None
            if isinstance(node, ast.BinOp):
                left, right = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Sub):
                    if tagged(left, 'object') and tagged(right, 'object') and left != right:
                        return ('vector', right[1], left[1])
                    if tagged(left, 'component') and tagged(right, 'component') and left[2] == right[2]:
                        if tagged(left[1], 'object') and tagged(right[1], 'object'):
                            return ('delta', right[1][1], left[1][1], left[2])
                    if tagged(left, 'product') and tagged(right, 'product'):
                        a, b, c, d = left[1], left[2], right[1], right[2]
                        if all(tagged(x, 'component') and tagged(x[1], 'vector') for x in (a, b, c, d)):
                            if (a[2], b[2], c[2], d[2]) == (0, 1, 1, 0) and a[1] == c[1] and b[1] == d[1]:
                                crosses.append((a[1], b[1]))
                if isinstance(node.op, ast.Mult) and tagged(left, 'component') and tagged(right, 'component'):
                    return ('product', left, right)
                if isinstance(node.op, ast.Div) and tagged(left, 'vector') and tagged(right, 'norm') and right[1] == left:
                    return left
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                values = [evaluate(arg) for arg in node.args]
                if name in ('np.array', 'numpy.array', 'np.asarray', 'numpy.asarray') and values:
                    return values[0]
                if name in ('np.linalg.norm', 'numpy.linalg.norm') and len(values) == 1:
                    return ('norm', values[0])
                if name in ('np.cross', 'numpy.cross') and len(values) == 2 and all(tagged(v, 'vector') for v in values):
                    crosses.append(tuple(values))
            return None

        for node in tree.body:
            if isinstance(node, ast.Assign):
                value = evaluate(node.value)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names[target.id] = value
            elif isinstance(node, ast.Expr):
                evaluate(node.value)
        roles = {(a[1], a[2], b[2]) for a, b in crosses if a[1] == b[1] and len({a[1], a[2], b[2]}) == 3}
        if len(roles) == 1:
            return next(iter(roles)), next(iter(sides)), call
    raise ValueError('quadrant_program_unresolved')


def quadrant(a, b, c, trace_side):
    centers = [np.asarray(obj['obb']['centroid'], dtype=np.float64)[:2] for obj in (a, b, c)]
    forward, target = centers[1] - centers[0], centers[2] - centers[0]
    require(np.isfinite(centers).all() and np.linalg.norm(forward) > 1e-9 and np.linalg.norm(target) > 1e-9, 'quadrant_degenerate')
    dot = float(np.dot(forward, target))
    cross = float(forward[0] * target[1] - forward[1] * target[0])
    angle = math.degrees(math.atan2(cross, dot))
    margin = min(abs(angle - axis) for axis in (-180, -90, 0, 90, 180))
    require(margin > 15 + 1e-9, 'quadrant_axis_margin')
    side = 'left' if cross > 0 else 'right'
    require(side == trace_side, 'quadrant_left_right_disagreement')
    answer = ('front' if dot > 0 else 'back') + '-' + side
    return answer, {'dot': dot, 'cross_z': cross, 'angle_degrees': angle, 'axis_margin_degrees': margin,
                    'trace_side': trace_side, 'quadrant': answer}


def make_row(entry, source_row, binding, cache, kind, ids, labels, values, calls, commit, counting=None):
    frame_sha = digest(source_row['student_input']['frames'])
    identity = labels[0] if kind.startswith('traceev_frames_') else sorted(ids)
    fact_key = [frame_sha, kind, identity]
    question, target = render(kind, labels, values)
    selected_entry = {key: entry[key] for key in ('qid', 'dataset', 'scene', 'question_type', 'row_path', 'row_sha256')}
    selected_entry['strict_accepted_trace'] = binding
    gt_assets = {'instances': cache.receipt['instances'], 'mesh': cache.receipt['instance_mesh'],
                 'annotations': cache.receipt['annotations']}
    checks, counting_entries = [], []
    if kind == 'traceev_count_list':
        gt_assets.update({key: cache.receipt[key] for key in ('dense', 'calibration', 'alignment')})
        checks, counting_entries = count_label_checks(entry, source_row, labels[0], values['count'], counting)
    return {'qid': f"traceev__{entry['scene']}__{kind}__{digest(fact_key)[:12]}", 'question_type': kind,
            'supports': SUPPORTS[kind], 'scene': entry['scene'], 'dataset': entry['dataset'],
            'source_qids': [entry['qid']], 'source_traces': [binding], 'fact_key': fact_key,
            'question': question, 'target': target, 'label_check': checks[0] if checks else None,
            'student_input': {**copy.deepcopy(source_row['student_input']), 'question': question, 'options': []},
            'evidence': {'tool_calls': list({call['call_id']: call for call in calls}.values()),
                         'gt': {'instance_ids': ids, 'labels': labels, 'assets': gt_assets, 'values_unrounded': values},
                         'scene_receipt': cache.receipt_pin, 'source_entry': selected_entry,
                         'label_checks': checks, 'counting_entries': counting_entries,
                         'selected_frames_sha256': frame_sha, 'source_question_type': entry['question_type'],
                         'owner_qid': entry['qid'], 'v3_index_sha256': INDEX_SHA, 'v3_split_sha256': SPLIT_SHA},
            'extractor_commit': commit}


def extract_entry(entry, cache_by_receipt, commit, kinds=None, only_key=None, counting=None):
    source_row, binding, trace, receipt_pin, receipt = source_trace(entry)
    require((entry['dataset'], entry['scene']) == (source_row['dataset'], source_row['scene']) ==
            (receipt['dataset'], receipt['scene_name']), 'source_scene_identity')
    require(trace['scene_name'] == receipt['runtime_scene_id'], 'trace_receipt_scene_identity')
    key = (receipt_pin['path'], receipt_pin['sha256'])
    if key not in cache_by_receipt:
        cache_by_receipt[key] = SceneCache(receipt_pin, receipt)
    cache = cache_by_receipt[key]
    calls = tool_pairs(trace)
    grounded, selected_labels, lifts = grounding(calls, cache.objects, receipt['runtime_scene_id'])
    unique = unique_ids(cache.objects, grounded)
    kinds = set(KINDS) if kinds is None else set(kinds)
    rows, drops, agreements = [], Counter(), defaultdict(list)
    stats = {'drops': drops, 'agreements': agreements, 'frame_mapping_passed': 1, 'frame_pairs_checked': 32,
             'tool_names': Counter(call['name'] for call in calls),
             'frame_modes': Counter(str(call['args'].get('num_frames')) for call in calls if call['name'] == 'find_frames_with_object')}

    def wanted(kind, ids, label):
        if kind not in kinds:
            return False
        identity = label if kind.startswith('traceev_frames_') else sorted(ids)
        return only_key is None or [digest(source_row['student_input']['frames']), kind, identity] == only_key

    def add(kind, ids, labels, values, witnesses):
        try:
            rows.append(make_row(entry, source_row, binding, cache, kind, ids, labels, values, witnesses, commit, counting))
        except ValueError as error:
            drops[str(error).split(':', 1)[0]] += 1

    for call in calls:
        if call['name'] != 'find_frames_with_object':
            continue
        label = str(call['args'].get('object_label', '')).lower().strip()
        mode = str(call['args'].get('num_frames'))
        kind = {'all': 'traceev_frames_all', '1': 'traceev_frames_first', '5': 'traceev_frames_some'}.get(mode)
        if kind not in kinds:
            continue
        if label not in cache.labels:
            drops['frame_label_not_in_gt'] += 1
            continue
        if not wanted(kind, [], label):
            continue
        try:
            numbers = frame_numbers(call['response'])
        except ValueError:
            drops['frame_response_invalid_or_empty'] += 1
            continue
        returned = numbers
        if kind == 'traceev_frames_first':
            numbers = numbers[:1]
        add(kind, cache.labels[label], [label], {'frames': numbers, 'returned_frames': returned,
            'unique': len(cache.labels[label]) == 1, 'num_frames_mode': mode}, [call])

    if 'traceev_size' in kinds:
        drops['size_nonunique_label'] += len(grounded) - len(unique)
    for iid in unique:
        if not wanted('traceev_size', [iid], cache.objects[iid]['label']):
            continue
        try:
            obj = cache.objects[iid]
            geometry.object_size(obj)
            dimensions = sorted((2 * float(value) for value in obj['obb']['axesLengths']), reverse=True)
            partial = [item for item in lifts.get(iid, []) if 'extent_xyz_p90' in item]
            ratios = [max(item['extent_xyz_p90']) / dimensions[0] for item in partial if len(item['extent_xyz_p90']) == 3]
            agreements['trace_lift_max_extent_over_gt_longest'].extend(ratios)
            add('traceev_size', [iid], [obj['label']], {'dimensions': dimensions},
                [grounded[iid]] + [item['call'] for item in partial])
        except ValueError as error:
            drops[str(error).split(':', 1)[0]] += 1

    for label, witness in sorted(selected_labels.items()):
        if 'traceev_count_list' not in kinds:
            continue
        try:
            valid_label(label)
            complete = complete_tool_visibility(calls, cache.objects, label)
            first, witnesses = complete if complete is not None else (cache.visibility(), [witness])
            ids = sorted(iid for iid in cache.labels[label] if iid in first)
            if not wanted('traceev_count_list', ids, label):
                continue
            count = geometry.object_count([cache.objects[iid] for iid in ids], label)
            require(count > 0, 'count_no_visible_instances')
            trace_ids = {iid for iid in grounded if cache.objects[iid]['label'] == label}
            agreements['count_trace_ids_over_gt'].append(len(trace_ids) / count)
            values = {'count': count, 'first_frames': sorted([[iid, first[iid]] for iid in ids], key=lambda pair: (pair[1], pair[0])),
                      'visibility_source': 'complete_gt_tool_outputs' if complete is not None else 'gtmeasure_all_32_frames',
                      'coverage_frames': list(range(1, 33))}
            add('traceev_count_list', ids, [label], values, witnesses)
        except (ValueError, OSError, KeyError) as error:
            drops[str(error).split(':', 1)[0]] += 1

    for left, right in itertools.combinations(unique, 2):
        if not wanted('traceev_abs_distance', [left, right], None):
            continue
        try:
            value = cache.distance(left, right)
            add('traceev_abs_distance', [left, right], [cache.objects[iid]['label'] for iid in (left, right)],
                {'distance': value}, [grounded[left], grounded[right]])
            if value > 0 and lifts.get(left) and lifts.get(right):
                ca, cb = lifts[left][0].get('centroid'), lifts[right][0].get('centroid')
                if ca is not None and cb is not None:
                    agreements['trace_centroid_distance_over_gt_surface_distance'].append(float(np.linalg.norm(np.asarray(ca) - cb)) / value)
        except (ValueError, OSError, KeyError) as error:
            drops[str(error).split(':', 1)[0]] += 1

    if 'traceev_rel_quadrant' in kinds and entry['question_type'].startswith('object_rel_direction'):
        try:
            ids, side, program = program_viewpoint(calls, lifts)
            require(all(iid in unique for iid in ids), 'quadrant_nonunique_or_ungrounded')
            if wanted('traceev_rel_quadrant', ids, None):
                objects = [cache.objects[iid] for iid in ids]
                for obj in objects:
                    box_corners(obj['obb'])
                answer, values = quadrant(*objects, side)
                agreements['quadrant_left_right_agrees'].append(1)
                add('traceev_rel_quadrant', list(ids), [obj['label'] for obj in objects], values,
                    [grounded[iid] for iid in ids] + [item['call'] for iid in ids for item in lifts.get(iid, [])] + [program])
        except (ValueError, KeyError) as error:
            reason = str(error).split(':', 1)[0]
            drops[reason] += 1
            if reason == 'quadrant_left_right_disagreement':
                agreements['quadrant_left_right_agrees'].append(0)
    return rows, stats


def dedupe_rows(rows):
    unique, drops = {}, Counter()
    for row in rows:
        key = canonical(row['fact_key'])
        if key not in unique:
            unique[key] = copy.deepcopy(row)
            continue
        prior = unique[key]
        if (prior['question'], prior['target'], prior['scene'], prior['dataset']) != (row['question'], row['target'], row['scene'], row['dataset']):
            drops['dedupe_conflicting_render'] += 1
            continue
        drops['duplicate_fact'] += 1
        prior['source_qids'] = sorted(set(prior['source_qids']) | set(row['source_qids']))
        bindings = {canonical(binding): binding for binding in prior['source_traces'] + row['source_traces']}
        prior['source_traces'] = [bindings[key] for key in sorted(bindings)]
    return list(unique.values()), drops


def count_value(row):
    return row['evidence']['gt']['values_unrounded']['count']


def label_disagreement(row):
    return (row.get('label_check') or {}).get('agree') is False


def limit_count_one(rows):
    others = [row for row in rows if count_value(row) != 1]
    protected = [row for row in rows if count_value(row) == 1 and label_disagreement(row)]
    singles = [row for row in rows if count_value(row) == 1 and not label_disagreement(row)]
    limit = max(0, len(others) * 3 // 17 - len(protected))
    return others + protected + singles[:limit], max(0, len(singles) - limit)


def select_budget(rows, budget=40000, seed=20260925):
    require(0 < budget <= 60000, 'invalid_budget')
    priorities = {kind: i for i, kind in enumerate(KINDS)}
    ordered = sorted(rows, key=lambda row: (priorities[row['question_type']],
        row['question_type'] == 'traceev_count_list' and count_value(row) == 1,
        not label_disagreement(row), digest([seed, row['fact_key']])))
    total = min(budget, len(rows))
    while True:
        selected, drops = [], Counter()
        scenes, owners, counts = Counter(), Counter(), Counter()
        scene_limit, frame_limit, quadrant_limit = total // 200, total * 3 // 10, total // 10
        for row in ordered:
            kind = row['question_type']
            scene = row['dataset'] + '/' + row['scene']
            reason = None
            if len(selected) >= total:
                reason = 'budget_total'
            elif scenes[scene] >= scene_limit:
                reason = 'budget_scene_fraction'
            elif kind.startswith('traceev_frames_') and counts['frames'] >= frame_limit:
                reason = 'budget_frame_fraction'
            elif kind == 'traceev_rel_quadrant' and counts['quadrant'] >= quadrant_limit:
                reason = 'budget_quadrant_fraction'
            elif kind == 'traceev_count_list' and count_value(row) == 1 and not label_disagreement(row) and counts['single'] >= counts['multiple'] * 3 // 17:
                reason = 'budget_count_one_fraction'
            owner = next((qid for qid in row['source_qids'] if owners[qid] < 4), None)
            if reason is None and owner is None:
                reason = 'budget_trace_new_facts'
            if reason:
                drops[reason] += 1
                continue
            row['evidence']['owner_qid'] = owner
            selected.append(row)
            scenes[scene] += 1
            owners[owner] += 1
            if kind.startswith('traceev_frames_'):
                counts['frames'] += 1
            elif kind == 'traceev_rel_quadrant':
                counts['quadrant'] += 1
            elif kind == 'traceev_count_list':
                counts['single' if count_value(row) == 1 else 'multiple'] += 1
        if len(selected) == total:
            return selected, drops
        total = len(selected)
        if total == 0:
            return [], drops


def replay(row):
    validate_text(row['question'], row['target'])
    require(row['question_type'] in KINDS and row['supports'] == SUPPORTS[row['question_type']], 'row_kind_contract')
    require(bool(re.fullmatch(r'[0-9a-f]{40}', row['extractor_commit'])), 'extractor_commit_contract')
    for binding in row['source_traces']:
        checked_json(binding)
    entry = row['evidence']['source_entry']
    require(entry['qid'] in row['source_qids'] and entry['strict_accepted_trace'] in row['source_traces'], 'replay_source_membership')
    counting = counting_catalog(row['evidence']['counting_entries'])
    candidates, stats = extract_entry(entry, {}, row['extractor_commit'], kinds={row['question_type']}, only_key=row['fact_key'], counting=counting)
    matches = [candidate for candidate in candidates if candidate['fact_key'] == row['fact_key']]
    require(bool(matches), 'replay_fact_not_admitted: ' + canonical(stats['drops']))
    expected = matches[0]
    for field in ('qid', 'question_type', 'supports', 'scene', 'dataset', 'fact_key', 'question', 'target', 'student_input', 'label_check'):
        require(row[field] == expected[field], 'replay_mismatch_' + field)
    for field in ('gt', 'scene_receipt', 'selected_frames_sha256', 'tool_calls', 'source_question_type', 'v3_index_sha256', 'v3_split_sha256',
                  'label_checks', 'counting_entries'):
        require(row['evidence'][field] == expected['evidence'][field], 'replay_evidence_mismatch_' + field)
    return expected['target']


def aggregate_stats(target, source):
    for name in ('drops', 'tool_names', 'frame_modes', 'facts_per_trace', 'trace_types'):
        target.setdefault(name, Counter()).update(source.get(name, {}))
    for name in ('frame_mapping_passed', 'frame_pairs_checked', 'traces_processed'):
        target[name] = target.get(name, 0) + source.get(name, 0)
    for name, values in source.get('agreements', {}).items():
        target.setdefault('agreements', {}).setdefault(name, []).extend(values)
    target.setdefault('trace_failures', []).extend(source.get('trace_failures', []))
    return target


def utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def heartbeat(args, message):
    print(f'{utc()} | {message}', flush=True)
    if args.heartbeat:
        with args.heartbeat.open('a') as stream:
            stream.write(f'{utc()} | {message}\n')
        (args.heartbeat.parent / 'PROGRESS.md').write_text(
            '# B1 extraction progress\n' + f'- {message}.\n- Output: {args.out}\n'
            '- The extractor uses CPU workers, nice 19, and inherited idle I/O priority.\n'
            '- Completed scene shards remain under the output directory.\n')


def worker_init():
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.nice(max(0, 19 - os.getpriority(os.PRIO_PROCESS, 0)))


def extract_scene(job):
    entries, out, commit, config_sha, counting_entries = job
    started = time.monotonic()
    rows, cache, stats = [], {}, {}
    counting = counting_catalog(counting_entries)
    for entry in sorted(entries, key=lambda entry: entry['qid']):
        try:
            facts, evidence = extract_entry(entry, cache, commit, counting=counting)
            rows.extend(facts)
            evidence.update(traces_processed=1, facts_per_trace={str(len(facts)): 1}, trace_types={entry['question_type']: 1})
            aggregate_stats(stats, evidence)
        except (ValueError, OSError, KeyError, TypeError) as error:
            reason = str(error).split(':', 1)[0] if isinstance(error, ValueError) else type(error).__name__
            aggregate_stats(stats, {'traces_processed': 1, 'drops': {reason: 1}, 'facts_per_trace': {'0': 1},
                                   'trace_types': {entry['question_type']: 1},
                                   'trace_failures': [{'qid': entry['qid'], 'reason': reason, 'detail': str(error)}]})
    unique, drops = dedupe_rows(rows)
    aggregate_stats(stats, {'drops': drops})
    name = entries[0]['dataset'] + '__' + entries[0]['scene']
    require(bool(re.fullmatch(r'[A-Za-z0-9_.-]+', name)), 'unsafe_scene_filename')
    path = Path(out) / 'shards' / (name + '.jsonl')
    with path.open('x') as stream:
        for row in unique:
            row['extractor_config_sha256'] = config_sha
            stream.write(canonical(row) + '\n')
    result = {'path': str(path), 'sha256': sha(path), 'rows': len(unique), 'seconds': time.monotonic() - started,
              'scene': name, 'stats': stats}
    write_json(path.with_suffix('.done.json'), result)
    return result


def distribution(values):
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return {'n': 0}
    return {'n': len(finite), 'mean': float(np.mean(finite)), 'min': min(finite), 'median': float(np.median(finite)), 'max': max(finite)}


def label_check_summary(rows):
    datasets = defaultdict(Counter)
    comparisons = defaultdict(dict)
    for row in rows:
        if row['question_type'] != 'traceev_count_list':
            continue
        counts = datasets[row['dataset']]
        counts['count_rows'] += 1
        counts['compared_rows'] += row.get('label_check') is not None
        counts['disagreement_rows'] += label_disagreement(row)
        counts['protected_count_one_rows'] += count_value(row) == 1 and label_disagreement(row)
        for check in row['evidence'].get('label_checks', []):
            comparisons[row['dataset']][(check['v3_qid'], check['gt_count'])] = check['agree']
    result = {}
    for dataset, counts in sorted(datasets.items()):
        pairs = comparisons[dataset]
        result[dataset] = {**counts, 'disagreement_percent': 100 * counts['disagreement_rows'] / max(1, counts['compared_rows']),
                           'label_comparisons': len(pairs), 'disagreeing_labels': sum(not agree for agree in pairs.values()),
                           'label_disagreement_percent': 100 * sum(not agree for agree in pairs.values()) / max(1, len(pairs))}
    return result


def composition(out, summary, rows, candidates):
    lines = ['# Trace-evidence composition', '',
             f"The extractor published {len(rows):,} budget-compliant rows from {summary['traces_processed']:,} selected train-side traces.",
             f"The extraction produced {len(candidates):,} distinct admissible facts before global budget caps.",
             f"Commit: `{summary['commit']}`. Evidence SHA-256: `{summary['sha256']}`.", '', '## Row kinds', '',
             '| Kind | Published | Before global caps |', '|---|---:|---:|']
    raw_counts = Counter(row['question_type'] for row in candidates)
    for kind in KINDS:
        lines.append(f"| {kind} | {summary['per_kind'].get(kind, 0)} | {raw_counts[kind]} |")
    raw_supported = Counter(support for row in candidates for support in row['supports'])
    lines += ['', '## Supported tasks', '', '| Supported task | Published rows | Before global caps |', '|---|---:|---:|']
    lines += [f"| {key} | {summary['per_supported_type'].get(key, 0)} | {raw_supported[key]} |"
              for key in sorted({support for values in SUPPORTS.values() for support in values})]
    lines += ['', 'Grounding is an auxiliary task, not a benchmark category. Multi-support rows contribute to both task counts.',
              '', '## Trace coverage and drops', '',
              f"Source question types: `{canonical(summary['source_question_types'])}`.",
              f"Facts per trace before scene deduplication: `{canonical(summary['facts_per_trace'])}`.",
              f"New published facts per owning trace: `{canonical(summary['new_facts_per_trace'])}`.",
              f"Frame mapping: {summary['frame_mapping_passed']} traces passed, covering {summary['frame_pairs_checked']} ordered path/SHA pairs.",
              f"Count-list distribution after caps: `{canonical(summary['count_distribution'])}`.",
              f"Count-list distribution before caps: `{canonical(summary['raw_count_distribution'])}`.",
              '', '| Drop reason | Count |', '|---|---:|']
    lines += [f'| {key} | {value} |' for key, value in sorted(summary['drops'].items())]
    lines += ['', 'Drops count rejected facts or source traces as indicated by the reason; they are not all distinct traces.',
              'The scene cap uses the actual published denominator and requires at least 200 contributing scenes for any nonempty output.',
              f"Before caps, this run covers {summary['candidate_scenes']} scenes. No cap is waived for a bounded sample.",
              '', '## Trace and GT agreement', '']
    lines += [f'- {key}: `{canonical(value)}`.' for key, value in sorted(summary['agreements'].items())]
    lines += ['Extent ratios compare partial-view trace extents with full GT box dimensions. Centroid/surface ratios compare different measures; neither ratio filters facts.',
              '', '## Counting label checks', '',
              'GT counts remain the targets when v3 labels disagree. The primary label_check prefers a disagreement; evidence.label_checks retains all matching comparisons.',
              'Comparisons require the same dataset, scene, exact frame set, and counted category. Rows without a matching v3 counting label have label_check=null.',
              'Count-one disagreement rows are exempt from the 15% count-one cap; all other global caps still apply.', '',
              '| Stage | Dataset | Compared rows | Disagreement rows | Disagreement % | V3 label comparisons | Disagreeing labels | Label disagreement % | Protected count-one rows |',
              '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for stage, records in (('published', summary['label_checks']), ('before caps', summary['raw_label_checks'])):
        for dataset, counts in records.items():
            lines.append(f"| {stage} | {dataset} | {counts.get('compared_rows', 0)} | {counts.get('disagreement_rows', 0)} | {counts['disagreement_percent']:.2f} | {counts['label_comparisons']} | {counts['disagreeing_labels']} | {counts['label_disagreement_percent']:.2f} | {counts.get('protected_count_one_rows', 0)} |")
    lines += ['', '## Runtime', '',
              f"Wall time: {summary['runtime_seconds']:.2f} seconds; {summary['seconds_per_trace']:.3f} seconds per selected trace with {summary['workers']} workers.",
              f"The wall-time extrapolation for all {summary['eligible_traces']} eligible traces is {summary['projected_full_seconds']:.2f} seconds.",
              'The extrapolation includes this sample\'s scene-cache costs and is not a completion guarantee.',
              '', '## Rendered examples', '',
              'Examples below come from distinct individually admitted facts before global caps when a kind has fewer than ten published rows. Such examples are diagnostic, not published training rows.']
    for kind in KINDS:
        selected = [row for row in rows if row['question_type'] == kind][:10]
        seen = {row['qid'] for row in selected}
        selected += [row for row in candidates if row['question_type'] == kind and row['qid'] not in seen][:10 - len(selected)]
        lines += ['', '### ' + kind, '']
        if not selected:
            lines.append('No individually admitted facts of this kind were available.')
        for row in selected:
            lines += [f"#### {row['qid']}", '```text', row['question'], '', row['target'], '```', '']
    with (out / 'COMPOSITION.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')


def extract(args):
    require(1 <= args.workers <= 32, 'workers_must_be_between_1_and_32')
    require(args.limit is None or args.limit > 0, 'limit_must_be_positive')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment_required')
    commit = source_commit()
    started = time.monotonic()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'shards').mkdir()
    heartbeat(args, 'Authenticate v3 membership and benchmark exclusions')
    counting_entries = []
    entries, pre_drops = v3_sources(args.v3_layout, counting_entries)
    counting_by_scene = defaultdict(list)
    for entry in counting_entries:
        counting_by_scene[(entry['dataset'], entry['scene'])].append(entry)
    total_eligible = len(entries)
    if args.limit is not None:
        if args.stratify:
            entries = stratified(entries, min(args.limit, len(entries)), args.seed)
        else:
            entries = random.Random(args.seed).sample(entries, min(args.limit, len(entries)))
    groups = defaultdict(list)
    for entry in entries:
        groups[(entry['dataset'], entry['scene'])].append(entry)
    inputs = {'commit': commit, 'index': {'path': str(args.v3_layout / 'candidate_index.jsonl'), 'sha256': INDEX_SHA},
              'split': {'path': str(args.v3_layout / 'split_trainer.json'), 'sha256': SPLIT_SHA},
              'seed': args.seed, 'limit': args.limit, 'stratify': args.stratify, 'workers': args.workers,
              'budget': args.budget, 'eligible_traces': total_eligible, 'selected_qids': sorted(entry['qid'] for entry in entries),
              'scene_groups': sorted(control.scene_group(*scene) for scene in groups), 'started_utc': utc()}
    config_sha = digest(inputs)
    write_json(args.out / 'BUILD_INPUTS.json', {**inputs, 'config_sha256': config_sha})
    jobs = [(values, str(args.out), commit, config_sha, counting_by_scene[key]) for key, values in sorted(groups.items())]
    stats, completed = {}, []
    last_heartbeat = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=worker_init) as pool:
        pending = {pool.submit(extract_scene, job) for job in jobs}
        while pending:
            done, pending = wait(pending, timeout=30, return_when=FIRST_COMPLETED)
            for future in done:
                result = future.result()
                completed.append(result)
                aggregate_stats(stats, result['stats'])
                print(f"{utc()} | scene {result['scene']} traces={result['stats']['traces_processed']} facts={result['rows']} seconds={result['seconds']:.2f}", flush=True)
            if time.monotonic() - last_heartbeat >= 60:
                heartbeat(args, f"Completed {len(completed)} scenes and {stats.get('traces_processed', 0)} traces")
                last_heartbeat = time.monotonic()
    heartbeat(args, 'Deduplicate complete shards and enforce every global budget cap')
    candidates = []
    for record in sorted(completed, key=lambda record: record['scene']):
        require(sha(record['path']) == record['sha256'], 'scene_shard_digest_mismatch')
        with Path(record['path']).open() as stream:
            candidates.extend(json.loads(line) for line in stream)
    candidates, dedupe_drops = dedupe_rows(candidates)
    selected, budget_drops = select_budget(candidates, args.budget, args.seed)
    selected.sort(key=lambda row: (row['dataset'], row['scene'], row['qid']))
    path = args.out / 'evidence_rows.jsonl'
    with path.open('x') as stream:
        for row in selected:
            stream.write(canonical(row) + '\n')
    drops = pre_drops + Counter(stats.get('drops', {})) + dedupe_drops + budget_drops
    write_json(args.out / 'DROPS.json', {'counts': drops, 'trace_failures': stats.get('trace_failures', []),
                                       'denominator': {'index_rows': 29399, 'eligible_traces': total_eligible, 'selected_traces': len(entries)}})
    wall = time.monotonic() - started
    owners = Counter(row['evidence']['owner_qid'] for row in selected)
    summary = {'path': str(path), 'sha256': sha(path), 'rows': len(selected), 'commit': commit, 'config_sha256': config_sha,
               'per_kind': {kind: sum(row['question_type'] == kind for row in selected) for kind in KINDS},
               'per_supported_type': dict(Counter(support for row in selected for support in row['supports'])),
               'raw_per_kind': dict(Counter(row['question_type'] for row in candidates)),
               'source_question_types': stats.get('trace_types', {}), 'eligible_traces': total_eligible,
               'traces_processed': stats.get('traces_processed', 0), 'facts_per_trace': stats.get('facts_per_trace', {}),
               'new_facts_per_trace': dict(Counter(map(str, owners.values()))), 'candidate_scenes': len({(row['dataset'], row['scene']) for row in candidates}),
               'frame_mapping_passed': stats.get('frame_mapping_passed', 0), 'frame_pairs_checked': stats.get('frame_pairs_checked', 0),
               'count_distribution': dict(Counter(str(count_value(row)) for row in selected if row['question_type'] == 'traceev_count_list')),
               'raw_count_distribution': dict(Counter(str(count_value(row)) for row in candidates if row['question_type'] == 'traceev_count_list')),
               'label_checks': label_check_summary(selected), 'raw_label_checks': label_check_summary(candidates),
               'agreements': {name: distribution(values) for name, values in stats.get('agreements', {}).items()},
               'drops': drops, 'runtime_seconds': wall, 'seconds_per_trace': wall / max(1, len(entries)),
               'projected_full_seconds': wall / max(1, len(entries)) * total_eligible, 'workers': args.workers,
               'scene_shards': len(completed), 'tool_names': stats.get('tool_names', {}), 'frame_modes': stats.get('frame_modes', {}),
               'finished_utc': utc()}
    composition(args.out, summary, selected, candidates)
    write_json(args.out / 'SUMMARY.json', summary)
    heartbeat(args, f"Published {len(selected)} rows from {len(entries)} traces")
    print(canonical(summary), flush=True)
    return summary


def audit(args):
    require(1 <= args.workers <= 16 and args.replay_per_kind >= 0, 'invalid_audit_limits')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment_required')
    started = time.monotonic()
    inputs, summary = read_json(args.out / 'BUILD_INPUTS.json'), read_json(args.out / 'SUMMARY.json')
    config_sha = inputs.pop('config_sha256')
    require(digest(inputs) == config_sha == summary['config_sha256'], 'audit_config_digest')
    require(inputs['commit'] == summary['commit'], 'audit_commit')
    require(inputs['index']['sha256'] == INDEX_SHA and inputs['split']['sha256'] == SPLIT_SHA, 'audit_v3_pins')
    counting_entries = []
    eligible, _ = v3_sources(Path(inputs['index']['path']).parent, counting_entries)
    by_qid = {entry['qid']: entry for entry in eligible}
    qids = set(inputs['selected_qids'])
    require(len(qids) == len(inputs['selected_qids']) and qids.issubset(by_qid), 'audit_selected_membership')
    require(summary['traces_processed'] == len(qids), 'audit_trace_denominator')
    scenes = {(by_qid[qid]['dataset'], by_qid[qid]['scene']) for qid in qids}
    require(inputs['scene_groups'] == sorted(control.scene_group(*scene) for scene in scenes), 'audit_scene_membership')
    candidates, processed = [], 0
    for dataset, scene in sorted(scenes):
        path = args.out / 'shards' / (dataset + '__' + scene + '.jsonl')
        done = read_json(path.with_suffix('.done.json'))
        require(done['path'] == str(path) and done['sha256'] == sha(path), 'audit_shard_digest')
        with path.open() as stream:
            rows = [json.loads(line) for line in stream]
        require(len(rows) == done['rows'], 'audit_shard_rows')
        processed += done['stats']['traces_processed']
        candidates.extend(rows)
    require(processed == len(qids) and summary['scene_shards'] == len(scenes), 'audit_shard_denominator')
    candidates, _ = dedupe_rows(candidates)
    catalog = counting_catalog([entry for entry in counting_entries if (entry['dataset'], entry['scene']) in scenes])
    catalog_by_scene = defaultdict(list)
    for item in catalog:
        catalog_by_scene[(item['entry']['dataset'], item['entry']['scene'])].append(item)
    source_rows, replay_rows = {}, []
    replay_counts = Counter()
    for row in candidates:
        entry = row['evidence']['source_entry']
        require(entry['qid'] in qids and all(qid in qids for qid in row['source_qids']), 'audit_fact_source_membership')
        require(all(entry[key] == by_qid[entry['qid']][key] for key in ('qid', 'dataset', 'scene', 'question_type', 'row_path', 'row_sha256')), 'audit_source_index_binding')
        if entry['qid'] not in source_rows:
            source_rows[entry['qid']] = checked_json({'path': entry['row_path'], 'sha256': entry['row_sha256']})
        source = source_rows[entry['qid']]
        require((row['dataset'], row['scene']) == (entry['dataset'], entry['scene']), 'audit_fact_scene')
        kind, gt = row['question_type'], row['evidence']['gt']
        require(render(kind, gt['labels'], gt['values_unrounded']) == (row['question'], row['target']), 'audit_render')
        require(row['student_input'] == {**source['student_input'], 'question': row['question'], 'options': []}, 'audit_student_input')
        frame_sha = digest(source['student_input']['frames'])
        identity = gt['labels'][0] if kind.startswith('traceev_frames_') else sorted(gt['instance_ids'])
        require(row['fact_key'] == [frame_sha, kind, identity], 'audit_fact_key')
        require(row['qid'] == f"traceev__{row['scene']}__{kind}__{digest(row['fact_key'])[:12]}", 'audit_qid')
        require(row['extractor_commit'] == summary['commit'] and row['extractor_config_sha256'] == config_sha, 'audit_fact_provenance')
        require(row['supports'] == SUPPORTS[kind], 'audit_supports')
        checks, checked_entries = [], []
        if kind == 'traceev_count_list':
            checks, checked_entries = count_label_checks(entry, source, gt['labels'][0], count_value(row), catalog_by_scene[(row['dataset'], row['scene'])])
        require(row['label_check'] == (checks[0] if checks else None), 'audit_label_check')
        require(row['evidence']['label_checks'] == checks and row['evidence']['counting_entries'] == checked_entries, 'audit_counting_coverage')
        if replay_counts[kind] < args.replay_per_kind:
            replay_rows.append(row)
            replay_counts[kind] += 1
    selected, _ = select_budget(candidates, inputs['budget'], inputs['seed'])
    selected.sort(key=lambda row: (row['dataset'], row['scene'], row['qid']))
    expected_sha = hashlib.sha256()
    for row in selected:
        expected_sha.update((canonical(row) + '\n').encode())
    path = args.out / 'evidence_rows.jsonl'
    require(summary['path'] == str(path) and expected_sha.hexdigest() == sha(path) == summary['sha256'], 'audit_published_bytes')
    require(len(selected) == summary['rows'] and len({row['qid'] for row in selected}) == len(selected), 'audit_published_rows')
    require(summary['per_kind'] == {kind: sum(row['question_type'] == kind for row in selected) for kind in KINDS}, 'audit_kind_counts')
    require(summary['per_supported_type'] == dict(Counter(support for row in selected for support in row['supports'])), 'audit_support_counts')
    require(summary['label_checks'] == label_check_summary(selected) and summary['raw_label_checks'] == label_check_summary(candidates), 'audit_label_summary')
    with ProcessPoolExecutor(max_workers=args.workers, initializer=worker_init) as pool:
        for row, target in zip(replay_rows, pool.map(replay, replay_rows)):
            require(target == row['target'], 'audit_replay_target')
    result = {'status': 'PASS', 'checked_at': utc(), 'extractor_commit': summary['commit'], 'auditor_source_sha256': sha(__file__),
              'path': str(path), 'sha256': summary['sha256'], 'rows': len(selected), 'admitted_facts': len(candidates),
              'traces_reconciled': processed, 'scene_shards_authenticated': len(scenes),
              'replayed_by_kind': dict(replay_counts), 'replayed_qids': [row['qid'] for row in replay_rows],
              'seconds': time.monotonic() - started}
    write_json(args.out / 'AUDIT.json', result)
    print(canonical(result), flush=True)
    return result


def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest='command', required=True)
    for command in ('inventory', 'extract'):
        item = sub.add_parser(command)
        item.add_argument('--v3-layout', type=Path, required=True)
        item.add_argument('--out', type=Path, required=True)
        item.add_argument('--limit', type=int)
        item.add_argument('--seed', type=int, default=20260925)
        if command == 'extract':
            item.add_argument('--stratify', action='store_true')
            item.add_argument('--workers', type=int, default=8)
            item.add_argument('--budget', type=int, default=40000)
            item.add_argument('--heartbeat', type=Path)
    item = sub.add_parser('audit')
    item.add_argument('--out', type=Path, required=True)
    item.add_argument('--replay-per-kind', type=int, default=2)
    item.add_argument('--workers', type=int, default=4)
    return root


if __name__ == '__main__':
    args = parser().parse_args()
    {'inventory': inventory, 'extract': extract, 'audit': audit}[args.command](args)
