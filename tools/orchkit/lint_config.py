"""Lint a kit configuration before it leaves for the batch host.

CLI: python lint_config.py CONFIG.json [--schema FAMILY.schema.json] [--pins PINS.json]
                          [--opacity-words FILE] [--code FILE.py ...] [--json OUT.json]
Prints one line per finding, "<rule> <json.path>: <message>", and exits 1 on any finding, 0 when
clean and 2 when an input cannot be read. dryrun.py imports lint(config, schema, pins).

Rules:
  schema     a JSON-schema subset (type, required, enum, pattern, properties, additionalProperties,
             items, minimum); runs only with --schema, so older configs still lint.
  prose      strings under digest, path, inventory, URI and pin keys must be identifiers, never prose;
             the field rules of the earlier sealed-config auditor (generation, md5, crc32c, sha256,
             members) apply wherever those keys appear.
  budget     every byte budget carries a per-item figure that covers n_items; the time budget fits
             job.time_limit_s. Runs only when the config has "budgets".
  host_path  no lane path, home or data mount, cluster host name or opacity word in any string.
  pins       with --pins: kit_pins_sha256 identifies the pins manifest and every record is pinned.
  cap_default with --code: numeric cap literals in argument defaults or module assignments.
"""
import argparse
import ast
import base64
import binascii
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from . import util
except ImportError:
    import util

PROSE_KEY = re.compile(r'sha|digest|members|inventory|path|uri|object|generation|pin', re.I)
INVENTORY_KEY = re.compile(r'members|inventory', re.I)
HEX64 = re.compile(r'[0-9a-f]{64}\Z', re.I)
DECIMAL = re.compile(r'[0-9]+\Z')
GS_URI = re.compile(r'gs://[a-z0-9][a-z0-9._-]*/\S+\Z')
PLUS_WORD = re.compile(r'\bplus\b', re.I)
HOST_RE = re.compile(r'\btrinity(-[0-9]+-[0-9]+)?\b', re.I)
DATA_RE = re.compile(r'(?:^|[\s"\'=:,;(\[{])/data[0-9]*/')
HOST_SUBSTRINGS = ('/scratch/jjyeung/', '/home/', '.vision.cs.cmu.edu')
UNSUPPORTED = ('anyOf', 'oneOf', 'allOf', 'not', '$ref', 'maximum', 'exclusiveMinimum',
               'exclusiveMaximum', 'minLength', 'maxLength', 'minItems', 'maxItems', 'uniqueItems',
               'const', 'patternProperties', 'dependencies', 'if', 'propertyNames')


def finding(rule, path, message):
    return {'rule': rule, 'path': path or '$', 'message': message}


def child_path(path, key):
    if isinstance(key, int):
        return '%s[%d]' % (path, key)
    return '%s.%s' % (path, key) if path else str(key)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def same(a, b):
    """JSON equality that keeps booleans apart from numbers."""
    if is_number(a) and is_number(b):
        return a == b
    try:
        return util.canonical_json(a) == util.canonical_json(b)
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------- schema

TYPE_TESTS = {
    'string': lambda v: isinstance(v, str),
    'integer': is_int,
    'number': is_number,
    'boolean': lambda v: isinstance(v, bool),
    'object': lambda v: isinstance(v, dict),
    'array': lambda v: isinstance(v, list),
    'null': lambda v: v is None,
}


