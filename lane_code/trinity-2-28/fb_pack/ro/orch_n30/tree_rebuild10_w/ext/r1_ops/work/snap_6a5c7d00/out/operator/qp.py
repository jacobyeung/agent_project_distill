"""Regenerate with authenticated native code; compare all fields and ordered indices."""
import argparse
import contextlib
import copy
import hashlib
import json
from pathlib import Path
import sys

BASELINE = 'f232d4160d75b5826d9e24aec324d690920a752a5bfaa33e5009d7550349dfc6'
RAW_BASELINE = 'd1e6715a19b5d9a15f647e3495815c63329afbc9b69cd81bbef8fcd086025c64'
CODE = 'd6273a970c30df760465013ff6789deb5466dfa887790dcf0d33abc262a9ba45'
PREFIX = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/'

def enc(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return hashlib.sha256(enc(value).encode()).hexdigest()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('Duplicate JSON key')
        out[k] = v
    return out

def load(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))

def write(path, value):
    with Path(path).open('x') as f:
        f.write(enc(value) + '\n')

def content(value):
    return {k: v for k, v in value.items() if k != 'implementation'}

def differences(a, b, path='$'):
    if type(a) is not type(b):
        return [path]
    if isinstance(a, dict):
        return [p for k in sorted(set(a) | set(b)) for p in
                ([path + '.' + k] if k not in a or k not in b else differences(a[k], b[k], path + '.' + k))]
    if isinstance(a, list):
        return ([path + '.length'] if len(a) != len(b) else []) + [p for i, (x, y) in enumerate(zip(a, b))
                                                                for p in differences(x, y, path + '[' + str(i) + ']')]
    return [] if a == b else [path]

def project(raw):
    """The pinned D0 policy moves the direct source to VQA, after native selection.

    Reproduce the exact transformation, never copy counts from the target receipt.
    The sealed raw receipt must project byte-for-byte to the pinned D0 receipt.
    """
    out = copy.deepcopy(raw)
    entry = out['sources']['ROUTE_direct']
    if entry['status'] != 'ELIGIBLE' or entry['reason'] is not None:
        raise ValueError('Direct-source policy precondition differs')
    entry.update(status='DEFERRED', reason='moved_to_vqa_store')
    for key in ('retained', 'per_type', 'selection'):
        entry.pop(key)
    entry['counts'] = {key: entry['counts'][key] for key in
                       ('seen', 'after_manifest_exclusions', 'eligible_before_source_policy')}
    out['selected_rows'] = sum(v.get('retained', 0) for v in out['sources'].values() if v['status'] == 'ELIGIBLE')
    return out

class Resolver:
    """Map catalog locators to kit bytes without changing any provenance fields."""
    def __init__(self, kit, catalog):
        self.kit, self.catalog = Path(kit).resolve(), catalog
        self.verified = {}

    def path(self, pin):
        path = self.catalog.get(pin['sha256'])
        if not isinstance(path, str) or not path.startswith(PREFIX):
            raise ValueError('Input is absent from the pinned catalog: ' + pin['sha256'])
        rel = Path(path[len(PREFIX):])
        if '..' in rel.parts or rel.is_absolute():
            raise ValueError('Unsafe catalog locator')
        physical = self.kit / rel
        if not physical.resolve().is_relative_to(self.kit):
            raise ValueError('Catalog escaped kit')
        return physical

    def __call__(self, pin):
        if set(pin) != {'path', 'sha256'}:
            raise ValueError('Malformed input pin')
        path = self.path(pin)
        if sha(path) != pin['sha256']:
            raise ValueError('Input digest differs: ' + pin['sha256'])
        self.verified[pin['sha256']] = dict(path=str(path), bytes=path.stat().st_size)
        return path

def input_pins(raw, manifest):
    pins = [raw['manifest'], raw['tokenizer'], *raw['exclusions'].values(), *raw['scene_exclusions'].values()]
    pins += [{k: v[k] for k in ('path', 'sha256')} for v in raw['remove_files']]
    for entry in manifest['sets']:
        metadata = entry['files']['packed' if 'packed' in entry['files'] else 'rows']
        pins.append({k: metadata[k] for k in ('path', 'sha256')})
    pins += [v['selection'] for v in raw['sources'].values() if 'selection' in v]
    return [pin for pin in pins if pin is not None]

