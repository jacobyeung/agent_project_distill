raise RuntimeError('UNVERIFIED_MODULE_EXECUTED')
"""Benchmark specifications for the official read kit (brief 07).

Each benchmark names its headline groups (tasks or categories) and the subtypes that
form each group. A group's score is the equal mean of its subtype means; the headline
is the equal mean of its groups (official aggregation).
"""

VSI = dict(
    name='vsibench5130',
    label='VSI-Bench official 5,130',
    items=5130,
    scenes=288,
    groups={
        'object_counting': ('object_counting',),
        'object_abs_distance': ('object_abs_distance',),
        'object_size_estimation': ('object_size_estimation',),
        'room_size_estimation': ('room_size_estimation',),
        'object_rel_distance': ('object_rel_distance',),
        'object_rel_direction': ('object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard'),
        'route_planning': ('route_planning',),
        'obj_appearance_order': ('obj_appearance_order',),
    },
    # Types a direct-only reader cannot answer for the step-544 lineage (they are routed).
    routed_groups=('object_abs_distance', 'room_size_estimation'),
    distance_group='object_abs_distance',
    room_group='room_size_estimation',
    direct_items=4008,
    headline='eight-task mean',
)

REVSI = dict(
    name='revsi999t32',
    label='ReVSI official999, tier 32',
    items=999,
    scenes=302,
    groups={
        'object_counting': ('object_counting_single', 'object_counting_multiple'),
        'object_rel_direction': ('object_rel_direction_forward_easy', 'object_rel_direction_backward_easy',
                                 'object_rel_direction_forward_hard', 'object_rel_direction_backward_hard'),
        'object_rel_distance': ('object_rel_distance_closest', 'object_rel_distance_farthest'),
        'object_size_estimation': ('object_size_estimation',),
        'route_planning': ('route_planning',),
        'object_abs_distance': ('object_abs_distance',),
        'room_size_estimation': ('room_size_estimation_single', 'room_size_estimation_multiple'),
    },
    routed_groups=('object_abs_distance', 'room_size_estimation'),
    distance_group='object_abs_distance',
    room_group='room_size_estimation',
    direct_items=679,
    headline='seven-category mean',
)

BENCHMARKS = {VSI['name']: VSI, REVSI['name']: REVSI}


def subtype_group(spec):
    return {t: g for g, ts in spec['groups'].items() for t in ts}


def direct_groups(spec):
    return tuple(g for g in spec['groups'] if g not in spec['routed_groups'])