def check_schema(value, schema, path='', out=None):
    out = [] if out is None else out
    if schema is True or schema == {}:
        return out
    if schema is False:
        out.append(finding('schema', path, 'no value is allowed here'))
        return out
    if not isinstance(schema, dict):
        out.append(finding('schema', path, 'schema node is not an object'))
        return out
    for key in UNSUPPORTED:
        if key in schema:
            out.append(finding('schema', path, 'schema keyword %s is not supported by the lint' % key))
    if 'type' in schema:
        types = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        unknown = [t for t in types if t not in TYPE_TESTS]
        if unknown:
            out.append(finding('schema', path, 'unsupported type %r' % unknown))
            return out
        if not any(TYPE_TESTS[t](value) for t in types):
            out.append(finding('schema', path, 'expected type %s, got %s'
                               % ('|'.join(types), type(value).__name__)))
            return out
    if 'enum' in schema and not any(same(value, option) for option in schema['enum']):
        out.append(finding('schema', path, 'value %s is not one of %s'
                           % (util.canonical_json(value).decode('utf-8'),
                              util.canonical_json(schema['enum']).decode('utf-8'))))
    if 'pattern' in schema and isinstance(value, str) and not re.search(schema['pattern'], value):
        out.append(finding('schema', path, 'value does not match pattern %s' % schema['pattern']))
    if 'minimum' in schema and is_number(value) and value < schema['minimum']:
        out.append(finding('schema', path, 'value %r is below minimum %r' % (value, schema['minimum'])))
    if isinstance(value, dict):
        props = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in value:
                out.append(finding('schema', path, 'required key %s is missing' % key))
        for key in sorted(value):
            if key in props:
                check_schema(value[key], props[key], child_path(path, key), out)
            elif 'additionalProperties' in schema:
                extra = schema['additionalProperties']
                if extra is False:
                    out.append(finding('schema', child_path(path, key),
                                       'key is not allowed (additionalProperties false)'))
                elif isinstance(extra, dict):
                    check_schema(value[key], extra, child_path(path, key), out)
    if isinstance(value, list) and 'items' in schema:
        items = schema['items']
        for i, item in enumerate(value):
            if isinstance(items, list):
                if i < len(items):
                    check_schema(item, items[i], child_path(path, i), out)
            else:
                check_schema(item, items, child_path(path, i), out)
    return out


# ---------------------------------------------------------------- prose

def clean_path(text):
    if not text or any(c.isspace() for c in text):
        return False
    if '//' in text or '<' in text or '>' in text:
        return False
    return '..' not in text.split('/')


def prose_problem(text):
    """Return why a string under an identifier key reads as prose, or None."""
    if any(c.isspace() for c in text) or '<' in text or '>' in text or '...' in text:
        return 'holds whitespace, angle brackets or an ellipsis'
    if 'TODO' in text or PLUS_WORD.search(text):
        return 'holds TODO or the word plus'
    if HEX64.match(text) or DECIMAL.match(text) or GS_URI.match(text) or clean_path(text):
        return None
    return 'is not a digest, clean path, gs:// URI or decimal integer'


def field_rule(key, value):
    """Field rules of the earlier sealed-config auditor. Returns (applies, problem)."""
    key = key.lower()
    if key == 'generation':
        ok = (is_int(value) and value > 0) or (isinstance(value, str) and DECIMAL.match(value)
                                               and int(value) > 0)
        return True, None if ok else 'generation must be a positive integer or digit string'
    if key in ('md5', 'crc32c'):
        want = 16 if key == 'md5' else 4
        try:
            ok = isinstance(value, str) and len(base64.b64decode(value, validate=True)) == want
        except (binascii.Error, ValueError, TypeError):
            ok = False
        return True, None if ok else '%s must be base64 of %d bytes' % (key, want)
    if key in ('sha256', 'digest') or key.endswith('_sha256') or key.endswith('_digest'):
        ok = isinstance(value, str) and bool(HEX64.match(value))
        return True, None if ok else 'must be a 64-hex sha256'
    return False, None


def is_members_key(key):
    key = key.lower()
    return key == 'members' or key.endswith('_members')


