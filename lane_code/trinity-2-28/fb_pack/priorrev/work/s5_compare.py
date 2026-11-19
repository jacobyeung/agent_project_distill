"""Checks 2 and 3 from the three s5 replays: absent identity, enabled slot changes,
per-cell and per clause x difficulty back shares from the drawn rows, repeat cap."""
import json, pickle
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parent
S = W/'s5'


def plan(path): return json.loads((path/'plan.json').read_text())


def strip(pop):
    return {k: v for k, v in pop.items() if k not in ('evidence', 'source_membership')}


def main():
    R = {}
    dirs = dict(base_absent=S/'base_absent', new_absent=S/'new_absent', new_enabled=S/'new_enabled_r2')
    rep = {n: json.loads((d/'REPLAY.json').read_text()) for n, d in dirs.items()}
    R['first_enabled_plan_equals_rerun'] = (S/'new_enabled/plan.json').read_bytes() == (dirs['new_enabled']/'plan.json').read_bytes()
    raw = {n: (d/'plan.json').read_bytes() for n, d in dirs.items()}
    R['plan_sha256'] = {n: r['plan_sha256'] for n, r in rep.items()}
    R['absent_plan_bytes_equal_base'] = raw['base_absent'] == raw['new_absent']
    pops = {n: json.loads((d/'pop/population.json').read_text()) for n, d in dirs.items()}
    idx = {n: json.loads((d/'pop/indices.json').read_text())['cells'] for n, d in dirs.items()}
    R['population_equal_except_evidence_paths'] = all(strip(pops[n]) == strip(pops['base_absent']) for n in rep)
    R['indices_cells_equal'] = all(idx[n] == idx['base_absent'] for n in rep)
    R['counts'] = pops['base_absent']['counts']
    for n in ('new_absent', 'new_enabled'):
        R[n+'_resume'] = rep[n].get('resume'); R[n+'_determinism'] = rep[n].get('determinism')
    R['tamper'] = rep['new_enabled']['tamper']
    dp = json.loads(Path(rep['new_enabled']['binding']['direction_prior']['path']).read_text())
    recs = pickle.loads((W/'rows.pkl').read_bytes())
    cells = idx['base_absent']
    card = json.loads(Path('/scratch/jjyeung/orch_n30/fb_pack/prior2/work/recovered/card.json').read_text())
    stream_of = {c['type']: c['stream'] for c in card['cells']}
    owner = {(stream_of[k], i): k for k, v in cells.items() for i in v}
    targets = {k: set(dp['cells'][k]['front']) | set(dp['cells'][k]['back']) for k in dp['cells']}
    th = {k: {r['i'] for r in recs if r['cell'] == k and r['details'] and r['details'][:2] == ('toward', 'hard')}
          for k in targets}
    R['offsets_file_equals_toward_hard_offsets'] = {k: targets[k] == th[k] for k in targets}
    R['offsets_file_sides_match_rows'] = {k: all(recs[i]['details'][2] == s and recs[i]['label'].split('-')[0] == s
                                                 for s in ('front', 'back') for i in dp['cells'][k][s]) for k in targets}
    a, e = plan(dirs['new_absent']), plan(dirs['new_enabled'])
    bad = Counter(); changed = Counter(); slots = Counter(); kinds_equal = True
    draws = {m: defaultdict(Counter) for m in ('absent', 'enabled')}
    rep_off = Counter()
    for step, (pa, pe) in enumerate(zip(a, e)):
        for (sa, oa), (se, oe) in zip(pa, pe):
            if sa != se or len(oa) != len(oe):
                bad['shape'] += 1; continue
            for x, y in zip(oa, oe):
                ka, ke = owner.get((sa, x), sa), owner.get((se, y), se)
                kinds_equal &= ka == ke
                rep_off[(se, y)] += 1
                if sa == 'vqa' and ka in targets and x in targets[ka]:
                    slots[ka] += 1
                    if y not in targets[ka]: bad['target_slot_left_target_set'] += 1
                elif x != y:
                    bad['non_target_slot_changed'] += 1
                changed[ka] += x != y
                if sa == 'vqa' and ka in ('direction', 'facing_pairs'):
                    for m, off in (('absent', x), ('enabled', y)):
                        d = recs[off]['details']
                        draws[m][(ka, d[0], d[1])][d[2]] += 1
                        draws[m][('pooled', d[0], d[1])][d[2]] += 1
    R['slot_violations'] = dict(bad)
    R['kind_sequence_equal'] = kinds_equal
    R['toward_hard_slots'] = dict(slots)
    R['changed_slots'] = dict(changed)
    R['max_repeat_enabled'] = max(rep_off.values())
    R['max_repeat_by_stream'] = {s: max(v for (t, _), v in rep_off.items() if t == s) for s in ('pose', 'vqa', 'routing', 'pointing')}
    R['shares'] = {m: {'|'.join(k): dict(draws=sum(c.values()), back=c['back'], front=c['front'],
                                          back_share=round(c['back']/max(1, c['back']+c['front']), 4),
                                          other=sum(v for s, v in c.items() if s not in ('front', 'back')))
                       for k, c in sorted(d.items())} for m, d in draws.items()}
    (W/'S5_COMPARE.json').write_text(json.dumps(R, indent=1) + '\n')
    print(json.dumps(R, indent=1))


if __name__ == '__main__':
    main()
