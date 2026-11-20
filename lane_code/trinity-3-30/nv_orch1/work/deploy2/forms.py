"""Paired-form chain for the Orchard runner (V7: open-vocabulary presence and points on 32 frames).
DRAFT prompts: replaced verbatim by nvkey2's V6 primary and verifier prompts (sha256 pinned in PROMPTS below) before any production send.
chain(primary_task, primary_result) -> [verifier task]: the verifier sees the same frames plus the primary's names and per-name counts, never its points."""
import json, re, hashlib
PRIMARY = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
           'List up to 40 distinct physical objects in the room (furniture, appliances, fixtures and smaller items). For each give: "name" (a common noun phrase), '
           '"aliases" (2 other phrases a person might use), "lookalike" (one object it could be confused with), "count" (how many distinct instances of this kind '
           'appear in the video), "frames" (every frame number where at least one instance is clearly visible), and "points" (for each listed frame, one point '
           '[x, y] on a visible instance, in 0-1000 coordinates: x from the left edge, y from the top edge).\n'
           'Then judge these nouns, which may or may not be present: {absent}. For each say "present" or "absent".\n'
           'Reply with one JSON object and nothing else: {{"objects": [{{"name": ..., "aliases": [..], "lookalike": ..., "count": n, "frames": [..], "points": {{"k": [x, y], ...}}}}, ...], '
           '"nouns": {{"<noun>": "present" | "absent", ...}}}}')
VERIFIER = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
            'Another annotator listed these object kinds with instance counts: {kinds}.\n'
            'For every frame and every listed kind, decide whether at least one object of that kind is visible in that frame (partly visible counts). '
            'If visible, give one point [x, y] on it in 0-1000 coordinates (x from the left edge, y from the top edge); otherwise null. '
            'Also list kinds you judge wrong ("rejects": the kind is not in the video, or the name is wrong, with the right name if any) and clearly visible '
            'objects the list missed ("missed": name and frames).\n'
            'Reply with one JSON object and nothing else: {{"frames": {{"1": {{"<kind>": [x, y] or null, ...}}, ..., "{n}": {{...}}}}, "rejects": [{{"name": ..., "why": ..., "right_name": ...}}], "missed": [{{"name": ..., "frames": [..]}}]}}')
PROMPTS = {'primary': hashlib.sha256(PRIMARY.encode()).hexdigest(), 'verifier': hashlib.sha256(VERIFIER.encode()).hexdigest()}
def parse(t):
    t = (t or '').strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
def chain(task, result):
    m = task['meta']; ch = m['chain']; d = parse(result.get('text'))
    if not isinstance(d, dict) or not isinstance(d.get('objects'), list): return []
    kinds = {}
    for o in d['objects'][:40]:
        if isinstance(o, dict) and isinstance(o.get('name'), str) and o['name'].strip():
            kinds[o['name'].strip()] = o.get('count') if isinstance(o.get('count'), int) else None
    if not kinds: return []
    text = VERIFIER.format(n=m['n'], kinds=json.dumps(kinds))
    content = [{'text': text}] + [c for c in task['content'] if 'image' in c or (c.get('text') or '').startswith('Frame ')]
    meta = {k: v for k, v in m.items() if k not in ('chain', 'absent')}; meta.update(role='verifier', primary_id=task['id'], kinds=kinds, prompt_sha256=PROMPTS['verifier'])
    return [{'id': task['id'][:-2] + '_v' if task['id'].endswith('_p') else task['id'] + '_v', 'model': ch['model'], 'effort': ch.get('effort'), 'max_tokens': ch.get('max_tokens', 32768),
             'content': content, 'meta': meta}]
