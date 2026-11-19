"""Explicit global stream budgets for the world-4 E2E leg."""
from collections import Counter


def apply(cfg, recipe):
    for key, default in (('max_row_tokens', 16384), ('max_routing_suffix_tokens', 9600)):
        if key in cfg:
            value = cfg[key]
            if type(value) is not int or not 1 <= value <= default:
                raise ValueError(f'{key} must be a positive integer no larger than {default}')
            recipe[key] = value
    budgets = cfg.get('stream_rows_per_step')
    if budgets is None:
        return recipe
    world = recipe['world_size']
    reference = recipe.get('reference_world_size', world)
    mix = cfg['mix']
    if (cfg.get('training_mode') != 'final' or len(mix) != len(set(mix))
            or not isinstance(budgets, dict) or set(budgets) != set(mix)
            or any(type(n) is not int or n < world or n % world for n in budgets.values())):
        raise ValueError('stream_rows_per_step needs one positive world-divisible budget per unique stream')
    groups = {s: min(reference, n) for s, n in budgets.items()}
    if any(budgets[s] % groups[s] for s in mix):
        raise ValueError('Stream budgets must form complete reference groups')
    recipe.update(mix=[s for s in mix for _ in range(budgets[s] // world)],
                  global_batch=sum(budgets.values()), stream_rows_per_step=dict(budgets),
                  stream_reference_rows=groups)
    return recipe


def plan_groups(recipe, plan):
    """Keep admission atomic within each stream's nominal reference group."""
    world = recipe['world_size']
    if Counter(s for s, _ in plan) != Counter({s: n // world for s, n in recipe['stream_rows_per_step'].items()}):
        raise ValueError('Plan differs from explicit stream budgets')
    start = 0
    while start < len(plan):
        stream = plan[start][0]
        factor = recipe['stream_reference_rows'][stream] // world
        group = plan[start:start + factor]
        if len(group) != factor or any(s != stream or len(ids) != world for s, ids in group):
            raise ValueError('Reference group must contain equal same-stream slices')
        yield group
        start += factor

