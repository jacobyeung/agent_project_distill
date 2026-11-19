"""Adapt only the native smoke/resume guard and output path for a measurement run."""
import ast
import inspect
from pathlib import Path


def measurement_train(run, output):
    """Keep native admission/restore; write smoke receipts inside the fresh kit output."""
    tree = ast.parse(inspect.getsource(run.train))
    guard_count = output_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and ast.unparse(node.test) == (
                'smoke_steps is not None and (type(smoke_steps) != int or not 1 <= smoke_steps <= 10 or resume_pin)'):
            # The replacement loop always stops after 2 or 10 disposable updates.
            # It can safely restore an explicit native checkpoint in smoke mode.
            node.test.values[1].values.pop()
            guard_count += 1
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and (
                ast.unparse(node.targets[0]) == 'output' and ast.unparse(node.value) == "Path(cfg['output'])"):
            node.value = ast.Name(id='_so_measurement_output', ctx=ast.Load())
            output_count += 1
    if (guard_count, output_count) != (1, 1):
        raise ValueError('Native train changed: refuse unaudited smoke/output instrumentation')
    ast.fix_missing_locations(tree)
    namespace = dict(run.__dict__, _so_measurement_output=Path(output))
    exec(compile(tree, '<so-disposable-native-train>', 'exec'), namespace)
    return namespace[run.train.__name__]
