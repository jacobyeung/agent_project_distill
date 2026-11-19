"""Mask phrase kit v2, part 1 (CPU): written-phrase pools built from the stored K1 stage-1 cache and priced through the
unchanged sb_kbox4 ladder. Only the per-name detect function and the call's name change; linker, selector (run_iso,
candidates_argmax), lifting, best1 and the room bootstrap are the ladder's own code, imported read-only.

Every priced pool holds one source prompt per anchor frame, so routed_features.cache_for (which keeps one presence per
frame) sees exactly the presence each instance carries; the mixed raw-plus-alias pool is counted offline only.

    bash run.sh kit.py capture SHARD NSHARDS [ONLY]   pools, objects and row prices per capture into work/caps2/
    bash run.sh kit.py recall SHARD NSHARDS [ONLY]    unpriced pool recall (P_all, P_cf, dry-run step 2) into work/recall2/
"""
import ast, gzip, hashlib, json, resource, sys, time, traceback
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
BOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
MASKFAIL = Path('/scratch/jjyeung/orch_n30/sb_maskfail')
VARIANTLIB = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/variantlib.py')
PER_ITEM = BOX/'out/box_ladder/PER_ITEM.jsonl'
LABELS = Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')
IDS = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
KBOX_TAR = BOX/'out/sb_kbox4.tar'
WORK = HERE/'work'; CAPS = WORK/'caps2'; RECALL = WORK/'recall2'; OUT = HERE/'out'
EXPECTED = {str(IDS): 'e7646798', str(LABELS): 'd781ac7b', str(PER_ITEM): '3bc7f87f'}

sys.path.insert(0, str(BOX))
import train_pricing as T  # noqa: E402  (ladder: setup, Objects, evaluate, StageOne, cache_detect)
import predicted as P  # noqa: E402
import math_v2 as M  # noqa: E402
sys.path.insert(0, str(MASKFAIL))
import analyze as A  # noqa: E402  (metrics, classify, stats)
sys.path.remove(str(MASKFAIL))

FLOOR, CAP, LIFT = .05, 30, .3


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def pin(path):
    T.PINS[str(path)] = sha(path)
    return T.PINS[str(path)]


def stub(c):
    return c['canonical'].replace('/', '__')


def alias_table():
    """ALIASES from variantlib.py, read as a literal (the module is never executed)."""
    src = T.read(VARIANTLIB).decode()
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.Assign)
                and any(getattr(t, 'id', None) == 'ALIASES' for t in n.targets))
    return ast.literal_eval(node.value)


def alias_list(name, table):
    return sorted(set(table.get(name, [])) - {name})


def decode(p):
    rle = p['mask']; h, w = rle['size']
    counts = np.asarray(rle['counts'], np.int64)
    if np.any(counts < 0) or counts.sum() != h*w:
        raise ValueError('invalid_rle')
    return T.F.resize(np.repeat(np.arange(len(counts)) % 2 == 1, counts).reshape((h, w), order='F'), T.F.SHAPE)


def presence_of(p, record, name):
    """An instance's own presence. Raw-name instances fall back to the record's presence as cache_detect does; an alias
    instance must carry source_presence, since the record's presence belongs to the raw name's call."""
    src = p.get('source_prompt', name)
    if src != name and 'source_presence' not in p:
        raise ValueError('alias_instance_without_source_presence')
    return float(p.get('source_presence', record['presence']))


def select(record, name, prompts, cap):
    """Stored instances whose source prompt is in `prompts` (None: every prompt), each with its own presence,
    score-sorted, joint floor 0.05, cap. With prompts={name} and cap 30 this is predicted.cache_detect."""
    if record is None:
        return []
    entries = [(p.get('source_prompt', name), p, presence_of(p, record, name)) for p in record.get('instances', [])
               if prompts is None or p.get('source_prompt', name) in prompts]
    entries = sorted(entries, key=lambda e: -float(e[1]['score']))
    return [e for e in entries if float(e[1]['score'])*e[2] >= FLOOR][:cap]


