import hashlib

ALIAS = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3')
NATIVE = dict(scannet='scannet', scannetpp='scannetppv2', scannetppv2='scannetppv2', arkitscenes='arkitscenes')

NATIVE = dict(scannet='scannet', scannetpp='scannetppv2', scannetppv2='scannetppv2', arkitscenes='arkitscenes')

def alias_of(canonical):
    """Division key 'dN/v<12 hex>' = 'v' + sha256('rung1 scene ' + native_dataset + '/' + scene)[:12]."""
    dataset, scene = canonical.split('/', 1)
    token = 'v' + hashlib.sha256(f'rung1 scene {NATIVE[dataset]}/{scene}'.encode()).hexdigest()[:12]
    return ALIAS[dataset] + '/' + token

def alias_key(key):
    """'scannet/scene0078' -> 'd1/scene0078'; alias keys pass through."""
    if not key or '/' not in key:
        return key
    dataset, rest = key.split('/', 1)
    return f'{ALIAS.get(dataset, dataset)}/{rest}'

def excluded(names, *keys):
    """True when any key (division alias, 'dN/scene', canonical, room group) is listed."""
    return bool(names) and any(k in names for k in keys if k)

def load_exclusions(pin): return set()