def check_members(members, path, out):
    for name in sorted(members):
        row = members[name]
        if not clean_path(name) or name.startswith('/') or prose_problem(name):
            out.append(finding('prose', path, 'member key %r is not a relative clean path' % name))
        if isinstance(row, str):
            if not HEX64.match(row):
                out.append(finding('prose', child_path(path, name), 'member must be a 64-hex sha256'))
        elif isinstance(row, dict):
            if set(row) != {'bytes', 'sha256'}:
                out.append(finding('prose', child_path(path, name),
                                   'member record must hold exactly bytes and sha256'))
            if 'bytes' in row and not (is_int(row['bytes']) and row['bytes'] >= 0):
                out.append(finding('prose', child_path(child_path(path, name), 'bytes'),
                                   'bytes must be a nonnegative integer'))
        else:
            out.append(finding('prose', child_path(path, name),
                               'member must be a sha256 string or {bytes, sha256}'))


def check_prose(value, path='', under=False, out=None, inventory=False):
    out = [] if out is None else out
    if isinstance(value, dict):
        for key in sorted(value):
            sub = value[key]
            here = child_path(path, key)
            if inventory and prose_problem(key):
                out.append(finding('prose', here, 'inventory key ' + prose_problem(key)))
            applies, problem = field_rule(key, sub)
            if applies:
                if problem:
                    out.append(finding('prose', here, problem))
            if INVENTORY_KEY.search(key):
                if not isinstance(sub, (dict, list)):
                    out.append(finding('prose', here, 'an inventory must be an object or list of '
                                       'identifiers, not %s %s' % (
                                           type(sub).__name__,
                                           util.canonical_json(sub).decode('utf-8')[:120])))
                    continue
                if isinstance(sub, dict):
                    for name in sorted(sub):
                        why = prose_problem(name)
                        if why:
                            out.append(finding('prose', here, 'key %r %s' % (name, why)))
                    if is_members_key(key):
                        check_members(sub, here, out)
            check_prose(sub, here, under or bool(PROSE_KEY.search(key)), out,
                        inventory or bool(INVENTORY_KEY.search(key)))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            check_prose(item, child_path(path, i), under, out, inventory)
    elif isinstance(value, str) and under:
        why = prose_problem(value)
        if why:
            out.append(finding('prose', path, 'value %r %s' % (value[:120], why)))
    return out


# ---------------------------------------------------------------- budget

def check_budget(config):
    out = []
    if not isinstance(config, dict) or 'budgets' not in config:
        return out
    budgets = config['budgets']
    if not isinstance(budgets, dict):
        return [finding('budget', 'budgets', 'budgets must be an object')]
    n_items = config.get('n_items')
    if not (is_int(n_items) and n_items >= 0):
        return [finding('budget', 'n_items', 'budgets need a nonnegative integer n_items to scale by')]
    for name in sorted(budgets):
        entry = budgets[name]
        path = child_path('budgets', name)
        if not isinstance(entry, dict):
            out.append(finding('budget', path, 'budget must be an object'))
            continue
        if name == 'time':
            per = entry.get('per_item_s')
            fixed = entry.get('fixed_s', 0)
            limit = (config.get('job') or {}).get('time_limit_s') \
                if isinstance(config.get('job'), dict) else None
            if not (is_number(per) and per >= 0):
                out.append(finding('budget', path, 'time budget needs nonnegative per_item_s'))
            elif not is_number(fixed) or fixed < 0:
                out.append(finding('budget', path, 'fixed_s must be a nonnegative number'))
            elif not is_number(limit):
                out.append(finding('budget', 'job.time_limit_s',
                                   'time budget cannot be checked without job.time_limit_s'))
            elif limit < n_items * per + fixed:
                out.append(finding('budget', path, 'job.time_limit_s %r < n_items %d * per_item_s %r '
                                   '+ fixed_s %r = %r' % (limit, n_items, per, fixed,
                                                          n_items * per + fixed)))
            continue
        per = entry.get('per_item_bytes')
        cap = entry.get('max_bytes')
        if not (is_int(per) and per > 0):
            out.append(finding('budget', path, 'budget has no positive integer per_item_bytes; a '
                               'constant default under-reserves a run that scales with n_items'))
        elif not is_int(cap):
            out.append(finding('budget', path, 'max_bytes must be an integer'))
        elif cap < n_items * per:
            out.append(finding('budget', path, 'max_bytes %d < n_items %d * per_item_bytes %d = %d'
                               % (cap, n_items, per, n_items * per)))
    return out


