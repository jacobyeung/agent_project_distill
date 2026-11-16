"""Opaque console summaries; authenticated artifacts retain their complete content."""
import hashlib
import json
import os


def console(value, *, force=False):
    if not force and os.environ.get('R1_OPAQUE_LOGS') != '1':
        return value
    payload = json.dumps(value, sort_keys=True, default=str).encode()
    return {'event': 'result', 'sha256': hashlib.sha256(payload).hexdigest()}
