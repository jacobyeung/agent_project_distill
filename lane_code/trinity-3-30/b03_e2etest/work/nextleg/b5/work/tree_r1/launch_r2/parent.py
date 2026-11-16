"""The sealed four-stream case has a lossless, override-free record path."""
from pathlib import Path
from student_pilot.p3_provenance import load, sha256


def validate_parent(cfg):
    if ('mdg' in cfg or set(cfg.get('streams', {})) != {'pose', 'vqa', 'routing', 'pointing'}
            or not isinstance(cfg.get('recipe'), dict) or not cfg.get('code')
            or not cfg.get('init_artifact') or not cfg.get('route_table')):
        raise ValueError('Invalid sealed four-stream parent')
    for stream in cfg['streams'].values():
        if not isinstance(stream, dict) or not stream:
            raise ValueError('Invalid sealed stream record')


def reproduce(base, output):
    base, output = Path(base), Path(output)
    key = load(base/'k/1.json')['0']
    cfg = load(base/'k'/f'{key}.json')
    from student_pilot.r2_config import configure
    produced = configure(cfg, None, overrides=False)
    if produced != cfg:
        raise ValueError('Override-free configuration differs')
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in (f'{key}.json', 'launch.json', '0.json', '1.json', '7.json'):
        raw = (base/'k'/name).read_bytes()
        target = output/name
        if name == f'{key}.json':
            import json
            if json.loads(raw) != produced:
                raise ValueError('Parent configuration serialization differs')
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
