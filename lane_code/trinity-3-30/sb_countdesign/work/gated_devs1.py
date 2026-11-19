"""Lane sb_countdesign: gated composite on dev-S1 counting (150 items) with the as-built deployed counting program's per-item scores
(lane b08_headrows) and the model's own "large" signal as the gate (answer >= 4, or a runaway). CPU, read-only."""
import json, collections, random, statistics
items = [json.loads(l) for l in open('../files/COUNT_ITEMS_535.jsonl')]
S = [x for x in items if x['set'] == 'dev-S1']
prog = {r['qid']: r['program'] for r in json.load(open('PROGRAM_PERITEM_devS1_counting.json')) if r['arm'] == 'step544_B2048'}
def num(p):
    try: return float(p)
    except Exception: return None
out = {}
for k in ('S1_544', 'R1_200'):
    gate = lambda x: bool(x['direct'][k]['forced_close']) or (num(x['direct'][k]['pred']) is not None and num(x['direct'][k]['pred']) >= 4)
    direct = [x['direct'][k]['score'] for x in S]; comp = [prog[x['id']] if gate(x) else x['direct'][k]['score'] for x in S]
    orac = [prog[x['id']] if x['truth'] >= 4 else x['direct'][k]['score'] for x in S]
    best = [max(prog[x['id']], x['direct'][k]['score']) for x in S]
    rooms = collections.defaultdict(list)
    for x, c, d in zip(S, comp, direct): rooms[x['room']].append(100 * (c - d))
    rk = sorted(rooms); rng = random.Random(20261119); bs = []
    for _ in range(10000):
        s = [v for r in rng.choices(rk, k=len(rk)) for v in rooms[r]]; bs.append(sum(s) / len(s))
    bs.sort()
    fired = sum(gate(x) for x in S)
    d = dict(direct=round(100 * statistics.mean(direct), 2), program_always=round(100 * statistics.mean(prog[x['id']] for x in S), 2), gated_by_model=round(100 * statistics.mean(comp), 2),
             gated_minus_direct=[round(100 * (statistics.mean(comp) - statistics.mean(direct)), 2), round(bs[250], 2), round(bs[9750], 2)], gate_fired=fired,
             gated_by_truth_ge4=round(100 * statistics.mean(orac), 2), per_item_best=round(100 * statistics.mean(best), 2))
    for name, sel in (('truth2', lambda x: x['truth'] == 2), ('truth3', lambda x: x['truth'] == 3), ('truth4', lambda x: x['truth'] == 4), ('truth5plus', lambda x: x['truth'] >= 5)):
        L = [x for x in S if sel(x)]
        d[name] = dict(n=len(L), fired=sum(gate(x) for x in L), direct=round(100 * statistics.mean(x['direct'][k]['score'] for x in L), 1), program=round(100 * statistics.mean(prog[x['id']] for x in L), 1),
                       gated=round(100 * statistics.mean(prog[x['id']] if gate(x) else x['direct'][k]['score'] for x in L), 1))
    out[k] = d; print(k, json.dumps(d))
json.dump(out, open('GATED_devS1.json', 'w'), indent=1)
