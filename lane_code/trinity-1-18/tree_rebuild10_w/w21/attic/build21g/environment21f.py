"""Fail closed on environment capabilities that lack literal source evidence.

This is a deliberately restricted source language, not a Python interpreter.
Bindings across scopes, mutations, unpacking and calls cannot prove literals.
The name scanner runs first, so known forbidden contributions retain its errors.
"""
import ast
import re
import shlex

# A literal key here may have a runtime value. It still undergoes the name check,
# as does every resolvable value. No inherited map or computed key is exempt.
ENVIRONMENT_VALUE_ALLOWLIST = frozenset()
UNKNOWN = object()


def scan_python(tree, name, doc):
    bindings = {}
    dirty = set()
    imports = {'os': {'os'}, 'subprocess': {'process'}}
    for builtin in ('getattr', 'setattr', 'delattr', 'eval', 'exec', '__import__', 'globals', 'locals', 'vars'):
        imports[builtin] = {'builtin:' + builtin}
    nodes = list(ast.walk(tree))
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    records = []
    functions = set()

    def refuse(node, reason):
        raise ValueError(f'ENV_UNRESOLVED:{doc}:{getattr(node, "lineno", 0)}:environment:{reason}: {ast.unparse(node)}')

    def bind(key, value):
        bindings.setdefault(key, []).append(value)

    def target(node, value):
        if isinstance(node, ast.Name):
            bind(node.id, value)
        elif isinstance(node, (ast.Tuple, ast.List, ast.Starred)):
            for child in ast.walk(node):
                if isinstance(child, ast.Name):
                    bind(child.id, UNKNOWN)
                    # Retain capability taint even when the literal is unknown.
                    bind(child.id, value)
        elif isinstance(node, (ast.Subscript, ast.Attribute)):
            for child in ast.walk(node.value):
                if isinstance(child, ast.Name):
                    dirty.add(child.id)

    for node in nodes:
        if isinstance(node, ast.Import):
            for item in node.names:
                key = item.asname or item.name.split('.')[0]
                bind(key, UNKNOWN)
                if item.name in ('os', 'posix', 'nt', 'subprocess'):
                    imports.setdefault(key, set()).add('process' if item.name == 'subprocess' else 'os')
                if item.name == 'builtins':
                    refuse(node, 'dynamic builtin namespace access')
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                if item.name == '*':
                    refuse(node, 'wildcard import may hide an environment capability')
                key = item.asname or item.name
                bind(key, UNKNOWN)
                if node.module in ('os', 'posix', 'nt'):
                    role = ('env' if item.name in ('environ', 'environb') else
                            'setter:putenv' if item.name in ('putenv', 'unsetenv') else
                            'launch:' + item.name if item.name.startswith(('exec', 'spawn')) else '')
                    if role:
                        imports.setdefault(key, set()).add(role)
                elif node.module == 'subprocess':
                    imports.setdefault(key, set()).add('launch:' + item.name)
                elif node.module == 'importlib' and item.name == 'import_module':
                    imports.setdefault(key, set()).add('builtin:__import__')
                elif node.module == 'builtins':
                    refuse(node, 'dynamic builtin namespace access')
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            for lhs in node.targets if isinstance(node, ast.Assign) else [node.target]:
                target(lhs, node.value if not isinstance(node, ast.AugAssign) else UNKNOWN)
                if not isinstance(parents.get(node), ast.Module) and isinstance(lhs, ast.Name):
                    # A local or conditional binding cannot prove a different scope's
                    # value. Reject ambiguity instead of merging scopes optimistically.
                    bind(lhs.id, UNKNOWN)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            target(node.target, UNKNOWN)
        elif isinstance(node, ast.arg):
            bind(node.arg, UNKNOWN)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
            bind(node.name, UNKNOWN)
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and child.value is not None:
                    bind(node.name, child.value)
        elif isinstance(node, ast.ClassDef):
            bind(node.name, UNKNOWN)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    target(item.optional_vars, UNKNOWN)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bind(node.name, UNKNOWN)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            bind(node.name, UNKNOWN)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bind(node.rest, UNKNOWN)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                dirty.add(node.func.value.id)
            # Passing a mutable map to an arbitrary helper loses its proof.
            for arg in node.args:
                for child in ast.walk(arg):
                    if isinstance(child, ast.Name):
                        dirty.add(child.id)

    # Aliases share mutation risk, including aliases retained inside containers.
    edges = []
    for key, values in bindings.items():
        for value in values:
            if value is not UNKNOWN:
                edges.extend((key, child.id) for child in ast.walk(value) if isinstance(child, ast.Name))
    for _ in range(len(bindings) + 1):
        added = {a for a, b in edges if b in dirty} | {b for a, b in edges if a in dirty}
        if added <= dirty:
            break
        dirty.update(added)

    def literal(node, seen=frozenset()):
        if node is UNKNOWN:
            return UNKNOWN
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name) and node.id not in seen and node.id not in dirty:
            values = bindings.get(node.id, [])
            if len(values) == 1:
                return literal(values[0], seen | {node.id})
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [literal(x, seen) for x in node.elts]
            if all(x is not UNKNOWN for x in values):
                return values
        if isinstance(node, ast.Dict):
            result = {}
            for key, value in zip(node.keys, node.values):
                if key is None:
                    extra = literal(value, seen)
                    if not isinstance(extra, dict):
                        return UNKNOWN
                    result.update(extra)
                else:
                    key = literal(key, seen)
                    if not isinstance(key, (str, bytes)):
                        return UNKNOWN
                    result[key] = literal(value, seen)
            return result
        return UNKNOWN

    role_names = {key: set(value) for key, value in imports.items()}

    def roles(node):
        if node is UNKNOWN:
            return set()
        if isinstance(node, ast.Name):
            return role_names.get(node.id, set())
        if isinstance(node, (ast.Tuple, ast.List, ast.Starred)):
            return set().union(*(roles(x) for x in ast.iter_child_nodes(node)))
        if isinstance(node, ast.Attribute):
            base = roles(node.value)
            # These explicit API names remain environment capabilities even when
            # their receiver comes from a helper or a dynamically loaded module.
            if node.attr in ('environ', 'environb'):
                return {'env'}
            if node.attr in ('putenv', 'unsetenv'):
                return {'setter:' + node.attr}
            if 'os' in base:
                if node.attr.startswith(('exec', 'spawn')):
                    return {'launch:' + node.attr}
            if 'env' in base:
                return {'setter:' + node.attr}
            if 'process' in base:
                return {'launch:' + node.attr}
        if isinstance(node, ast.Call):
            if 'builtin:getattr' in roles(node.func) and len(node.args) >= 2:
                attribute = literal(node.args[1])
                if isinstance(attribute, str):
                    return roles(ast.Attribute(value=node.args[0], attr=attribute, ctx=ast.Load()))
            if isinstance(node.func, ast.Name) and node.func.id in functions:
                return roles(node.func)
        return set()

    # Capability propagation is monotone and finite; it does not recursively walk
    # a cyclic binding graph for each use site.
    while True:
        changed = False
        for key, values in bindings.items():
            inferred = set().union(*(roles(value) for value in values))
            known = role_names.setdefault(key, set())
            if inferred - known:
                known.update(inferred)
                changed = True
        if not changed:
            break

    def string(value):
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return UNKNOWN
        return value if isinstance(value, str) else UNKNOWN

    def pair(key, value, node):
        key = string(key)
        if key is UNKNOWN:
            refuse(node, 'environment key is not a literal string')
        where = f'{doc}:{node.lineno}:environment'
        name(key, where)
        value = string(value)
        if value is UNKNOWN:
            if key not in ENVIRONMENT_VALUE_ALLOWLIST:
                refuse(node, 'value for literal key ' + repr(key) + ' is unresolved')
        else:
            name(value, where)

    def mapping(value, node):
        if isinstance(value, dict):
            items = list(value.items())
        elif isinstance(value, list) and all(isinstance(x, list) and len(x) == 2 for x in value):
            items = value
        else:
            refuse(node, 'environment map is not a complete literal mapping')
        for key, val in items:
            pair(key, val, node)

    for node in nodes:
        if isinstance(node, ast.Name) and node.id == '__builtins__':
            refuse(node, 'dynamic builtin namespace access')
        if isinstance(node, ast.Attribute) and node.attr in ('modules', 'import_module'):
            refuse(node, 'dynamic module namespace access')
        capability = roles(node)
        if capability and isinstance(node, ast.expr) and not isinstance(getattr(node, 'ctx', None), ast.Store):
            parent = parents.get(node)
            allowed = (isinstance(parent, ast.Attribute) and parent.value is node and bool(capability & {'os', 'env', 'process'}) or
                       isinstance(parent, ast.Call) and parent.func is node or
                       isinstance(parent, ast.Subscript) and parent.value is node and capability == {'env'})
            if isinstance(parent, (ast.Assign, ast.AnnAssign)) and parent.value is node:
                targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
                allowed = all(isinstance(x, ast.Name) for x in targets)
            if isinstance(parent, ast.Call) and parent.args and parent.args[0] is node:
                allowed |= 'builtin:getattr' in roles(parent.func) and bool(capability & {'os', 'env', 'process'})
            if not allowed:
                refuse(node, 'environment capability escapes supported literal operations')
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            for lhs in node.targets if isinstance(node, ast.Assign) else [node.target]:
                if isinstance(lhs, ast.Attribute) and any(x.startswith(('setter:', 'launch:')) for x in roles(lhs)):
                    refuse(node, 'environment or process method replacement')
                if isinstance(lhs, (ast.Tuple, ast.List)) and any(
                        isinstance(x, ast.Subscript) and 'env' in roles(x.value) or
                        isinstance(x, ast.Attribute) and 'env' in roles(x) for x in ast.walk(lhs)):
                    refuse(node, 'unpacked environment write')
                if isinstance(lhs, ast.Subscript) and 'env' in roles(lhs.value):
                    pair(literal(lhs.slice), literal(node.value) if not isinstance(node, ast.AugAssign) else UNKNOWN, node)
                    records.append(ast.unparse(node))
                elif 'env' in roles(lhs) and isinstance(lhs, ast.Attribute):
                    mapping(literal(node.value), node)
                    records.append(ast.unparse(node))
        if isinstance(node, ast.Delete) and any(
                isinstance(x, ast.Subscript) and 'env' in roles(x.value) for x in ast.walk(node)):
            refuse(node, 'unsupported environment removal')
        if isinstance(node, ast.Attribute) and roles(node.value) & {'os', 'env', 'process'} and node.attr.startswith('__'):
            if node.attr != '__setitem__':
                refuse(node, 'reflective access to an environment capability')
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        kind = roles(func)
        builtins = {x.split(':', 1)[1] for x in kind if x.startswith('builtin:')}
        if any(key in bindings for key in builtins):
            refuse(node, 'shadowed reflection builtin')
        if builtins & {'eval', 'exec', '__import__', 'globals', 'locals', 'vars'}:
            refuse(node, 'dynamic execution or namespace access may hide an environment write')
        if builtins & {'getattr', 'setattr', 'delattr'}:
            if builtins == {'getattr'} and (len(node.args) != 2 or not isinstance(literal(node.args[1]), str)):
                refuse(node, 'dynamic attribute lookup may hide an environment capability')
            if node.args and roles(node.args[0]) & {'os', 'env', 'process'}:
                if builtins != {'getattr'} or len(node.args) != 2 or not isinstance(literal(node.args[1]), str):
                    refuse(node, 'dynamic environment capability lookup or replacement')
        for key in node.keywords:
            if key.arg == 'env':
                mapping(literal(key.value), node)
                records.append(ast.unparse(node))
            elif key.arg is None:
                values = literal(key.value)
                if not isinstance(values, dict):
                    refuse(node, 'keyword expansion may pass an unresolved environment map')
                if 'env' in values:
                    mapping(values['env'], node)
        setters = {x.split(':', 1)[1] for x in kind if x.startswith('setter:')}
        for setter in setters:
            if setter in ('get', 'keys', 'values', 'items', 'copy', '__getitem__'):
                continue
            if setter in ('putenv', 'setdefault', '__setitem__') and len(node.args) == 2 and not node.keywords:
                pair(literal(node.args[0]), literal(node.args[1]), node)
            elif setter in ('update', '__ior__') and len(node.args) <= 1:
                if node.args:
                    mapping(literal(node.args[0]), node)
                for key in node.keywords:
                    if key.arg is None:
                        mapping(literal(key.value), node)
                    else:
                        pair(key.arg, literal(key.value), node)
            else:
                refuse(node, 'unsupported environment operation ' + setter)
            records.append(ast.unparse(node))
        launchers = {x.split(':', 1)[1] for x in kind if x.startswith('launch:')}
        for launcher in launchers:
            if any(isinstance(arg, ast.Starred) for arg in node.args):
                refuse(node, 'positional expansion may pass an environment map')
            if launcher in ('execve', 'execvpe', 'spawnve', 'spawnvpe', 'execle', 'execlpe', 'spawnle', 'spawnlpe'):
                if not node.args:
                    refuse(node, 'missing literal environment map')
                mapping(literal(node.args[-1]), node)
            elif launcher == 'Popen' and len(node.args) >= 11:
                mapping(literal(node.args[10]), node)
            elif len(node.args) > 1:
                refuse(node, 'unsupported positional process options')
        # An environment capability passed to a helper can be mutated there.
        for arg in node.args:
            if roles(arg) & {'os', 'env', 'process'}:
                if builtins != {'getattr'}:
                    refuse(node, 'environment capability escapes to a call')
        if kind & {'env', 'os', 'process'}:
            refuse(node, 'environment capability is called dynamically')
    return records


