"""Build retained 32-frame RGB anchors without consulting object-id metadata."""
import argparse
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

MDG_ROOT = Path(os.environ.get('RK_MDG_ROOT', '/scratch/jjyeung/orch_cd/mdg_next/work/c1mix_mdg_ro'))
if str(MDG_ROOT) not in sys.path:
    sys.path.insert(0, str(MDG_ROOT))
from student_pilot import mdg_eval as E
from student_pilot.p3_provenance import digest, load, write

REVSI = Path('/scratch/jjyeung/orch_cd/revsi_dev/MEMBERSHIP_REVSI_DEV_cap71.json')
DEV = Path('/scratch/jjyeung/orch_cd/evalx/work/devpool')
DATASETS = {'arkitscenes', 'scannet', 'scannetpp', '3rscan', 'multiscan'}


def scene_key(dataset, scene):
    dataset = re.sub('[^a-z0-9]', '', dataset.lower().replace('++', 'pp'))
    dataset = {'scannetv2': 'scannet', 'scannetppv2': 'scannetpp'}.get(dataset, dataset)
    if dataset not in DATASETS or not re.fullmatch(r'[A-Za-z0-9_-]+', scene):
        raise ValueError('Invalid dataset/scene')
    return dataset + '/' + scene


class RateLimitedVideo:
    """Seekable PyAV input; charge all reads to a conservative NFS rate limit."""
    def __init__(self, source, mbps=8):
        self.source = source
        self.rate = mbps * 1000 * 1000
        self.next_read = time.monotonic()

    def read(self, size=-1):
        # PyAV normally asks for 32 KB. Bound unusual reads as well.
        data = self.source.read(min(size, 1024*1024) if size >= 0 else 1024*1024)
        now = time.monotonic()
        self.next_read = max(now, self.next_read) + len(data)/self.rate
        time.sleep(max(0, self.next_read-time.monotonic()))
        return data

    def seek(self, offset, whence=0):
        return self.source.seek(offset, whence)

    def tell(self):
        return self.source.tell()


def rows_list(value):
    if isinstance(value, list):
        return value
    for key in ('items', 'rows', 'selections'):
        if key in value:
            return value[key]
    raise ValueError('Expected rows/items list')


def build_revsi(rows, videos, out, labels, *, membership=REVSI, scenes=None):
    """Names come only from labels (a scene mapping or callable), never object ids.

    Membership and nonempty question labels define scene coverage.
    At most one 32-frame clip is retained in RAM. Each source is opened once.
    """
    import av
    members = rows_list(load(membership))
    keys = sorted({scene_key(r['dataset'], r['scene']) for r in members})
    if scenes is not None:
        requested = set(scenes)
        if not requested <= set(keys):
            raise ValueError('Requested scene outside membership')
        keys = [k for k in keys if k in requested]
    cached = rows_list(load(rows)) if rows is not None and Path(rows).is_file() else members
    names = {key: sorted({E.label(n) for n in
             (labels(key, cached) if callable(labels) else labels.get(key, []))}) for key in keys}
    if scenes is not None and any(not names[key] for key in keys):
        raise ValueError('Requested scene has no labels')
    keys = [key for key in keys if names[key]]
    output, videos = Path(out), Path(videos)
    if (output/'A_MANIFEST.json').exists() or (output/'MEMBERSHIP.json').exists():
        raise FileExistsError('Anchor output already has a manifest')
    selections, items, sources = [], [], []
    for key in keys:
        ds, scene = key.split('/')
        source = videos/(scene + '.mp4')
        if not source.is_file():
            source = videos/(key + '.mp4')
        frames, arrays, count = [], [], 0
        with source.open('rb') as raw, av.open(RateLimitedVideo(raw)) as container:
            stream = container.streams.video[0]
            fps = float(stream.average_rate or stream.guessed_rate or 0)
            if not np.isfinite(fps) or fps <= 0:
                raise ValueError('Video lacks a positive stream fps: ' + str(source))
            for decoded in container.decode(stream):
                count += 1
                if count <= 32:
                    arrays.append(decoded.to_ndarray(format='rgb24'))
        if count != 32:
            raise ValueError(f'{source}: expected 32 decoded frames, got {count}')
        pixels = np.stack(arrays)
        del arrays
        target = output/'png'/ds/scene
        target.mkdir(parents=True, exist_ok=True)
        for k, array in enumerate(pixels):
            path = target/f'{k}.png'
            if path.exists():
                raise FileExistsError(path)
            Image.fromarray(array).save(path, format='PNG')
            frames.append(dict(index=k, path=f'{key}/{k}.png', sha256=E.sha256(path)))
        entry = dict(scene=key, video_rel=key+'.mp4', frame_indices=list(range(32)), fps=fps,
                     total_num_frames=32, frames=frames, anchor_pixel_sha256=E.pixel_digest(pixels),
                     duplicate_pixel_sha256=E.pixel_digest(np.repeat(pixels, 2, axis=0)))
        selections.append(entry)
        for name in names[key]:
            items.append(dict(id=digest(dict(scene=key, obj=name)), scene=key, obj=name, frame=1,
                              kind='point', **{k: entry[k] for k in
                                  ('video_rel', 'frame_indices', 'fps', 'total_num_frames')}))
        sources.append(dict(scene=key, path=str(source.resolve()), size_bytes=source.stat().st_size,
                            decoded_frames=count, fps=fps))
        del pixels
    if not selections:
        raise ValueError('No selected scenes')
    write(output/'A_MANIFEST.json', dict(selections=selections))
    write(output/'MEMBERSHIP.json', dict(items=items))
    write(output/'SOURCES.json', dict(videos=sources))
    E.manifest_entries(output/'A_MANIFEST.json')
    return dict(scenes=len(selections), items=len(items), sources=sources)


