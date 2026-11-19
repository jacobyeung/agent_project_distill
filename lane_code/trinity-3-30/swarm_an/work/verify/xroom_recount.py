"""Recount of deep3_xroom: room effect under two statistics, duration correlation, priced loss in the worst fifth of rooms."""
import sys, random, collections, math
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
DD = collections.defaultdict
def mean(v): return sum(v) / float(len(v))
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r
def pear(a, b):
    ma, mb = mean(a), mean(b); sa = sum((x - ma) ** 2 for x in a) ** 0.5; sb = sum((x - mb) ** 2 for x in b) ** 0.5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)
random.seed(5)
for st in ['R0-dev', 'dev-S1']:
    rs = K.direct('R1', 200, st); tm = DD(list)
    for r in rs: tm[r['type']].append(r['score'])
    mu = dict((t, mean(v)) for t, v in tm.items())
    res = [(r['score'] - mu[r['type']], r['room'], r['type'], r) for r in rs]
    def stats(vals):
        per = DD(list)
        for v, (x, room, t, r) in zip(vals, res): per[room].append(v)
        ms = [mean(v) for v in per.values()]; m0 = mean(ms)
        unw = mean([(m - m0) ** 2 for m in ms])                      # the analyst's statistic: variance of room means, rooms equal
        wtd = sum(len(v) * mean(v) ** 2 for v in per.values()) / len(vals)   # item-weighted between-room sum of squares
        return unw, wtd
    obs = stats([x[0] for x in res]); byt = DD(list)
    for i, x in enumerate(res): byt[x[2]].append(i)
    sh = []
    for _ in range(500):
        vals = [x[0] for x in res]
        for t, idx in byt.items():
            vv = [res[i][0] for i in idx]; random.shuffle(vv)
            for i, v in zip(idx, vv): vals[i] = v
        sh.append(stats(vals))
    for k, name in [(0, 'rooms weighted equally'), (1, 'rooms weighted by items')]:
        print('%-7s %-24s observed %.5f shuffle mean %.5f p %.3f' % (st, name, obs[k], mean([s[k] for s in sh]), (1 + sum(s[k] >= obs[k] for s in sh)) / 501.0))
    per = DD(list)
    for x in res: per[x[1]].append(x)
    print('   rooms', len(per), 'items per room: min %d median %d max %d; rooms under 5 items: %d' % (min(len(v) for v in per.values()), sorted(len(v) for v in per.values())[len(per) // 2], max(len(v) for v in per.values()), sum(len(v) < 5 for v in per.values())))
    tim = K.timing('R1', 200, st); dur = {}
    for x in res:
        t = tim.get(x[3]['id'])
        if t and t.get('timestamps_s'): dur[x[1]] = max(t['timestamps_s'])
    rooms = [r for r in per if r in dur]
    rho = pear(rank([dur[r] for r in rooms]), rank([mean([x[0] for x in per[r]]) for r in rooms]))
    print('   duration against the room mean: Spearman %.3f over %d rooms; median duration %.0f s' % (rho, len(rooms), sorted(dur.values())[len(dur) // 2]))
    srt = sorted(rooms, key=lambda r: dur[r]); n3 = len(srt) // 3
    for name, grp in [('shortest third', srt[:n3]), ('middle', srt[n3:2 * n3]), ('longest third', srt[2 * n3:])]:
        it = [x for r in grp for x in per[r]]
        print('      %-14s rooms %d, %.0f to %.0f s, items %d, mean residual %+.3f' % (name, len(grp), dur[grp[0]], dur[grp[-1]], len(it), mean([x[0] for x in it])))
    if st == 'R0-dev':
        leaf = DD(list)
        def leafkey(r):
            t, s = r['type'], r.get('subtype')
            if t == 'object_counting': return ('counting', s, 0.5)
            if t == 'object_rel_distance': return ('reldist', s, 0.5)
            if t == 'object_size_estimation': return ('size', None, 1.0)
            if t in ('object_rel_direction_easy', 'object_rel_direction_hard'): return ('direction', t[-4:] + str(s), 0.25)
            return None
        for r in rs:
            k = leafkey(r)
            if k: leaf[k].append(r)
        w = {}
        for k, v in leaf.items():
            for r in v: w[r['id']] = 100.0 * k[2] / 7.0 / len(v)
        tot = sum(w.get(r['id'], 0) * (1 - r['score']) for r in rs)
        worst = sorted(per, key=lambda r: mean([x[0] for x in per[r]]))[:20]
        part = sum(w.get(x[3]['id'], 0) * (1 - x[3]['score']) for r in worst for x in per[r])
        print('   ReVSI proxy points lost on R0-dev direct types: %.2f; in the 20 rooms with the lowest standardised mean: %.2f (%d items, %.1f score units of %.1f)' % (tot, part, sum(len(per[r]) for r in worst), sum(1 - x[3]['score'] for r in worst for x in per[r]), sum(1 - r['score'] for r in rs)))
