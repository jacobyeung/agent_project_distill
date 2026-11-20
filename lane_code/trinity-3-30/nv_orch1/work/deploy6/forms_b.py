"""V7 in the boolean form (ORCH ANSWER 0532Z). PROMPT = C1's presence-and-point prompt (nvkey1 kit/c1_jobs.py, scored in C1/V1), copied verbatim.
(a) kinds = the 17 ARKit annotated classes + 4 frozen open decoys; both families, independent calls, kinds split so outputs stay under ~6K tokens.
(b) NAMING (Astra): inventory names only (<= 25 singular count nouns); chain() then asks both families the boolean form on the names outside the 17
classes (<= 12) plus 4 decoys. (b) files carry the note "open vocabulary; size uncertified; presence from two families; points are not labels"."""
import json, re, hashlib, random
PROMPT = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
          'Object kinds: {kinds}.\n'
          'For every frame and every object kind, decide whether at least one object of that kind is visible in that frame, fully or partly '
          '(partly visible or partly occluded objects count; reflections and pictures of objects do not). '
          'If it is visible, give one point on a visible part of it (if several are visible, pick the most visible one) as [x, y] in 0-1000 coordinates '
          'of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. If it is not visible, give null.\n'
          'Reply with one JSON object and nothing else, with one entry for every frame from 1 to {n} and every object kind: '
          '{{"1": {{"{k0}": [x, y] or null, ...}}, "2": {{...}}, ..., "{n}": {{...}}}}')
NAMING = ('These are 32 frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to 32).\n'
          'List the distinct kinds of physical objects visible in these frames (furniture, appliances, fixtures, and objects at least the size of a book), '
          'at most 25 kinds, each as a singular count noun (for example "chair", not "chairs" or "seating"). Do not list walls, floors, ceilings, windowsills '
          'or other parts of larger objects.\n'
          'Reply with one JSON object and nothing else: {"names": ["...", ...]}')
ARKIT17 = ['bathtub', 'bed', 'cabinet', 'chair', 'dishwasher', 'fireplace', 'oven', 'refrigerator', 'shelf', 'sink', 'sofa', 'stool', 'stove', 'table', 'toilet', 'tv', 'washer']
DECOYS = ['fire extinguisher', 'whiteboard', 'projector', 'bottle crate', 'trolley', 'paper towel dispenser', 'yoga mat', 'pillar', 'whiteboard eraser', 'intercom', 'rice cooker', 'mop']  # frozen: CHECK_VOCAB (ebac12b2) nouns rarely found in homes, outside the ARKit 17 and their R3 siblings
NOTE_B = 'open vocabulary; size uncertified; presence from two families; points are not labels'
FORM = 'c1-boolean'
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
PROMPTS = {'boolean_template': sha(PROMPT), 'naming': sha(NAMING), 'decoys': sha(json.dumps(DECOYS))}
SPLIT = {'argon': 6, 'other': 11}  # kinds per call: Argon ~1.1K output tokens per kind at 32 frames, Astra ~0.75K
def fam(model): return 'argon' if 'argon' in model else 'other'
def chunks(kinds, model):
    k = SPLIT[fam(model)]; n = -(-len(kinds) // k); return [kinds[i::n] for i in range(n)]
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv', 'couch': 'sofa', 'fridge': 'refrigerator', 'washing machine': 'washer'}.get(l, l)
def boolean_tasks(base_id, frames_content, kinds, models, meta, tag):
    out = []
    for model, effort in models:
        for qi, ks in enumerate(chunks(kinds, model)):
            text = PROMPT.format(n=32, kinds=json.dumps(ks), k0=ks[0])
            m = dict(meta, role=tag, kinds=ks, q=qi, prompt_sha256=sha(text), template_sha256=PROMPTS['boolean_template'], form=FORM)
            out.append({'id': '%s_%s_q%d_%s' % (base_id, tag, qi, fam(model)[:2]), 'model': model, 'effort': effort, 'max_tokens': 16384,
                        'content': [{'text': text}] + frames_content, 'meta': m})
    return out
def parse(t):
    t = (t or '').strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    for cand in (t, t[t.find('{'):t.rfind('}') + 1]):
        for fix in (lambda x: x, lambda x: re.sub(r',\s*([}\]])', r'\1', x)):
            try: return json.loads(fix(cand))
            except Exception: pass
    return None
def chain(task, result):
    m = task['meta']; ch = m['chain']; d = parse(result.get('text'))
    names = [norm(x) for x in ((d or {}).get('names') or []) if isinstance(x, str) and x.strip()] if isinstance(d, dict) else []
    seen = set(); keep = []
    for x in names:
        if x not in seen and x not in ARKIT17 and x not in ('wall', 'floor', 'ceiling'): seen.add(x); keep.append(x)
    keep = keep[:12]
    if not keep: return []
    dec = [x for x in ch['decoy_pool'] if x not in seen][:4]
    kinds = keep + dec; random.Random('b ' + task['id']).shuffle(kinds)
    frames = [c for c in task['content'] if 'image' in c or (c.get('text') or '').startswith('Frame ')]
    meta = {k: v for k, v in m.items() if k not in ('chain',)}; meta.update(names_from=task['id'], named=keep, decoys=dec, note=NOTE_B)
    return boolean_tasks(task['id'][:-2], frames, kinds, [tuple(x) for x in ch['models']], meta, 'b')
