"""Read-only bindings to sb_kbox4's unchanged ladder (train_pricing, pricing, summarize_train, predicted)."""
import gzip, json, sys
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
