#!/usr/bin/env python3
"""Count pricing kit (lane sb_countdesign, 2026-11-19): build the SAM 3 teacher manifest (schema owngrd-teacher-manifest-v1, read by
lane b05_owngrd's `python -m owngrd.teacher`) for the dev counting items. One capture per scene; its names are the categories the
scene's counting items ask about, verbatim; its frames are the item's 32 source frame indices.

R0-dev (frames on trinity-1-18):
  python3 build_count_manifest.py --items COUNT_ITEMS_535.jsonl --set R0-dev \
      --frames-root /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp \
      --frame-manifests /scratch/jjyeung/orch_n30/b10_reserve/out/frame_manifests --out MANIFEST_R0DEV.json
dev-S1 (frames staged by the builder as <root>/<dataset>/<scene_name>/<index:06d>.png; hashes are computed here):
  python3 build_count_manifest.py --items COUNT_ITEMS_535.jsonl --set dev-S1 --frames-root <root> --out MANIFEST_DEVS1.json
--large-only keeps only scenes that hold an item with truth >= 5.  --dry skips every file check (counts only)."""
import argparse, collections, hashlib, json, os, sys

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--items', required=True); ap.add_argument('--set', required=True, choices=['R0-dev', 'dev-S1'])
    ap.add_argument('--frames-root', required=True); ap.add_argument('--frame-manifests'); ap.add_argument('--out', required=True)
    ap.add_argument('--large-only', action='store_true'); ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    items = [json.loads(l) for l in open(a.items)]
    items = [x for x in items if x['set'] == a.set]
    by = collections.OrderedDict()
    for x in items: by.setdefault(x['scene'], []).append(x)
    caps = []; nprompt = 0
    for scene, xs in sorted(by.items()):
        if a.large_only and not any(x['truth'] >= 5 for x in xs): continue
        idx = xs[0]['source_frame_indices']
        if len(idx) != 32 or any(x['source_frame_indices'] != idx for x in xs): raise SystemExit('frame indices differ inside ' + scene)
        ds, name = scene.split('/', 1)
        sub = name if a.set == 'R0-dev' else os.path.join(ds, name)
        hashes = None
        if a.frame_manifests and not a.dry:
            hashes = json.load(open(os.path.join(a.frame_manifests, name + '.json')))['frames']
        frames = []
        for slot, i in enumerate(idx):
            p = os.path.join(a.frames_root, sub, '%06d.png' % i)
            if a.dry: sha = None
            else:
                if not os.path.isfile(p): raise SystemExit('missing frame ' + p)
                sha = sha256_file(p)
                if hashes is not None and hashes.get(str(i)) != sha: raise SystemExit('frame hash differs from its manifest: ' + p)
            frames.append(dict(index=int(i), path=p, sha256=sha, slot=slot))
        names = sorted(set(c for x in xs for c in x['categories']))
        nprompt += len(names)
        caps.append(dict(aliases=[], canonical=scene, frames=frames, gt=None, k1_split='dev', operands=[], room=xs[0]['room'],
                         names=[dict(name=n, role='gt', instances=[]) for n in names]))
    m = dict(schema='owngrd-teacher-manifest-v1', source=dict(items=os.path.abspath(a.items), items_sha256=sha256_file(a.items), set=a.set, large_only=a.large_only),
             counts=dict(captures=len(caps), names=nprompt), captures=caps)
    with open(a.out, 'w') as f: json.dump(m, f, sort_keys=True)
    print('captures', len(caps), 'prompts', nprompt, 'manifest sha256', sha256_file(a.out))

if __name__ == '__main__':
    main()
