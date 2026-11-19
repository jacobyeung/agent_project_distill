"""Adapt only the native smoke/resume guard and output path for a measurement run."""
import ast
import inspect
from pathlib import Path


def measurement_train(run, output, resume_check=None, max_steps=10, redact=None):
    """Keep native admission/restore; write smoke receipts inside the fresh kit output."""
    tree = ast.parse(inspect.getsource(run.train))
    guard_count = output_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and ast.unparse(node.test) == (
                'smoke_steps is not None and (type(smoke_steps) != int or not 1 <= smoke_steps <= 10 or resume_pin)'):
            # The replacement loop always stops after 2 or 10 disposable updates.
            # It can safely restore an explicit native checkpoint in smoke mode.
            node.test.values[1].values.pop()
            # The kit supplies a separately bounded measured loop (warm-up included).
            for child in ast.walk(node.test):
                if isinstance(child, ast.Constant) and type(child.value) is int and child.value == 10:
                    child.value = max_steps
            guard_count += 1
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and (
                ast.unparse(node.targets[0]) == 'output' and ast.unparse(node.value) == "Path(cfg['output'])"):
            node.value = ast.Name(id='_so_measurement_output', ctx=ast.Load())
            output_count += 1
    if (guard_count, output_count) != (1, 1):
        raise ValueError('Native train changed: refuse unaudited smoke/output instrumentation')
    if resume_check is not None:
        body = tree.body[0].body
        index = next(i for i,n in enumerate(body) if isinstance(n, ast.Assign)
                     and ast.unparse(n) == 'commit = authenticate(cfg)')
        body.insert(index + 1, ast.parse('_so_restore_bound = _so_resume_check(cfg, commit, resume_pin)').body[0])
        assignment = next(n for n in body if isinstance(n, ast.Assign)
                          and ast.unparse(n.targets[0]) == 'restore_bound')
        assignment.value = ast.Name(id='_so_restore_bound', ctx=ast.Load())
    ast.fix_missing_locations(tree)
    namespace = dict(run.__dict__, _so_measurement_output=Path(output), _so_resume_check=resume_check)
    if redact is not None:
        namespace['write'] = lambda path, value: run.write(path, redact(value))
    exec(compile(tree, '<so-disposable-native-train>', 'exec'), namespace)
    return namespace[run.train.__name__]
