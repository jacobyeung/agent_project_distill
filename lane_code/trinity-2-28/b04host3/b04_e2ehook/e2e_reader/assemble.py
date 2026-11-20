"""Pin a real export as one e2e artifact. Run on the host that holds the export (the step-544 weights live there).

Layout of ROOT (one directory per component; every regular file under it is pinned):
  checkpoint/      LM, own ViT, connector and the trained heads (full_weights + heads.pt of the export)
  tokenizer/       processor and tokenizer files
  g3t/             frozen G3T tower (model.safetensors, config.json)
  sam3/            frozen SAM 3 tower (sam3.pt, its receipt)
  scale_head/      scale_head.safetensors + scale_head.json
  selector_head/   selector_head.safetensors + selector_head.json
Usage: python -B -m e2e_reader.assemble ROOT --code reader=DIR --code tree=DIR [--code heads=DIR]
Prints the manifest sha256 the read config pins.
"""
import argparse
import json
from pathlib import Path

from .artifact import build_manifest, write_manifest

ROLES = dict(checkpoint='checkpoint', tokenizer='tokenizer', g3t='g3t', sam3='sam3', scale_head='scale_head',
             selector_head='selector_head')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--code', action='append', default=[])
    a = ap.parse_args()
    root = Path(a.root)
    comps = {}
    for name, role in ROLES.items():
        d = root / name
        if not d.is_dir():
            continue
        files = sorted(str(p.relative_to(root)) for p in d.rglob('*') if p.is_file() and not p.is_symlink())
        if not files:
            raise SystemExit('empty component ' + name)
        comps[name] = (role, files)
    missing = {'checkpoint', 'tokenizer', 'g3t', 'scale_head'} - set(comps)
    if missing:
        raise SystemExit('missing components: ' + ', '.join(sorted(missing)))
    code = dict(c.split('=', 1) for c in a.code)
    manifest = build_manifest(root, comps, code_roots=code)
    path, digest = write_manifest(root, manifest)
    print(json.dumps(dict(manifest=str(path), sha256=digest, components={k: len(v[1]) for k, v in comps.items()},
                          code_files=len(manifest['code']))))


if __name__ == '__main__':
    main()
