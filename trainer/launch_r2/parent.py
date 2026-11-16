"""The sealed four-stream case has a lossless, override-free record path."""
from pathlib import Path
from student_pilot.p3_provenance import load, sha256


def reproduce(base, output):
    base, output = Path(base), Path(output)
    key = load(base/'k/1.json')['0']
    cfg = load(base/'k'/f'{key}.json')
    if 'mdg' in cfg or set(cfg['streams']) != {'pose', 'vqa', 'routing', 'pointing'}:
        raise ValueError('Expected the declared four-stream parent')
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in (f'{key}.json', 'launch.json', '0.json', '1.json', '7.json'):
        raw = (base/'k'/name).read_bytes()
        target = output/name
        target.write_bytes(raw)
        results.append(dict(file=name, sha256=sha256(target), identical=raw == target.read_bytes()))
    return results


def layout_config(parent, model, layout):
    if layout == 'four':
        if 'mdg' in parent or set(parent.get('streams', {})) != {'pose', 'vqa', 'routing', 'pointing'}:
            raise ValueError('Four-stream layout requires its sealed parent')
        return {k: parent[k] for k in ('streams', 'mix')}
    if layout != 'five':
        raise ValueError('Unknown declared stream layout')
    return {k: model[k] for k in ('streams', 'mdg', 'mix')}