def uniform(frames):
    """The reader contract: one presence per anchor frame (routed_features.cache_for keeps the first entry's)."""
    for slot, fr in enumerate(frames):
        if len({e['presence'] for e in fr}) > 1:
            raise ValueError(f'mixed_presence_frame slot={slot}')
    return frames


def pools(cache, name, table, offline=False):
    """{variant: (frames, signature, call)}; `call` is the name the reader runs with.
    raw = P0; cap100 = P_cap100; q:<a> = alias a alone (W1, W2c second call); fb:<a> = raw, and alias a's pool in the
    frames where the raw pool is empty (W2). offline=True adds all = raw plus every stored alias (P_all, recall only)."""
    decoded = {}
    def frames_for(prompts, cap):
        frames, sig = [], []
        for slot in range(32):
            record = cache['frames'][str(slot)]['phrases'].get(name)
            chosen = select(record, name, prompts, cap)
            out = []
            for src, p, pres in chosen:
                key = (slot, id(p))
                if key not in decoded:
                    decoded[key] = decode(p)
                out.append(dict(mask=decoded[key], score=float(p['score']), presence=pres, source_prompt=src))
            frames.append(out)
            sig.append(tuple((src, p.get('query'), float(p['score']), pres) for src, p, pres in chosen))
        return frames, tuple(sig)
    al = alias_list(name, table)
    out = {'raw': (*frames_for({name}, CAP), name), 'cap100': (*frames_for({name}, 100), name)}
    for a in al:
        out['q:'+a] = (*frames_for({a}, CAP), a)
    raw_frames, raw_sig, _ = out['raw']
    for a in al:
        qf, qs, _ = out['q:'+a]
        out['fb:'+a] = ([raw_frames[s] if raw_frames[s] else qf[s] for s in range(32)],
                        tuple(raw_sig[s] if raw_frames[s] else qs[s] for s in range(32)), name)
    if offline:
        out['all'] = (*frames_for(None if name in table else {name}, CAP), None)
    return out


def reader_frames(frames):
    """The entries the reader receives: mask, score and presence only (the cache_detect format)."""
    return [[dict(mask=e['mask'], score=e['score'], presence=e['presence']) for e in fr] for fr in frames]


class ArmObjects(T.Objects):
    """train_pricing.Objects with only the detect function and the call's name changed. Candidate identities come from
    this pool's own StageOne/link run; no serving-table label is read (ref rows are empty)."""
    def __init__(self, c, geo, head, gt):
        self.c = dict(c, gt_name_ids=dict(c['gt_name_ids'])); self.geo, self.gt = geo, gt
        self.ref = dict(rows=[], same_geometry=False)
        self.frames = {}; self.bound = {}
        self.stage = T.StageOne(lambda call: self.frames[call], head, geo, rule='candidates_argmax')
        self.data = {}; self.nonull = {}

    def bind(self, call, name, frames):
        self.bound[call] = self.c['gt_name_ids'].get(call)
        self.c['gt_name_ids'][call] = self.c['gt_name_ids'][name]
        self.frames[call] = frames

    def unbind(self, call):
        self.data.pop(call, None); self.stage.raw.pop(call, None); self.frames.pop(call, None)
        old = self.bound.pop(call)
        if old is None:
            self.c['gt_name_ids'].pop(call)
        else:
            self.c['gt_name_ids'][call] = old


def survival(objects, call):
    """Per-proposal score and presence after routed_features.cache_for and routed_candidates.lift, against the pool
    entries the detect function returned; covers every lifted proposal and every member of the linked tracks."""
    F, stage = T.F, objects.stage
    frames = stage.raw[call]
    props, _ = F.candidates.lift(F.cache_for(call, frames), call, stage.geometry, floor=LIFT, grids=stage.grids, phrase=call)
    members = [p for t in objects.data[call]['tracks'] for p in t.proposals]
    bad = [dict(frame=p.frame, index=p.index, score=p.score, presence=p.presence,
                entry=(frames[p.frame-1][p.index]['score'], frames[p.frame-1][p.index]['presence']))
           for p in props+members
           if p.score != frames[p.frame-1][p.index]['score'] or p.presence != frames[p.frame-1][p.index]['presence']]
    return dict(proposals=len(props), track_members=len(members), mismatched=len(bad), examples=bad[:3], passed=not bad)