def regenerate(raw, baseline, resolver, output, code, runtime=None):
    # Authenticate source bytes before any native module can execute.
    for name, expected in code['files'].items():
        p = Path(code['tree']) / name
        if p.is_symlink() or sha(p) != expected:
            raise ValueError('Source tree differs')
    # Install the byte resolver before importing modules that bind pinned by name.
    from student_pilot import p3_provenance as provenance
    original = provenance.pinned
    provenance.pinned = resolver
    for module in list(sys.modules.values()):
        if getattr(module, '__name__', '').startswith('student_pilot.') and getattr(module, 'pinned', None) is original:
            module.pinned = resolver
    try:
        from student_pilot import s1_pool
        if Path(s1_pool.__file__).resolve().parent.parent != Path(code['tree']).resolve():
            raise ValueError('Native selector imported from another tree')
        actual = s1_pool.implementation()
        if any(code['files'].get(n) != h for n, h in actual.items()):
            raise ValueError('Source closure differs')
        manifest = load(resolver(raw['manifest']))
        for pin in input_pins(raw, manifest):
            resolver(pin)  # Refuse missing inputs even for deferred sources.
        with (output / 'native.log').open('x') as log, contextlib.redirect_stdout(log):
            result = s1_pool.prepare(raw['manifest'], output / 'native', raw['remove_files'],
                                     raw['tokenizer'], raw['room_sets'])
        indices = {}
        for name, before in raw['sources'].items():
            if 'selection' not in before:
                continue
            after = result['sources'][name].get('selection')
            expected = load(resolver(before['selection']))
            observed = load(after['path']) if after else None
            equal = after is not None and differences(expected, observed) == [] and after['sha256'] == before['selection']['sha256']
            indices[name] = dict(equal=equal, sha256=after['sha256'] if after else None,
                                 count=len(observed) if isinstance(observed, list) else None)
            if equal:
                # Only restore a locator after both generated bytes and ordered indices match.
                result['sources'][name]['selection'] = dict(before['selection'])
        raw_diff = differences(content(raw), content(result))
        candidate = project(result)
        write(output / 'r.json', candidate)
        diff = differences(content(baseline), content(candidate))
        equal = not raw_diff and not diff and all(v['equal'] for v in indices.values())
        report = dict(schema='selection-equality-v1', status='EQUAL' if equal else 'DIFFERENT', regenerated=True,
            reference_sha256=BASELINE, raw_reference_sha256=RAW_BASELINE,
            selection_sha256=sha(output / 'r.json'), content_sha256=digest(content(candidate)),
            raw_content_sha256=digest(content(result)), implementation_sha256=digest(actual),
            tree_sha256=code['tree_sha256'], code_sha256=CODE, tool_sha256=sha(__file__),
            differences=diff, raw_differences=raw_diff, indices=indices,
            fields={k: k in candidate and not differences(baseline[k], candidate[k]) for k in baseline if k != 'implementation'},
            inputs=resolver.verified, production_authorized=False, runtime=runtime or {})
        write(output / 'q.json', report)
        return 0 if equal else 1
    finally:
        provenance.pinned = original
        for module in list(sys.modules.values()):
            if getattr(module, '__name__', '').startswith('student_pilot.') and getattr(module, 'pinned', None) is resolver:
                module.pinned = original

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--kit', required=True)
    p.add_argument('--tree', required=True)
    p.add_argument('--records', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--runtime')
    args = p.parse_args()
    records, output = Path(args.records), Path(args.out)
    output.mkdir(mode=0o700)
    runtime = {}
    try:
        for name, expected in [('b.json', BASELINE), ('a.json', RAW_BASELINE), ('c.json', CODE)]:
            if sha(records / name) != expected:
                raise ValueError('Reference digest differs')
        baseline, raw, code = (load(records / n) for n in ('b.json', 'a.json', 'c.json'))
        if project(raw) != baseline:
            raise ValueError('Reference policy projection differs')
        cfg = load(records / 'f.json')
        if cfg['s1_routing']['selection']['sha256'] != BASELINE:
            raise ValueError('Reference config differs')
        resolver = Resolver(args.kit, cfg['s1_routing']['catalog'])
        code['tree'] = str(Path(args.tree).resolve())
        sys.path.insert(0, code['tree'])
        if args.runtime:
            # Authenticate all source bytes before the preflight executes imports.
            for name, expected in code['files'].items():
                path = Path(code['tree']) / name
                if path.is_symlink() or sha(path) != expected:
                    raise ValueError('Source tree differs')
            scope = {}
            exec(compile(Path(args.runtime).read_text(), args.runtime, 'exec'), scope)
            scope['prepare'](code['tree'], records / 'd', load(records / 'e.json'), runtime)
        return regenerate(raw, baseline, resolver, output, code, runtime)
    except Exception as exc:
        if not (output / 'q.json').exists():
            write(output / 'q.json', dict(schema='selection-equality-v1', status='BLOCKED', regenerated=False,
                error=type(exc).__name__ + ': ' + str(exc), production_authorized=False, runtime=runtime))
        print('Input or comparison refused; inspect private q.json.', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
