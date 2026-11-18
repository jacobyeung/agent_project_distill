"""Trinity side: decode fam.py / s2sum.py family codes. Usage: famdecode.py FILE.json"""
import hashlib, json, sys, re
CATS = ['box_3d', 'obj_appearance_order', 'object_counting', 'object_rel_direction_easy', 'object_rel_direction_hard',
        'object_rel_direction_medium', 'object_rel_distance', 'object_size_estimation', 'route_planning', 'object_abs_distance',
        'room_size_estimation', 'None']
M = {hashlib.sha256(c.encode()).hexdigest()[:8]: c for c in CATS}
print(re.sub(r'\b([0-9a-f]{8})\|', lambda m: M.get(m.group(1), m.group(1)) + '|', open(sys.argv[1]).read()))