def fresh_labels(producer, objects, call, geo, gt):
    """Selector labels rebuilt on this pool with the table producer's unchanged label function."""
    accepted = objects.data[call]['accepted']
    group = [dict(a, features=dict(a['features'])) for a in accepted]
    rows, _ = producer.label(objects.c, {call: group}, T.F.Geometry(geo), gt)
    return {r['candidate_id']: int(r['y']) for r in rows}


def frame_records(c, name, iid, data, obj, inst, raster, valid, classes):
    """sb_maskfail measure/classify records for the served track (seed members) and this pool."""
    choice = data['A0']
    selected = {} if choice < 0 else {p.frame: p for p in data['tracks'][choice].proposals}
    served = np.zeros((32,)+tuple(T.F.OUTPUT_SHAPE), bool)
    for f, p in selected.items():
        served[f-1] = data['raw'][f-1][p.index]['mask'][::2, ::2]
    recs = []
    for f in range(32):
        target = inst[f] == iid; m = served[f]; iou, inter, area = A.metrics(m, target)
        pool = [(A.metrics(p['mask'][::2, ::2], target)[0] or 0., p['score']) for p in data['raw'][f]]
        ids, counts = np.unique(inst[f][m], return_counts=True)
        annotated = [(int(k), int(n)) for k, n in zip(ids, counts) if int(k) in classes]
        dominant = max(annotated, key=lambda v: (v[1], -v[0])) if annotated else (None, 0)
        covered = [k for k, n in annotated if area and n/area >= .1 and n/int(np.count_nonzero(inst[f] == k)) >= .1]
        r = dict(capture=c['canonical'], dataset=c['canonical'].split('/')[0], object=name, instance=iid, frame=f+1,
                 **{'class': classes.get(iid)}, share=float(np.mean(raster[f] == iid)), iou=iou, valid=bool(valid[f]),
                 visible=bool(target.any()), served_area=area, precision=inter/area if area else 0.,
                 merged=len(covered) >= 2, dominant_id=dominant[0], dominant_class=classes.get(dominant[0]),
                 dominant_fraction=dominant[1]/area if area else 0., pool_candidates=len(pool),
                 deployed_best_iou=max((v for v, s in pool), default=0.),
                 lift_best_iou=max((v for v, s in pool if s >= LIFT), default=0.), teacher_best_iou=None,
                 teacher_status='NOT LOADED: part 1 reads the stored stage-1 cache only', pricing_best_frame=obj.get('best'))
        if not r['valid']:
            r['iou'] = None
        elif not r['visible']:
            r['iou'] = 0. if r['served_area'] else None
        r['failure_kinds'] = {str(t): A.classify(r, t) for t in A.THRESH}; r['failure_kind'] = r['failure_kinds']['0.5']
        recs.append(r)
    return recs


def category(obj, recs):
    """Design-record operand categories: refused, good, wrong_object, poor_priced_frame, weak."""
    best = obj.get('best') if obj['seen'] else None
    priced = recs[best-1]['iou'] if best and recs[best-1]['valid'] else None
    served = [r for r in recs if r['valid'] and r['served_area']]
    max_iou = max((r['iou'] or 0. for r in served), default=0.)
    max_prec = max((r['precision'] for r in served), default=0.)
    if not obj['seen']:
        kind = 'refused'
    elif priced is not None and priced >= .5:
        kind = 'good'
    elif max_iou < .1 and max_prec < .2:
        kind = 'wrong_object'
    elif max_iou >= .5:
        kind = 'poor_priced_frame'
    else:
        kind = 'weak'
    return dict(priced_frame=best, priced_iou=priced, on_target=bool(priced is not None and priced >= .5),
                category=kind, max_iou=max_iou, max_precision=max_prec)