# ---------------------------------------------------------------- host_path

def host_problem(text, opacity_words):
    for marker in HOST_SUBSTRINGS:
        if marker in text:
            return 'holds %s' % marker
    if DATA_RE.search(text):
        return 'holds a /data mount path'
    if HOST_RE.search(text):
        return 'holds a cluster host name'
    low = text.lower()
    for word in opacity_words or ():
        if word and word.lower() in low:
            return 'holds an opacity word'
    return None


def check_host_path(value, opacity_words=None, path='', out=None):
    out = [] if out is None else out
    if isinstance(value, dict):
        for key in sorted(value):
            why = host_problem(key, opacity_words)
            if why:
                out.append(finding('host_path', child_path(path, key), 'key ' + why))
            check_host_path(value[key], opacity_words, child_path(path, key), out)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            check_host_path(item, opacity_words, child_path(path, i), out)
    elif isinstance(value, str):
        why = host_problem(value, opacity_words)
        if why:
            out.append(finding('host_path', path, 'value ' + why))
    return out


# ---------------------------------------------------------------- pins

def check_pins(config, manifest):
    out = []
    if not isinstance(manifest, dict) or manifest.get('schema') != 'orchkit-pins-v1':
        return [finding('pins', '$', 'pins manifest schema is not orchkit-pins-v1')]
    config = config if isinstance(config, dict) else {}
    want = util.canonical_sha256(manifest)
    if config.get('kit_pins_sha256') != want:
        out.append(finding('pins', 'kit_pins_sha256', 'does not equal the pins manifest identity %s'
                           % want))
    entries = manifest.get('entries')
    if not isinstance(entries, list) or not all(
            isinstance(e, dict) and isinstance(e.get('logical_path'), str) for e in entries):
        return out + [finding('pins', '$', 'pins entries must be objects with a logical_path')]
    paths = [e['logical_path'] for e in entries]
    if paths != sorted(paths):
        out.append(finding('pins', '$', 'pins entries are not sorted by logical_path'))
    if len(set(paths)) != len(paths):
        out.append(finding('pins', '$', 'pins entries repeat a logical_path'))
    index = dict((e['logical_path'], e) for e in entries)
    records = config.get('records', [])
    if not isinstance(records, list):
        return out + [finding('pins', 'records', 'records must be a list')]
    for i, rec in enumerate(records):
        path = child_path('records', i)
        if not isinstance(rec, dict):
            out.append(finding('pins', path, 'record must be an object'))
            continue
        logical_path = rec.get('logical_path')
        entry = index.get(logical_path) if isinstance(logical_path, str) else None
        if entry is None:
            out.append(finding('pins', path, 'logical_path %r is not pinned' % rec.get('logical_path')))
        elif entry.get('role') != 'record':
            out.append(finding('pins', path, 'pinned entry has role %r, not record' % entry.get('role')))
        elif not isinstance(rec.get('sha256'), str) or not HEX64.match(rec['sha256']) or \
                entry.get('sha256') != rec.get('sha256'):
            out.append(finding('pins', path, 'sha256 differs from the pinned entry'))
    return out


# ---------------------------------------------------------------- entry points

CAP_NAME = re.compile(r'max|cap|limit|budget|bytes|timeout|quota', re.I)


