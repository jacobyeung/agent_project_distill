"""Pinned camera poses for selected routed questions; trainer parsing and printing."""
import hashlib
import json
from pathlib import Path
import re
from types import FunctionType

DEFAULT_TYPES = ('camera_movement_direction', 'camera_displacement')


def validate_spec(spec):
    from .pointing_candidates import validate_pin
    if not isinstance(spec, dict) or set(spec) != {'values', 'types'}:
        raise ValueError('Pose override requires values and types')
    validate_pin(spec['values'])
    types = spec['types']
    if (not isinstance(types, list) or not types
            or any(not isinstance(t, str) or not re.fullmatch('[a-z][a-z0-9_]*', t) for t in types)
            or len(set(types)) != len(types)):
        raise ValueError('Pose override types must be distinct question types')


def load_values(spec):
    """Read and authenticate the same bounded bytes that are parsed."""
    import numpy as np
    validate_spec(spec)
    with Path(spec['values']['path']).open('rb') as stream:
        raw = stream.read((64 << 20) + 1)
    if len(raw) > 64 << 20 or hashlib.sha256(raw).hexdigest() != spec['values']['sha256']:
        raise ValueError('Pose override values pin differs or exceeds budget')

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate pose override key')
            result[key] = value
        return result

    data = json.loads(raw, object_pairs_hook=unique)
    if (not isinstance(data, dict) or data.get('schema') != 'pose-override-v1'
            or not isinstance(data.get('g3t_pin'), str) or not data['g3t_pin']
            or not isinstance(data.get('scale_rule_sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', data['scale_rule_sha256'])
            or not isinstance(data.get('scenes'), dict)):
        raise ValueError('Pose override schema differs')
    scenes = {}
    for scene, frames in data['scenes'].items():
        if not re.fullmatch(r'[^/\s]+/[^/\s]+', scene) or not isinstance(frames, dict):
            raise ValueError('Invalid pose override scene')
        scenes[scene] = {}
        for key, values in frames.items():
            if not re.fullmatch(r'[1-9]|[12][0-9]|3[0-2]', key):
                raise ValueError('Pose override frame must be 1..32')
            if (not isinstance(values, list) or len(values) != 16
                    or any(type(v) not in (int, float) for v in values)):
                raise ValueError('Pose override requires 16 numeric values')
            matrix = np.asarray(values, dtype=np.float64).reshape(4, 4)
            rotation = matrix[:3, :3]
            if (not np.isfinite(matrix).all() or not np.allclose(matrix[3], [0, 0, 0, 1], atol=1e-6, rtol=0)
                    or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-4, rtol=0)
                    or not np.isclose(np.linalg.det(rotation), 1., atol=1e-4, rtol=0)):
                raise ValueError('Pose override requires rigid finite camera-to-world matrices')
            scenes[scene][int(key)] = matrix
    return scenes


def geometry_from_c2w(frames, student):
    """Use the trainer's level frame/gravity and printer with relative c2w poses."""
    import numpy as np
    from student_pilot.carrier_c1_routing import OwnGeometry

    class Geometry(OwnGeometry):
        def camera(self, k):
            # C_1^-1 C_k is the inverse of the trainer's pose code E_k.
            if k == 1:
                return np.eye(3), np.zeros(3)
            first, target = frames[1], frames[k]
            return (first[:3, :3].T @ target[:3, :3],
                    first[:3, :3].T @ (target[:3, 3] - first[:3, 3]))

    # No gravity or FoV override is defined by pose-override-v1.
    result = Geometry.__new__(Geometry)
    result.__dict__ = {**student.__dict__, '_poses': {}}
    return result


class Responder:
    def __init__(self, scenes, task, types):
        self.enabled = task['question_type'] in types
        self.frames = scenes.get(task['dataset']+'/'+task['scene_name'], {})
        self.calls = []

    def respond(self, text, registry, student):
        from student_pilot import carrier_c1_decode as decode
        if not self.enabled:
            return decode.respond(text, registry, student)
        try:
            call = decode.parse_head(text)
        except decode.CallError:
            return decode.respond(text, registry, student)
        if call['name'] not in ('move', 'pose', 'turn'):
            return decode.respond(text, registry, student)
        called = [call['frame']] if call['name'] == 'pose' else [call['i'], call['j']]
        missing = sorted({1, *called} - self.frames.keys())
        own_text, own_info = decode.respond(text, registry, student)
        response, info = own_text, own_info
        override_text = None
        used = False
        if not missing and student is not None:
            override_text, override_info = decode.respond(text, registry, geometry_from_c2w(self.frames, student))
            if override_info['kind'] == 'head':
                response, info, used = override_text, override_info, True
        audit = dict(call=text, frames_called=called, required_frames=sorted({1, *called}),
                     missing_frames=missing, override_used=used, override_missing=bool(missing),
                     override_response_text=override_text, student_response_text=own_text)
        self.calls.append(audit)
        return response, {**info, **{k:v for k,v in audit.items() if k != 'call'}}

    def fields(self):
        return dict(override_used=any(c['override_used'] for c in self.calls),
                    override_missing=any(c['override_missing'] for c in self.calls),
                    override_frames_called=sorted({f for c in self.calls for f in c['frames_called']}),
                    override_calls=list(self.calls))


def generate(trainer_generate, responder, *args, **kwargs):
    """Run identical trainer bytecode with a private response binding per item."""
    import torch
    original = trainer_generate.__wrapped__
    hooked = FunctionType(original.__code__, {**original.__globals__, 'respond': responder.respond},
                          original.__name__, original.__defaults__, original.__closure__)
    hooked.__kwdefaults__ = original.__kwdefaults__
    return torch.no_grad()(hooked)(*args, **kwargs)