def summarize(objects, call, name, iid, c, inst, raster, valid, classes):
    data = objects.load(call); obj, diag = objects.get(call, 'A0')
    recs = frame_records(c, name, iid, data, obj, inst, raster, valid, classes)
    taus = {}
    target = inst == iid
    for tau in M.TAUS:
        _, d = objects.get(call, 'A0', tau)
        added = []
        if data['A0'] >= 0:
            seed = {(p.frame, p.index) for p in data['tracks'][data['A0']].proposals}
            members = list(next(o for o in data['merges'][tau] if data['A0'] in o['ids'])['members'].values())
            added = [p for p in members if (p.frame, p.index) not in seed]
        mp = P.member_precision(added, target)
        taus[str(tau)] = dict(added=d['added'], correct=d['correct'], gt_members=mp['members'], gt_correct=mp['correct'])
    vis = [r for r in recs if r['valid'] and r['visible']]
    s = dict(call=call, choice=int(data['A0']), accepted=len(data['accepted']), seen=bool(obj['seen']), frames=list(obj['frames']),
             pool_per_frame=[len(f) for f in data['raw']],
             pool_recall=any(r['deployed_best_iou'] >= .5 for r in vis),
             pool_recall_lift=any(r['lift_best_iou'] >= .5 for r in vis),
             served_absent=sum(r['valid'] and not r['visible'] and r['served_area'] > 0 for r in recs),
             taus=taus, **category(obj, recs))
    return s, obj, diag, recs


