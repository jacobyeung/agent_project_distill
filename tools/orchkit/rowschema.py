"""Stream row checks using an orchkit-rowprofile-v1 JSON profile.

Profiles contain required (non-null dotted paths), vocab (path -> allowed values),
when (clauses with config equality predicates, required, positive_int and enum),
forbid_substrings (case-insensitive), forbid_values (path -> values), and
forbid_values_files (path -> newline-separated values, relative to the profile).
groups contains {key: dotted path, size: integer}; unique lists dotted paths.
family_field defaults to family; id_field defaults to id. Numeric path components
index lists; other components traverse objects. Missing families use <none>.

Use load_profile(filename) to resolve file-backed exclusions before check().
Direct profiles resolve exclusion filenames against the current directory.
check(rows_iter, profile, config) consumes rows once and returns rows, violations,
ok, and families with row counts, per-rule counts, and bounded first examples.
Group violations count once per incomplete group in each affected family;
unique violations count each repeat after the first. Missing group keys violate
groups; missing unique or vocabulary fields require a separate required rule.
Memory grows with distinct group/unique values and families, never with all rows.

CLI: python rowschema.py check --rows FILE.jsonl[.gz] --profile PROFILE.json
     [--config CONFIG.json] [--max-print 20] [--json OUT.json]
Exits 0 when clean, 1 on violations, and 2 on unreadable input.
"""
import argparse
import gzip
import io
import json
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from . import util
except ImportError:
    import util


MISSING = object()


def get_path(value, path):
    """Return a dotted field, or MISSING (distinct from a JSON null)."""
    for part in path.split('.'):
        if isinstance(value, dict):
            value = value.get(part, MISSING)
        elif isinstance(value, list) and part.isdigit():
            index = int(part)
            value = value[index] if index < len(value) else MISSING
        else:
            return MISSING
        if value is MISSING:
            return MISSING
    return value


def equal(left, right):
    if left is MISSING or right is MISSING:
        return False
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    return util.canonical_json(left) == util.canonical_json(right)


def load_profile(filename):
    """Read a profile and resolve exclusion files relative to its location."""
    profile = util.read_json(filename)
    if not isinstance(profile, dict):
        raise ValueError('profile must be an object')
    profile = dict(profile)
    profile['_profile_dir'] = os.path.dirname(os.path.abspath(filename))
    return profile


def _exclusions(profile):
    values = dict((path, list(items)) for path, items in profile.get('forbid_values', {}).items())
    for path, filename in profile.get('forbid_values_files', {}).items():
        full = os.path.join(profile.get('_profile_dir', '.'), filename)
        with open(full, encoding='utf-8') as handle:
            values.setdefault(path, []).extend(line.rstrip('\r\n') for line in handle
                                               if line.rstrip('\r\n'))
    return values


def _substring_path(value, needle, path=''):
    """Locate the first matching key or scalar, including JSON escape sequences."""
    if isinstance(value, dict):
        for key, item in value.items():
            here = path + '.' + key if path else key
            if needle in key.lower() or needle in util.canonical_json(key).decode('utf-8').lower():
                return here
            found = _substring_path(item, needle, here)
            if found is not None:
                return found
    elif isinstance(value, list):
        for i, item in enumerate(value):
            here = '%s.%d' % (path, i) if path else str(i)
            found = _substring_path(item, needle, here)
            if found is not None:
                return found
    else:
        raw = value if isinstance(value, str) else ''
        if needle in raw.lower() or needle in util.canonical_json(value).decode('utf-8').lower():
            return path or '$'
    return None


