"""Validate and freeze the three optional performance switches before model load."""
import os

NAMES = ('C1_CPU_PREFETCH', 'C1_DECODED_CACHE_MIB', 'C1_BATCH_METRICS')
_frozen = None


def parse():
    values = tuple(os.environ.get(name, '0') for name in NAMES)
    for name, value in zip(NAMES, values):
        if name == 'C1_DECODED_CACHE_MIB':
            if not value.isdecimal() or not 0 <= int(value) <= 4096:
                raise ValueError(name + ' must be 0 (OFF) or 1..4096')
        elif value not in ('0', '1'):
            raise ValueError(name + ' must be 0 or 1')
    return tuple(str(int(value)) for value in values)


def get(name):
    return (_frozen if _frozen is not None else parse())[NAMES.index(name)]


def prefetch_supported(model, streams=()):
    if getattr(model, 'training_mode', None) != 'final':
        raise ValueError('C1 CPU prefetch requires final-mode fail-without-substitution admission')
    if (getattr(model, 'geometry_online', None) or getattr(model, 'geometry_connector', None) == 'gf1'
            or getattr(model, 'gf1', None) or getattr(model, 'mdg', None)
            or 'mdg' in streams):
        raise ValueError('C1 CPU prefetch has not audited MDG, geometry_online or gf1 paths')


def startup(cfg, group):
    """Gather errors as well as settings so every rank refuses before loading assets."""
    global _frozen
    import torch.distributed as dist
    from types import SimpleNamespace
    values, error = None, None
    try:
        values = parse()
        if values[0] == '1':
            prefetch_supported(SimpleNamespace(**cfg))
    except (ValueError, TypeError, AttributeError) as exc:
        error = str(exc)
    gathered = [None] * dist.get_world_size(group)
    dist.all_gather_object(gathered, (values, error), group=group)
    if any(item[1] is not None for item in gathered):
        raise ValueError('C1 switch startup refusal: ' + repr(gathered))
    if any(item[0] != values for item in gathered):
        raise ValueError('C1 switches differ across ranks')
    _frozen = values
