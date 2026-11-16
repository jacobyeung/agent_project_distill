"""Apply the pre-registered C-rule (GEO_TOWERS_K1_PREREG_20261116.md) to k1_price output via E3's agg.py.

Usage: python decide.py CAPTURES_DIR FITS OUT.json [--heldout-go FILE]
Train tables are always computed. Held-out tables are computed only with --heldout-go naming an ORCH note that
holds a line 'GO heldout' (written after the independent review). Reference: S4+G1 (distance), S4+G1+R0 (room).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = {'moge2': 'moge2_scale', 'mapanything': 'mapanything_native', 'da3': 'da3_native', 'pi3x': 'pi3x_native'}
REF = 'S4+G1'
LINE = re.compile(r'^(\S+)\s+(-?[\d.]+) \[\s*(-?[\d.]+),\s*(-?[\d.]+)\] ref=(\d+)(.*)$')
DIFF = re.compile(r'\| vs (\S+): ([-+][\d.]+) \[([-+][\d.]+),([-+][\d.]+)\]')


def table(caps, split, fits, agg):
    text = subprocess.run([sys.executable, '-B', str(agg), caps, split, fits, REF], check=True,
                          capture_output=True, text=True).stdout
    out, typ = {}, None
    for line in text.splitlines():
        if line.startswith('## '):
            typ = line.split()[1]
            out[typ] = dict(header=line, arms={})
            continue
        m = LINE.match(line)
        if m and typ:
            arm = dict(mean=float(m[2]), lo=float(m[3]), hi=float(m[4]), refusals=int(m[5]))
            d = DIFF.search(m[6])
            if d:
                arm.update(vs=d[1], diff=float(d[2]), diff_lo=float(d[3]), diff_hi=float(d[4]))
            out[typ]['arms'][m[1]] = arm
    return text, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('captures'); ap.add_argument('fits'); ap.add_argument('out')
    ap.add_argument('--agg', default=str(HERE / 'agg.py'))
    ap.add_argument('--heldout-go')
    a = ap.parse_args()
    splits = ['train']
    if a.heldout_go:
        if not any(l.strip() == 'GO heldout' for l in Path(a.heldout_go).read_text().splitlines()):
            raise PermissionError('held-out tables need an ORCH note with a "GO heldout" line')
        splits.append('heldout')
    res = dict(prereg_sha256='dd40e6d26a723300547c84b72add275bd2488993c2f70cd1b64fba7ae29b5c88', reference=REF, tables={}, raw={})
    for s in splits:
        res['raw'][s], res['tables'][s] = table(a.captures, s, a.fits, a.agg)
    tr = res['tables']['train']; ho = res['tables'].get('heldout')
    keys = {'object_abs_distance': '', 'room_size_estimation': '+R0'}
    dec = {}
    for m, arm in PRIMARY.items():
        d = {}
        for typ, suf in keys.items():
            t = tr.get(typ, {}).get('arms', {}).get(arm + suf)
            if not t:
                d[typ] = dict(status='absent'); continue
            row = dict(train_mean=t['mean'], train_diff=t.get('diff'), train_diff_lo=t.get('diff_lo'))
            if ho:
                h = ho.get(typ, {}).get('arms', {}).get(arm + suf, {})
                ref = ho.get(typ, {}).get('arms', {}).get(REF + suf, {})
                row.update(heldout_mean=h.get('mean'), heldout_diff=h.get('diff'))
                row['qualifies'] = bool(row['train_diff_lo'] is not None and row['train_diff_lo'] > 0
                                        and h.get('diff') is not None and h['diff'] > 0)
                if typ == 'object_abs_distance':
                    row['bar'] = (ref.get('mean') or 0) + 5
                else:
                    row['bar'], row['bar_sensitivity'] = 73.4, 79.0
                row['clears_bar'] = h.get('mean') is not None and h['mean'] >= row['bar']
            d[typ] = row
        if ho:
            q = [t for t in keys if d[t].get('qualifies')]
            other_ok = all((d[o].get('train_diff_lo') or -1e9) >= -2 for t in q for o in keys if o != t)
            d['replaces_g3t_candidate'] = bool(q) and other_ok
        dec[m] = d
    if ho:
        cands = [m for m in dec if dec[m].get('replaces_g3t_candidate')]
        res['winner'] = max(cands, key=lambda m: max(dec[m][t]['train_mean'] for t in keys if dec[m][t].get('qualifies')),
                            default='G3T')
    res['decision'] = dec
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(dec, indent=1)); print(res.get('winner', 'heldout not read'))


if __name__ == '__main__':
    main()
