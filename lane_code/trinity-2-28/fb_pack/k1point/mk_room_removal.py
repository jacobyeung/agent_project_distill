"""Build a protected-room removal list from a census row-key file (any stream).

Usage: python mk_room_removal.py <census_keys.json|.jsonl> <out.jsonl> [reason]
Input: a JSON list, a JSON object with a list under 'rows'/'hits'/'keys', or JSONL; each item is a row_key
string or a dict with 'row_key' (or 'qid'), optionally 'room'/'canonical'/'status'.
Output: one {"row_key", "reason", ...} line per unique key, sorted by row_key, the format
row_removals.Removals reads (plain pin, no 'defects'); prints count and sha256.
"""
import hashlib
import json
import sys


def items(path):
    text = open(path).read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(data, dict):
        for key in ('rows', 'hits', 'keys', 'row_keys'):
            if isinstance(data.get(key), list):
                return data[key]
        raise SystemExit('no row list in ' + path)
    return data


def main():
    src, out = sys.argv[1], sys.argv[2]
    reason = sys.argv[3] if len(sys.argv) > 3 else 'protected_room'
    rows = {}
    for item in items(src):
        if isinstance(item, str):
            item = dict(row_key=item)
        key = item.get('row_key') or item.get('qid')
        if not isinstance(key, str) or not key:
            raise SystemExit('item without row_key: ' + json.dumps(item)[:200])
        entry = dict(row_key=key, reason=item.get('reason') or reason)
        for field in ('room', 'canonical', 'status', 'stream'):
            if item.get(field) is not None:
                entry[field] = item[field]
        rows[key] = entry
    body = ''.join(json.dumps(rows[k], sort_keys=True) + '\n' for k in sorted(rows))
    open(out, 'w').write(body)
    print(len(rows), hashlib.sha256(body.encode()).hexdigest(), out)


if __name__ == '__main__':
    main()