def hardcoded_caps(py_source_text, filename):
    """Find numeric cap literals in argument defaults and module assignments.

    This is an AST-only check: it never imports or executes the supplied code.
    SyntaxError propagates so callers can distinguish unreadable code from findings.
    """
    tree = ast.parse(py_source_text, filename=filename)
    out = []

    def numeric(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
                ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitAnd, ast.BitXor)):
            return numeric(node.left) and numeric(node.right)
        try:
            return is_number(ast.literal_eval(node))
        except (ValueError, TypeError, SyntaxError):
            return False

    def string(node):
        try:
            value = ast.literal_eval(node)
        except (ValueError, TypeError, SyntaxError):
            return None
        return value if isinstance(value, str) else None

    def report(node, name):
        out.append(finding('cap_default', '%s:%d' % (filename, node.lineno),
                           '%s has a numeric cap default' % name))

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = 0

        def visit_Call(self, node):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', '')
            if name == 'add_argument':
                names = [string(arg) for arg in node.args]
                names += [string(kw.value) for kw in node.keywords if kw.arg == 'dest']
                matches = [name for name in names if name is not None and CAP_NAME.search(name)]
                if matches and any(kw.arg == 'default' and numeric(kw.value)
                                   for kw in node.keywords):
                    report(node, matches[0])
            self.generic_visit(node)

        def visit_Assign(self, node):
            def binding(target, value):
                if isinstance(target, ast.Name) and CAP_NAME.search(target.id) and numeric(value):
                    report(node, target.id)
                elif isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
                    for left, right in zip(target.elts, value.elts):
                        binding(left, right)
            if self.scope == 0:
                for target in node.targets:
                    binding(target, node.value)
            self.generic_visit(node)

        def visit_AnnAssign(self, node):
            if self.scope == 0 and isinstance(node.target, ast.Name) and \
                    CAP_NAME.search(node.target.id) and numeric(node.value):
                report(node, node.target.id)
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            args = node.args
            positional = getattr(args, 'posonlyargs', []) + args.args
            defaults = list(zip(positional[len(positional) - len(args.defaults):], args.defaults))
            defaults += list(zip(args.kwonlyargs, args.kw_defaults))
            for arg, default in defaults:
                if CAP_NAME.search(arg.arg) and numeric(default):
                    report(node, arg.arg)
            self.scope += 1
            self.generic_visit(node)
            self.scope -= 1

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_Lambda = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.scope += 1
            self.generic_visit(node)
            self.scope -= 1

    Visitor().visit(tree)
    return out

def lint(config, schema=None, pins=None, opacity_words=None):
    """Return every finding as a list of {'rule', 'path', 'message'}."""
    out = []
    if schema is not None:
        out.extend(check_schema(config, schema))
    out.extend(check_prose(config))
    out.extend(check_budget(config))
    out.extend(check_host_path(config, opacity_words))
    if pins is not None:
        out.extend(check_pins(config, pins))
    return out


def read_words(path):
    with open(path, 'rb') as handle:
        lines = handle.read().decode('utf-8').splitlines()
    return [line.strip() for line in lines if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('config')
    parser.add_argument('--schema')
    parser.add_argument('--pins')
    parser.add_argument('--opacity-words')
    parser.add_argument('--code', action='append', default=[])
    parser.add_argument('--json', dest='json_out')
    args = parser.parse_args(argv)
    try:
        config = util.read_json(args.config)
        schema = util.read_json(args.schema) if args.schema else None
        pins = util.read_json(args.pins) if args.pins else None
        words = read_words(args.opacity_words) if args.opacity_words else None
        code_findings = []
        for filename in args.code:
            with open(filename, encoding='utf-8') as handle:
                code_findings.extend(hardcoded_caps(handle.read(), filename))
    except (IOError, OSError, ValueError, UnicodeDecodeError, SyntaxError) as err:
        sys.stderr.write('lint_config: unreadable input: %s\n' % err)
        return 2
    findings = lint(config, schema, pins, words) + code_findings
    for item in findings:
        sys.stdout.write('%s %s: %s\n' % (item['rule'], item['path'], item['message']))
    sys.stderr.write('lint_config: %d finding(s)\n' % len(findings))
    if args.json_out:
        util.write_json(args.json_out, {'schema': 'orchkit-lint-v1', 'ok': not findings,
                                        'findings': findings})
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
