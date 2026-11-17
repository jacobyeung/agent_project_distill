"""EAT-1 static scanner (A2, A3, A4, A5 static parts).

Scope: the Python files on the path between heads and tokens. In a dynamic run the scope is every
reader file with a line executed during generate() outside the forwards of model modules, and each
finding carries `executed`; only executed findings fail. In static-only mode the caller names the scope
files and every finding in them fails.

Rules
  A3.table_load      a call that loads a table (json/np/pickle/torch/pandas/yaml load functions)
  A3.data_file       a string literal that names a data file (.json .npz .npy .pkl .pt .csv ...)
  A3.constant        a numeric literal outside the reviewed allowlist (allowlist.json), a constant-only
                     expression whose value is outside it (`(2+3)**2`), or a multiplicative or additive chain whose
                     combined constant factor or offset is outside it (`x*4*25`); integer shape arguments of
                     reshape/view/permute-like calls are exempt; `declared_constants` lists reviewed model constants
  A3.reformat        a precision choice outside the model: round(), .round(), format specs (`{x:.2f}`, `%.2f`,
                     format(x, '.2f')); USER 2026-11-16: number formatting is done by the model in its CoT
  A3.unit_conversion an identifier or string naming a unit other than the head's own (feet, inches, cm, mm,
                     square feet, yards, degrees) or a unit-conversion helper (USER ruling 2026-11-16: the model
                     converts units and formats answers in its CoT)
  A3.threshold       an ordering comparison against a number outside `threshold_numbers` (0, 1, -1), an
                     UPPER_CASE name, a threshold-like name, an attribute (`self.settings.edge`), or a config/table
                     lookup; and any comparison or clamp API (torch.gt, np.less, clamp, clip, threshold, ...)
  A3.selection       max/min/sort/argmax-like calls or comparisons of two computed values; judged (run.py) only on
                     lines executed inside a registered call handler's forward
  (run.py adds A3.response_value, A3.module_data and config-role A3.table_load from the dynamic run)
  A4.guard           an identifier naming a guard, fallback, refusal, veto, substitution or rejection
  A4.status_literal  a status string ('not seen', 'unavailable', 'refused', 'error: ' ...) outside the
                     reviewed head-status formatters
  A4.except_substitute an except-handler that does not end by raising (a return, an assignment, an empty
                     return or `pass` all let a substitute flow on)
  A4.or_fallback     `x or <literal holding a number>`: a literal substitutes a falsy result
  A5.cache           an identifier or string naming a precomputed tower/mask/feature/geometry cache
  A2.response_outside_model  response text ('tool_response') produced in code that is not a method of
                     a torch module class
  A2.entry_after_decode      a model entry or prompt build after decoding model output in one function
"""
import ast
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE_LOADERS = {'load', 'loads', 'loadtxt', 'genfromtxt', 'fromfile', 'read_csv', 'read_json', 'read_parquet',
                 'safe_load', 'full_load', 'read_pickle', 'load_file', 'load_npz', 'rows', 'unpack_archive',
                 'read_text', 'read_bytes', 'literal_eval', 'frombuffer', 'fromstring', 'memmap', 'JSONDecoder',
                 'raw_decode', 'Unpickler', 'unpackb', 'eval', 'exec'}
COMPARE_CALLS = {'gt', 'lt', 'ge', 'le', 'greater', 'less', 'greater_equal', 'less_equal', 'clamp', 'clamp_',
                 'clamp_min', 'clamp_max', 'clip', 'clip_', 'threshold', 'heaviside', 'searchsorted', 'bucketize',
                 'digitize'}
SHAPE_CALLS = {'reshape', 'view', 'permute', 'transpose', 'unsqueeze', 'squeeze', 'flatten', 'unflatten', 'expand',
               'movedim', 'swapaxes', 'chunk', 'split', 'narrow', 'select', 'zeros', 'ones', 'empty', 'new_zeros',
               'new_ones', 'new_empty', 'arange', 'eye', 'size', 'repeat', 'tile'}
