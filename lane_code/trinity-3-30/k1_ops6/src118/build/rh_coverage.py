"""Rehearsal-only coverage, including callbacks that CPython will not trace."""
import ast
import dis
import hashlib
from pathlib import Path
import types


def statements(code):
    lines = {line for _, line in dis.findlinestarts(code) if line > 0}
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            lines |= statements(child)
    return lines


def observer_tree(filename, hits):
    """Insert executed probes in observe only; never infer hits from output files.

    Expressions retain their evaluation order, short circuiting and values.
    Statement probes run before the statement. Source files remain untouched.
    """
    tree = ast.parse(Path(filename).read_text(), filename)
    class Probes(ast.NodeTransformer):
        def visit(self, node):
            result = super().visit(node)
            if isinstance(node, ast.stmt) and not isinstance(node, (ast.Nonlocal, ast.Global)):
                probe = ast.Expr(ast.Call(ast.Name('_rh_hit', ast.Load()),
                                         [ast.Constant(node.lineno)], []))
                return [ast.copy_location(probe, node), result]
            if isinstance(node, ast.expr) and (not hasattr(node, 'ctx') or isinstance(node.ctx, ast.Load)):
                # Do not wrap starred argument syntax or assignment targets.
                if not isinstance(node, ast.Starred):
                    return ast.copy_location(ast.Call(ast.Name('_rh_value', ast.Load()),
                        [ast.Constant(node.lineno), result], []), node)
            return result
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'observe':
            instrumented = []
            for statement in node.body:
                value = Probes().visit(statement)
                instrumented.extend(value if isinstance(value, list) else [value])
            node.body = instrumented
            break
    else:
        raise AssertionError('Observer not found')
    ast.fix_missing_locations(tree)
    def hit(line):
        hits.setdefault(str(filename), set()).add(line)
    def value(line, result):
        hit(line)
        return result
    return tree, dict(_rh_hit=hit, _rh_value=value)


def instrument_observer(module, hits):
    tree, probes = observer_tree(module.__file__, hits)
    module.__dict__.update(probes)
    exec(compile(tree, module.__file__, 'exec'), module.__dict__)


def report(hits, extra=()):
    result = {}
    for filename in sorted(set(hits) | set(map(str, extra))):
        path = Path(filename)
        if not path.is_file():
            continue
        raw = path.read_bytes()
        possible = statements(compile(raw, filename, 'exec'))
        observed = hits.get(filename, set()) & possible
        result[filename] = dict(sha256=hashlib.sha256(raw).hexdigest(),
            executed=len(observed), total=len(possible), executed_lines=sorted(observed),
            unexecuted_lines=sorted(possible - observed))
    return result


def union(reports):
    """Merge only byte-identical sources, retaining the source and run provenance."""
    grouped = {}
    for origin, coverage in reports:
        for filename, row in coverage.items():
            key = (Path(filename).name, row['sha256'])
            value = grouped.setdefault(key, dict(sha256=row['sha256'], sources=[], runs=[],
                                                executed_lines=set(), possible=set()))
            value['sources'].append(filename)
            value['runs'].append(origin)
            value['executed_lines'].update(row['executed_lines'])
            value['possible'].update(row['executed_lines'] + row['unexecuted_lines'])
    result = {}
    for (name, digest), value in sorted(grouped.items()):
        possible = value.pop('possible')
        observed = value['executed_lines']
        value.update(executed=len(observed), total=len(possible),
                     unexecuted_lines=sorted(possible - observed), executed_lines=sorted(observed),
                     sources=sorted(set(value['sources'])), runs=sorted(set(value['runs'])))
        result[name + '@' + digest[:12]] = value
    return result
