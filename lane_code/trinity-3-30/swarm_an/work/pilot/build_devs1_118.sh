set -u
W=/scratch/jjyeung/orch_n30/swarm_an_pilot; mkdir -p $W/devs1
cat > $W/sheets.py <<'PYEOF'
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

PYEOF
cat > $W/devs1_spec.json <<'JSEOF'
{"v495102e2dd15": {"anchors": [0, 444, 889, 1334, 1779, 2224, 2669, 3114, 3559, 4004, 4449, 4893, 5338, 5783, 6228, 6673, 7118, 7563, 8008, 8453, 8898, 9342, 9787, 10232, 10677, 11122, 11567, 12012, 12457, 12902, 13347, 13792]}, "v01b11f30bc97": {"anchors": [0, 717, 1435, 2153, 2870, 3588, 4306, 5023, 5741, 6459, 7177, 7894, 8612, 9330, 10047, 10765, 11483, 12201, 12918, 13636, 14354, 15071, 15789, 16507, 17225, 17942, 18660, 19378, 20095, 20813, 21531, 22249]}, "v2833ae71ea9f": {"anchors": [0, 75, 151, 227, 302, 378, 454, 529, 605, 681, 756, 832, 908, 983, 1059, 1135, 1210, 1286, 1362, 1437, 1513, 1589, 1664, 1740, 1816, 1891, 1967, 2043, 2118, 2194, 2270, 2346]}, "v29047ab90731": {"anchors": [0, 377, 754, 1131, 1508, 1885, 2262, 2639, 3016, 3393, 3770, 4147, 4524, 4901, 5278, 5655, 6032, 6409, 6786, 7163, 7540, 7917, 8294, 8671, 9048, 9425, 9802, 10179, 10556, 10933, 11310, 11687]}, "v073865611e37": {"anchors": [0, 136, 272, 408, 544, 680, 817, 953, 1089, 1225, 1361, 1498, 1634, 1770, 1906, 2042, 2179, 2315, 2451, 2587, 2723, 2860, 2996, 3132, 3268, 3404, 3541, 3677, 3813, 3949, 4085, 4222]}, "v1f05547c1b67": {"anchors": [0, 74, 149, 224, 299, 374, 449, 524, 599, 674, 749, 824, 899, 974, 1049, 1124, 1199, 1274, 1349, 1424, 1499, 1574, 1649, 1724, 1799, 1874, 1949, 2024, 2099, 2174, 2249, 2324]}, "va28ddcd4c020": {"anchors": [0, 337, 674, 1011, 1348, 1685, 2022, 2360, 2697, 3034, 3371, 3708, 4045, 4383, 4720, 5057, 5394, 5731, 6068, 6406, 6743, 7080, 7417, 7754, 8091, 8429, 8766, 9103, 9440, 9777, 10114, 10452]}, "v0a20639f3e2b": {"anchors": [0, 413, 826, 1239, 1653, 2066, 2479, 2892, 3306, 3719, 4132, 4545, 4959, 5372, 5785, 6198, 6612, 7025, 7438, 7851, 8265, 8678, 9091, 9504, 9918, 10331, 10744, 11157, 11571, 11984, 12397, 12811]}, "v2b064520b5a1": {"anchors": [0, 435, 870, 1305, 1740, 2175, 2610, 3045, 3480, 3915, 4350, 4785, 5220, 5655, 6090, 6525, 6960, 7395, 7830, 8265, 8700, 9135, 9570, 10005, 10440, 10875, 11310, 11745, 12180, 12615, 13050, 13486]}, "vc80d5683cd2a": {"anchors": [0, 255, 510, 765, 1020, 1275, 1530, 1785, 2040, 2295, 2550, 2806, 3061, 3316, 3571, 3826, 4081, 4336, 4591, 4846, 5101, 5357, 5612, 5867, 6122, 6377, 6632, 6887, 7142, 7397, 7652, 7908]}, "v179cffe696d9": {"anchors": [0, 224, 449, 674, 899, 1124, 1349, 1574, 1799, 2024, 2249, 2473, 2698, 2923, 3148, 3373, 3598, 3823, 4048, 4273, 4498, 4722, 4947, 5172, 5397, 5622, 5847, 6072, 6297, 6522, 6747, 6972]}, "v3cfbd8882289": {"anchors": [0, 378, 756, 1135, 1513, 1892, 2270, 2648, 3027, 3405, 3784, 4162, 4541, 4919, 5297, 5676, 6054, 6433, 6811, 7189, 7568, 7946, 8325, 8703, 9082, 9460, 9838, 10217, 10595, 10974, 11352, 11731]}, "v1c251118de59": {"anchors": [0, 85, 170, 255, 340, 425, 510, 595, 680, 765, 850, 935, 1020, 1105, 1190, 1275, 1360, 1445, 1530, 1615, 1700, 1785, 1870, 1955, 2040, 2125, 2210, 2295, 2380, 2465, 2550, 2636]}, "v40e256cd6056": {"anchors": [0, 485, 970, 1455, 1940, 2425, 2910, 3395, 3880, 4365, 4850, 5335, 5820, 6305, 6790, 7275, 7760, 8245, 8730, 9215, 9700, 10185, 10670, 11155, 11640, 12125, 12610, 13095, 13580, 14065, 14550, 15036]}, "v918fd0be1f8f": {"anchors": [0, 103, 206, 309, 412, 515, 619, 722, 825, 928, 1031, 1134, 1237, 1340, 1443, 1546, 1650, 1753, 1856, 1959, 2062, 2165, 2268, 2371, 2474, 2577, 2681, 2784, 2887, 2990, 3093, 3196]}, "v4385d1646505": {"anchors": [0, 272, 545, 817, 1090, 1362, 1635, 1908, 2180, 2453, 2725, 2998, 3270, 3543, 3816, 4088, 4361, 4633, 4906, 5179, 5451, 5724, 5996, 6269, 6541, 6814, 7087, 7359, 7632, 7904, 8177, 8450]}, "v2305177609f5": {"anchors": [0, 60, 121, 182, 242, 303, 364, 425, 485, 546, 607, 668, 728, 789, 850, 911, 971, 1032, 1093, 1154, 1214, 1275, 1336, 1397, 1457, 1518, 1579, 1640, 1700, 1761, 1822, 1883]}, "v7c30bd2aafd8": {"anchors": [0, 124, 249, 374, 499, 624, 749, 874, 999, 1124, 1249, 1374, 1499, 1624, 1749, 1874, 1999, 2124, 2249, 2374, 2499, 2624, 2749, 2874, 2999, 3124, 3249, 3374, 3499, 3624, 3749, 3874]}, "v0484391feb7c": {"anchors": [0, 30, 59, 89, 118, 148, 177, 207, 236, 266, 295, 325, 354, 384, 413, 443, 472, 502, 531, 561, 590, 620, 649, 679, 708, 738, 767, 797, 826, 856, 885, 915]}, "v0f24266bb01a": {"anchors": [0, 83, 167, 250, 334, 417, 501, 585, 668, 752, 835, 919, 1002, 1086, 1170, 1253, 1337, 1420, 1504, 1588, 1671, 1755, 1838, 1922, 2005, 2089, 2173, 2256, 2340, 2423, 2507, 2591]}, "v13a3de1af2bd": {"anchors": [0, 575, 1151, 1727, 2302, 2878, 3454, 4029, 4605, 5181, 5757, 6332, 6908, 7484, 8059, 8635, 9211, 9787, 10362, 10938, 11514, 12089, 12665, 13241, 13817, 14392, 14968, 15544, 16119, 16695, 17271, 17847]}, "v1f03074675d4": {"anchors": [0, 66, 133, 199, 266, 332, 398, 465, 531, 597, 664, 730, 797, 863, 929, 996, 1062, 1129, 1195, 1261, 1328, 1394, 1461, 1527, 1593, 1660, 1726, 1792, 1859, 1925, 1992, 2058]}, "v7856fc13c7e0": {"anchors": [0, 296, 593, 890, 1186, 1483, 1780, 2076, 2373, 2670, 2966, 3263, 3560, 3856, 4153, 4450, 4746, 5043, 5340, 5636, 5933, 6230, 6526, 6823, 7120, 7416, 7713, 8010, 8306, 8603, 8900, 9197]}, "v862c0990c252": {"anchors": [0, 86, 173, 260, 347, 434, 521, 608, 695, 782, 869, 955, 1042, 1129, 1216, 1303, 1390, 1477, 1564, 1651, 1738, 1824, 1911, 1998, 2085, 2172, 2259, 2346, 2433, 2520, 2607, 2694]}}
JSEOF
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
R=/scratch/jjyeung/orch_n30/trin_read/root/k6tk/parts
nice -n 10 /scratch/jjyeung/envs/planner_local_v1/bin/python $W/sheets.py --clips $W/devs1_spec.json --out $W/devs1 --map /scratch/jjyeung/orch_n30/sb_framepool/work/frame_map.jsonl.gz --tar $R/t3ecb8dfaec72452681be8e6f9aefb17a/t3ecb8dfaec72452681be8e6f9aefb17a_000.tar --tar $R/t7e4068331d564270a404fa8e6d834691/t7e4068331d564270a404fa8e6d834691_000.tar 2>&1 | tail -32
cd $W && tar cf devs1_sheets.tar devs1 && ls -la devs1_sheets.tar | cut -c20-100 && sha256sum devs1_sheets.tar | cut -c1-64 && ls devs1 | wc -l
