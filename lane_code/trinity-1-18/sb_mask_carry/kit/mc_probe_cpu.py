"""Dry-run item 4a: load SAM 3's video model from the pinned checkpoint on CPU, embed 8 frames, track one raster seed.

Usage: python mc_probe_cpu.py <capture> <name> <out.json>. A failure is written with its traceback, never retried.
"""
import json, resource, sys, time, traceback
import numpy as np
import mc_common as C


def window(slots, center, n=8):
    lo = max(0, min(center-n//2+1, len(slots)-n))
    return list(range(lo, lo+n))


def main():
    capture, name, dest = sys.argv[1], sys.argv[2], sys.argv[3]
    rec = dict(stage='sam3_cpu_probe', capture=capture, name=name, status='STARTED')
    t0 = time.monotonic()
    try:
        manifest = C.read_json(C.BOX/'pinned_train.json')
        c = next(c for c in manifest['captures'] if c['canonical'] == capture)
        z = np.load(C.local(c['gt']['path']))
        C.read(c['gt']['path'])
        iid = c['gt_name_ids'][name][0]
        inst, valid = z['inst'], z['valid'].astype(bool)
        share = [(float(np.mean(inst[f] == iid)) if valid[f] else 0., f) for f in range(32)]
        best = max(share, key=lambda x: (x[0], -x[1]))[1]
        seed = C.nearest(inst[best] == iid, C.CANVAS)
        dense = c['dense_frames']
        center = c['anchor_slots'][best]
        frames = window(dense, center)
        import torch
        torch.set_num_threads(8)
        from mc_tracker import Sam3Carry
        tracker = Sam3Carry('cpu')
        rec.update(load_seconds=tracker.load_seconds, shims=tracker.shims, modules_outside_scratch=tracker.outside,
                   parameters=int(sum(p.numel() for p in tracker.model.parameters())),
                   dtype=str(next(tracker.model.parameters()).dtype))
        t1 = time.monotonic()
        images = tracker.frames([dense[i]['path'] for i in frames], [dense[i]['sha256'] for i in frames])
        cache, hw = tracker.embed(images)
        rec.update(embed_seconds=time.monotonic()-t1, frames=frames, video_hw=hw)
        t2 = time.monotonic()
        out = tracker.track(cache, frames.index(center), seed)
        rec['track_seconds'] = time.monotonic()-t2
        anchors = {c['anchor_slots'].index(d): k for k, d in enumerate(frames) if d in c['anchor_slots']}
        per = []
        for slot, k in sorted(anchors.items()):
            m, score = out[k]
            truth = C.nearest(inst[slot] == iid, C.CANVAS)
            per.append(dict(anchor=slot+1, dense_slot=frames[k], object_score=score, carried=score > 0,
                            area=float(m.mean()), iou=C.iou(m, truth), raster_share=share[slot][0], seed=slot == best))
        rec.update(status='PASS', seed_anchor=best+1, anchors=per,
                   scores=[out[k][1] for k in range(len(frames))])
    except Exception as exc:
        rec.update(status='FAIL', error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc())
    rec.update(seconds=time.monotonic()-t0, peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    C.write_json(dest, rec)
    print(json.dumps({k: rec.get(k) for k in ['status', 'error', 'load_seconds', 'embed_seconds', 'track_seconds', 'seconds', 'peak_rss_mib']}), flush=True)


if __name__ == '__main__':
    main()
