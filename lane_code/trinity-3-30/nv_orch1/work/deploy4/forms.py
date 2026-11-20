"""Paired form for V7 on Orchard: nvkey2's V6 form v2 (v6_jobs.py a5281b8a), templates copied verbatim (PRIMARY 19b990ae, VERIFIER 73619978).
chain(primary_task, primary_result) -> [verifier task], as v6_jobs.chain: the verifier sees the named kinds (marked "named") and the primary's inventory
names with counts, never points or states, plus the check kinds for states only."""
import json, re, hashlib, collections
FORM = 'v6-form-v2'
STATES = ('Size states: for an object in a frame write L if it is visible and covers 5% of the frame or more, M if it is visible and covers 1% to 5%, '
          'S if it is visible but covers under 1%, is cut off at the frame edge, is mostly hidden, or you are unsure, and A if it is not visible in that frame. '
          'A "states" value is a string of exactly 32 characters from L, M, S, A, one per frame in order (frame 1 first).\n'
          'Points are [x, y] in 0-1000 coordinates of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. '
          'Give points only for frames whose state is L or M.\n')
HEAD = 'These are 32 frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to 32).\n'
PRIMARY = (HEAD + STATES +
           'Task 1, named kinds: {named}. For each kind give "states" (the state of the most visible object of that kind in each frame) and "points" '
           '(for every L or M frame, one point on a visible part of that object).\n'
           'Task 2, check kinds: {check}. Some of these may be in the room and some may not. For each give "states" only.\n'
           'Task 3, inventory: list up to 40 other distinct physical objects visible in these frames (furniture, appliances, fixtures, and objects at least the size '
           'of a book) that are not of the named kinds. An object seen in several frames is one instance; two objects of the same kind are two instances. For each give '
           '"name" (a singular count noun), "aliases" (two other names), "look_alike" (a kind of object it could be mistaken for), "one_object" (true if it is one '
           'physical object), "part_of_larger" (true if it is part of a larger object), "group" (true if it is several objects named as one), "states" and "points" '
           '(on up to 12 of its L or M frames, spread over the video).\n'
           'Reply with one JSON object and nothing else: {{"named": {{"<kind>": {{"states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...}}, '
           '"check": {{"<kind>": {{"states": "..."}}, ...}}, "inventory": [{{"name": "...", "aliases": ["...", "..."], "look_alike": "...", "one_object": true, '
           '"part_of_larger": false, "group": false, "states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...]}}')
VERIFIER = (HEAD + STATES +
            'Another annotator listed these kinds of objects in this video, with how many distinct objects of each kind it saw: {listed}.\n'
            'For each listed kind give "states" (the state of the most visible object of that kind in each frame) and "points" (for every L or M frame, one point '
            'on a visible part of that object). Then give "rejects": the listed kinds you do not see anywhere in the video, and "missed": other distinct physical '
            'objects (furniture, appliances, fixtures, objects at least the size of a book) that are not of any listed kind, each with "name", "aliases", "states" '
            'and "points" (on up to 12 of its L or M frames).\n'
            'Check kinds, states only (no points): {check}.\n'
            'Reply with one JSON object and nothing else: {{"kinds": {{"<kind>": {{"states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...}}, '
            '"check": {{"<kind>": {{"states": "..."}}, ...}}, "rejects": ["..."], "missed": [{{"name": "...", "aliases": ["...", "..."], "states": "...", '
            '"points": {{"<frame>": [x, y], ...}}}}, ...]}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1] if l.split() else l; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
PROMPTS = {'primary': sha(PRIMARY), 'verifier': sha(VERIFIER)}
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    for cand in (t, t[t.find('{'):t.rfind('}') + 1]):
        for fix in (lambda x: x, lambda x: re.sub(r',\s*([}\]])', r'\1', x)):
            try: return json.loads(fix(cand))
            except Exception: pass
    return None
def chain(task, result):
    m = task['meta']; ch = m['chain']; d = parse(result.get('text'))
    inv = [x for x in ((d or {}).get('inventory') or []) if isinstance(x, dict) and x.get('name')] if isinstance(d, dict) else []
    cnt = collections.Counter(norm(x['name']) for x in inv)
    listed = [(k, None) for k in m['named']] + [(k, v) for k, v in sorted(cnt.items()) if k not in m['named']]
    ltxt = ', '.join('%s (%s)' % (k, 'named' if v is None else v) for k, v in listed)
    text = VERIFIER.format(listed=ltxt, check=json.dumps(m['check']))
    content = [{'text': text}] + [c for c in task['content'] if 'image' in c or (c.get('text') or '').startswith('Frame ')]
    meta = {k: v for k, v in m.items() if k != 'chain'}
    meta.update(role='verifier', primary_id=task['id'], primary_parsed=d is not None, listed=[k for k, v in listed], counts=dict(cnt), prompt_sha256=sha(VERIFIER))
    return [{'id': task['id'][:-2] + '_v', 'model': ch['model'], 'effort': ch.get('effort'), 'max_tokens': ch.get('max_tokens', 32768), 'content': content, 'meta': meta}]
