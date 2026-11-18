"""An explicit read population; validate the full source before selecting it."""
from collections import Counter
from contextlib import contextmanager
import importlib

EXCLUDED = ('object_abs_distance', 'room_size_estimation')


def excluded(spec):
    value = spec.get('types')
    if value is not None and value != 'direct':
        raise ValueError('Unknown type filter')
    return EXCLUDED if value == 'direct' else ()


def select(rows, spec):
    result = [r for r in rows if r['question_type'] not in excluded(spec)]
    if not result:
        raise ValueError('Type filter empties family')
    return result


def population(rows, spec):
    counts = Counter(r['question_type'] for r in rows)
    kept = select(rows, spec)
    return dict(items=len(kept), types=dict(Counter(r['question_type'] for r in kept)),
                excluded={t:dict(excluded=True, items=counts[t]) for t in excluded(spec) if counts[t]},
                rooms_with_items=(len({r.get('room', r.get('scene')) for r in kept})
                                  if all(r.get('room', r.get('scene')) is not None for r in kept) else None))


@contextmanager
def task_provider(spec, validate):
    """Use one validated population in worker, both mergers and reports.

    No evaluator source, protocol, scorer or parity implementation changes.
    Imported aliases must also use the same provider.
    """
    modules = [importlib.import_module(n) for n in ('data', 'worker', 'merge', 'budget_merge')]
    original = modules[0].tasks_for
    def tasks(dataset, roots):
        rows = original(dataset, roots)
        validate(rows)
        return select(rows, spec)
    saved = [(m, m.tasks_for) for m in modules]
    try:
        for m, _ in saved:
            m.tasks_for = tasks
        yield
    finally:
        for m, fn in saved:
            m.tasks_for = fn
