"""cont_ops23: classify wrong reworded camera displacement/rotation items that called the tool (step-544 return).
Usage: python3 wclass.py OUT.json [--show N]"""
import glob, gzip, json, re, sys, collections
R = '/dev/shm/c23/work/h544m/SCORES/current'
ITEMS = '/dev/shm/c23/inp_rem/src/items'
by = {i['id']: i for i in json.load(open(ITEMS + '/H_FULL.json'))['items']}
tw = json.load(open(ITEMS + '/HELDOUT_CAMERA_TWINS.json'))['twins']
rows = {}
for seg in ('parent', 'remainder'):
    for f in glob.glob(R + '/%s/metadata/reads/0/metadata/journals/*/*/items.jsonl*' % seg):
        op = gzip.open if f.endswith('.gz') else open
        for line in op(f, 'rt'):
            r = json.loads(line)
            rows[r['id']] = dict(r, segment=seg)
NUM = r'[-+]?\d+(?:\.\d+)?'

def frames(q):
    q = re.sub(r'32-frame|of 32|32 displayed|32 frames|with 32 frames|clip of 32', ' ', q)
    return [int(x) for x in re.findall(r'frames? (\d+)|and (\d+)', q) for x in x if x][:2] or [int(x) for x in re.findall(r'\d+', q) if x != '32'][:2]

def info(iid):
    r = rows[iid]; o = r['output']; t = o['text']
    ans = t.split('</think>')[-1]
    nums = re.findall(NUM, ans)
    recs = o['calls']['records']
    return dict(id=iid, score=o['scores']['answer'], pred=float(nums[-1]) if nums else None, answer_text=ans.strip()[-160:],
                calls=[(c['call'], c.get('response')) for c in recs], fams=[c.get('family') for c in recs], gt=by[iid]['ground_truth'], q=by[iid]['question'],
                qframes=frames(by[iid]['question']), finish=o.get('finish'), think_tail=t.split('</think>')[0][-500:], segment=r['segment'])

def cframes(c):
    m = re.search(r'from=(\d+) to=(\d+)', c)
    return [int(m.group(1)), int(m.group(2))] if m else None

def served(x, fam):
    key = {'move': 'distance =', 'turn': 'turn ='}[fam]
    return any(c[0].startswith('<' + fam + ' from=') and key in (c[1] or '') for c in x['calls'])

def classify(typ, x, o):
    fam = {'camera_displacement': 'move', 'camera_rotation': 'turn'}[typ]
    key = {'move': 'distance =', 'turn': 'turn ='}[fam]
    right = [c for c in x['calls'] if c[0].startswith('<' + fam + ' from=') and key in (c[1] or '')]
    runaway = len(x['calls']) >= 10 or x['finish'] != 'eos'
    end = 'RUNAWAY' if runaway or x['pred'] is None else 'ANSWERED'
    if not right:
        first = x['calls'][0][0]
        if re.match(r'<\s*(ground|gap)', first):
            return 'OBJECT_TOOL_FIRST_' + end
        other = {'move': 'turn', 'turn': 'move'}[fam]
        if first.startswith('<' + other + ' from=') and '=' in (x['calls'][0][1] or '') and 'error' not in (x['calls'][0][1] or ''):
            return 'OTHER_CAMERA_TOOL_' + end
        return 'CAMERA_TOOL_MALFORMED_' + end
    if x['pred'] is None:
        return 'RIGHT_TOOL_NO_ANSWER'
    call, resp = right[-1]
    cf = cframes(call)
    if cf and sorted(cf) != sorted(x['qframes']):
        return 'RIGHT_TOOL_WRONG_FRAMES'
    rev = '_REVERSED' if cf and cf != x['qframes'] else ''
    vals = {k: float(v) for k, v in re.findall(r'(\w+) = (' + NUM + ')', resp or '')}
    p = x['pred']; same_as_orig = o['calls'][-1:] == [right[-1]] if o['calls'] else False
    tag = '_TOOL_ERROR_TOO_IN_ORIGINAL' if same_as_orig and o['score'] < 0.5 else ''
    if typ == 'camera_displacement':
        if 'distance' in vals and abs(p - vals['distance']) < 0.015:
            return 'RIGHT_TOOL_COPIED' + rev + tag
        for k in ('dx', 'dy', 'dz'):
            if k in vals and abs(abs(p) - abs(vals[k])) < 0.015:
                return 'RIGHT_TOOL_REPORTED_COMPONENT_' + k
        return 'RIGHT_TOOL_OTHER_VALUE'
    if 'turn' not in vals:
        return 'RIGHT_TOOL_NO_VALUE'
    y = vals['turn']
    if abs(p - y) < 0.6:
        return 'RIGHT_TOOL_COPIED' + rev + tag
    if abs(p + y) < 0.6:
        return 'RIGHT_TOOL_SIGN_FLIPPED' + rev
    return 'RIGHT_TOOL_OTHER_VALUE'

out = {}
for typ in ('camera_displacement', 'camera_rotation'):
    lst = []
    for w in tw:
        if w['type'] != typ: continue
        x = info(w['reworded_id']); o = info(w['original_id'])
        if not x['calls'] or x['score'] >= 0.5: continue
        x['class'] = classify(typ, x, o); x['wording'] = w['wording_id']
        x['original'] = dict(score=o['score'], pred=o['pred'], calls=o['calls'])
        lst.append(x)
    out[typ] = lst
    called = sum(1 for w in tw if w['type'] == typ and info(w['reworded_id'])['calls'])
    print(typ, 'reworded called', called, 'wrong(<0.5)&called', len(lst))
    print('  classes', dict(collections.Counter(x['class'] for x in lst).most_common()))
    print('  by wording', dict(sorted(collections.Counter(x['wording'] for x in lst).items())))
    print('  original twin correct(>=0.5)', sum(x['original']['score'] >= 0.5 for x in lst)); print('  wrong-tool by wording', dict(sorted(collections.Counter(x['wording'] for x in lst if x['class'].startswith('OBJECT_TOOL')).items()))); allc=[info(w['reworded_id']) for w in tw if w['type']==typ]; fam={'camera_displacement':'move','camera_rotation':'turn'}[typ]; print('  all reworded: served right camera tool', sum(served(a, fam) for a in allc), 'of', len(allc)); print('  all original: served right camera tool', sum(served(info(w['original_id']), fam) for w in tw if w['type']==typ)); print('  reworded per wording', dict(sorted(collections.Counter(w['wording_id'] for w in tw if w['type']==typ).items()))); print('  all reworded right-tool by wording', dict(sorted(collections.Counter(w['wording_id'] for w in tw if w['type']==typ and served(info(w['reworded_id']), fam)).items())))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
if '--show' in sys.argv:
    n = int(sys.argv[sys.argv.index('--show') + 1])
    for typ, lst in out.items():
        for x in lst[:n]:
            print('---', typ, x['wording'], x['class'], 'score', x['score'], 'GT', x['gt'], 'pred', x['pred'], 'qframes', x['qframes'])
            print('  Q:', x['q']); print('  calls:', x['calls']); print('  ans:', x['answer_text'][-120:])
            print('  orig:', x['original'])
