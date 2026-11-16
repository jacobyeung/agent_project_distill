"""Reader-owned gravity decision, installed only after authenticated restore."""
import ast
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import inspect
from pathlib import Path
import textwrap

import numpy as np
from student_pilot.geometry_profiles import GeometryError

SEALED_VALIDATE_SHA256 = "05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a"
UP_PLANE_MIN = .3


def validate_up_convention(rotations):
    """Ignore ill-conditioned roll signs; retain upright-convention refusals."""
    R = np.asarray(rotations, float)
    plane = np.linalg.norm(R[:, 2, :2], axis=1)
    margin = -R[:, 2, 1]
    if plane[0] >= UP_PLANE_MIN:
        invalid = margin[0] <= 0
    else:
        usable = plane >= UP_PLANE_MIN
        invalid = usable.any() and np.median(margin[usable] / plane[usable]) <= 0
    if invalid:
        raise GeometryError('reference_camera_up_opposes_gravity')


_capture = ContextVar('gravity_guard_capture', default=None)
_installed = False
_recorder = None


def identity():
    return dict(evaluation_gravity_guard=dict(name='validate_up_convention',
                    sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                sealed_gravity_guard=dict(name='GeometryContract.validate',
                    inspect_sha256=SEALED_VALIDATE_SHA256))


@contextmanager
def capture(capture_set, native):
    if not isinstance(capture_set, str) or not capture_set or not isinstance(native, str) or not native:
        raise RuntimeError('gravity_guard_capture_identity_missing')
    token = _capture.set((capture_set, native))
    try:
        yield
    finally:
        _capture.reset(token)


class Recorder:
    def __init__(self):
        self.records = {}
        self.contracts = {}

    def record(self, sealed_refused, reviewed_refused, contract=None):
        key = _capture.get()
        if key is None and contract is not None:
            bound = self.contracts.get(id(contract))
            if bound is not None and bound[0] is contract:
                key = bound[1]
        if key is None:
            raise RuntimeError('gravity_guard_capture_context_missing')
        verdict = (bool(sealed_refused), bool(reviewed_refused))
        if key in self.records and self.records[key] != verdict:
            raise RuntimeError('gravity_guard_capture_verdict_changed')
        self.records[key] = verdict
        if contract is not None:
            self.contracts[id(contract)] = (contract, key)

    def report(self):
        result = {}
        for capture_set in sorted({key[0] for key in self.records}):
            rows = {native: value for (scope, native), value in self.records.items() if scope == capture_set}
            sealed = sorted(name for name, value in rows.items() if value[0])
            reviewed = sorted(name for name, value in rows.items() if value[1])
            added = sorted(set(reviewed) - set(sealed))
            result[capture_set] = dict(captures=sorted(rows), capture_count=len(rows),
                sealed_refused=sealed, sealed_refused_count=len(sealed),
                reviewed_refused=reviewed, reviewed_refused_count=len(reviewed),
                reviewed_only_refused=added, reviewed_only_refused_count=len(added))
        return result


def report():
    return {} if _recorder is None else _recorder.report()


def install(geometry_profiles_module, recorder):
    global _installed, _recorder
    if _installed:
        raise RuntimeError('gravity_guard_already_installed')
    if geometry_profiles_module.GeometryError is not GeometryError:
        raise RuntimeError('gravity_guard_exception_class_mismatch')
    original = geometry_profiles_module.GeometryContract.validate
    source = inspect.getsource(original)
    if hashlib.sha256(source.encode()).hexdigest() != SEALED_VALIDATE_SHA256:
        raise RuntimeError('sealed_validate_mismatch')
    body = ast.parse(textwrap.dedent(source)).body[0].body
    terminal = ast.parse("if -R[0, 2, 1] <= 0:\n    raise GeometryError('reference_camera_up_opposes_gravity')\nreturn self").body
    if len(body) < 2 or any(ast.dump(a) != ast.dump(b) for a, b in zip(body[-2:], terminal)):
        raise RuntimeError('sealed_validate_terminal_mismatch')

    def validate(self):
        sealed_refused = False
        try:
            original(self)
        except geometry_profiles_module.GeometryError as error:
            if str(error) != 'reference_camera_up_opposes_gravity':
                raise
            sealed_refused = True
        C = np.asarray(self.camera_to_world, float)
        R = C[:, :3, :3]
        try:
            validate_up_convention(R)
        except GeometryError:
            recorder.record(sealed_refused, True, self)
            raise
        recorder.record(sealed_refused, False, self)
        return self

    geometry_profiles_module.GeometryContract.validate = validate
    _recorder = recorder
    _installed = True
