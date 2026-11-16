"""THINK-0 overrides for the copied aws_vl64o worker; scoring stays upstream."""
MODELS = {'t0m800': 'T0_m800', 'cp1m200': 'CP1_m200'}
DIRECT_TYPES = ('object_counting', 'object_size_estimation', 'room_size_estimation',
                'obj_appearance_order', 'route_planning', 'object_rel_direction_easy')


def validate(cell):
    from cells import frame_count
    if frame_count(cell) != 32 or cell.get('layout') != 'duplicate' or cell.get('model') not in MODELS:
        raise ValueError('THINK-0 requires T0 m800 or CP1 m200 at the trained format, 32 duplicate')
    if type(cell.get('thinking')) is not bool or cell.get('max_tokens') != (16384 if cell.get('thinking') else 4096):
        raise ValueError('Require explicit thinking: ON16k cap 16384, OFF cap 4096')
    if cell.get('decoding') != 'greedy':
        raise ValueError('THINK-0 requires greedy decoding')


def sampling(cell, cls, output_kind):
    validate(cell)
    return cls(temperature=0, max_tokens=cell['max_tokens'], output_kind=output_kind)


def select_tasks(tasks, cell):
    # Both full sets are retained. Analysis excludes the routed types.
    validate(cell)
    return tasks
