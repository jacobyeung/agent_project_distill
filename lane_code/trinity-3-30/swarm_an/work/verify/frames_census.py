import sys, json, re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import defaultdict, Counter
FR = re.compile(r'frames? (\d+(?:\.\d+)?)')
SEEN = re.compile(r'(?:first seen in|Seen: [^.\n]*? in|\bin) (?!frame)(the [a-z ]{2,40}|hand)')
def think(t): return (t or '').split('</think>')[0]
def cens(rows, label):
    d = defaultdict(lambda: Counter())
    for r in rows:
        t = think(r['text']); k = (label, r['type'])
        nums = [float(x) for x in FR.findall(t)]
        d[k]['n'] += 1
        if not nums: d[k]['nofr'] += 1; d[k]['nofr_ok'] += r['score'] >= 1
        elif max(nums) > 32: d[k]['gt32'] += 1; d[k]['gt32_ok'] += r['score'] >= 1
        else: d[k]['le32'] += 1; d[k]['le32_ok'] += r['score'] >= 1
        if any(x != int(x) for x in nums): d[k]['dec'] += 1
        if re.search(r'first seen in (?!frame)', t) or re.search(r'Seen:[^\n]*\bin (?!frame)(?:hand|the )', t): d[k]['nonframe'] += 1; d[k]['nonframe_ok'] += r['score'] >= 1
    for k, c in sorted(d.items()):
        f = lambda a: '%3d(%s)' % (c[a], ('%.0f%%' % (100 * c[a + '_ok'] / c[a])) if c[a] else '-')
        print('%-14s %-28s n=%3d le32=%s gt32=%s nofr=%s dec=%3d nonframe=%s' % (k[0], k[1], c['n'], f('le32'), f('gt32'), f('nofr'), c['dec'], f('nonframe')))
cens(K.direct('R1', 200, 'dev-S1'), 'S1@200'); cens(K.direct('R1', 200, 'R0-dev'), 'R0@200'); cens(K.direct('S1', 544, 'R0-dev'), 'R0@544'); cens(K.direct('S1', 544, 'dev-S1'), 'S1@544')
cens(K.vsti('R1', 200), 'vsti@200'); cens(K.facing('R1', 200, 'away'), 'away@200')
