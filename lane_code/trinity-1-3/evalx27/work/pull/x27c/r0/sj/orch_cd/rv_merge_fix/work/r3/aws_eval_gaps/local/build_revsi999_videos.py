"""Pin the landed official ReVSI videos of one tier: local/build_revsi999_videos.py VIDEO_DIR TIER -> inputs/revsi999_videos_t<TIER>.json.

Every scene of the 999 must be present as <scene>.mp4 and decode to exactly TIER frames (checked with PyAV when available)."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(video_dir, tier):
    tier = int(tier)
    rows = json.loads((ROOT/f'inputs/revsi999_rows_t{tier}.json').read_text())
    files = {}
    for scene in sorted({r['scene'] for r in rows}):
        p = Path(video_dir)/(scene+'.mp4'); raw = p.read_bytes()
        files[scene] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        try:
            import av
        except ImportError:
            continue
        with av.open(str(p)) as c:
            n = sum(1 for _ in c.decode(video=0))
        if n != tier: raise SystemExit(f'{scene}: {n} frames, tier {tier}')
        files[scene]['frames'] = n
    out = ROOT/f'inputs/revsi999_videos_t{tier}.json'
    out.write_text(json.dumps(dict(tier=tier, source=str(video_dir), files=files), indent=0, sort_keys=True)+'\n')
    print(out.name, hashlib.sha256(out.read_bytes()).hexdigest(), len(files))


if __name__ == '__main__':
    main(*sys.argv[1:3])
