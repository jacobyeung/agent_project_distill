"""Pin resolved host files under one artifact root, without copying weights."""
import argparse
from pathlib import Path

from parity_kit.common import LANE, TREE, read, sha, write


def codes(code_roots=None, sam3=None):
    result = dict(code_roots or dict(reader=LANE / 'e2e_reader', tree=TREE, heads=LANE / 'heads'))
    if sam3:
        result['sam3_source'] = Path(sam3['source_root'])
    return result


def build(root, export_dir, g3t, *, selector_head=None, scale_head=None, sam3=None,
          code_roots=None):
    root, export = Path(root).resolve(), Path(export_dir).resolve()
    code_roots = codes(code_roots, sam3)
    components = {}

    def component(name, paths):
        entries = {}
        for path in paths:
            p = Path(path).resolve(strict=True)
            rel = str(p.relative_to(root))  # refuse symlinks that leave the host root
            entries[rel] = dict(rel=rel, bytes=p.stat().st_size, sha256=sha(p))
        if not entries:
            raise ValueError('empty component: ' + name)
        components[name] = dict(role=name, files=list(entries.values()))

    full = read(export / 'full_weights/full_weights.json')
    component('checkpoint', [export / 'full_weights' / e['name'] for e in full['files'] + [full['index']]] +
              [export / 'full_weights/full_weights.json', export / 'heads.pt', export / 'artifact.json'])
    weights = {e['name'] for e in full['files'] + [full['index']]}
    component('tokenizer', [export / 'base' / n for n in read(export / 'model.json')['files'] if n not in weights])
    component('g3t', [Path(g3t) / n for n in ('model.safetensors', 'config.json')])
    for name, directory in (('selector_head', selector_head), ('scale_head', scale_head)):
        if directory:
            component(name, [Path(directory) / (name + ext) for ext in ('.json', '.safetensors')])
    if sam3:
        # The upstream builder opens its packaged BPE vocabulary inside the call.
        assets = list((Path(sam3['source_root']) / 'sam3/assets').glob('*'))
        component('sam3', [sam3[k] for k in ('checkpoint_path', 'receipt_path')] +
                  [p for p in assets if p.is_file() and p.suffix not in ('.py', '.pyc')])
    code = []
    for name, directory in sorted(code_roots.items()):
        base = Path(directory).resolve()
        for p in sorted(base.rglob('*.py')):
            resolved = p.resolve()
            resolved.relative_to(base)
            code.append(dict(root=name, rel=str(resolved.relative_to(base)), bytes=resolved.stat().st_size,
                             sha256=sha(resolved)))
    return dict(schema='e2e-artifact-v1', components=components, code=code)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'export-dir', 'g3t', 'out'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--selector-head')
    p.add_argument('--scale-head')
    p.add_argument('--sam3', help='JSON file containing checkpoint_path, receipt_path, source_root')
    p.add_argument('--code', action='append', default=[])
    a = p.parse_args()
    sam = read(a.sam3) if a.sam3 else None
    code = codes(dict(x.split('=', 1) for x in a.code), sam)
    output = Path(a.out).resolve()
    output.relative_to(Path(a.root).resolve())
    manifest = build(a.root, a.export_dir, a.g3t, selector_head=a.selector_head, scale_head=a.scale_head,
                     sam3=sam, code_roots=code)
    write(output, manifest)
    binding = dict(root=str(Path(a.root).resolve()), name=str(output.relative_to(Path(a.root).resolve())),
                   sha256=sha(output), code_roots={k: str(Path(v).resolve()) for k, v in code.items()})
    write(output.with_suffix('.binding.json'), binding)
    print(output.with_suffix('.binding.json'))


if __name__ == '__main__':
    main()
