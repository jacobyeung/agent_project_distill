"""Exercise the three sealed deployment guards without importing job entrypoints."""
import ast
import copy
from pathlib import Path
from packet_config import CONFIG, MEMBERS

cases = [('packet', copy.deepcopy(CONFIG), True)]
integer_zero = copy.deepcopy(CONFIG)
integer_zero['scheduled_sampling']['max_own_probability'] = 0
integer_zero['recipe']['scheduled_sampling']['max_own_probability'] = 0
cases.append(('integer zero', integer_zero, True))
for field, values in (
    ('routing_pose_targets', [False, 0, 1, 'true', None]),
    ('faithful_own_camera_rows', [True, 0, 1, 'false', None]),
):
    for value in values:
        cfg = copy.deepcopy(CONFIG)
        cfg['h1'][field] = value
        cases.append((field+'='+repr(value), cfg, False))
    cfg = copy.deepcopy(CONFIG)
    cfg['h1'].pop(field)
    cases.append(('missing '+field, cfg, False))
for path in (('scheduled_sampling',), ('recipe', 'scheduled_sampling')):
    for value in (True, False, '0', None, 0.1, -0.1, float('nan'), float('inf')):
        cfg = copy.deepcopy(CONFIG)
        target = cfg
        for key in path:
            target = target[key]
        target['max_own_probability'] = value
        cases.append(('/'.join(path)+'='+repr(value), cfg, False))
    cfg = copy.deepcopy(CONFIG)
    target = cfg
    for key in path:
        target = target[key]
    target.pop('max_own_probability')
    cases.append(('missing probability '+str(path), cfg, False))
for path in (('h1',), ('scheduled_sampling',), ('recipe',), ('recipe', 'scheduled_sampling')):
    cfg = copy.deepcopy(CONFIG)
    target = cfg
    for key in path[:-1]:
        target = target[key]
    target.pop(path[-1])
    cases.append(('missing section '+str(path), cfg, False))

sources = {name: MEMBERS[name].decode() for name in ('d.py', 'p.py')}
sources['proof_decoded.py'] = Path(__file__).with_name('proof_decoded.py').read_text()
for name, source in sources.items():
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'validate_switches']
    assert len(functions) == 1
    scope = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]), name, 'exec'), scope)
    for label, cfg, accepted in cases:
        try:
            scope['validate_switches'](cfg)
        except (ValueError, TypeError, KeyError, AttributeError):
            assert not accepted, (name, label)
        else:
            assert accepted, (name, label)
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id == 'validate_switches' for node in ast.walk(tree))
    print(f'PASS {name}: {len(cases)} switch cases; exact S2/S1/dual-zero conjunction')
print(f'PASS {len(sources)*len(cases)} sealed switch cases; no driver-side off-only guard remains')
