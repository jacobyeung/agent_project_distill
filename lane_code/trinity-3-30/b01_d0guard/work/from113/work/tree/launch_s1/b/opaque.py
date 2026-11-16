#!/usr/bin/env python3
"""Emit bounded opaque records for console and observer output. No input text is retained.
If the sink fails (closed pipe, I/O error), keep draining the input so the producer never sees SIGPIPE."""
import hashlib
import json
import re
import sys


def record(block):
    try:
        value = json.loads(block)
    except (ValueError, UnicodeError, RecursionError):
        value = None
    if (isinstance(value, dict) and set(value) == {'event', 'bytes', 'sha256'}
            and value['event'] == 'output' and type(value['bytes']) is int
            and 0 < value['bytes'] <= 65536 and isinstance(value['sha256'], str)
            and re.fullmatch('[0-9a-f]{64}', value['sha256'])):
        return value
    return {'event': 'output', 'bytes': len(block),
            'sha256': hashlib.sha256(block).hexdigest()}


def main():
    sink = True
    while True:
        try:
            block = sys.stdin.buffer.readline(65536)
        except OSError:
            continue
        if not block:
            break
        if not sink:
            continue
        try:
            sys.stdout.write(json.dumps(record(block), sort_keys=True) + '\n')
            sys.stdout.flush()
        except (OSError, ValueError):
            sink = False


if __name__ == '__main__':
    try:
        main()
    finally:
        try:
            sys.stdout.close()
        except Exception:
            pass
