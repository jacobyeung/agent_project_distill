"""Run gen_questions or decode_frames over R0 ScanNet++ full-GT captures, in parallel, skipping finished outputs.

usage: run_scenes.py gen|decode [--workers N] [--split R0-dev|R0-rl|all]
gen    -> out/questions/<scene>.jsonl  (+ out/questions_meta/<scene>.json); R0-dev caps x1, R0-rl caps x3
decode -> frames/scannetpp/<scene>/*.png + out/frame_manifests/<scene>.json
Run only after the stream carrying the inputs has exited 0 (a scene's files may be partial while tar writes them).
"""
import argparse, contextlib, io, json, os, sys, traceback
from multiprocessing import Pool
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(L, 'code'))
DATA = os.path.join(L, 'data_cache', 'scannetpp')


def job(arg):
    mode, scene, split = arg
    import gen_questions, decode_frames
    sdir = os.path.join(DATA, scene)
    try:
        if mode == 'gen':
            out = os.path.join(L, 'out', 'questions', scene + '.jsonl')
            if os.path.exists(out):
                return scene, 'skip'
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                gen_questions.main(sdir, split, 1 if split == 'R0-dev' else 3, out + '.part')
            os.replace(out + '.part', out)
            open(os.path.join(L, 'out', 'questions_meta', scene + '.json'), 'w').write(buf.getvalue())
            return scene, 'ok ' + buf.getvalue().strip()[:200]
        out = os.path.join(L, 'out', 'frame_manifests', scene + '.json')
        if os.path.exists(out):
            return scene, 'skip'
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rec = decode_frames.main(sdir, os.path.join(L, 'frames', 'scannetpp', scene), out + '.part')
        if not rec['count_match'] or rec['missing']:
            return scene, 'BAD ' + buf.getvalue().strip()
        os.replace(out + '.part', out)
        return scene, 'ok ' + buf.getvalue().strip()
    except Exception:
        return scene, 'ERROR ' + traceback.format_exc()[-1500:]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=('gen', 'decode'))
    ap.add_argument('--workers', type=int, default=12); ap.add_argument('--split', default='all')
    a = ap.parse_args()
    for d in ('questions', 'questions_meta', 'frame_manifests'):
        os.makedirs(os.path.join(L, 'out', d), exist_ok=True)
    r0 = json.load(open(os.path.join(L, 'out', 'R0_SCENES.json')))
    todo = sorted((a.mode, k.split('/')[1], c['r0_split']) for k, c in r0['captures'].items()
                  if c['dataset'] == 'scannetpp' and c['gt_level'] == 'full' and (a.split == 'all' or c['r0_split'] == a.split))
    todo.sort(key=lambda t: (t[2] != 'R0-dev', t[1]))
    if a.mode == 'decode':  # progressive: only scenes whose rgb.mkv has reached its source size
        assets = json.load(open(os.path.join(L, 'out', 'scannetpp_assets.json')))
        def ready(s):
            f = os.path.join(DATA, s, 'iphone', 'rgb.mkv')
            return os.path.exists(f) and os.path.getsize(f) == assets[s]['iphone/rgb.mkv'] and os.path.exists(os.path.join(DATA, s, 'iphone', 'pose_intrinsic_imu.json'))
        todo = [t for t in todo if ready(t[1])]
    log = open(os.path.join(L, 'work', 'run_%s.log' % a.mode), 'a')
    with Pool(a.workers) as p:
        for scene, msg in p.imap_unordered(job, todo):
            log.write('%s %s\n' % (scene, msg)); log.flush()
    print('done', len(todo))


if __name__ == '__main__':
    main()