def build_dev(a_manifest, membership, scenes, out, labels=None):
    """With labels (scene key -> names, from `rk.sets labels --set dev`) the export grounds only the dev questions'
    objects, one frame-1 item per name; otherwise it keeps the dev scenes' rows of the pointing membership."""
    if labels is not None:
        wanted = set(labels)
    else:
        value = load(scenes)
        wanted = value['scenes'] if isinstance(value, dict) else value
        wanted = {s if '/' in s else 'scannet/'+s for s in wanted}
    entries = E.manifest_entries(a_manifest)
    selected = [e for e in entries.values() if e['scene'] in wanted]
    missing = wanted - {e['scene'] for e in selected}
    if missing:
        raise ValueError('Missing dev anchors: '+', '.join(sorted(missing)))
    if labels is not None:
        items = [dict(id=digest(dict(scene=e['scene'], obj=name)), scene=e['scene'], obj=name, frame=1, kind='point',
                      **{k: e[k] for k in ('video_rel', 'frame_indices', 'fps', 'total_num_frames')})
                 for e in sorted(selected, key=lambda e: e['scene']) for name in labels[e['scene']]]
    else:
        items = [r for r in E.members(membership) if r['scene'] in wanted]
    subset = {E.selection_id(e): e for e in selected}
    for row in items:
        E.selection_for(row, subset)
    output = Path(out)
    write(output/'A_MANIFEST.json', dict(selections=selected))
    write(output/'MEMBERSHIP.json', dict(items=items))
    return dict(scenes=len(wanted), selections=len(selected), items=len(items),
                png_root='Use the original anchor PNG root; frame paths are preserved.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    rev = sub.add_parser('revsi')
    rev.add_argument('--rows', default='rk/data/revsi_cap71_rows.json')
    rev.add_argument('--membership', default=str(REVSI))
    rev.add_argument('--videos', required=True)
    rev.add_argument('--labels', required=True, help='JSON scene key -> list of object names')
    rev.add_argument('--scene', action='append', help='Optional bounded scene subset')
    rev.add_argument('--out', required=True)
    dev = sub.add_parser('dev')
    dev.add_argument('--a-manifest', required=True)
    dev.add_argument('--membership', default=str(DEV/'GROUND_MEMBERSHIP.json'))
    dev.add_argument('--scenes', default=str(DEV/'DEV_SCENES.json'))
    dev.add_argument('--labels', help='JSON scene key -> names; replaces the membership rows')
    dev.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    if args.command == 'revsi':
        result = build_revsi(args.rows, args.videos, args.out, load(args.labels),
                             membership=args.membership, scenes=args.scene)
    else:
        result = build_dev(args.a_manifest, args.membership, args.scenes, args.out,
                           load(args.labels) if args.labels else None)
    print(E.encoded(result))
    return result


if __name__ == '__main__':
    main()
