#!/usr/bin/env python3
"""Measure the bytes and estimated tokens a fresh orchestrator reads before any work.

Usage: measure_reads.py --set NAME SPEC [SPEC ...] [--set NAME SPEC ...] [--json]
                        [--bytes-per-token 4.0]

A SPEC is `LABEL=PATH` (the whole file), `LABEL=PATH#above=HEADING` (the lines before the first
line that starts with HEADING), `LABEL=PATH#sections=A,B` (the `## ` sections whose titles start
with A or B, headings included) or `LABEL=@BYTES` (a size taken from a stat, for a file the
measurement may not read). Tokens are estimated as bytes / --bytes-per-token; the estimate is a
ratio, not a tokenizer count. Reads only the files named. Standard library only; Python 3.6-safe.
"""
import argparse
import json
import sys


def _lines_above(text, heading):
    out = []
    for line in text.splitlines(True):
        if line.startswith(heading):
            break
        out.append(line)
    return ''.join(out)


def _sections(text, titles):
    out = []
    keep = False
    for line in text.splitlines(True):
        if line.startswith('## '):
            title = line[3:].strip().lower()
            keep = any(title.startswith(t.strip().lower()) for t in titles)
        if keep:
            out.append(line)
    return ''.join(out)


def measure_spec(spec):
    """Return (label, bytes) for one SPEC."""
    if '=' not in spec:
        raise ValueError('SPEC needs LABEL=...: %r' % spec)
    label, target = spec.split('=', 1)
    if target.startswith('@'):
        return label, int(target[1:])
    path, _, mode = target.partition('#')
    with open(path, 'rb') as handle:
        data = handle.read()
    if not mode:
        return label, len(data)
    text = data.decode('utf-8', 'replace')
    kind, _, arg = mode.partition('=')
    if kind == 'above':
        part = _lines_above(text, arg)
    elif kind == 'sections':
        part = _sections(text, arg.split(','))
    else:
        raise ValueError('unknown mode %r in %r' % (kind, spec))
    return label, len(part.encode('utf-8'))


def measure(sets, bytes_per_token=4.0):
    result = []
    for name, specs in sets:
        items = [measure_spec(spec) for spec in specs]
        total = sum(size for _, size in items)
        result.append({'set': name, 'items': [{'label': l, 'bytes': b,
                                               'tokens': int(round(b / bytes_per_token))}
                                              for l, b in items],
                       'bytes': total, 'tokens': int(round(total / bytes_per_token))})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--set', nargs='+', action='append', required=True, metavar='NAME SPEC')
    parser.add_argument('--bytes-per-token', type=float, default=4.0)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    sets = []
    for group in args.set:
        if len(group) < 2:
            parser.error('--set needs a name and at least one SPEC')
        sets.append((group[0], group[1:]))
    try:
        result = measure(sets, args.bytes_per_token)
    except (OSError, ValueError) as err:
        sys.stderr.write('REFUSED: %s\n' % err)
        return 2
    if args.json:
        sys.stdout.write(json.dumps(result, indent=1, sort_keys=True) + '\n')
        return 0
    for entry in result:
        sys.stdout.write('## %s: %d bytes, ~%d tokens\n' % (entry['set'], entry['bytes'],
                                                           entry['tokens']))
        for item in entry['items']:
            sys.stdout.write('  %-28s %8d bytes  ~%6d tokens\n' % (item['label'], item['bytes'],
                                                                  item['tokens']))
    if len(result) >= 2 and result[0]['tokens']:
        first, last = result[0], result[-1]
        sys.stdout.write('saving %s -> %s: %d bytes, ~%d tokens (%.0f%%)\n' % (
            first['set'], last['set'], first['bytes'] - last['bytes'],
            first['tokens'] - last['tokens'],
            100.0 * (first['tokens'] - last['tokens']) / first['tokens']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
