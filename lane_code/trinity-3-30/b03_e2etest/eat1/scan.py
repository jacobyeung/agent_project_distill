"""EAT-1 static scanner (A2, A3, A4, A5 static parts).

Scope: the Python files on the path between heads and tokens. In a dynamic run the scope is every
reader file with a line executed during generate() outside the forwards of model modules, and each
finding carries `executed`; only executed findings fail. In static-only mode the caller names the scope
files and every finding in them fails.

Rules
  A3.table_load      a call that loads a table (json/np/pickle/torch/pandas/yaml load functions)
  A3.data_file       a string literal that names a data file (.json .npz .npy .pkl .pt .csv ...)
  A3.constant        a numeric literal outside the reviewed allowlist (allowlist.json)
  A3.unit_conversion an identifier or string naming a unit other than the head's own (feet, inches, cm, mm,
                     square feet, yards, degrees) or a unit-conversion helper (USER ruling 2026-11-16: the model
                     converts units and formats answers in its CoT)
  A3.threshold       a comparison in a branch test against a non-allowlisted number, an UPPER_CASE
                     name, a threshold-like name, or a config/table lookup
  A4.guard           an identifier naming a guard, fallback, refusal, veto, substitution or rejection
  A4.status_literal  a status string ('not seen', 'unavailable', 'refused', 'error: ' ...) outside the
                     reviewed head-status formatters
  A4.except_substitute an except-handler that returns or assigns a substitute value
  A5.cache           an identifier or string naming a precomputed tower/mask/feature/geometry cache
  A2.response_outside_model  response text ('tool_response') produced in code that is not a method of
                     a torch module class
  A2.entry_after_decode      a model entry or prompt build after decoding model output in one function
"""
import ast
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE_LOADERS = {'load', 'loads', 'loadtxt', 'genfromtxt', 'fromfile', 'read_csv', 'read_json', 'read_parquet',
                 'safe_load', 'full_load', 'read_pickle', 'load_file', 'load_npz', 'rows', 'unpack_archive'}
DATA_FILE = re.compile(r'\.(json|jsonl|npz|npy|pkl|pickle|pt|pth|ckpt|csv|tsv|safetensors|bin|h5|hdf5|parquet|'
                       r'yaml|yml|tar|tgz|gz)\b', re.I)
GUARD = re.compile(r'guard|fallback|refus|substitut|veto|reject', re.I)
STATUS = re.compile(r'not seen|unavailable|refus|fallback|no answer|cannot answer|^error: |^error$', re.I)
CACHE = re.compile(r'(mask|tower|feature|geometry|proposal|candidate|frame|sam3?|g3t|depth|pose|head)s?_?cache|'
                   r'cache_?bind|cached_(mask|tower|feature|geometry|proposal|candidate)', re.I)
THRESHOLD_NAME = re.compile(r'thresh|tau|floor|margin|cutoff|_cut\b|^cut_|limit|min_|max_|_min$|_max$|eps', re.I)
UNIT_WORDS = {'feet', 'foot', 'inch', 'inches', 'sqft', 'ft2', 'yard', 'yards', 'degree', 'degrees', 'centimeter',
              'centimeters', 'centimetre', 'centimetres', 'millimeter', 'millimeters', 'millimetre', 'millimetres'}
UNIT_ABBREV = {'ft', 'cm', 'mm', 'deg', 'yd'}  # only as one part of a compound name (dist_ft, to_cm); bare `ft` is common


class _UnitIdent:
    conv = re.compile(r'unit_?conv|convert_?units?', re.I)

    def search(self, ident):
        parts = [p for p in re.split(r'_+', ident.lower()) if p]
        return bool(self.conv.search(ident) or any(p in UNIT_WORDS for p in parts)
                    or (len(parts) > 1 and any(p in UNIT_ABBREV for p in parts)))


UNIT_IDENT = _UnitIdent()
UNIT_TEXT = re.compile(r'\b(feet|foot|inch(es)?|centimet\w*|millimet\w*|sq\.? ?ft|ft2|yards?|degrees?)\b|'
                       r'\d\s?(ft|in|cm|mm)\b|\{[^}]*\}\s?(ft|in|cm|mm|°)|°', re.I)
