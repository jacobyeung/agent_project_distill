"""ORCH ORDER 0422Z item 2: filter Codex's 80 drafted wordings to 40 NEW ones. Rules: placeholders {a}, {b}, {u} each exactly
once, written "the {a}" / "the {b}"; a closest-point word (closest / nearest); 8-30 words; no forbidden phrase; normalized
character edit distance (Levenshtein / longer length, on lowercased text without punctuation) of at least 0.40 to every
dev-S1 wording and to the routed wording, and at least 0.25 to every earlier kept draft; then the 40 kept drafts with the
lowest sha256('dist_diag|new|' + wording)."""
import json, re, hashlib, sys
def norm(s): return re.sub(r'\s+', ' ', re.sub(r'[^a-z{} ]', ' ', s.lower())).strip()
def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
def nd(a, b): a, b = norm(a), norm(b); return lev(a, b) / max(len(a), len(b))
draft = json.load(open(sys.argv[1])); forb = json.load(open(sys.argv[2]))
dev = forb['dev_s1_wordings'] + [forb['routed_and_r0_wording']]
BAD = ('minimal span', 'measurable gap', 'measure of space', 'linear distance', 'separation distance', 'measuring from the closest point of each object')
counts = dict(drafted=len(draft)); kept = []; reasons = {}
for w in draft:
    why = None
    if not isinstance(w, str): why = 'not_text'
    elif any(w.count(p) != 1 for p in ('{a}', '{b}', '{u}')) or 'the {a}' not in w or 'the {b}' not in w: why = 'placeholders'
    elif not re.search(r'\b(closest|nearest)\b', w.lower()): why = 'no_closest_point_word'
    elif not 8 <= len(w.split()) <= 30: why = 'length'
    elif any(b in w.lower() for b in BAD): why = 'forbidden_phrase'
    elif re.search(r'\ba \{u\}|\d', w): why = 'unit_article_or_number'
    elif min(nd(w, d) for d in dev) < 0.40: why = 'near_dev_wording'
    elif kept and min(nd(w, k) for k in kept) < 0.25: why = 'near_other_draft'
    if why: reasons[why] = reasons.get(why, 0) + 1
    else: kept.append(w)
counts.update(reasons); counts['passed'] = len(kept)
chosen = sorted(kept, key=lambda w: hashlib.sha256(('dist_diag|new|' + w).encode()).hexdigest())[:40]
counts['chosen'] = len(chosen)
mind = {w: round(min(nd(w, d) for d in dev), 3) for w in chosen}
json.dump(dict(rule=__doc__, counts=counts, new=chosen, min_distance_to_dev=mind), open(sys.argv[3], 'w'), indent=1)
print(json.dumps(counts)); print('min distance to dev among chosen:', min(mind.values()), 'median', sorted(mind.values())[20])