def capture(c, ctx, check_builder=True):
    labels, rowids, folds, truth, head, table, producer = ctx
    start = time.monotonic()
    rows = [r for r in c['rows'] if r['id'] in rowids]
    geo, cache, meta, tower, receipt = T.R.geometry(c)
    gt, gt_raw = T.R.gt_arrays(c)
    gt['raster'] = gt_raw.get('inst', gt_raw.get('instances')); gt['valid'] = gt_raw['valid'].astype(bool)
    ref = json.loads(gzip.decompress(T.read(T.R.TABLES/(stub(c)+'.json.gz'))))
    T.PINS.update(ref['input_sha256'])
    inst, raster, valid = gt['instances'], gt['raster'], gt['valid']
    classes = {int(i): str(n) for i, n in zip(gt_raw['ids'], gt_raw['labels'])}
    label_gt = dict(instances=gt['instances'], frame_indices=gt['frame_indices'])
    names = sorted({n for r in rows for n in r['operands']})
    base = T.Objects(c, cache, geo, head, gt, ref)
    arms = {}
    out, objs, diags, builder, checks, refused = {}, {}, {}, [], [], []
    for name in names:
        iid = c['gt_name_ids'][name]; assert len(iid) == 1; iid = int(iid[0])
        pv = pools(cache, name, table)
        keys, results, vmap, calls = {}, {}, {}, {}
        for v, (frames, sig, call) in pv.items():
            uniform(frames)
            if (call, sig) in keys:
                vmap[v] = keys[(call, sig)]; continue
            k = f'k{len(results)}'; keys[(call, sig)] = k; vmap[v] = k; calls[k] = call
            if v == 'raw':
                objects = base
            else:
                if v not in arms:
                    arms[v] = ArmObjects(c, geo, head, gt)
                objects = arms[v]; objects.bind(call, name, reader_frames(frames))
            try:
                results[k] = summarize(objects, call, name, iid, c, inst, raster, valid, classes)
            except Exception as exc:  # dry-run step 3: report the reader's exact refusal; reader code is not edited
                if v == 'raw':
                    raise
                refused.append(dict(name=name, variant=v, call=call, error=f'{type(exc).__name__}: {exc}',
                                    traceback=traceback.format_exc()[-1500:]))
                del vmap[v], keys[(call, sig)], calls[k]; objects.unbind(call); continue
            surv = survival(objects, call)
            fresh = fresh_labels(producer, objects, call, geo, label_gt)
            accepted = objects.data[call]['accepted']; a0 = objects.data[call]['A0']
            ids = [a['candidate_id'] for a in accepted]
            positive = [i for i, a in enumerate(ids) if fresh.get(a) == 1]
            tracks = objects.data[call]['tracks']
            oracle = min(positive, key=lambda i: (-len(tracks[i].proposals), i)) if positive else a0
            lab = dict(candidates=len(ids), positives=len(positive), selected_y=fresh.get(ids[a0]) if a0 >= 0 else None,
                       oracle=oracle, identities_match=set(fresh) == set(ids), source='fresh: table producer label() on this pool')
            if v == 'raw':
                table_y = {r['candidate_id']: int(r['y']) for r in ref['rows'] if r['name'] == name}
                lab['equals_serving_table'] = table_y == fresh
            results[k][0].update(survival=surv, labels=lab)
            checks.append(dict(name=name, key=k, variant=v, call=call, survival=surv['passed'], identities=lab['identities_match'],
                               table=lab.get('equals_serving_table')))
            if v == 'raw' and check_builder:
                ref_frames = base.stage.raw[name]
                same = all(len(a) == len(b) and all(x['score'] == y['score'] and x['presence'] == y['presence']
                           and np.array_equal(x['mask'], y['mask']) for x, y in zip(a, b)) for a, b in zip(ref_frames, frames))
                builder.append(dict(name=name, passed=bool(same)))
        al = alias_list(name, table)
        raw = results[vmap['raw']][0]
        fills = {}
        for a in al:
            if 'q:'+a in vmap:
                vmap['call:'+a] = vmap['raw'] if raw['seen'] else vmap['q:'+a]
            fq, fr = pv['q:'+a][0], pv['raw'][0]
            fills[a] = sum(bool(fq[s]) and not fr[s] for s in range(32))
        out[name] = dict(instance=iid, aliases=al, in_dictionary=name in table, variants=vmap, calls=calls, fills=fills,
                         prompts=stored_prompts(cache, name), keys={k: v[0] for k, v in results.items()},
                         records={k: v[3] for k, v in results.items()})
        objs[name] = {k: v[1] for k, v in results.items()}; diags[name] = {k: v[2] for k, v in results.items()}
        for v, o in arms.items():
            for call in list(o.bound):
                o.unbind(call)
        base.data.pop(name, None); base.stage.raw.pop(name, None)
    items = []
    for row in rows:
        a, b = row['operands']; assert a != b
        combos = set()
        for family in families(out[a]['variants'], out[b]['variants']):
            combos |= family
        for ka, kb in sorted(combos):
            r = T.evaluate(c, [row], geo, {a: objs[a][ka], b: objs[b][kb]}, 'combo', 'best1', labels, folds, truth, gt,
                           {a: diags[a][ka], b: diags[b][kb]}, meta)[0]
            r['keys'] = {a: ka, b: kb}
            items.append(r)
    return dict(capture=c['canonical'], room=c['room'], fold=folds[c['room']], dataset=c['canonical'].split('/')[0],
                k1_split=c['k1_split'], rows=[dict(id=r['id'], operands=r['operands'], gt_instances=r['gt_instances']) for r in rows],
                names=out, items=items, builder_parity=builder, checks=checks, reader_refused=refused, arms_built=sorted(arms),
                seconds=time.monotonic()-start, peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)


def families(va, vb):
    """Key pairs some arm can serve: P_cap100 (cap100 for both), W1 and W2c (raw or q:*), W2 (raw or fb:*)."""
    def keys(vm, prefix):
        return {vm['raw']} | {k for v, k in vm.items() if v.startswith(prefix)}
    yield {(va['cap100'], vb['cap100'])}
    for prefix in ('q:', 'fb:'):
        yield {(x, y) for x in keys(va, prefix) for y in keys(vb, prefix)}


def stored_prompts(cache, name):
    """Count of stored instances per source prompt, and of those above the joint floor."""
    count, above = {}, {}
    for slot in range(32):
        record = cache['frames'][str(slot)]['phrases'].get(name)
        if record is None:
            continue
        for p in record.get('instances', []):
            src = p.get('source_prompt', name)
            pres = float(p.get('source_presence', record['presence']))
            count[src] = count.get(src, 0)+1
            above[src] = above.get(src, 0)+int(float(p['score'])*pres >= FLOOR)
    return dict(stored=count, above_floor=above)