def check(rows_iter, profile, config=None, max_examples=20):
    """Check an iterable once; keep at most max_examples examples per family."""
    if not isinstance(profile, dict) or profile.get('schema', 'orchkit-rowprofile-v1') != \
            'orchkit-rowprofile-v1':
        raise ValueError('profile schema must be orchkit-rowprofile-v1')
    if max_examples < 0:
        raise ValueError('max_examples must be nonnegative')
    config = {} if config is None else config
    forbidden = _exclusions(profile)
    active = [clause for clause in profile.get('when', [])
              if all(equal(get_path(config, path), value)
                     for path, value in clause.get('config', {}).items())]
    group_rules = profile.get('groups', [])
    for group in group_rules:
        if type(group.get('size')) is not int or group['size'] <= 0:
            raise ValueError('group size must be a positive integer')
    groups = [{} for _ in group_rules]
    seen = dict((path, set()) for path in profile.get('unique', []))
    result = {'schema': 'orchkit-rowcheck-v1', 'ok': True, 'rows': 0,
              'violations': {}, 'families': {}}

    def add(family, rule, path, row_number, row_id, message):
        result['ok'] = False
        counts = result['violations']
        counts[rule] = counts.get(rule, 0) + 1
        summary = result['families'][family]
        counts = summary['violations']
        counts[rule] = counts.get(rule, 0) + 1
        if len(summary['examples']) < max_examples:
            summary['examples'].append({'rule': rule, 'path': path, 'row': row_number,
                                        'id': row_id, 'message': message})

    for number, row in enumerate(rows_iter, 1):
        result['rows'] += 1
        family = get_path(row, profile.get('family_field', 'family'))
        if family is MISSING:
            family = '<none>'
        elif not isinstance(family, str):
            family = util.canonical_json(family).decode('utf-8')
        summary = result['families'].setdefault(family, {'rows': 0, 'violations': {}, 'examples': []})
        summary['rows'] += 1
        row_id = get_path(row, profile.get('id_field', 'id'))
        if row_id is MISSING:
            row_id = None

        def fail(rule, path, message):
            add(family, rule, path, number, row_id, message)

        if not isinstance(row, dict):
            fail('row_type', '$', 'row must be an object')
        required = list(profile.get('required', []))
        for clause in active:
            required.extend(clause.get('required', []))
            for path in clause.get('positive_int', []):
                value = get_path(row, path)
                if type(value) is not int or value <= 0:
                    fail('positive_int', path, 'must be a positive integer')
            for path, allowed in clause.get('enum', {}).items():
                value = get_path(row, path)
                if not any(equal(value, item) for item in allowed):
                    fail('enum', path, 'must be present and one of the allowed values')
        for path in dict.fromkeys(required):
            value = get_path(row, path)
            if value is MISSING or value is None:
                fail('required', path, 'must be present and non-null')
        for path, allowed in profile.get('vocab', {}).items():
            value = get_path(row, path)
            if value is not MISSING and not any(equal(value, item) for item in allowed):
                fail('vocab', path, 'value is outside the vocabulary')
        for word in profile.get('forbid_substrings', []):
            path = _substring_path(row, word.lower())
            if path is None and word.lower() in util.canonical_json(row).decode('utf-8').lower():
                path = '$'
            if path is not None:
                fail('forbid_substrings', path, 'contains forbidden substring %r' % word)
        for path, values in forbidden.items():
            value = get_path(row, path)
            if any(equal(value, item) for item in values):
                fail('forbid_values', path, 'value is excluded')
        for path, values in seen.items():
            value = get_path(row, path)
            if value is MISSING:
                continue
            token = util.canonical_json(value)
            if token in values:
                fail('unique', path, 'value repeats an earlier row')
            values.add(token)
        for rule, counts in zip(group_rules, groups):
            path = rule['key']
            value = get_path(row, path)
            if value is MISSING:
                fail('groups', path, 'group key is missing')
                continue
            token = util.canonical_json(value)
            entry = counts.setdefault(token, {'count': 0, 'first': {}})
            entry['count'] += 1
            entry['first'].setdefault(family, (number, row_id))

    for rule, counts in zip(group_rules, groups):
        for entry in counts.values():
            if entry['count'] != rule['size']:
                for family, first in entry['first'].items():
                    add(family, 'groups', rule['key'], first[0], first[1],
                        'group has %d rows; expected %d' % (entry['count'], rule['size']))
    return result


def iter_rows(filename):
    """Read JSONL once, detecting gzip by suffix or magic bytes."""
    with open(filename, 'rb') as raw:
        compressed = str(filename).endswith('.gz') or raw.peek(2)[:2] == b'\x1f\x8b'
        stream = gzip.GzipFile(fileobj=raw, mode='rb') if compressed else raw
        with io.TextIOWrapper(stream, encoding='utf-8') as handle:
            for number, line in enumerate(handle, 1):
                try:
                    yield json.loads(line)
                except ValueError as err:
                    raise ValueError('row %d: %s' % (number, err))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    commands = parser.add_subparsers(dest='command')
    command = commands.add_parser('check')
    command.add_argument('--rows', required=True)
    command.add_argument('--profile', required=True)
    command.add_argument('--config')
    command.add_argument('--max-print', type=int, default=20)
    command.add_argument('--json', dest='json_out')
    args = parser.parse_args(argv)
    if args.command != 'check':
        parser.error('the check command is required')
    try:
        profile = load_profile(args.profile)
        config = util.read_json(args.config) if args.config else None
        result = check(iter_rows(args.rows), profile, config, args.max_print)
        if args.json_out:
            util.write_json(args.json_out, result)
    except (OSError, ValueError, UnicodeError, EOFError, zlib.error) as err:
        sys.stderr.write('rowschema: unreadable input: %s\n' % err)
        return 2
    for family, summary in sorted(result['families'].items()):
        print('%s: rows=%d violations=%s' %
              (family, summary['rows'], util.canonical_json(summary['violations']).decode('utf-8')))
        for item in summary['examples']:
            print('  row %d id=%s %s %s: %s' %
                  (item['row'], util.canonical_json(item['id']).decode('utf-8'),
                   item['rule'], item['path'], item['message']))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
