# Compact side-by-side lines: step-200 stated frames/order, truth, step-544 stated distances, the room's other items
import sys, json, random
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
D = dev(); by = {(d['id'], d['step']): d for d in D}
which = sys.argv[1]; n = int(sys.argv[2]); seed = int(sys.argv[3])
its = [d for d in D if d['step'] == 200 and d['type'] in CAM and ((d['score'] == 1) == (which == 'right'))]
random.Random(seed).shuffle(its)
for d in its[:n]:
    o = by[(d['id'], 544)]; t = d['opts'][ord(d['gt']) - 65]
    s = ' '.join('%s@%d' % (x.replace(' ', '_')[:14], d['fs'].get(x, -1)) for x in d['opts'])
    od = '>'.join(x.replace(' ', '_')[:10] for x in d['order'])
    dd = ' '.join('%.1f' % o['dist'].get(x, -1) for x in d['opts'])
    sib = [e for e in D if e['step'] == 200 and e['room'] == d['room'] and e['id'] != d['id'] and e['type'] in CAM]
    sibs = ' | '.join('k%d:%s(T:%s)' % (e['k'], e['order'][0].replace(' ', '_')[:10], e['opts'][ord(e['gt']) - 65].replace(' ', '_')[:10]) for e in sib if set(e['opts']) & set(d['opts']))[:150]
    print('%s %s k%d [%s] M:%s T:%s 544:%s(%s) || %s' % (d['id'][:6], d['type'][-2:], d['k'], s, od, t.replace(' ', '_')[:12], o['pred'], dd, sibs))
