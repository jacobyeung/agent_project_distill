"""Epoch selection and public failure grammar shared by serving and row rendering."""
from contextlib import contextmanager
from contextvars import ContextVar
import re

_epoch = ContextVar('contract_epoch', default=True)
RUNTIME_STATUSES = ('unresolved', 'not seen', 'box unavailable', 'heading unavailable',
                    'frame unavailable', 'size unavailable', 'unavailable')


def new_contracts():
    return _epoch.get()


@contextmanager
def contract_epoch(enabled=True):
    if type(enabled) is not bool:
        raise ValueError('contract_epoch_must_be_boolean')
    token = _epoch.set(enabled)
    try:
        yield
    finally:
        _epoch.reset(token)


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
            if line == status or line.endswith(': '+status) or line.endswith(' '+status):
                return status
    return 'ok'


def status_text(status, name=None):
    if status not in RUNTIME_STATUSES:
        raise ValueError('unknown_runtime_status')
    return (name + ': ' if name else '') + status


def heading_available(geometry):
    if not new_contracts():
        return True
    import numpy as np
    from student_pilot.geometry_profiles import UP_PLANE_MIN
    if getattr(geometry, 'down', None) is not None:
        return bool(np.linalg.norm(np.asarray(geometry.down)[:2]) >= UP_PLANE_MIN)
    if geometry is None or not hasattr(geometry, 'cam'):
        return True
    return bool(np.linalg.norm(np.asarray(geometry.cam(1)[0])[2, :2]) >= UP_PLANE_MIN)