def write_gz(path, obj):
    tmp = path.with_suffix('.tmp')
    with gzip.open(tmp, 'wt') as f:
        json.dump(T.clean(obj), f, separators=(',', ':'), allow_nan=False)
    tmp.rename(path)


def setup(threads=2):
    caps, labels, rowids, tableids, folds, truth, head = T.setup()
    T.torch.set_num_threads(threads)
    table = alias_table()
    producer = T.R.producers({c['canonical'] for c in caps})
    for p in [HERE/'kit.py', HERE/'run.sh', MASKFAIL/'analyze.py', MASKFAIL/'RULES.md', BOX/'run.sh', HERE/'out/BARS.json']:
        T.read(p)
    return caps, (labels, rowids, folds, truth, head, table, producer)


def recall(c, ctx):
    """Unpriced: does each pool hold an IoU >= 0.5 mask of the operand in a valid visible anchor, at the retention floor
    and at the lifting floor (score >= 0.3) as well."""
    labels, rowids, folds, truth, head, table, producer = ctx
    rows = [r for r in c['rows'] if r['id'] in rowids]
    cache = json.loads(T.read(T.R.K1/'run_convert_2'/T.R.digest(c['canonical'])[:16]/'candidates.json'))
    gt, gt_raw = T.R.gt_arrays(c); inst = gt['instances']; valid = gt_raw['valid'].astype(bool)
    out = {}
    for name in sorted({n for r in rows for n in r['operands']}):
        iid = int(c['gt_name_ids'][name][0]); res = {}
        for v, (frames, sig, call) in pools(cache, name, table, offline=True).items():
            hits, lift = [], []
            for f in range(32):
                target = inst[f] == iid
                if not (valid[f] and target.any()):
                    continue
                ious = [(A.metrics(p['mask'][::2, ::2], target)[0] or 0., p['score']) for p in frames[f]]
                if max((i for i, s in ious), default=0.) >= .5:
                    hits.append(f+1)
                if max((i for i, s in ious if s >= LIFT), default=0.) >= .5:
                    lift.append(f+1)
            res[v] = dict(recall=bool(hits), frames=hits, recall_lift=bool(lift), frames_lift=lift,
                          candidates=sum(map(len, frames)), mixed_presence_frames=sum(len({e['presence'] for e in fr}) > 1 for fr in frames))
        out[name] = dict(instance=iid, aliases=alias_list(name, table), in_dictionary=name in table, pools=res)
    return dict(capture=c['canonical'], room=c['room'], fold=folds[c['room']], dataset=c['canonical'].split('/')[0],
                k1_split=c['k1_split'], rows=[dict(id=r['id'], operands=r['operands']) for r in rows], names=out)


def main():
    mode = sys.argv[1]; assert mode in ('capture', 'recall')
    shard, n = int(sys.argv[2]), int(sys.argv[3])
    only = set(sys.argv[4].split(',')) if len(sys.argv) > 4 else None
    caps, ctx = setup(); common = dict(T.PINS)
    folder = CAPS if mode == 'capture' else RECALL
    folder.mkdir(parents=True, exist_ok=True)
    todo = [c for c in sorted(caps, key=lambda c: c['canonical']) if only is None or c['canonical'] in only][shard::n]
    for c in todo:
        dest = folder/(stub(c)+'.json.gz')
        if dest.exists():
            continue
        T.PINS.clear(); T.PINS.update(common)
        start = time.monotonic()
        result = capture(c, ctx) if mode == 'capture' else recall(c, ctx)
        result['input_sha256'] = dict(T.PINS)
        write_gz(dest, result)
        print(json.dumps(dict(mode=mode, capture=c['canonical'], seconds=round(time.monotonic()-start, 1),
                              refused=len(result.get('reader_refused', [])),
                              peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)), flush=True)


if __name__ == '__main__':
    main()
