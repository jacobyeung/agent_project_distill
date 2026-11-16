"""Typed tower failures and the per-item decode boundary."""
from functools import wraps


class TowerError(ValueError):
    """An item cannot supply validated tower geometry; never use own poses."""


def tower_guard(function):
    """Translate input, asset and numerical failures at tower boundaries."""
    @wraps(function)
    def guarded(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except TowerError:
            raise
        except (ValueError, RuntimeError, OSError) as exc:
            raise TowerError(f'{function.__name__}: {exc}') from exc
    return guarded


def tower_item(function):
    """Return a failed item that the rank's ordinary record loop can retain."""
    @wraps(function)
    def decode(model, processor, batch, *args, **kwargs):
        source = kwargs.get('pose_source', 'own')
        if source == 'own' and kwargs.get('tower_state') is not None:
            raise ValueError('own pose_source refuses tower_state')
        try:
            return function(model, processor, batch, *args, **kwargs)
        except TowerError as exc:
            if source != 'tower':
                raise
            return dict(tokens=[], text='', calls=[], finish='tower_error',
                        mode=kwargs.get('mode', 'own'), tower_error=str(exc),
                        heads=dict(pose_source='tower', tower_scale=None, pose9=None,
                                   gravity=None, depth_queries=[]),
                        geometry_error=str(exc), prompt_tokens=int(batch['input_ids'].shape[1]),
                        generated_tokens=0, errors=1)
    return decode
