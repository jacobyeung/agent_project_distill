"""J1 step 1 (CPU, p1cpu): the 32 served anchors of relift's 46 eligible captures, checked against frame_binding_sha256 and
copied into the kit (j1/frames/<capture stub>/<slot 01..32>.png) so the GPU node needs no other frame store.

Per capture: frame_binding_sha256 = digest({anchors: FRAMES.json[native], dense: DENSE_MANIFEST[native]}) must reproduce and
equal every item's items544 mapping, the dump's metadata and lever6's FRAMES_GTC.json; the anchor indices must equal the items'
source_indices; each slot's pinned sha256 is the FRAMES.json manifest's. Sources: ScanNet and ScanNet++ from the content-
addressed store FRAMES_GTC.json names; ARKit from lever7/gtcd/arkit/frames_k6/<id>/<native index %06d>.png (OpenCV 4.14.0
re-decode). A file whose bytes do not hash to the pinned sha256 fails its capture (status SHA_MISMATCH), and nothing is
substituted. A missing file writes j1/FILES_NEEDED.md and exits 3. Writes out/FRAMES_J1.json.
Usage: CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B frames_j1.py
"""
import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import j1_common as G


def source_path(cap, frame):
    """Where the anchor's bytes come from: frames_k6 for ARKit, FRAMES_GTC's store path otherwise."""
    if cap.startswith('arkitscenes/'):
        return G.ARKIT_FRAMES/cap.split('/', 1)[1]/('%06d.png' % int(frame['index']))
    return Path(frame['path'])


def main():
    R = G.load_relift(); R.dependencies()
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, _, _ = G.eligible(R, refs)
    caps, dense = G.frame_manifests()
    depths = G.depth_rows(R)
    gtc = {c['capture']: c for c in G.read_frames_index()['captures']}
    decode = G.read_json(G.ARKIT_DECODE)
    ark_ok = {c['capture'] for c in decode['captures'] if c['status'] == 'OK'}
    out, missing, failed, total = [], [], [], 0
    for cap in sorted({i['capture'] for i in items}):
        mine = [refs[i['item_id']] for i in items if i['capture'] == cap]
        natives = {r['mapping']['native'] for r in mine}
        if len(natives) != 1:
            raise ValueError('capture maps to several natives: '+cap)
        native = natives.pop()
        bind = G.binding(native, caps, dense)
        if any(r['mapping']['frame_binding_sha256'] != bind for r in mine) or depths[cap]['metadata']['frame_binding_sha256'] != bind \
                or gtc[cap]['frame_binding_sha256'] != bind:
            raise ValueError('frame binding does not reproduce: '+cap)
        pinned = caps[native]['frames']
        if [f['index'] for f in pinned] != mine[0]['source_indices'] or any(r['source_indices'] != mine[0]['source_indices'] for r in mine):
            raise ValueError('anchor indices differ: '+cap)
        if [f['sha256'] for f in pinned] != [f['sha256'] for f in gtc[cap]['frames']]:
            raise ValueError('FRAMES_GTC slots differ from the pinned manifest: '+cap)
        if cap.startswith('arkitscenes/') and cap not in ark_ok:
            failed.append(dict(capture=cap, status='ARKIT_DECODE_NOT_OK')); continue
        frames, status = [], 'OK'
        for slot, (pf, gf) in enumerate(zip(pinned, gtc[cap]['frames']), 1):
            src = source_path(cap, gf)
            if not src.is_file():
                missing.append(dict(capture=cap, slot=slot, path=str(src), sha256=pf['sha256'])); status = 'MISSING'; continue
            got = G.sha256_file(src)
            if got != pf['sha256']:
                status = 'SHA_MISMATCH'; frames.append(dict(slot=slot, source=str(src), sha256=pf['sha256'], got=got)); continue
            dst = G.FRAMES_DIR/G.stub(cap)/('%02d.png' % slot)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.is_file() or G.sha256_file(dst) != got:
                shutil.copyfile(src, dst)
            if G.sha256_file(dst) != got:
                raise ValueError('copy differs: '+str(dst))
            n = os.path.getsize(dst); total += n
            frames.append(dict(slot=slot, index=int(pf['index']), file=str(dst.relative_to(G.ROOT)), source=str(src),
                               sha256=got, bytes=n))
        if status != 'OK':
            failed.append(dict(capture=cap, status=status)); continue
        out.append(dict(capture=cap, native=native, dataset=G.fine(cap), hw=gtc[cap]['hw'], frame_binding_sha256=bind,
                        anchor_indices=[f['index'] for f in pinned], frames=frames, items=sorted(r['item_id'] for r in mine)))
    body = dict(schema='j1-frames-v1', captures=out, failed=failed, missing=missing, anchor_files=sum(len(c['frames']) for c in out),
                anchor_bytes=total, binding_rule='digest({anchors: FRAMES.json capture, dense: DENSE_MANIFEST capture}) = '
                'parity_adapter.map_items; equal to items544, the dump and FRAMES_GTC.json',
                sources=dict(frames_json=str(G.FRAMES_JSON), frames_json_sha256=G.sha256_file(G.FRAMES_JSON),
                             dense_json=str(G.DENSE_JSON), dense_json_sha256=G.sha256_file(G.DENSE_JSON),
                             frames_gtc=str(G.FRAMES_PATH), frames_gtc_sha256=G.sha256_file(G.FRAMES_PATH),
                             arkit_frames=str(G.ARKIT_FRAMES), arkit_decode_sha256=G.sha256_file(G.ARKIT_DECODE)))
    G.write_json(G.FRAMES_J1, body)
    if missing:
        lines = ['# Files needed (J1 frames)', '', '%d anchor PNGs are not on %s.' % (len(missing), os.uname().nodename), '',
                 '| capture | slot | path | sha256 |', '|---|---|---|---|'] + \
                ['| %s | %d | %s | %s |' % (m['capture'], m['slot'], m['path'], m['sha256']) for m in missing]
        (G.ROOT/'FILES_NEEDED.md').write_text('\n'.join(lines)+'\n')
        print(json.dumps(dict(status='MISSING', missing=len(missing)))); return 3
    print(json.dumps(dict(status='PASS' if not failed else 'FAILED_CAPTURES', captures=len(out), failed=failed,
                          anchor_files=body['anchor_files'], anchor_bytes=total)))
    return 0 if not failed else 4


if __name__ == '__main__':
    sys.exit(main())