def scan_shell(source, name, doc):
    """Accept only literal shell environment writes; reject dynamic dispatch.

    Shell expansion runs before builtins and can introduce assignments or commands.
    We therefore reject indirection/evaluation globally and expanded export/env
    operands, including scheduler exports. Any assigned shell variable may already
    be exported by the caller, so assignments also require literal evidence.
    """
    records = []
    exported = set()
    assignments = {}
    lines = source.replace('\\\n', '').splitlines()

    def refuse(number, line, why):
        raise ValueError(f'ENV_UNRESOLVED:{doc}:{number}:environment:{why}: {line}')

    def entry(token, number, line):
        if '=' not in token:
            refuse(number, line, 'environment entry has no literal value')
        key, value = token.split('=', 1)
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', key):
            refuse(number, line, 'environment key is not a literal name')
        where = f'{doc}:{number}:environment'
        name(key, where)
        name(value, where)
        if any(c in value for c in ('$','`')) and key not in ENVIRONMENT_VALUE_ALLOWLIST:
            refuse(number, line, 'value for literal key ' + repr(key) + ' is unresolved')
        records.append(dict(location=where, key=key, expression=line))

    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith('#') and not line.startswith('#SBATCH'):
            continue
        if '${!' in line or re.search(r'\b(eval|source|declare|typeset|read|mapfile|alias|trap|let|for|select|unset)\b|printf\s+-v|\blocal\s+-\S*[nx]|\bset\s+-[^\s]*a|\(\(|\b[A-Za-z_]\w*\s*\+=', line):
            refuse(number, line, 'shell indirection or dynamic assignment')
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=';&|()<>')
            lexer.whitespace_split = True
            lexer.commenters = ''
            tokens = list(lexer)
        except ValueError:
            refuse(number, line, 'shell syntax cannot be resolved')
        # Split control operators conservatively; any uncertain export still refuses.
        tokens = [x for x in tokens if x not in (';', '&&', '||', 'then', 'do')]
        for index, token in enumerate(tokens):
            if token == '.' or token.startswith(('$', '`')):
                refuse(number, line, 'computed shell command')
            if token in ('bash', 'sh', '/bin/bash', '/bin/sh') and '-c' in tokens[index + 1:]:
                refuse(number, line, 'dynamic shell program')
            if token in ('export', 'env') or token.startswith('--export'):
                rest = tokens[index + 1:]
                if token.startswith('--export='):
                    rest = token.split('=', 1)[1].split(',')
                if not rest:
                    refuse(number, line, 'environment export cannot be enumerated')
                for operand in rest:
                    if token == 'env' and '=' not in operand:
                        if any(c in operand for c in ('$','`')) or operand.startswith('-'):
                            refuse(number, line, 'dynamic env command or options')
                        break
                    if operand in assignments and '=' not in operand:
                        operand += '=' + assignments[operand]
                    entry(operand.rstrip(';'), number, line)
                    exported.add(operand.split('=', 1)[0])
            match = re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*)=(.*)', token.rstrip(';'))
            if match:
                key, value = match.groups()
                assignments[key] = value
                entry(token.rstrip(';'), number, line)
    return records
