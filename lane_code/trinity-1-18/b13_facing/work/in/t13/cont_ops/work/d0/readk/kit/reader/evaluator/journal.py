"""One conflict rule for resume, merge, and budget journals."""
import json
from pathlib import Path


def records(path):
    path = Path(path)
    if not path.exists():
        return
    with path.open() as stream:
        lines = iter(stream)
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                # A trailing partial write is recoverable. append() separates any
                # recovered tail from the next attempt with an empty line.
                following = next(lines, None)
                if following is not None and following.strip():
                    raise ValueError(f'Broken journal {path}:{number}') from exc
                continue
            if not isinstance(row, dict) or not isinstance(row.get('key'), str):
                raise ValueError(f'Broken journal row {path}:{number}')
            yield row, line.rstrip('\n')


def retain(rows, row):
    key = row['key']
    previous = rows.get(key)
    if previous and previous.get('status') == 'complete':
        if row.get('status') == 'complete' and previous != row:
            raise ValueError('Conflicting complete rows: '+key)
        return
    rows[key] = row


class _PartialJSON(Exception):
    pass


def _partial_key(text):
    """Accept only a syntactically valid, unfinished JSON object with a known key."""
    import re
    pos = 0
    item_key = None

    def space():
        nonlocal pos
        while pos < len(text) and text[pos] in ' \t\r\n':
            pos += 1

    def need():
        space()
        if pos == len(text):
            raise _PartialJSON

    def string():
        nonlocal pos
        start = pos
        pos += 1
        while pos < len(text):
            c = text[pos]
            pos += 1
            if c == '"':
                return json.loads(text[start:pos])
            if ord(c) < 32:
                raise ValueError('Control character in JSON string')
            if c == '\\':
                if pos == len(text):
                    raise _PartialJSON
                c = text[pos]
                pos += 1
                if c == 'u':
                    for _ in range(4):
                        if pos == len(text):
                            raise _PartialJSON
                        if text[pos] not in '0123456789abcdefABCDEF':
                            raise ValueError('Invalid JSON escape')
                        pos += 1
                elif c not in '"\\/bfnrt':
                    raise ValueError('Invalid JSON escape')
        raise _PartialJSON

    def value(root=False):
        nonlocal pos, item_key
        need()
        c = text[pos]
        if c == '"':
            return string()
        if c in '{[':
            pos += 1
            end = '}' if c == '{' else ']'
            need()
            if text[pos] == end:
                pos += 1
                return
            while True:
                need()
                if c == '{':
                    if text[pos] != '"':
                        raise ValueError('Invalid JSON member')
                    name = string()
                    need()
                    if text[pos] != ':':
                        raise ValueError('Invalid JSON member separator')
                    pos += 1
                    result = value()
                    if root and name == 'key':
                        if not isinstance(result, str) or item_key is not None:
                            raise ValueError('Ambiguous partial item key')
                        item_key = result
                else:
                    value()
                need()
                if text[pos] == end:
                    pos += 1
                    return
                if text[pos] != ',':
                    raise ValueError('Invalid JSON separator')
                pos += 1
        for literal in ('true', 'false', 'null'):
            if text.startswith(literal, pos):
                pos += len(literal)
                return
            if literal.startswith(text[pos:]):
                raise _PartialJSON
        match = re.match(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?', text[pos:])
        if match:
            pos += len(match[0])
            # A numeric token can itself be interrupted after a dot or exponent.
            if text[pos:] in ('.', 'e', 'E', 'e+', 'e-', 'E+', 'E-'):
                raise _PartialJSON
            return
        if text[pos:] == '-':
            raise _PartialJSON
        raise ValueError('Invalid JSON value')

    if not text.lstrip().startswith('{'):
        raise ValueError('Partial journal row must be an object')
    try:
        value(root=True)
    except _PartialJSON:
        if item_key is not None:
            return item_key
    raise ValueError('Not an identifiable partial JSON row')


def annotation_records(path):
    """Recover interrupted legacy writes only during immutable-copy annotation."""
    def reject_constant(value):
        raise ValueError('Non-JSON constant: '+value)
    rows, skipped = [], []
    offset = 0
    with Path(path).open('rb') as stream:
        for number, raw in enumerate(stream, 1):
            start = offset
            offset += len(raw)
            if not raw.strip():
                continue
            try:
                line = raw.decode('utf-8')
                try:
                    row = json.loads(line, parse_constant=reject_constant)
                except json.JSONDecodeError:
                    key = _partial_key(line.rstrip('\r\n'))
                    skipped.append(dict(line=number, byte_offset=start, byte_length=len(raw), key=key))
                    continue
                if not isinstance(row, dict) or not isinstance(row.get('key'), str):
                    raise ValueError('Invalid row identity')
                rows.append((row, line.rstrip('\n'), start))
            except (ValueError, RecursionError) as exc:
                raise ValueError(f'Broken journal {path}:{number} at byte {start}') from exc
    present = {row['key'] for row, _, _ in rows}
    for skip in skipped:
        later = any(row['key'] == skip['key'] and row.get('status') == 'complete'
                    and start > skip['byte_offset'] for row, _, start in rows)
        if later:
            skip['disposition'] = 'completed_later'
        elif skip['key'] not in present:
            skip['disposition'] = 'missing'
        else:
            raise ValueError('Broken journal: partial item lacks a later complete row: '+skip['key'])
    audit = dict(skipped_line_count=len(skipped), skipped_lines=skipped,
                 missing_keys=sorted({s['key'] for s in skipped if s['disposition'] == 'missing'}))
    return [(row, raw) for row, raw, _ in rows], audit
