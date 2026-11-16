"""Authenticate the guard that contradicts a legacy substitution fixture."""
import ast
import hashlib
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
rows = []
for label, folder in [('tree', 'work/tree_r1'), ('base', 'work/base/tree_b01ce449')]:
    root = L / folder
    source = root / 'student_pilot/carrier_c1_run.py'
    parsed = ast.parse(source.read_text())
    fetch = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == 'fetch')
    guard = next(n for n in ast.walk(fetch) if isinstance(n, ast.If)
                 and any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                         and c.value.startswith('Final-mode row failure:') for c in ast.walk(n))
                 and any(isinstance(c, ast.Raise) for c in n.body))
    fixture = root / 'tests/test_carrier_c1_t0.py'
    parsed_test = ast.parse(fixture.read_text())
    test = next(n for n in ast.walk(parsed_test) if isinstance(n, ast.FunctionDef)
                and n.name == 'test_records_finite_rows_substitutions_and_failures')
    sha = lambda value: hashlib.sha256(value).hexdigest()
    rows.append(dict(variant=label, source=str(source.relative_to(L)),
                     source_sha256=sha(source.read_bytes()), guard_line=guard.lineno,
                     guard_ast_sha256=sha(ast.dump(guard, include_attributes=False).encode()),
                     fixture=str(fixture.relative_to(L)), fixture_line=test.lineno,
                     fixture_ast_sha256=sha(ast.dump(test, include_attributes=False).encode())))
assert rows[0]['guard_ast_sha256'] == rows[1]['guard_ast_sha256']
assert rows[0]['fixture_ast_sha256'] == rows[1]['fixture_ast_sha256']
result = dict(test='tests.test_carrier_c1_t0.FirstBatchCheck.test_records_finite_rows_substitutions_and_failures',
              cause='The legacy fixture expects substitution after a deliberately failing row; both native implementations refuse that row immediately.',
              scope='Static guard and fixture identity explains the expected-substitution failure. No internal forward error is inferred.',
              sources=rows, verified=True)
(L / 'work/build6/LEGACY_SUBSTITUTION.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
