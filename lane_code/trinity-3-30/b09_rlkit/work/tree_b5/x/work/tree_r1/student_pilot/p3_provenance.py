"""Content pins, immutable receipts and parent-owned clean-code authentication."""
import hashlib
import json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('Duplicate JSON key: ' + k)
        result[k] = v
    return result


def load(path):
    value = json.loads(Path(path).read_text(), object_pairs_hook=unique,
                       parse_constant=lambda s: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+s)))
    if isinstance(value, dict) and value.get('encoding') == 'base64-json':
        import base64
        raw = base64.b64decode(value['payload'], validate=True)
        if hashlib.sha256(raw).hexdigest() != value['sha256']:
            raise ValueError('Capsule digest differs')
        return json.loads(raw, object_pairs_hook=unique)
    return value


def pinned(pin):
    if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}:
        raise ValueError('Input requires an exact path/SHA256 pin')
    path = Path(pin['path'])
    if not path.is_absolute() or not path.is_file() or sha256(path) != pin['sha256']:
        raise ValueError('Missing or changed pinned input: ' + str(path))
    return path


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        f.write(encoded(value)+'\n')


def file_pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha256(path)}


def source_files(entrypoints=()):
    """Resolve local Python imports from the bounded core entrypoints."""
    import ast
    root = Path(__file__).resolve().parent
    pending = [Path(p).resolve() for p in entrypoints] if entrypoints else [
        p for p in root.glob('p3_*.py') if p.name != 'p3_kit.py']
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen: continue
        if not path.is_relative_to(root.parent):
            raise ValueError('Source entrypoint is outside the repository')
        seen.add(path)
        tree = ast.parse(path.read_text())
        for parent in path.parents:
            if parent == root.parent: break
            init = parent/'__init__.py'
            if init.is_file(): pending.append(init)
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    parent = path.parent
                    for _ in range(node.level-1): parent = parent.parent
                    if node.module:
                        base = parent.joinpath(*node.module.split('.'))
                        modules.append(base)
                        modules.extend(base/a.name for a in node.names)
                    else: modules.extend(parent/a.name for a in node.names)
                elif node.module:
                    base = root.parent.joinpath(*node.module.split('.'))
                    modules.append(base)
                    modules.extend(base/a.name for a in node.names)
            elif isinstance(node, ast.Import):
                modules.extend(root.parent.joinpath(*a.name.split('.')) for a in node.names)
            for mod in modules:
                for candidate in (mod.with_suffix('.py'), mod/'__init__.py'):
                    if candidate.is_file() and candidate.is_relative_to(root.parent): pending.append(candidate)
    return sorted(seen)


def authenticate_code(pin):
    seal = load(pinned(pin))
    if (seal.get('schema') != 'p3-clean-source-v1' or seal.get('clean') is not True
            or len(seal.get('commit', '')) != 40):
        raise ValueError('Parent must supply a clean committed source seal')
    actual = {str(p.relative_to(Path(__file__).parent.parent)): sha256(p) for p in source_files()}
    if seal.get('sources') != actual:
        raise ValueError('Runtime source closure differs from clean code seal')
    return seal
