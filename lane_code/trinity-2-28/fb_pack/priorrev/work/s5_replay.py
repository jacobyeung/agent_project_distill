"""Replay native produce() and plans() on the reconstructed VQA population.

usage: s5_replay.py {base|new} {absent|enabled} OUT
Real VQA rows come from eligible_vqa.sqlite in offset order; pose, pointing and routing
rows are synthetic stand-ins at the card's ceilings, because those streams own disjoint
cells and RNG-independent pools.
"""
import copy, hashlib, json, sqlite3, sys
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
TREE, MODE, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, str(W/TREE))
from student_pilot.p3_provenance import file_pin, load, pinned, write
from student_pilot.r1_population import produce
from student_pilot.r1_mix import plans
from student_pilot.r1_training import STREAMS

CARD = FB/'prior2/work/recovered/card.json'
WEIGHTS = FB/'prior2/out/TOWARD_HARD_WEIGHTS.json'
COUNTS = dict(pose=194987, pointing=20239, routing=50000)


class Reader:
    def __init__(self):
        e = sqlite3.connect('file:'+str(FB/'prior2b/work/source/eligible_vqa.sqlite')+'?mode=ro&immutable=1', uri=True)
        self.vqa = [json.loads(r) for (r,) in e.execute('SELECT row FROM rows ORDER BY i')]
        e.close()
        self.n = dict(COUNTS, vqa=len(self.vqa))

    def count(self, stream): return self.n[stream]

    def row(self, stream, i):
        if not 0 <= i < self.n[stream]: raise IndexError(i)
        if stream == 'vqa': return self.vqa[i], None
        return dict(qid=f'{stream}{i:06d}', dataset='d1', scene=f'scene{i % 700:04d}_00'), None

    def close(self): pass


def run_plans(binding, reader, start=0):
    counts = {s: reader.count(s) for s in STREAMS}
    return [[[s, list(o)] for s, o in p] for p in plans(binding, counts, 1000, start_step=start)]


def refused(fn):
    try:
        fn()
    except ValueError as error:
        return 'refused:'+str(error)
    return 'accepted'


def tamper(binding, reader, out):
    """Each probe rewrites one input and re-pins only where stated."""
    res = {}
    dp = json.loads(Path(binding['direction_prior']['path']).read_text())
    def variant(name, mutate, repin=True):
        v = copy.deepcopy(dp); mutate(v)
        p = out/f'tamper_{name}.json'; write(p, v)
        b = dict(binding, direction_prior=file_pin(p) if repin else dict(binding['direction_prior'], path=str(p)))
        return refused(lambda: run_plans(b, reader, 999))
    res['bytes_changed_pin_kept'] = variant('bytes', lambda v: v['cells']['direction']['back'].reverse(), repin=False)
    res['card_sha_changed'] = variant('card', lambda v: v.update(card_sha256='0'*64))
    res['population_sha_changed'] = variant('pop', lambda v: v.update(population_sha256='0'*64))
    res['back_offset_dropped'] = variant('drop', lambda v: v['cells']['direction']['back'].pop())
    res['back_offset_duplicated'] = variant('dup', lambda v: v['cells']['direction']['back'].__setitem__(0, v['cells']['direction']['back'][1]))
    cells = load(pinned(binding['indices']))['cells']
    other = cells['relative_distance'][0]
    res['offset_outside_cell'] = variant('outside', lambda v: v['cells']['direction']['back'].__setitem__(0, other))
    targets = set(dp['cells']['direction']['back']) | set(dp['cells']['direction']['front'])
    non_target = next(i for i in cells['direction'] if i not in targets)
    res['non_target_offset_in_cell_repinned'] = variant('nontarget', lambda v: v['cells']['direction']['back'].__setitem__(0, non_target))
    res['sides_swapped_repinned'] = variant('swap', lambda v: v['cells']['facing_pairs'].update(
        back=v['cells']['facing_pairs']['front'][:len(v['cells']['facing_pairs']['back'])],
        front=v['cells']['facing_pairs']['back']+v['cells']['facing_pairs']['front'][len(v['cells']['facing_pairs']['back']):]))
    w = json.loads(WEIGHTS.read_text())
    w['cells']['direction']['rows'][0]['side'] = {'back': 'front', 'front': 'back'}[w['cells']['direction']['rows'][0]['side']]
    wp = out/'tamper_weights.json'; write(wp, w)
    res['weight_side_flipped_repinned'] = variant('policy', lambda v: v.update(policy=file_pin(wp)))
    res['policy_pin_sha_wrong'] = variant('policysha', lambda v: v.update(policy=dict(v['policy'], sha256='0'*64)))
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    reader = Reader()
    write(OUT/'membership.json', dict(schema='r1-source-membership-v1', sources={},
          routing_slices='deferred_first_boundary'))
    write(OUT/'evidence.json', dict(note='s5 replay stand-in evidence'))
    cfg = {'r1_training': {'routing_slices': 'deferred_first_boundary'}}
    if MODE == 'enabled':
        cfg['r1_training']['direction_prior'] = file_pin(WEIGHTS)
    binding = produce(reader, file_pin(CARD), file_pin(OUT/'membership.json'), [file_pin(OUT/'evidence.json')],
                      OUT/'pop', cfg=cfg)
    full = run_plans(binding, reader)
    (OUT/'plan.json').write_text(json.dumps(full, separators=(',', ':')))
    result = dict(tree=TREE, mode=MODE, binding=binding,
                  plan_sha256=hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest(),
                  population_sha256=binding['population']['sha256'], indices_sha256=binding['indices']['sha256'])
    if TREE == 'new':
        result['resume'] = {s: run_plans(binding, reader, s) == full[s:] for s in (1, 250, 723, 999, 1000)}
        result['determinism'] = run_plans(binding, reader) == full
    if MODE == 'enabled':
        result['tamper'] = tamper(binding, reader, OUT)
    (OUT/'REPLAY.json').write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'binding'}, indent=1))


if __name__ == '__main__':
    main()
