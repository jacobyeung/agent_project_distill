"""Step 1: the RGB anchor frames of relift's 46 eligible captures, verified against frame_binding_sha256.

For each eligible capture: reproduce frame_binding_sha256 = digest({anchors: FRAMES.json[native], dense: DENSE_MANIFEST[native]})
(h1eval/h10/parity_adapter.map_items) and require it equal to every item's items544 mapping and to the dump's metadata;
require FRAMES.json anchor indices == mapping anchor_indices == source_indices, and the dense manifest's anchor slots to
point at the same files; then find each anchor PNG in a local content-addressed store and check its bytes' sha256.
Writes out/FRAMES_GTC.json; when any frame is missing, writes FRAMES_NEEDED.md and exits 3.
Usage: p1cpu python frames.py
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gtc_common as G


def main():
    R = G.load_relift(); R.dependencies()
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    caps, dense = G.frame_manifests()
    depths = G.depth_rows(R)
    out, missing, bytes_total, roots = [], [], 0, {}
    dense_local = 0
    for cap in sorted({i['capture'] for i in items}):
        mine = [refs[i['item_id']] for i in items if i['capture'] == cap]
        natives = {r['mapping']['native'] for r in mine}
        if len(natives) != 1:
            raise ValueError('capture maps to several natives: '+cap)
        native = natives.pop()
        bind = G.binding(native, caps, dense)
        if any(r['mapping']['frame_binding_sha256'] != bind for r in mine):
            raise ValueError('frame binding does not reproduce: '+cap)
        if depths[cap]['metadata']['frame_binding_sha256'] != bind:
            raise ValueError('dump binding differs: '+cap)
        c, d = caps[native], dense[native]
        anchors = [f['index'] for f in c['frames']]
        if not all(anchors == c['anchor_indices'] == r['mapping']['anchor_indices'] == r['source_indices'] for r in mine):
            raise ValueError('anchor indices differ: '+cap)
        if [d['frames'][s]['sha256'] for s in d['anchor_slots']] != [f['sha256'] for f in c['frames']]:
            raise ValueError('dense anchor slots differ: '+cap)
        frames = []
        for slot, f in enumerate(c['frames'], 1):
            p, root = G.resolve_frame(f['path'], f['sha256'])
            if p is None:
                missing.append(dict(capture=cap, slot=slot, rel=f['path'], sha256=f['sha256']))
                continue
            got = G.sha256_file(p)
            if got != f['sha256']:
                raise ValueError('frame sha256 mismatch '+str(p))
            n = os.path.getsize(p); bytes_total += n; roots[str(root)] = roots.get(str(root), 0)+1
            frames.append(dict(slot=slot, index=f['index'], path=str(p), sha256=f['sha256'], bytes=n))
        dl = sum(any((r/os.path.relpath(x['path'], '/scratch/jjyeung/devs1_frames')).is_file() for r in G.FRAME_ROOTS)
                 for x in d['frames'])
        dense_local += dl == len(d['frames'])
        out.append(dict(capture=cap, native=native, dataset=G.dataset(cap), hw=c['hw'], frame_binding_sha256=bind,
                        anchor_indices=anchors, frames=frames, dense_count=len(d['frames']), dense_all_local=dl == len(d['frames']),
                        items=sorted(r['item_id'] for r in mine)))
    body = dict(schema='gtc-frames-v1', captures=out, eligible_items=len(items), eligible_captures=len(out),
                anchor_files=sum(len(c['frames']) for c in out), anchor_bytes=bytes_total, roots_used=roots,
                missing=missing, dense_all_local_captures=dense_local,
                binding_rule='digest({anchors: FRAMES.json capture, dense: DENSE_MANIFEST capture}) = parity_adapter.map_items',
                sources=dict(frames_json=str(G.FRAMES_JSON), frames_json_sha256=G.sha256_file(G.FRAMES_JSON),
                             dense_json=str(G.DENSE_JSON), dense_json_sha256=G.sha256_file(G.DENSE_JSON),
                             items=str(G.ITEMS), items_sha256=G.sha256_file(G.ITEMS), frame_roots=[str(r) for r in G.FRAME_ROOTS]))
    G.write_json(G.OUT/'FRAMES_GTC.json', body)
    if missing:
        lines = ['# Frames needed (GTC)', '', f'{len(missing)} anchor PNGs of the eligible captures are not on this node.', '',
                 '| capture | slot | sha256 |', '|---|---|---|'] + [f"| {m['capture']} | {m['slot']} | {m['sha256']} |" for m in missing]
        (G.ROOT/'FRAMES_NEEDED.md').write_text('\n'.join(lines)+'\n')
        print(json.dumps(dict(status='MISSING', missing=len(missing))))
        return 3
    print(json.dumps(dict(status='PASS', captures=len(out), items=len(items), anchor_files=body['anchor_files'],
                          anchor_bytes=bytes_total, roots_used=roots, dense_all_local_captures=dense_local)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
