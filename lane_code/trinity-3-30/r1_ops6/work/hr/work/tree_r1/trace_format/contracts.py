"""Epoch selection and public failure grammar shared by serving and row rendering."""
from contextlib import contextmanager
from contextvars import ContextVar
import re
import math

_epoch = ContextVar('contract_epoch', default=True)
HEADING_PLANE_MIN_DEFAULT = 0.3
_UNSET = object()
_heading_plane_min = ContextVar('heading_plane_min', default=HEADING_PLANE_MIN_DEFAULT)


def heading_plane_min(value=_UNSET):
    """Read or validate the configuration-bound heading threshold."""
    value = _heading_plane_min.get() if value is _UNSET else value
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value < 1:
        raise ValueError('heading_plane_min_must_be_finite_in_open_interval_0_1')
    return float(value)


def contract_identity():
    return dict(contract_epoch=True, heading_plane_min=heading_plane_min()) if new_contracts() else {}

RUNTIME_STATUSES = ('unresolved', 'not seen', 'box unavailable', 'heading unavailable',
                    'frame unavailable', 'size unavailable', 'unavailable')


def new_contracts():
    return _epoch.get()


@contextmanager
def contract_epoch(enabled=True, *, heading_plane_min=_UNSET):
    if type(enabled) is not bool:
        raise ValueError('contract_epoch_must_be_boolean')
    threshold = globals()['heading_plane_min'](heading_plane_min)
    heading_token = _heading_plane_min.set(threshold)
    token = _epoch.set(enabled)
    try:
        yield
    finally:
        _epoch.reset(token)
        _heading_plane_min.reset(heading_token)


def geometry_mode(session):
    mode = getattr(session, 'geometry_mode', 'sensor')
    if mode not in ('sensor', 'predicted'):
        raise ValueError('unknown_geometry_mode')
    return mode


def response_status(text):
    if not isinstance(text, str) or not text.strip():
        return 'missing response'
    text = text.strip().removeprefix('<tool_response>').removesuffix('</tool_response>').strip()
    if not text:
        return 'missing response'
    first = text.splitlines()[0].strip()
    body = first.split(': ', 1)[1] if ': ' in first and not first.lower().startswith('error:') else first
    if body.lower().startswith('error:'):
        return 'error'
    if body == 'heading unavailable' and any(
            line.startswith(('size ', 'distance ', 'count ')) and 'unavailable' not in line
            for line in text.splitlines()[1:]):
        return 'ok'
    return body if body in RUNTIME_STATUSES else 'ok'


def status_text(status, name=None):
    if status not in RUNTIME_STATUSES:
        raise ValueError('unknown_runtime_status')
    return (name + ': ' if name else '') + status


def heading_available(geometry, frame=1):
    if not new_contracts():
        return True
    import numpy as np
    threshold = heading_plane_min()
    if getattr(geometry, 'heading', None) is not None:
        rotation = np.eye(3) if frame == 1 else geometry.camera(frame)[0]
        return geometry.heading('availability', rotation, geometry.down)
    if getattr(geometry, 'down', None) is not None:
        down = np.asarray(geometry.down, float)
        down = down / np.linalg.norm(down)
        rotation = np.eye(3) if frame == 1 else geometry.camera(frame)[0]
        return bool(np.linalg.norm((np.asarray(rotation).T @ down)[:2]) >= threshold)
    if geometry is None or not hasattr(geometry, 'cam'):
        return True
    return bool(np.linalg.norm(np.asarray(geometry.cam(frame)[0])[2, :2]) >= threshold)


def partial_f1(values, number):
    """The public level frame has y up; only its horizontal components need heading."""
    return '(heading unavailable, '+number(values[1])+', heading unavailable)'


def private_metric_basis(camera_rotation, up):
    """Anchor hidden rounded operands to a nonreference camera, never its yaw."""
    import numpy as np
    for frame in range(2, 33):
        try:
            rotation = np.asarray(camera_rotation(frame), dtype=float)
        except (ValueError, IndexError, KeyError):
            continue
        if rotation.shape != (3, 3) or not np.isfinite(rotation).all():
            continue
        forward = rotation[:, 2] - (rotation[:, 2] @ up) * up
        if np.linalg.norm(forward) < heading_plane_min():
            forward = rotation[:, 0] - (rotation[:, 0] @ up) * up
        norm = np.linalg.norm(forward)
        if norm < 1e-6:
            continue
        forward /= norm
        return np.column_stack((np.cross(forward, up), up, forward))
    return None


def epoch_class(sealed, current):
    """Keep a subclassable class while choosing the implementation at construction."""
    implementations = {}
    class EpochMeta(type):
        def __getattr__(cls, name):
            return getattr(current if new_contracts() else sealed, name)

        def __call__(cls, *args, **kwargs):
            key = (cls, new_contracts())
            if key not in implementations:
                base = current if key[1] else sealed
                implementations[key] = type(cls.__name__, (cls, base), {'__module__': cls.__module__})
            return type.__call__(implementations[key], *args, **kwargs)
    return EpochMeta(sealed.__name__, (), {'__module__': sealed.__module__})
