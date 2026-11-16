"""Strict shared admission for uploader completion records."""
import json
import re
from pathlib import Path


def parse_done(path, run=None, step=None):
    text = Path(path).read_text()
    if text.lstrip().startswith('{'):
        def unique(pairs):
            out = {}
            for key, value in pairs:
                if key in out: raise ValueError('Duplicate done field')
                out[key] = value
            return out
        value = json.loads(text, object_pairs_hook=unique)
    else:
        lines = text.splitlines()
        if len(lines) != 1 or len(lines[0].split()) != 3:
            raise ValueError('Done requires exactly one line with three fields')
        obj, size, digest = lines[0].split()
        if not re.fullmatch('[1-9][0-9]*', size): raise ValueError('Invalid done bytes')
        value = dict(object=obj, bytes=int(size), sha256=digest)
    if (not isinstance(value, dict) or set(value) != {'object', 'bytes', 'sha256'} or
            type(value['bytes']) is not int or value['bytes'] <= 0 or
            not isinstance(value['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', value['sha256'])):
        raise ValueError('Done requires object, positive integer bytes, and whole-tar sha256 only')
    match = re.fullmatch(r'q8/8865619b/(469ddece|359fcc3c)_m([1-9][0-9]*)\.tar', str(value['object']))
    if not match or (run is not None and match[1] != run) or (step is not None and int(match[2]) != step):
        raise ValueError('Done object must match allowed run and step in q8/8865619b')
    return value
