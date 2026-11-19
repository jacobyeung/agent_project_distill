"""Validate and freeze the optional performance switches before model load."""
import os

NAMES = ('C1_CPU_PREFETCH', 'C1_DECODED_CACHE_MIB', 'C1_BATCH_METRICS')
FALLBACK = 'C1_CPU_PREFETCH_FALLBACK'
_frozen = None


def parse():
    values = tuple(os.environ.get(name, '0') for name in NAMES)
    for name, value in zip(NAMES, values):
        if name == 'C1_DECODED_CACHE_MIB':
            if not value.isdecimal() or not 0 <= int(value) <= 4096:
                raise ValueError(name + ' must be 0 (OFF) or 1..4096')
        elif value not in ('0', '1'):
            raise ValueError(name + ' must be 0 or 1')
    fallback = os.environ.get(FALLBACK, '0')
    if fallback not in ('0', '1'):
        raise ValueError(FALLBACK + ' must be 0 or 1')
    if fallback == '1' and values[0] != '1':
        raise ValueError(FALLBACK + ' requires C1_CPU_PREFETCH=1')
    values = tuple(str(int(value)) for value in values)
    # Preserve the original three-value startup payload unless fallback is ON.
    return values + ('1',) if fallback == '1' else values


def get(name):
    values = _frozen if _frozen is not None else parse()
    if name == FALLBACK:
        return values[3] if len(values) == 4 else '0'
    return values[NAMES.index(name)]


def record():
    values = _frozen if _frozen is not None else parse()
    return {'performance': dict(zip(NAMES + (FALLBACK,), values))} if any(v != '0' for v in values) else {}


def prefetch_supported(model, streams=()):
    if getattr(model, 'training_mode', None) != 'final':
        raise ValueError('C1 CPU prefetch requires final-mode fail-without-substitution admission')
    if (getattr(model, 'geometry_online', None) or getattr(model, 'geometry_connector', None) == 'gf1'
            or getattr(model, 'gf1', None) or getattr(model, 'mdg', None)
            or 'mdg' in streams):
        raise ValueError('C1 CPU prefetch has not audited MDG, geometry_online or gf1 paths')


def startup(cfg):
    """Parse locally; the trainer carries agreement through its existing collectives."""
    from types import SimpleNamespace
    values, error = None, None
    try:
        values = parse()
        if values[0] == '1':
            prefetch_supported(SimpleNamespace(**cfg))
    except (ValueError, TypeError, AttributeError) as exc:
        error = str(exc)
    return values, error


def accept(local, root_values):
    """Return a local error for the existing agree(), and freeze validated values."""
    global _frozen
    values, error = local
    if error is not None:
        return 'C1 switch startup refusal: ' + error
    if values != root_values:
        return 'C1 switches differ across ranks'
    _frozen = values
