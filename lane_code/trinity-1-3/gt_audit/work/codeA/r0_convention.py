"""R0-dev distance labels: reproduce the mesh-vertex rule and measure the same pairs under the box-grid rule.

Box rule = box_v313.box_grid_5cm (the benchmark sampler port the training labels use) on the ScanNet++ segments_anno
OBBs, after a per-instance vertex-containment check of their length convention. Read-only on rows_r1/work/r0gt.
"""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
import ast, collections, json, math, pathlib, sys
import numpy as np
from scipy.spatial import cKDTree

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
sys.path.insert(0, str(LANE / 'work/r0/code'))
import r0lib  # noqa: E402
GT = pathlib.Path('/scratch/jjyeung/orch_n30/rows_r1/work/r0gt')
Q = LANE / 'work/r0/out/qsets/R0_QUESTIONS_dev_f32.jsonl'
LABEL = pathlib.Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/tree_r1/trace_format/box_v313.py')
OUT = LANE / 'work/r0conv'


def extract(path, names):
    tree = ast.parse(path.read_text()); nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    env = {'np': np}; exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env); return env


S = extract(LABEL, {'box', 'grid_points', 'box_grid_5cm'})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(Q)]
    want = [i for i in items if i['question_type'] in ('object_abs_distance', 'object_rel_distance')]
    by_scene = collections.defaultdict(list)
    for i in want:
        by_scene[i['scene']].append(i)
    rows = []
    for si, (scene, its) in enumerate(sorted(by_scene.items())):
        sdir = GT / scene
        if not (sdir / 'scans/segments_anno.json').exists():
            for i in its:
                rows.append(dict(qid=i['qid'], scene=scene, type=i['question_type'], status='no_inputs'))
            continue
        Sc = r0lib.load_scene(str(sdir))
        anno = {int(g['id']): g for g in json.load(open(sdir / 'scans/segments_anno.json'))['segGroups']}
        inst = Sc['inst']
        keep = [k for k, it in enumerate(inst) if it['label'] not in r0lib.STRUCT and len(it['v']) >= 20
                and not any(w in it['label'] for w in ('wall', 'floor', 'ceiling'))]
        by_label = collections.defaultdict(list)
        for k in keep:
            by_label[inst[k]['label']].append(k)
        cache = {}

        def obj(label):
            if label in cache:
                return cache[label]
            ks = by_label.get(label, [])
            if len(ks) != 1:
                cache[label] = None; return None
            k = ks[0]; P = Sc['V'][inst[k]['v']]; g = anno[inst[k]['id']]['obb']
            c = np.asarray(g['centroid'], float); L = np.asarray(g['axesLengths'], float); A = np.asarray(g['normalizedAxes'], float).reshape(3, 3)
            q = np.abs((P - c) @ A.T); stable = L >= .12
            rel = np.max(q[:, stable] / L[stable], axis=1) if stable.any() else np.max(q / L, axis=1)
            inside_full = float(np.mean((q <= L * .5 + .06).all(1)))
            cache[label] = dict(P=P, tree=cKDTree(P), c=c, L=L, A=A, p98_rel=float(np.quantile(rel, .98)), inside_x1=inside_full)
            return cache[label]

        def box_d(a, b, f=1.0):
            return S['box_grid_5cm'](dict(centre=a['c'], lengths=a['L'] * f, axes=a['A']), dict(centre=b['c'], lengths=b['L'] * f, axes=b['A']))

        for i in its:
            if i['question_type'] == 'object_abs_distance':
                a, b = (obj(x) for x in i['gt']['pair'])
                if a is None or b is None:
                    rows.append(dict(qid=i['qid'], scene=scene, type=i['question_type'], status='instance_not_unique')); continue
                mesh = float(a['tree'].query(b['P'], k=1)[0].min())
                rows.append(dict(qid=i['qid'], scene=scene, type=i['question_type'], status='ok', label=float(i['answer']), stored_mesh_m=i['gt']['distance_m'],
                                 mesh_m=mesh, box_m=box_d(a, b), p98_rel=[a['p98_rel'], b['p98_rel']], inside_x1=[a['inside_x1'], b['inside_x1']]))
            else:
                t = obj(i['gt']['target']); ds = i['gt']['distances_m']
                os_ = {o: obj(o) for o in ds}
                if t is None or any(v is None for v in os_.values()):
                    rows.append(dict(qid=i['qid'], scene=scene, type=i['question_type'], status='instance_not_unique')); continue
                box = {o: box_d(t, v) for o, v in os_.items()}
                mode = i['subtype']
                pick = (min if mode == 'closest' else max)
                mesh_ans = pick(ds, key=ds.get); box_ans = pick(box, key=box.get)
                srt = sorted(box.values(), reverse=(mode == 'farthest'))
                rows.append(dict(qid=i['qid'], scene=scene, type=i['question_type'], status='ok', subtype=mode, mesh_answer=mesh_ans, box_answer=box_ans,
                                 flips=mesh_ans != box_ans, box_gap_m=abs(srt[0] - srt[1]), mesh_distances=ds, box_distances=box))
        print('scene', si + 1, len(by_scene), flush=True)
    with open(OUT / 'R0_CONVENTION_ROWS.jsonl', 'w') as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + '\n')
    ab = [r for r in rows if r['type'] == 'object_abs_distance' and r['status'] == 'ok']
    rd = [r for r in rows if r['type'] == 'object_rel_distance' and r['status'] == 'ok']
    rat = np.array([r['box_m'] / r['mesh_m'] for r in ab if r['mesh_m'] > 0])
    rel = np.array([x for r in ab for x in r['p98_rel']])
    summ = dict(abs_items=len(ab), abs_status=dict(collections.Counter(r['status'] for r in rows if r['type'] == 'object_abs_distance')),
                mesh_reproduces_label=int(sum(abs(round(r['mesh_m'], 2) - r['label']) < 1e-9 for r in ab)),
                box_over_mesh=dict(median=float(np.median(rat)), p05=float(np.quantile(rat, .05)), p25=float(np.quantile(rat, .25)), p75=float(np.quantile(rat, .75)), p95=float(np.quantile(rat, .95))),
                obb_p98_relative_extent=dict(median=float(np.median(rel)), p05=float(np.quantile(rel, .05)), p95=float(np.quantile(rel, .95)), share_in_full_band=float(np.mean((rel >= .35) & (rel <= .60)))),
                rel_items=len(rd), rel_flips=int(sum(r['flips'] for r in rd)))
    json.dump(summ, open(OUT / 'R0_CONVENTION_SUMMARY.json', 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
