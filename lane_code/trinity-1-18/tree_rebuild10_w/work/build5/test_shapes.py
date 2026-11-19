"""Inspect test entry styles without importing or executing tests."""
import ast
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
rows=[]
for path in sorted((L/'work/tree_r1').rglob('test_*.py')):
    value=ast.parse(path.read_text())
    functions=[node.name for node in value.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_')]
    if functions:rows.append(dict(file=str(path.relative_to(L/'work/tree_r1')),functions=functions))
(L/'work/build5/TEST_SHAPES.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
