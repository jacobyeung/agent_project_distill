import hashlib

ALIAS = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3')

NATIVE = dict(scannet='scannet', scannetpp='scannetppv2', scannetppv2='scannetppv2', arkitscenes='arkitscenes')

def alias_key(key):
    """'scannet/scene0078' -> 'd1/scene0078'; alias keys pass through."""
    if not key or '/' not in key:
        return key
    dataset, rest = key.split('/', 1)
    return f'{ALIAS.get(dataset, dataset)}/{rest}'

def alias_names(data):
    """All exclusion names in alias form only (dN/...), the shippable form of the list."""
    return sorted({alias_key(k) for k in data['scenes']} | {alias_key(k) for k in data.get('physical_groups', [])}
                  | {'/'.join(t) for t in data.get('rung1_tokens', [])})
