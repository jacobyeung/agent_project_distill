"""Recompute review availability using the kit's Objects and mask metrics, CPU only."""
import collections
import json
import pickle
from pathlib import Path
import numpy as np
import analyze as A

T = A.T
REVIEW = Path('/scratch/jjyeung/orch_n30/sb_mfrev')

def main():
    pins = {str(p): A.sha(p) for p in [Path(__file__), A.HERE/'run.sh', A.HERE/'analyze.py', A.OUT/'MASKFAIL.json', REVIEW/'REVIEW_NUMBERS.json', REVIEW/'REVIEW_VERDICT.md', REVIEW/'compare.py', REVIEW/'rerun.py', REVIEW/'SPOTCHECK_20.json']}
    records = A.readj(A.OUT/'MASKFAIL.json')['records']
    weight = collections.Counter((r['capture'], r['object'], r['frame']) for r in records)
    unique = {(r['capture'], r['object'], r['frame']): r for r in records}
    headpath = T.R.SEL/'work/run_iso'
    for ext in ['json', 'safetensors']: T.read(headpath/f'selector_head.{ext}')
    head, _ = T.R.load_head(headpath)
    common = dict(T.PINS)
    layers = {str(t): collections.Counter() for t in A.THRESH}
    bykind = {str(t): collections.defaultdict(collections.Counter) for t in A.THRESH}
    details, endpoints, objects_out = [], [], []
    paths = sorted(A.WORK.glob('*.pkl'))
    assert len(paths) == 209
    for ci, path in enumerate(paths):
        T.PINS.clear(); T.PINS.update(common)
        pins[str(path)] = A.sha(path)
        with path.open('rb') as f: saved = pickle.load(f)
        c = saved['capture']; geo = T.R.from_arrays(**saved['geometry'])
        cachepath = T.R.K1/'run_convert_2'/T.R.digest(c['canonical'])[:16]/'candidates.json'
        cache = json.loads(T.read(cachepath))
        gt, rawgt = T.R.gt_arrays(c)
        labels = {int(i): str(n) for i, n in zip(rawgt['ids'], rawgt['labels'])}
        ref = A.readj_gz(T.R.TABLES/(A.stub(c)+'.json.gz'))
        objects = T.Objects(c, cache, geo, head, gt, ref)
        for name in sorted(saved['base']):
            d = objects.load(name)
            iid = int(c['gt_name_ids'][name][0])
            intrack = {(p.frame, p.index) for track in d['tracks'] for p in track.proposals}
            # This is the same lift call and floor used by Objects.load and StageOne.
            lifted, _ = T.F.candidates.lift(T.F.cache_for(name, d['raw']), name, geo, floor=.3, grids=objects.stage.grids, phrase=name)
            lifted_ids = {(p.frame, p.index) for p in lifted}
            assert intrack <= lifted_ids
            selected = d['tracks'][d['A0']].proposals if d['A0'] >= 0 else []
            majority = T.majority(selected, gt['instances'])
            objects_out.append(dict(capture=c['canonical'], object=name, instance=iid, exact_label_instances=sum(n == labels[iid] for n in labels.values()), selected_track_majority_instance=majority, wrong_object_track=majority is not None and majority != iid))
            for frame in range(1, 33):
                key = (c['canonical'], name, frame); r = unique[key]
                target = gt['instances'][frame-1] == iid
                pool = [(A.metrics(p['mask'][::2, ::2], target)[0] or 0., float(p['score']), (frame, k) in intrack, (frame, k) in lifted_ids) for k, p in enumerate(d['raw'][frame-1])]
                assert abs(max((p[0] for p in pool), default=0.) - r['deployed_best_iou']) < 1e-12
                if not r['valid'] or not r['visible']: continue
                for t in A.THRESH:
                    if r['iou'] >= t: continue
                    correct = [p for p in pool if p[0] >= t]
                    level = 'in_accepted_track' if any(p[2] for p in correct) else 'passes_floor_no_accepted_track' if any(p[1] >= .3 for p in correct) else 'below_floor' if correct else 'none'
                    layers[str(t)][level] += weight[key]
                    bykind[str(t)][r['failure_kinds'][str(t)]][level] += weight[key]
                    if t == .5:
                        details.append(dict(capture=c['canonical'], object=name, frame=frame, row_weight=weight[key], layer=level, correct_survives_lift=any(p[3] for p in correct)))
            objects.data.pop(name); objects.stage.raw.pop(name)
        # Reprice both endpoints from the copied, frozen geometry and lifted masks.
        for arm, objs in [('A0_deployed', saved['base']), ('A2_gt_masks', saved['gt'])]:
            endpoints.extend(A.price_rows(c, saved['rows'], geo, objs, saved['labels'], arm))
        pins.update(T.PINS)
        if (ci+1) % 20 == 0 or ci+1 == len(paths):
            print(f'Recomputed {ci+1}/{len(paths)} captures', flush=True)
    A.codepins(); pins.update(T.PINS)
    reviewer = A.readj(REVIEW/'REVIEW_NUMBERS.json')
    comparisons = {}
    for t, q in layers.items():
        expected = reviewer['availability'][t]
        mapped = dict(wrong=sum(q.values()), any_correct=sum(q.values())-q['none'], liftable_score_ge_0p3=q['in_accepted_track']+q['passes_floor_no_accepted_track'], in_accepted_track=q['in_accepted_track'])
        comparisons[t] = {k: dict(recomputed=v, reviewer=expected[k], matches=v==expected[k]) for k, v in mapped.items()}
    wrong = {(x['capture'], x['object']) for x in objects_out if x['wrong_object_track']}
    result = dict(input_sha256=pins, floor=.3, floor_location=str(T.F.candidates.__file__)+':lift', layers=layers, by_kind=bykind, reviewer_comparison=comparisons, objects=objects_out, wrong_object_tracks=len(wrong), omitted_frames_on_wrong_object_tracks=sum((r['capture'], r['object']) in wrong and r['failure_kind']=='omitted_selection' for r in records), details=details)
    A.write(A.OUT/'RECOMPUTED.json', result)
    per = A.BOX/'out/box_ladder/PER_ITEM.jsonl'; pins[str(per)] = A.sha(per)
    ids = {r['row_id'] for r in endpoints}
    old = {}
    with per.open() as f:
        for line in f:
            r = json.loads(line)
            if r['row_id'] in ids and r['arm'] in ('A0_deployed', 'A2_gt_masks'): old[(r['arm'],r['row_id'])] = r
    for r in endpoints:
        expected = old[(r['arm'], r['row_id'])]
        assert r['prediction'] == expected['prediction'] and r['label'] == expected['label']
        r.update(expected_prediction=expected['prediction'], passed=True)
    assert len(endpoints) == 2074
    A.write(A.OUT/'FRESH_ENDPOINT_PARITY.json', dict(rows=endpoints, input_sha256=pins))
    A.status('Candidate availability is recomputed with the kit’s Objects.load and routed_candidates.lift at floor 0.3. Both endpoints were repriced from the copied frozen masks and match PER_ITEM exactly on all 1,037 rows. Report rendering and packaging remain.')
    (A.HERE.parent/'STATUS.md').write_text((A.HERE/'STATUS.md').read_text())
    print(json.dumps(dict(layers=layers, wrong_object_tracks=len(wrong), omitted_frames_on_wrong_object_tracks=result['omitted_frames_on_wrong_object_tracks'], reviewer_comparison=comparisons)), flush=True)

if __name__ == '__main__': main()
