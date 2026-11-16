import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

from .assets import safe_scene
from .blocking import scene_key
from .formats import UNIT_METERS, format_value


POLICY = 'vsi590k-authenticated-training-exact-scan-room-label-v1'
AREA_UNITS = re.compile(r'\b(square meters|square feet)\b')


class RoomLabelDeferred(ValueError):
    pass


def parse_label(row):
    turns = row.get('conversations', [])
    human = [turn['value'] for turn in turns if turn.get('from') == 'human']
    answers = [turn['value'] for turn in turns if turn.get('from') == 'gpt']
    if len(human) != 1 or len(answers) != 1 or not isinstance(human[0], str) or not isinstance(answers[0], str):
        raise ValueError('room_label_invalid')
    units = set(AREA_UNITS.findall(human[0]))
    if len(units) != 1 or not re.fullmatch(r'\d+(?:\.\d+)?', answers[0]):
        raise ValueError('room_label_invalid')
    unit = units.pop()
    value = Decimal(answers[0]) * UNIT_METERS[unit]
    if not value.is_finite() or value <= 0 or not math.isfinite(float(value)) or float(value) == 0:
        raise ValueError('room_label_invalid')
    return {'answer': answers[0], 'units': unit, 'question': human[0], 'value_si_decimal': str(value)}


class RoomLabels:
    def __init__(self, authority, identities, split, blocked):
        self.authority = copy.deepcopy(authority)
        self.labels, self.deferred = {}, {}
        wanted = {safe_scene({'dataset': dataset, 'scene_name': scene}) for dataset, scene in identities}
        allowed = set()
        for dataset, scene in wanted:
            key = dataset, scene
            if scene_key(dataset, scene) in blocked:
                self.deferred[key] = 'room_label_benchmark_scene'
            elif split.side(dataset, scene) != 'train':
                self.deferred[key] = 'room_label_not_training'
            else:
                allowed.add(key)
                self.deferred[key] = 'room_label_missing'
        path = Path(authority['path'])
        size = authority.get('bytes', authority.get('size_bytes'))
        if path.is_symlink() or not path.is_file() or size is not None and path.stat().st_size != size:
            raise ValueError('room label source is missing, symlinked, or size-drifted')
        hasher = hashlib.sha256()
        candidates, invalid = {}, set()
        with path.open('rb') as handle:
            for number, raw in enumerate(handle, 1):
                hasher.update(raw)
                row = json.loads(raw)
                if row.get('question_type') != 'absolute_size_room' or not isinstance(row.get('video'), str):
                    continue
                video = PurePosixPath(row['video'])
                if len(video.parts) != 2 or str(video) != row['video'] or video.suffix != '.mp4':
                    continue
                key = video.parent.name, video.stem
                if key not in allowed:
                    continue
                try:
                    label = parse_label(row)
                except (ValueError, InvalidOperation, KeyError, TypeError, AttributeError):
                    invalid.add(key)
                    continue
                candidates.setdefault(key, []).append({**label, 'schema': POLICY, 'dataset': key[0], 'scene': key[1],
                    'video': row['video'], 'source': copy.deepcopy(authority), 'source_line': number,
                    'source_line_sha256': hashlib.sha256(raw).hexdigest(), 'split_side': 'train',
                    'training_split': copy.deepcopy(split.published_pin),
                    'inherited_split': copy.deepcopy(split.inherited_pin)})
        if hasher.hexdigest() != authority['sha256']:
            raise ValueError('room label source digest mismatch')
        for key in allowed:
            records = candidates.get(key, [])
            if key in invalid:
                self.deferred[key] = 'room_label_invalid'
            elif len({Decimal(record['value_si_decimal']) for record in records}) > 1:
                self.deferred[key] = 'room_label_conflict'
            elif records:
                self.labels[key] = {**records[0], 'agreeing_source_lines': [record['source_line'] for record in records]}
                self.deferred.pop(key)

    def lookup(self, dataset, scene):
        key = dataset, scene
        if key not in self.labels:
            raise RoomLabelDeferred(self.deferred.get(key, 'room_label_unrequested_scene'))
        return copy.deepcopy(self.labels[key])


def label_measurement(label, unit, conventions):
    if unit not in ('square meters', 'square feet'):
        raise ValueError('room_label_requires_area_unit')
    value = Decimal(label['value_si_decimal'])
    text = format_value(value, 'absolute_size_room', unit, conventions)
    return {'value_si': float(value), 'si_unit': 'square meters', 'value': float(value / UNIT_METERS[unit]),
            'units': unit, 'rounded_value': text, 'object_ids': []}
