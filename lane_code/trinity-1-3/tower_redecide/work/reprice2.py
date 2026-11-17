"""Unregistered sensitivity: the GEO C-rule with the deployed G3T geometry (GD_reviewed) as the reference (lane tower_redecide).

Distance on corrected K1 labels (as priced: refusals score 0; and refusal-neutral: rows both arms answer); room R0 against
GD_reviewed+R0 (room labels are unaffected by the half-extent defect). Guard: other-type train lower bound >= -2.
Also reports GD's mean on the held-out rows each candidate refuses.
"""
import collections, json, os, sys
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/tower_redecide/work')
import reprice as R

D = R.D
W = R.W
CANDS = ['pi3x_native', 'da3_native', 'moge2_scale']


def load_rows():
    rows = []
    for f in sorted(os.listdir(os.path.join(W, 'caps_corrected'))):
        rows += json.load(open(os.path.join(W, 'caps_corrected', f)))['items']
    for l in open(R.GD):
        r = json.loads(l)
        if r['arm'].startswith('GD_reviewed'):
            rows.append(R.fix(r, 'corrected'))
    return rows


def vals(rows, typ, split, arms):
    by = collections.defaultdict(dict)
    for r in rows:
        if r['type'] == typ and r['split'] == split:
            by[r['arm']][r['row_id']] = r
    gt = 'GT' if typ == R.DIST else 'GT+R0'
    ids = sorted(by[gt]); rooms = [by[gt][i]['room'] for i in ids]
    v = {a: np.array([by[a][i]['mra'] if i in by[a] else 0. for i in ids]) for a in arms}
    ok = {a: np.array([i in by[a] and by[a][i]['refusal_code'] is None and by[a][i]['pred'] is not None for i in ids]) for a in arms}
    return ids, rooms, v, ok, by


def diff(v, ok, rooms, a, ref, neutral):
    m = ok[a] & ok[ref] if neutral else np.ones(len(rooms), bool)
    d = v[a][m] - v[ref][m]; rr = [rooms[k] for k in np.flatnonzero(m)]
    return dict(mean=float(100 * d.mean()), ci95=D.interval(d, rr, R.DRAWS), n=int(m.sum()))


def main():
    rows = load_rows()
    out = {}
    for neutral in (False, True):
        tag = 'refusal_neutral' if neutral else 'as_priced'
        dec = {}
        for c in CANDS:
            rec = {}
            for typ, arm, ref in ((R.DIST, c, 'GD_reviewed'), ('room_size_estimation', c + '+R0', 'GD_reviewed+R0')):
                t = {}
                for split in ('train', 'heldout'):
                    ids, rooms, v, ok, by = vals(rows, typ, split, [arm, ref])
                    t[split] = diff(v, ok, rooms, arm, ref, neutral)
                    t[split + '_mean_arm'] = float(100 * v[arm].mean()); t[split + '_mean_ref'] = float(100 * v[ref].mean())
                t['qualifies'] = t['train']['ci95'][0] > 0 and t['heldout']['mean'] > 0
                rec[typ] = t
            q = [t for t in (R.DIST, 'room_size_estimation') if rec[t]['qualifies']]
            rec['guard_ok'] = all(rec[o]['train']['ci95'][0] >= -2 for t in q for o in (R.DIST, 'room_size_estimation') if o != t)
            rec['replaces_g3t'] = bool(q) and rec['guard_ok']
            dec[c] = rec
        win = {}
        for typ in (R.DIST, 'room_size_estimation'):
            qual = sorted(((dec[c][typ]['train_mean_arm'], c) for c in CANDS if dec[c][typ]['qualifies']), reverse=True)
            win[typ] = (qual[0][1] if dec[qual[0][1]]['replaces_g3t'] else 'G3T (top qualifier fails guard: %s)' % qual[0][1]) if qual else 'G3T'
        out[tag] = dict(decision=dec, winners=win)
        print('###', tag, 'winners', win)
        for c in CANDS:
            for typ in (R.DIST, 'room_size_estimation'):
                t = dec[c][typ]
                print(f"  {c:12s} {typ[:8]:8s} train {t['train_mean_arm']:6.2f} vs {t['train_mean_ref']:6.2f}: {t['train']['mean']:+6.2f} [{t['train']['ci95'][0]:+6.2f},{t['train']['ci95'][1]:+6.2f}] n={t['train']['n']}"
                      f" | heldout {t['heldout_mean_arm']:6.2f} vs {t['heldout_mean_ref']:6.2f}: {t['heldout']['mean']:+6.2f} [{t['heldout']['ci95'][0]:+6.2f},{t['heldout']['ci95'][1]:+6.2f}] n={t['heldout']['n']} qual={t['qualifies']}")
            print(f"  {c:12s} guard_ok={dec[c]['guard_ok']} replaces_g3t={dec[c]['replaces_g3t']}")
    ids, rooms, v, ok, by = vals(rows, R.DIST, 'heldout', ['GD_reviewed', 'pi3x_native', 'da3_native', 'S4+G1'])
    for a in ('pi3x_native', 'da3_native', 'S4+G1'):
        m = ~ok[a]
        out['gd_on_refused_' + a] = dict(n=int(m.sum()), gd_mean=float(100 * v['GD_reviewed'][m].mean()) if m.any() else None,
                                         gd_mean_on_answered=float(100 * v['GD_reviewed'][~m].mean()),
                                         arm_mean_on_answered=float(100 * v[a][~m].mean()))
        print('held-out rows refused by', a, out['gd_on_refused_' + a])
    json.dump(out, open(os.path.join(W, 'GD_REFERENCE_SENSITIVITY.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
