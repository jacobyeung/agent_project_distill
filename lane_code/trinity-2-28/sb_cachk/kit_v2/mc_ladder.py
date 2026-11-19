"""Read-only bindings to sb_kbox4's unchanged ladder (train_pricing, pricing, summarize_train, predicted)."""
import gzip, json, sys
from types import SimpleNamespace as NS
import mc_common as C

_T = None


def T():
    """Import sb_kbox4's train_pricing; its PINS (module dryrun) record every ladder input it reads."""
    global _T
    if _T is None:
        sys.path.insert(0, str(C.BOX))
        import train_pricing
        _T = train_pricing
    return _T


def S():
    """sb_kbox4's summarize_train (precision, contrast, sizes, appearance, mean), unchanged."""
    T()
    import summarize_train
    return summarize_train


def M():
    T()
    import math_v2
    return math_v2


def setup(threads=None):
    t = T()
    out = t.setup()
    if threads:
        t.torch.set_num_threads(threads)
    return out


def capture_inputs(c):
    """Serving geometry, stage-1 cache, raster arrays and the capture's serving label table, as train_pricing.one loads them."""
    t = T()
    geo, cache, meta, tower, receipt = t.R.geometry(c)
    gt, gt_raw = t.R.gt_arrays(c)
    gt['raster'] = gt_raw.get('inst', gt_raw.get('instances'))
    gt['valid'] = gt_raw['valid'].astype(bool)
    ref = json.loads(gzip.decompress(t.read(t.R.TABLES/(C.stub(c['canonical'])+'.json.gz'))))
    t.PINS.update(ref['input_sha256'])
    return geo, cache, meta, gt, gt_raw, ref


def carry_diag(c, geo, gt, name, seed, members, raw):
    """The ladder's own member test: train_pricing.Objects.get, unchanged, on an injected track whose seed proposals are
    `seed` and whose merged object is `members` ({frame: proposal}); raw[frame-1][index]['mask'] is each member's
    480 x 640 mask. Returns get()'s (object, diag); diag holds added, correct and seed_majority."""
    t = T()
    objects = t.Objects.__new__(t.Objects)
    objects.c, objects.geo, objects.gt, objects.ref, objects.nonull = c, geo, gt, dict(rows=[]), {}
    objects.data = {name: dict(accepted=[], tracks=[NS(proposals=list(seed))], raw=raw, A0=0, A1=0, A8=-1,
                               merges={'carry': [dict(ids=[0], members=dict(members))]}, points={}, objects={}, got={})}
    return objects.get(name, 'A0', 'carry')


def carried_track(slots_masks, seed_slot):
    """(seed, members, raw) for carry_diag from [(slot, 480 x 640 mask)]; a member's own mask is its 240 x 320 serving
    mask ([::2, ::2]), the resolution majority() compares against the raster."""
    raw = [[] for _ in range(32)]
    members = {}
    for slot, mask in slots_masks:
        raw[slot-1] = [dict(mask=mask)]
        members[slot] = NS(frame=slot, index=0, mask=mask[::2, ::2], score=1.)
    return [members[seed_slot]], members, raw


def published(arms=('A0_deployed', 'A2_gt_masks', 'fused_cf')):
    """Stream sb_kbox4's PER_ITEM.jsonl once, keeping the named arms by (arm, row_id)."""
    path = C.BOX/'out/box_ladder/PER_ITEM.jsonl'
    C.pin(path)
    keep = {}
    with path.open() as f:
        for line in f:
            if not any(f'"arm": "{a}"' in line[:200] for a in arms):
                continue
            r = json.loads(line)
            if r['arm'] in arms:
                keep[(r['arm'], r['row_id'])] = r
    return keep


def maskfail_records():
    """sb_maskfail's per (row, operand, anchor) records of A0's served masks, grouped by capture."""
    data = C.read_json(C.MASKFAIL/'out/MASKFAIL.json')
    by = {}
    for r in data['records']:
        by.setdefault(r['capture'], []).append(r)
    return by
