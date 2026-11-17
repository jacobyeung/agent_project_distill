"""Registered intervention identities and type-specific decode plans."""
import math
TARGETS = {'scale_translation': 'camera_displacement',
           'rotate_translation': 'camera_movement_direction',
           'negate_turn': 'camera_rotation', 'scale_scene': 'object_abs_distance'}
DEFAULT_MODES = 'scale_translation:0.5,scale_translation:2,rotate_translation:180,negate_turn,scale_scene:0.5,scale_scene:2'

def mode_key(mode):
    name = mode['name']
    parameter = 'k' if name in ('scale_translation','scale_scene') else 'deg' if name=='rotate_translation' else None
    if parameter:
        value=float(mode[parameter])
        if not math.isfinite(value) or (parameter=='k' and value<=0):
            raise ValueError('Invalid mode parameter')
        return name+':'+format(value,'.15g')
    return name

def applies(mode, item):
    name=mode['name']
    if name=='none':return True
    kind=item.get('question_type',item.get('type'))
    if name in TARGETS:return kind==TARGETS[name]
    # Optional diagnostic controls apply to routed types only.
    return kind in TARGETS.values()

def plan(items, arms, modes):
    return {(r['id'],a,mode_key(m)) for r in items for a in arms
            for m in modes if (a=='own' or m['name']=='none') and applies(m,r)}

def read_counts(items, modes, arms=('own','tower'), tower_reused=False):
    baseline=len(items) if 'own' in arms else 0
    perturbed=sum(applies(m,r) for r in items for m in modes if m['name']!='none') if 'own' in arms else 0
    tower=len(items) if 'tower' in arms else 0
    return dict(own_baseline=baseline,own_perturbed=perturbed,tower=tower,
                tower_reused=tower if tower_reused else 0,
                reads=baseline+perturbed+(0 if tower_reused else tower))
