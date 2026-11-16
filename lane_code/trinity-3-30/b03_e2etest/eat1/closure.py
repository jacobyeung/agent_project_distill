"""Static import closure of a reader's entry files inside named source roots (EAT-1 static scope).

Follows module-level and function-level `import` / `from ... import` statements, including relative
imports, and resolves them only against the given roots; anything outside (stdlib, site-packages) is
left out. Usage: python -m eat1.closure --root DIR [--root DIR ...] --seed FILE ... [--json OUT]
"""
import argparse
import ast
import json
from pathlib import Path


def _resolve(name, roots):
    parts = name.split('.')
    for r in roots:
        base = Path(r).joinpath(*parts)
        for cand in (base.with_suffix('.py'), base/'__init__.py'):
            if cand.is_file():
                return cand.resolve()
    return None


def _module_name(path, roots):
    for r in roots:
        try:
            rel = path.relative_to(Path(r).resolve())
        except ValueError:
            continue
        parts = list(rel.with_suffix('').parts)
        return '.'.join(parts[:-1] if parts[-1] == '__init__' else parts)
    return None


def imports_of(path, roots):
    tree = ast.parse(path.read_text(errors='replace'))
    mod = _module_name(path, roots) or ''
    pkg = mod if path.name == '__init__.py' else mod.rpartition('.')[0]
    out = set()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ''
            if node.level:
                up = pkg.split('.') if pkg else []
                up = up[:len(up)-(node.level-1)] if node.level > 1 else up
                base = '.'.join([p for p in up+[base] if p])
            names = [base]+[f'{base}.{a.name}' if base else a.name for a in node.names]
        for n in names:
            for k in range(len(n.split('.')), 0, -1):
                hit = _resolve('.'.join(n.split('.')[:k]), roots)
                if hit:
                    out.add(hit)
                    break
    return out


def closure(seeds, roots):
    roots = [str(Path(r).resolve()) for r in roots]
    todo = [Path(s).resolve() for s in seeds]
    seen, edges = set(), {}
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        deps = imports_of(f, roots)
        edges[str(f)] = sorted(str(d) for d in deps)
        todo += [d for d in deps if d not in seen]
    return sorted(str(f) for f in seen), edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', action='append', required=True)
    ap.add_argument('--seed', nargs='+', required=True)
    ap.add_argument('--json')
    a = ap.parse_args()
    files, edges = closure(a.seed, a.root)
    if a.json:
        Path(a.json).write_text(json.dumps(dict(roots=a.root, seeds=a.seed, files=files, edges=edges), indent=1)+'\n')
    print(len(files))


if __name__ == '__main__':
    main()
