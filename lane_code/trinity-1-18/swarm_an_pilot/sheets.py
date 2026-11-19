"""Contact sheets for the labelling pilot (lane swarm_an). Reads frames out of tar archives (or a tar stream on stdin) and writes,
per clip, 4 JPEG sheets of 8 frames (4 x 2), each tile labelled with its sampled-frame number 1..32. Frames never land on disk.
usage: python sheets.py --clips CLIPS.json --out DIR [--map FRAME_MAP.jsonl.gz] [--tar A.tar --tar B.tar | --stdin]
CLIPS.json: {alias: {"anchors": [32 source frame indices]}} with --map (lines {"s": alias, "i": index, "sha256": ...}),
or {alias: {"shas": [32 sha256]}} without. Prints one summary line per clip and a total."""
import argparse, gzip, io, json, os, sys, tarfile
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser()
ap.add_argument('--clips'); ap.add_argument('--out'); ap.add_argument('--map'); ap.add_argument('--tar', action='append', default=[])
ap.add_argument('--stdin', action='store_true'); ap.add_argument('--tw', type=int, default=496); ap.add_argument('--th', type=int, default=372)
ap.add_argument('--quality', type=int, default=78)
a = ap.parse_args()
clips = json.load(open(a.clips)); os.makedirs(a.out, exist_ok=True)
want = {}            # sha -> list of (alias, position 0..31)
if a.map:
    key = dict(((al, i), None) for al, c in clips.items() for i in c['anchors'])
    with gzip.open(a.map, 'rt') as f:
        for l in f:
            r = json.loads(l)
            if (r['s'], r['i']) in key: key[(r['s'], r['i'])] = r['sha256']
    for al, c in clips.items(): c['shas'] = [key[(al, i)] for i in c['anchors']]
for al, c in clips.items():
    for k, s in enumerate(c['shas']):
        if s: want.setdefault(s, []).append((al, k))
tiles = {}           # (alias, k) -> JPEG bytes of the fitted tile
def fit(img):
    img = img.convert('RGB'); w, h = img.size; s = min(a.tw / float(w), a.th / float(h))
    im = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    t = Image.new('RGB', (a.tw, a.th), (0, 0, 0)); t.paste(im, ((a.tw - im.size[0]) // 2, (a.th - im.size[1]) // 2)); return t
def scan(tf):
    n = 0
    for m in tf:
        if not m.isfile(): continue
        sha = os.path.basename(m.name).split('.')[0]
        if sha in want and not all(k in tiles for k in want[sha]):
            t = fit(Image.open(io.BytesIO(tf.extractfile(m).read()))); b = io.BytesIO(); t.save(b, 'JPEG', quality=92)
            for k in want[sha]: tiles[k] = b.getvalue()
            n += 1
    return n
if a.stdin:
    print('stream members used', scan(tarfile.open(fileobj=sys.stdin.buffer, mode='r|')))
for p in a.tar:
    with tarfile.open(p) as tf: print(os.path.basename(p), 'members used', scan(tf))
try: font = ImageFont.load_default(size=30)
except TypeError: font = ImageFont.load_default()
tot = miss = 0; nbytes = 0
for al, c in sorted(clips.items()):
    have = [k for k in range(len(c['shas'])) if (al, k) in tiles]; tot += len(c['shas']); miss += len(c['shas']) - len(have)
    if len(have) < len(c['shas']):
        print('INCOMPLETE', al, len(have), 'of', len(c['shas'])); continue
    for s in range(4):
        sheet = Image.new('RGB', (4 * a.tw, 2 * a.th), (0, 0, 0)); d = ImageDraw.Draw(sheet)
        for j in range(8):
            k = s * 8 + j
            if k >= len(c['shas']): break
            x, y = (j % 4) * a.tw, (j // 4) * a.th
            sheet.paste(Image.open(io.BytesIO(tiles[(al, k)])), (x, y))
            d.rectangle([x, y, x + 150, y + 38], fill=(0, 0, 0)); d.text((x + 6, y + 2), 'frame %d' % (k + 1), fill=(255, 255, 0), font=font)
            d.rectangle([x, y, x + a.tw - 1, y + a.th - 1], outline=(255, 255, 255))
        out = os.path.join(a.out, '%s_s%d.jpg' % (al, s + 1)); sheet.save(out, 'JPEG', quality=a.quality); nbytes += os.path.getsize(out)
    print('ok', al)
print('clips', len(clips), 'frames wanted', tot, 'missing', miss, 'sheet bytes', nbytes)

