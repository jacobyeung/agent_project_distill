"""ReVSI object programs on the shared SPEC scene primitives."""
from .programs import fit_gbox, robust
from .sets import parse_revsi


def execute(item, scene):
    roles = item.get('roles') or parse_revsi(item)['roles']
    typ = item['type']
    if typ == 'object_abs_distance':
        return scene.distance(roles['a'], roles['b'])
    if typ == 'object_rel_distance':
        return scene.relative_distance(roles['target'], roles['cands'], item['options'], roles['farthest'])
    if typ == 'object_size_estimation':
        points = robust(scene.points(roles['a'])[0])
        if len(points) < 4:
            return None
        return float(max(fit_gbox(points)['axesLengths'])) * 100
    if typ == 'object_rel_direction':
        return scene.direction(roles, item['options'], hard=roles['hard'], away=roles['away'])
    raise ValueError('Unsupported ReVSI type: '+typ)


def run(item, scene):
    return scene.run(item)
