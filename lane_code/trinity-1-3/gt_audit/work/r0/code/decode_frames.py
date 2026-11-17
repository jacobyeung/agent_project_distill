"""Decode R0 student frames from a ScanNet++ iphone rgb.mkv into 640x480 PNGs (trained layout).

Layouts: floor(linspace(0, total-1, n)) for n in 32 and 64; total = frames in pose_intrinsic_imu.json, checked against
the decoded frame count. Decoding is sequential (every frame decoded, only layout frames converted) with PyAV
(pinned in the manifest) and swscale bicubic resize to 640x480 rgb24, then PNG (PIL, compress_level 6).
usage: decode_frames.py SCENE_DIR OUT_DIR MANIFEST.json
"""
import hashlib, io, json, os, sys
import av, numpy as np, PIL
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r0lib  # noqa: E402

W, H = 640, 480


def total_from_pose(sdir):
    with open(os.path.join(sdir, 'iphone', 'pose_intrinsic_imu.json')) as f:
        return len(json.load(f))


def decode(mkv, want, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    want = sorted(set(want)); ws = set(want); got = {}; n = 0
    with av.open(mkv) as c:
        st = c.streams.video[0]; st.thread_type = 'AUTO'
        info = dict(codec=st.codec_context.name, width=st.codec_context.width, height=st.codec_context.height,
                    rate=str(st.average_rate), declared_frames=int(st.frames))
        for fr in c.decode(st):
            if n in ws:
                rgb = fr.reformat(width=W, height=H, format='rgb24', interpolation='BICUBIC').to_ndarray()
                buf = io.BytesIO(); Image.fromarray(rgb).save(buf, format='PNG', compress_level=6)
                b = buf.getvalue(); p = os.path.join(out_dir, '%06d.png' % n)
                with open(p, 'wb') as f:
                    f.write(b)
                got[n] = hashlib.sha256(b).hexdigest()
            n += 1
    return n, got, info


def main(sdir, out_dir, manifest, mkv=None):
    total = total_from_pose(sdir)
    lay = {n: r0lib.layout(total, n) for n in (32, 64)}
    decoded, got, info = decode(mkv or os.path.join(sdir, 'iphone', 'rgb.mkv'), lay[32] + lay[64], out_dir)
    rec = dict(scene=os.path.basename(os.path.normpath(sdir)), total_pose=total, total_decoded=decoded,
               count_match=decoded == total, layout_f32=lay[32], layout_f64=lay[64], video=info, frames=got,
               missing=[i for i in sorted(set(lay[32] + lay[64])) if i not in got], size=[W, H],
               lib=dict(av=av.__version__, ffmpeg=av.library_versions.get('libavcodec'), pil=PIL.__version__, numpy=np.__version__),
               rule=__doc__.strip().splitlines()[0])
    json.dump(rec, open(manifest, 'w'), indent=0, sort_keys=True)
    print(json.dumps({k: rec[k] for k in ('scene', 'total_pose', 'total_decoded', 'count_match', 'missing')}))
    return rec


if __name__ == '__main__':
    main(*sys.argv[1:4])