ROUND_CALLS = {'round', 'around', 'round_'}
# value-dependent selection; judged only on lines executed inside a registered call handler's forward
HEADISH = re.compile(r'(?i)(head|tower)')
SELECT_CALLS = {'max', 'min', 'sorted', 'argmax', 'argmin', 'topk', 'sort', 'argsort', 'amax', 'amin', 'maximum',
                'minimum', 'fmax', 'fmin', 'median', 'nanmax', 'nanmin', 'kthvalue', 'mode', 'nanargmax', 'nanargmin'}
LOG_CALLS = {'debug', 'info', 'warning', 'warn', 'error', 'exception', 'print', 'log', 'critical'}
UNIT_NORMAL = [(re.compile(r'^(sq\.? ?ft|ft2|sqft)$', re.I), 'ft2'), (re.compile(r'^(feet|foot|ft)$', re.I), 'ft'),
               (re.compile(r'^(inch(es)?|in)$', re.I), 'in'), (re.compile(r'^(centimet\w*|cm)$', re.I), 'cm'),
               (re.compile(r'^(millimet\w*|mm)$', re.I), 'mm'), (re.compile(r'^(yards?|yd)$', re.I), 'yd'),
               (re.compile(r'^(degrees?|deg|°)$', re.I), 'deg')]
UNIT_TOKEN = re.compile(r'sq\.? ?ft|ft2|sqft|feet|foot|inch(?:es)?|centimet\w*|millimet\w*|yards?|degrees?|°|'
                        r'(?<=\d)\s?(?:ft|in|cm|mm)\b|(?<=\})\s?(?:ft|in|cm|mm)\b|^\s?(?:ft|in|cm|mm|yd)\b', re.I)


