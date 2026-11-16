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
    for line in text.splitlines():
        line = line.strip()
        if 'error:' in line.lower():
            return 'error'
        for status in RUNTIME_STATUSES:
            if (line == status or line.endswith(': '+status) or line.endswith(' '+status)
                    or (status == 'heading unavailable' and status in line)):
                return status
    return 'ok'


def status_text(status, name=None):
    if status not in RUNTIME_STATUSES:
        raise ValueError('unknown_runtime_status')
    return (name + ': ' if name else '') + status


def heading_available(geometry, frame=1):
    if not new_contracts():
        return True
    import numpy as np
    threshold = heading_plane_min()
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
