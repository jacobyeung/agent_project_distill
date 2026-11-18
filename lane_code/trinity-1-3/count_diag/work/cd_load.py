"""Load counting items (scored budget B2048) for each export and set; CPU only, read-only inputs."""
import json, re, os, hashlib

K = '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build'
E193 = '/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl'

SOURCES = {
    'S544': {'dev-S1': E193, 'R0-dev': f'{K}/adff67f7ae9/fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl'},
    'D0m100': {'dev-S1': f'{K}/af35386aa3e/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl',
               'R0-dev': f'{K}/af35386aa3e/fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl'},
    'H1m100': {'dev-S1': f'{K}/a24ea1a1936/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl',
               'R0-dev': f'{K}/a24ea1a1936/fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl'},
    'R1m100': {'dev-S1': f'{K}/a5d2d909067/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl',
               'R0-dev': f'{K}/a5d2d909067/fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl'},
    'D0m200': {'R0-dev': f'{K}/ae470417b41/fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl'},
}
ITEMS = {  # summary ITEMS.jsonl files (scores used by the tools; count_kind)
    'S544': {'dev-S1': '/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/evidence/A544.jsonl', 'R0-dev': f'{K}/adff67f7ae9/fetched/x/ITEMS.jsonl'},
    'R1m100': {'dev-S1': f'{K}/a5d2d909067/fetched/x/ITEMS.jsonl', 'R0-dev': f'{K}/a5d2d909067/fetched/x/ITEMS.jsonl'},
    'D0m100': {'dev-S1': f'{K}/af35386aa3e/fetched/x/ITEMS.jsonl', 'R0-dev': f'{K}/af35386aa3e/fetched/x/ITEMS.jsonl'},
    'H1m100': {'dev-S1': f'{K}/a24ea1a1936/fetched/x/ITEMS.jsonl', 'R0-dev': f'{K}/a24ea1a1936/fetched/x/ITEMS.jsonl'},
    'D0m200': {'R0-dev': f'{K}/ae470417b41/fetched/x/ITEMS.jsonl'},
}
FAM = {'dev-S1': 'main', 'R0-dev': 'a7'}
KEEP = ('id', 'room', 'scene', 'dataset', 'question', 'question_type', 'ground_truth', 'released_answer', 'answer',
        'extracted_answer', 'response_text', 'score', 'raw_generation', 'output_tokens', 'think_tokens', 'hit_token_cap',
        'forced_close', 'stopped_unclosed', 'parse_failed', 'empty_think', 'finish_reason', 'extract_branch', 'scorer', 'stratum')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load(types=('object_counting',)):
    out, shas = {}, {}
    for ex, sets in SOURCES.items():
        out[ex] = {}
        for s, p in sets.items():
            shas[p] = sha(p)
            d = {}
            with open(p) as f:
                for line in f:
                    r = json.loads(line)
                    if r.get('question_type') in types:
                        d[r['id']] = {k: r.get(k) for k in KEEP}
            # attach count_kind and tool score from ITEMS.jsonl
            ip = ITEMS[ex][s]
            shas[ip] = sha(ip)
            with open(ip) as f:
                for line in f:
                    r = json.loads(line)
                    if r.get('family') == FAM[s] and r['id'] in d:
                        d[r['id']]['count_kind'] = r.get('count_kind')
                        d[r['id']]['tool_score'] = r.get('score')
                        d[r['id']]['tool_pred'] = r.get('prediction')
            out[ex][s] = d
    return out, shas


NUM = re.compile(r'^\s*-?\d+(\.\d+)?\s*$')


def as_num(x):
    if x is None:
        return None
    t = str(x).strip()
    if NUM.match(t):
        return float(t)
    return None


def mra(pred, gt):
    if pred is None or gt is None or gt == 0:
        return 0.0
    rel = abs(pred - gt) / abs(gt)
    ths = [0.5 + 0.05 * i for i in range(10)]
    return sum(rel < 1 - t + 1e-9 for t in ths) / 10.0


def on16k_path(p):
    """ON16k (full-generation) file beside a budget_2048 file."""
    if p.endswith('items_leg_m544_main.jsonl'):
        return p.replace('/budget_2048/0/', '/0/')
    return p.replace('/results/budget_2048/0/', '/results/0/')


def load_on16k(types=('object_counting',)):
    out, shas = {}, {}
    for ex, sets in SOURCES.items():
        out[ex] = {}
        for s, p in sets.items():
            q = on16k_path(p)
            shas[q] = sha(q)
            d = {}
            with open(q) as f:
                for line in f:
                    r = json.loads(line)
                    if r.get('question_type') in types:
                        d[r['id']] = {k: r.get(k) for k in KEEP}
            out[ex][s] = d
    return out, shas
