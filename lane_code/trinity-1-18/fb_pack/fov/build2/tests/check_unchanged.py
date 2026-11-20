"""Compare the scorer's numerical AST with the read-only previous build."""
import ast
import hashlib
import json
from pathlib import Path
import shlex
import sys

WORK = Path(__file__).resolve().parents[1]
OLD = WORK.parent / 'build' / 'score_fov.py'
NEW = WORK / 'score_fov.py'


def main():
    old = ast.parse(OLD.read_text())
    new = ast.parse(NEW.read_text())
    tests = []
    def function(tree, name):
        return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    for name in ('evaluate', 'summaries', 'agreement', 'fresh_output'):
        assert ast.dump(function(old, name)) == ast.dump(function(new, name)), name
        tests.append({'name': name + ' unchanged AST', 'pass': True})
    def numerical_run(tree):
        body = function(tree, 'run').body
        start = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Tuple) and any(isinstance(e, ast.Name) and e.id == 'records' for e in t.elts)
            for t in n.targets))
        end = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'result' for t in n.targets))
        return [ast.dump(n) for n in body[start:end]]
    assert numerical_run(old) == numerical_run(new)
    tests.append({'name': 'all numerical scoring, aggregation, fit and ratios unchanged AST', 'pass': True})
    paths = (OLD, NEW, Path(__file__).resolve(), Path(sys.executable))
    result = {'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'command': shlex.join([sys.executable, '-B', str(Path(__file__).resolve())]), 'tests': tests}
    (WORK / 'tests' / 'UNCHANGED_NUMERICS.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'pass': True, 'tests': len(tests)}))


if __name__ == '__main__':
    main()