ENTRY_CALLS = {'generate', 'prefill', 'prompt_batch', 'apply_chat_template', '_prepare_decode', 'chat',
               'teacher_batch', 'build_prompt'}


def load_allowlist(path=None, extra=None):
    data = json.loads(Path(path or HERE/'allowlist.json').read_text())
    for p in extra or ():
        more = json.loads(Path(p).read_text())
        for key in ('numbers', 'threshold_exempt_names'):
            data.setdefault(key, {}).update(more.get(key, {}))
        for key in ('loader_functions', 'head_status_formatters', 'suppress'):
            data[key] = list(data.get(key, []))+list(more.get(key, []))
    data['_values'] = {float(k) for k in data['numbers']}
    return data


def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _number(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float) and not isinstance(node.value, bool):
        return node.value
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Constant) and type(node.operand.value) in (int, float)
            and not isinstance(node.operand.value, bool)):
        return -node.operand.value
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self, path, rel, source, allow):
        self.path, self.rel, self.allow = path, rel, allow
        self.lines = source.splitlines()
        self.findings = []
        self.parents = []
        self.func_stack, self.class_stack = [], []
        self.loader_ok = [e.split('::') for e in allow.get('loader_functions', [])]
        self.status_ok = [e.split('::') for e in allow.get('head_status_formatters', [])]

    # helpers
    def add(self, clause, rule, node, detail):
        line = getattr(node, 'lineno', 0)
        text = self.lines[line-1].strip()[:160] if 0 < line <= len(self.lines) else ''
        self.findings.append(dict(clause=clause, rule=rule, file=str(self.path), rel=self.rel, line=line,
                                  function=self.qualname(), detail=detail, text=text))

    def qualname(self):
        return '.'.join([c for c, _ in self.class_stack]+self.func_stack) or '<module>'

    def allowed(self, entries):
        """Entries are (file suffix, function); the function is the innermost enclosing def."""
        func = self.func_stack[-1] if self.func_stack else '<module>'
        path = str(self.path)
        return any((path.endswith('/'+f) or self.rel == f) and fn == func for f, fn in entries)

    def in_context(self, *types):
        return any(isinstance(p, types) for p in self.parents)

    def generic_visit(self, node):
        self.parents.append(node)
        super().generic_visit(node)
        self.parents.pop()

    def in_module_class(self):
        return any(is_mod for _, is_mod in self.class_stack)

    # structure
    def visit_ClassDef(self, node):
        bases = [ast.unparse(b) for b in node.bases]
        is_mod = any(b.split('.')[-1] in ('Module', 'ModuleDict', 'ModuleList', 'PreTrainedModel') for b in bases)
        if GUARD.search(node.name):
            self.add('A4', 'A4.guard', node, f'class {node.name}')
        if CACHE.search(node.name):
            self.add('A5', 'A5.cache', node, f'class {node.name}')
        self.class_stack.append((node.name, is_mod))
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        if GUARD.search(node.name):
            self.add('A4', 'A4.guard', node, f'def {node.name}')
        if CACHE.search(node.name):
            self.add('A5', 'A5.cache', node, f'def {node.name}')
        if UNIT_IDENT.search(node.name):
            self.add('A3', 'A3.unit_conversion', node, f'def {node.name}')
        self.func_stack.append(node.name)
        self._entry_after_decode(node)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _entry_after_decode(self, fn):
        decode_lines, entries = [], []
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Call):
                n = _name(sub.func)
                if n in ('decode', 'batch_decode'):
                    decode_lines.append(sub.lineno)
                elif n in ENTRY_CALLS:
                    entries.append(sub)
        if decode_lines:
            first = min(decode_lines)
            for call in entries:
                if call.lineno > first:
                    self.add('A2', 'A2.entry_after_decode', call,
                             f'{_name(call.func)}() after decoding output at line {first}')

    # names
    def visit_Name(self, node):
        self._ident(node, node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        self._ident(node, node.attr)
        self.generic_visit(node)

    def visit_keyword(self, node):
        if node.arg:
            self._ident(node, node.arg)
        self.generic_visit(node)

    def visit_arg(self, node):
        self._ident(node, node.arg)
        self.generic_visit(node)

    def _ident(self, node, ident):
        if self.in_context(ast.Raise):
            return
        if GUARD.search(ident):
            self.add('A4', 'A4.guard', node, f'identifier {ident}')
        if CACHE.search(ident):
            self.add('A5', 'A5.cache', node, f'identifier {ident}')
        if UNIT_IDENT.search(ident):
            self.add('A3', 'A3.unit_conversion', node, f'identifier {ident}')

    # calls
    def visit_Call(self, node):
        n = _name(node.func)
        if n in TABLE_LOADERS and not self.allowed(self.loader_ok) and not self.in_context(ast.Raise):
            self.add('A3', 'A3.table_load', node, f'{ast.unparse(node.func)}()')
        self.generic_visit(node)

    # constants
    def visit_Constant(self, node):
        value = node.value
        if isinstance(value, str):
            self._string(node, value)
        elif type(value) in (int, float) and not isinstance(value, bool):
            parent = self.parents[-1] if self.parents else None
            if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.USub):
                value = -value
            self._numeric(node, value)
        self.generic_visit(node)

    def _string(self, node, value):
        if self.in_context(ast.Raise) or self._docstring(node):
            return
        if DATA_FILE.search(value) and len(value) < 300 and not self.allowed(self.loader_ok):
            self.add('A3', 'A3.data_file', node, f'string {value[:80]!r}')
        if STATUS.search(value) and not self.allowed(self.status_ok):
            self.add('A4', 'A4.status_literal', node, f'string {value[:80]!r}')
        if CACHE.search(value):
            self.add('A5', 'A5.cache', node, f'string {value[:80]!r}')
        after_value = bool(self.parents) and isinstance(self.parents[-1], ast.JoinedStr) and re.match(
            r'\s?(ft|in|cm|mm|yd)\b', value)
        if (UNIT_TEXT.search(value) or after_value) and len(value) < 300:
            self.add('A3', 'A3.unit_conversion', node, f'string {value[:80]!r}')
        if 'tool_response' in value and not self.in_module_class():
            self.add('A2', 'A2.response_outside_model', node,
                     'response text built outside a torch module method')

    def _docstring(self, node):
        if len(self.parents) >= 2 and isinstance(self.parents[-1], ast.Expr):
            return True
        return False

    def _exempt(self, node):
        if self.in_context(ast.Raise):
            return True
        kws = set(self.allow['exempt_contexts']['keyword'])
        for i, p in enumerate(self.parents):
            if isinstance(p, ast.Subscript):
                inner = self.parents[i+1] if i+1 < len(self.parents) else node
                if inner is p.slice or inner in ast.walk(p.slice):
                    return True
            if isinstance(p, ast.keyword) and p.arg in kws:
                return True
        parent = self.parents[-1] if self.parents else None
        if isinstance(parent, ast.UnaryOp) and len(self.parents) >= 2:
            parent = self.parents[-2]
        if (isinstance(parent, ast.Call) and _name(parent.func) == 'round' and len(parent.args) == 2
                and (parent.args[1] is node or parent.args[1] is self.parents[-1])):
            return True
        return False

    def _numeric(self, node, value):
        if float(value) in self.allow['_values'] or self._exempt(node):
            return
        self.add('A3', 'A3.constant', node, f'constant {value!r}')

    # branches on thresholds
    def visit_If(self, node):
        # `if <test>: raise ...` refuses the item with an error; it writes no token. Its test is validation.
        if len(node.body) == 1 and isinstance(node.body[0], ast.Raise) and not node.orelse:
            self.parents.append(node)
            self.parents.append(ast.Raise())
            self.visit(node.test)
            self.parents.pop()
            for stmt in node.body:
                self.visit(stmt)
            self.parents.pop()
            return
        self.generic_visit(node)

    def visit_Compare(self, node):
        ordering = any(isinstance(o, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for o in node.ops)
        if not self.in_context(ast.Raise) and ordering:
            for operand in [node.left]+list(node.comparators):
                why = self._threshold_operand(operand)
                if why:
                    self.add('A3', 'A3.threshold', node, why)
                    break
        self.generic_visit(node)

    def _threshold_operand(self, op, ordering=True):
        v = _number(op)
        if v is not None:
            return None if float(v) in self.allow['_values'] else f'compares against {v!r}'
        n = _name(op)
        if n in self.allow.get('threshold_exempt_names', {}):
            return None
        if n and (n.isupper() and len(n) > 1 or THRESHOLD_NAME.search(n)) and not n.startswith('__'):
            return f'compares against {n}'
        if isinstance(op, ast.Subscript) and isinstance(op.slice, ast.Constant) and isinstance(op.slice.value, str):
            return f'compares against table entry {ast.unparse(op)[:60]}'
        if (isinstance(op, ast.Call) and _name(op.func) == 'get' and op.args
                and isinstance(op.args[0], ast.Constant) and isinstance(op.args[0].value, str)):
            return f'compares against table entry {ast.unparse(op)[:60]}'
        return None

    # substitutes on failure
    def visit_ExceptHandler(self, node):
        for stmt in node.body:
            empty = (isinstance(stmt.value, ast.Constant) and stmt.value.value in (None, '')) or (
                isinstance(stmt.value, (ast.List, ast.Tuple, ast.Dict)) and not getattr(
                    stmt.value, 'elts', getattr(stmt.value, 'keys', [1]))) if isinstance(stmt, ast.Return) else False
            if isinstance(stmt, ast.Return) and stmt.value is not None and not empty:
                self.add('A4', 'A4.except_substitute', stmt, 'except-handler returns a substitute')
                break
        self.generic_visit(node)


def scan_file(path, allow, root=None):
    path = Path(path)
    rel = str(path.relative_to(root)) if root and path.is_relative_to(root) else path.name
    source = path.read_text(errors='replace')
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [dict(clause='A3', rule='A3.unparsed', file=str(path), rel=rel, line=exc.lineno or 0,
                     function='', detail='file does not parse', text='')]
    v = _Visitor(path, rel, source, allow)
    v.visit(tree)
    return v.findings


def scan(files, allow=None, root=None, executed=None):
    """files: iterable of paths. executed: {abs path: set(lines)} or None (static-only).
    Returns (findings, suppressed). Findings in a dynamic run carry `executed`."""
    allow = allow or load_allowlist()
    supp = [s for s in allow.get('suppress', []) if isinstance(s, dict)]
    findings, suppressed, seen = [], [], set()
    for f in sorted({str(Path(p).resolve()) for p in files}):
        for item in scan_file(f, allow, root):
            key = (item['rule'], item['file'], item['line'], item['detail'])
            if key in seen:
                continue
            seen.add(key)
            if executed is not None:
                item['executed'] = item['line'] in executed.get(item['file'], ())
            hit = [x for x in supp if x['rule'] == item['rule'] and int(x['line']) == item['line']
                   and (item['file'].endswith('/'+x['file']) or item['rel'] == x['file'])]
            if hit:
                item['suppressed_reason'] = hit[0].get('reason', '')
                suppressed.append(item)
            else:
                findings.append(item)
    return findings, suppressed


def failing(findings, dynamic):
    return [f for f in findings if (f.get('executed') if dynamic else True)]


def main():
    import argparse
    ap = argparse.ArgumentParser(description='EAT-1 static scan of named call-path files')
    ap.add_argument('files', nargs='+')
    ap.add_argument('--root')
    ap.add_argument('--allowlist')
    ap.add_argument('--allowlist-extra', action='append')
    ap.add_argument('--json')
    a = ap.parse_args()
    files = []
    for f in a.files:
        p = Path(f)
        files += sorted(p.rglob('*.py')) if p.is_dir() else [p]
    findings, suppressed = scan(files, load_allowlist(a.allowlist, a.allowlist_extra),
                                root=Path(a.root).resolve() if a.root else None)
    if a.json:
        Path(a.json).write_text(json.dumps(dict(findings=findings, suppressed=suppressed), indent=1)+'\n')
    by = {}
    for f in findings:
        by[f['rule']] = by.get(f['rule'], 0)+1
    print(json.dumps(dict(files=len(files), findings=len(findings), by_rule=by), indent=1))


if __name__ == '__main__':
    main()