def unit_names(text):
    out = set()
    for m in UNIT_TOKEN.finditer(text):
        tok = m.group(0).strip()
        out.add(next((n for rx, n in UNIT_NORMAL if rx.match(tok)), tok.lower()))
    return out
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
        for key in ('numbers', 'threshold_exempt_names', 'native_units'):
            data.setdefault(key, {}).update(more.get(key, {}))
        for key in ('loader_functions', 'head_status_formatters', 'suppress', 'declared_constants'):
            data[key] = list(data.get(key, []))+list(more.get(key, []))
    data['_values'] = {float(k) for k in data['numbers']}
    data['_threshold_values'] = {float(k) for k in data.get('threshold_numbers', ['0', '1', '-1'])}
    data['_native_units'] = set(data.get('native_units', {}))
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
        self.func_stack, self.class_stack, self.const_stack, self.valued_stack = [], [], [], []
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

    def declared(self, value):
        """A reviewed model constant: allowlist `declared_constants` entry {file, function, value, reason}."""
        path, func = str(self.path), self.qualname()
        return any((path.endswith('/'+d['file']) or self.rel == d['file']) and d.get('function') == func
                   and abs(float(d['value'])-float(value)) <= 1e-12*max(1., abs(float(value)))
                   for d in self.allow.get('declared_constants', []))

    def ok_value(self, value):
        v = float(value)
        return any(abs(v-a) <= 1e-9*max(1., abs(a)) for a in self.allow['_values']) or self.declared(value)

    # constant folding (constant-only expressions, and names bound once to one in the same function)
    def fold(self, node):
        v = _number(node)
        if v is not None:
            return float(v)
        if isinstance(node, ast.Name) and self.const_stack and node.id in self.const_stack[-1]:
            return self.const_stack[-1][node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = self.fold(node.operand)
            return None if v is None else (-v if isinstance(node.op, ast.USub) else v)
        if isinstance(node, ast.BinOp):
            a, b = self.fold(node.left), self.fold(node.right)
            if a is None or b is None:
                return None
            try:
                return float({ast.Add: lambda: a+b, ast.Sub: lambda: a-b, ast.Mult: lambda: a*b,
                              ast.Div: lambda: a/b, ast.FloorDiv: lambda: a//b, ast.Mod: lambda: a % b,
                              ast.Pow: lambda: a**b}[type(node.op)]())
            except (KeyError, ZeroDivisionError, OverflowError, TypeError, ValueError):
                return None
        return None

    def _chain(self, node, ops, inv=False):
        """Flatten a Mult/Div (or Add/Sub) chain -> list of (leaf, inverted)."""
        if isinstance(node, ast.BinOp) and type(node.op) in ops and self.fold(node) is None:
            first, second = ops
            right_inv = (not inv) if isinstance(node.op, second) else inv
            return self._chain(node.left, ops, inv)+self._chain(node.right, ops, right_inv)
        return [(node, inv)]

    def visit_BinOp(self, node):
        parent = self.parents[-1] if self.parents else None
        exempt = self._exempt(node)
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) \
                and re.search(r'%[-+ #0]*\d*(\.\d*)?[fgeFGEd]', node.left.value) and not self.allow.get('format_precision'):
            self.add('A3', 'A3.reformat', node, 'printf-style precision outside the model')
        folded = self.fold(node)
        top_fold = not (isinstance(parent, (ast.BinOp, ast.UnaryOp)) and self.fold(parent) is not None)
        if folded is not None:
            if top_fold and not exempt and not self.ok_value(folded):
                self.add('A3', 'A3.constant', node, f'constant expression {ast.unparse(node)[:40]} = {folded!r}')
        else:
            for ops, kind in (((ast.Mult, ast.Div), 'factor'), ((ast.Add, ast.Sub), 'offset')):
                if type(node.op) not in ops or (isinstance(parent, ast.BinOp) and type(parent.op) in ops
                                                and self.fold(parent) is None):
                    continue
                leaves = self._chain(node, ops)
                consts = [(self.fold(n), inv) for n, inv in leaves if self.fold(n) is not None]
                compound = any(not isinstance(n, ast.Constant) and self.fold(n) is not None for n, _ in leaves)
                if len(consts) < 2 and not compound:
                    continue
                total = 1. if kind == 'factor' else 0.
                try:
                    for v, inv in consts:
                        total = (total/v if inv else total*v) if kind == 'factor' else (total-v if inv else total+v)
                except ZeroDivisionError:
                    continue
                if not exempt and not self.ok_value(total):
                    self.add('A3', 'A3.constant', node, f'combined constant {kind} {total!r} in {ast.unparse(node)[:60]}')
        self.generic_visit(node)

    def visit_FormattedValue(self, node):
        if node.format_spec is not None and not self.allow.get('format_precision'):
            spec = ''.join(str(c.value) for c in ast.walk(node.format_spec) if isinstance(c, ast.Constant))
            if re.search(r'\.\d|[eEfFgG%]', spec):
                self.add('A3', 'A3.reformat', node, f'format spec {spec[:30]} outside the model')
        self.generic_visit(node)

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
        if UNIT_IDENT.search(node.name) and not self._native_ident(node.name):
            self.add('A3', 'A3.unit_conversion', node, f'def {node.name}')
        self.func_stack.append(node.name)
        self.const_stack.append(self._constants(node))
        self.valued_stack.append(self._head_valued(node))
        self._entry_after_decode(node)
        self.generic_visit(node)
        self.valued_stack.pop()
        self.const_stack.pop()
        self.func_stack.pop()

    def _head_valued(self, fn):
        """Local names that hold a head's output: assigned from float()/.item()/.tolist() or from a call on an
        attribute naming a head, tower or model, or from an expression over such names."""
        names = set()
        for st in ast.walk(fn):
            if isinstance(st, ast.Assign) and self._valued(st.value, names):
                names |= {t.id for t in st.targets if isinstance(t, ast.Name)}
        return names

    @staticmethod
    def _valued(expr, names):
        for c in ast.walk(expr):
            if isinstance(c, ast.Name) and c.id in names:
                return True
            if isinstance(c, ast.Call):
                f = ast.unparse(c.func)
                if _name(c.func) in ('float', 'item', 'tolist') or HEADISH.search(f):
                    return True
        return False

    def _constants(self, fn):
        counts, values = Counter(), {}
        for sub in ast.walk(fn):
            targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target] if isinstance(
                sub, (ast.AugAssign, ast.AnnAssign, ast.For, ast.NamedExpr)) else []
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        counts[n.id] += 1
                        if isinstance(sub, ast.Assign) and t is n and len(sub.targets) == 1:
                            values[n.id] = sub.value
        self.const_stack.append({})
        out = {}
        for name, value in values.items():
            if counts[name] == 1:
                v = self.fold(value)
                if v is not None:
                    out[name] = v
        self.const_stack.pop()
        return out

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
        if UNIT_IDENT.search(ident) and not self._native_ident(ident):
            self.add('A3', 'A3.unit_conversion', node, f'identifier {ident}')

    def _native_ident(self, ident):
        parts = [p for p in re.split(r'_+', ident.lower()) if p]
        units = {next((n for rx, n in UNIT_NORMAL if rx.match(p)), None) for p in parts} - {None}
        return bool(units) and units <= self.allow['_native_units'] and not UNIT_IDENT.conv.search(ident)

    # calls
    def visit_Call(self, node):
        n = _name(node.func)
        if n in TABLE_LOADERS and not self.allowed(self.loader_ok) and not self.in_context(ast.Raise):
            self.add('A3', 'A3.table_load', node, f'{ast.unparse(node.func)}()')
        if not self.in_context(ast.Raise):
            bounds = [a for a in node.args[1:]]+[k.value for k in node.keywords if k.arg in ('min', 'max', 'other')]
            relu_like = n in ('clamp', 'clamp_', 'clamp_min', 'clip', 'clip_') and bounds and all(
                self.fold(b) is not None and (self.fold(b) in self.allow['_threshold_values'] or self.declared(self.fold(b)))
                for b in bounds)
            parent = self.parents[-1] if self.parents else None
            # sorted() without a key, consumed whole as the iterable of a loop, only reorders (serialization)
            in_order = (n == 'sorted' and not node.keywords and isinstance(parent, (ast.comprehension, ast.For))
                        and parent.iter is node)
            if n in SELECT_CALLS and self.allow.get('_selection') and not in_order:
                self.add('A3', 'A3.selection', node, f'{ast.unparse(node.func)[:40]}() selects among values')
            if n in COMPARE_CALLS and not relu_like:
                self.add('A3', 'A3.threshold', node, f'comparison or clamp API {ast.unparse(node.func)[:40]}()')
            if not self.allow.get('format_precision'):
                spec = node.args[1] if n == 'format' and len(node.args) > 1 else None
                if n in ROUND_CALLS or (spec is not None and not (isinstance(spec, ast.Constant) and spec.value == '')):
                    self.add('A3', 'A3.reformat', node, f'{ast.unparse(node.func)[:40]}() sets precision outside the model')
                if (n == 'format' and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Constant)
                        and isinstance(node.func.value.value, str) and re.search(r'\{[^}]*:[^}]*(\.\d|[eEfFgG%])[^}]*\}',
                                                                             node.func.value.value)):
                    self.add('A3', 'A3.reformat', node, 'str.format precision outside the model')
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
            units = unit_names(value)
            if not units or not units <= self.allow['_native_units']:
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
        # integer shape arguments of reshape/view-like calls (positional, or inside a tuple/list argument)
        chain = self.parents+[node]
        for i in range(len(chain)-1, 0, -1):
            p, child = chain[i-1], chain[i]
            if isinstance(p, ast.Call) and child in p.args and _name(p.func) in SHAPE_CALLS:
                return all(isinstance(c.value, int) for c in ast.walk(child) if isinstance(c, ast.Constant)
                           and not isinstance(c.value, str))
            if not isinstance(p, (ast.UnaryOp, ast.Tuple, ast.List, ast.Starred)):
                break
        return False

    def _numeric(self, node, value):
        if self.ok_value(value) or self._exempt(node):
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
        operands = [node.left]+list(node.comparators)
        # in a handler, ordering two computed values, or a head's output against a constant (a sign test), picks
        # among outputs; comparisons that involve len() are bookkeeping
        computed = [o for o in operands if self.fold(o) is None]
        valued = self.valued_stack[-1] if self.valued_stack else set()
        if ordering and self.allow.get('_selection') and not self.in_context(ast.Raise) and computed and not any(
                isinstance(o, ast.Call) and _name(o.func) == 'len' for o in operands) and (
                len(computed) == len(operands) or any(self._valued(o, valued) for o in computed)):
            self.add('A3', 'A3.selection', node, 'orders a computed value (value-dependent selection)')
        if not self.in_context(ast.Raise) and ordering:
            for operand in [node.left]+list(node.comparators):
                why = self._threshold_operand(operand)
                if why:
                    self.add('A3', 'A3.threshold', node, why)
                    break
        self.generic_visit(node)

    def _threshold_operand(self, op, ordering=True):
        v = self.fold(op)
        if v is not None:
            return None if v in self.allow['_threshold_values'] else f'compares against {v!r}'
        n = _name(op)
        if n in self.allow.get('threshold_exempt_names', {}):
            return None
        if n and (n.isupper() and len(n) > 1 or THRESHOLD_NAME.search(n)) and not n.startswith('__'):
            return f'compares against {n}'
        if isinstance(op, ast.Attribute):
            return f'compares against attribute {ast.unparse(op)[:60]} (a configured value)'
        if isinstance(op, ast.Subscript) and isinstance(op.slice, ast.Constant) and isinstance(op.slice.value, str):
            return f'compares against table entry {ast.unparse(op)[:60]}'
        if (isinstance(op, ast.Call) and _name(op.func) == 'get' and op.args
                and isinstance(op.args[0], ast.Constant) and isinstance(op.args[0].value, str)):
            return f'compares against table entry {ast.unparse(op)[:60]}'
        return None

    # substitutes on failure
    def visit_ExceptHandler(self, node):
        """An except-handler passes when it re-raises, or when it only does bookkeeping: integer counters on
        attributes or subscripts, and logging calls. Anything else (a return, a local substitute, pass) lets a
        substitute flow on."""
        def bookkeeping(st):
            if isinstance(st, (ast.Assign, ast.AugAssign)):
                targets = st.targets if isinstance(st, ast.Assign) else [st.target]
                count = (isinstance(st.value, ast.Constant) and type(st.value.value) is int) or (
                    isinstance(st, ast.AugAssign) and isinstance(st.value, ast.Call) and _name(st.value.func) == 'len')
                return all(isinstance(t, (ast.Subscript, ast.Attribute)) for t in targets) and count
            return isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) and _name(st.value.func) in LOG_CALLS
        # a try whose body only does bookkeeping has no value to substitute: its handler may also pass
        parent = self.parents[-1] if self.parents else None
        quiet = isinstance(parent, ast.Try) and node in parent.handlers and parent.body and all(
            bookkeeping(st) for st in parent.body) and not parent.orelse
        if quiet and all(isinstance(st, ast.Pass) or bookkeeping(st) for st in node.body):
            self.generic_visit(node)
            return
        if not (node.body and isinstance(node.body[-1], ast.Raise)) and not all(bookkeeping(st) for st in node.body):
            stmt = next((s for s in node.body if not isinstance(s, ast.Raise) and not bookkeeping(s)), node)
            self.add('A4', 'A4.except_substitute', stmt, 'except-handler does not re-raise; a substitute flows on')
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.Or) and not self.in_context(ast.Raise):
            last = node.values[-1]
            if isinstance(last, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set, ast.UnaryOp)) and any(
                    _number(c) is not None for c in ast.walk(last)):
                self.add('A4', 'A4.or_fallback', node, f'or-fallback to the literal {ast.unparse(last)[:40]}')
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
