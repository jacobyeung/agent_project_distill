"""Train-only geometry provenance and StageOne replay; no fitting or held-out reads."""
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import resource
import sys
import time
import numpy as np
import torch
from adapters import ROOT, TREE, READER, reviewed_loader
from dryrun import read, write, PINS, OUT
from predicted import cache_detect

PACK = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')
SEL = READER/'heads/selector'
K1 = Path('/scratch/jjyeung/k1')
sys.path[:0] = [str(ROOT/'reader_src'), str(SEL/'sl118'), str(SEL), str(TREE)]
from e2e_reader.stage1 import StageOne, median_ratio
from e2e_reader.geometry import from_tower
from selector_head import load_head
from student_pilot import camera_targets, tower_scale_rule
from student_pilot.scene_state import FrameMap


def npz(p):
    with np.load(io.BytesIO(read(p)), allow_pickle=False) as z:
        return {k:z[k] for k in z.files}


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def functions(path, names, bindings):
    tree = ast.parse(read(path).decode())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names)
    exec(compile(ast.Module(nodes, []), str(path), 'exec'), bindings)
    return bindings


def sources():
    for p in [ROOT/'KIT_SPEC_box_ladder_k1_v2.md', ROOT/'run.sh', ROOT/'debug_geometry.py',
              PACK/'R1_A4_SRC_SHA256.txt', PACK/'MANIFEST.sha256',
              PACK/'r1_src/b/heads/selector/sl118/sl_tables.py',
              PACK/'r1_src/b/heads/selector/isolate_tables.py',
              K1/'CONVERT1.log', K1/'CONVERT2.log',
              SEL/'sl118/SCALES_S4.json']:
        read(p)
    for m in list(sys.modules.values()):
        p = getattr(m, '__file__', None)
        if p and p.endswith('.py') and p.startswith((str(ROOT),str(TREE),str(READER))):
            read(p)


def main():
    torch.set_num_threads(8)
    started = time.monotonic()
    OUT.mkdir(exist_ok=True, parents=True)
    head_dir = SEL/'work/run_iso'
    for ext in ['json','safetensors']: read(head_dir/f'selector_head.{ext}')
    head, _ = load_head(head_dir)
    caps = json.loads(read(ROOT/'train_manifest.json'))['captures']
    train_ids = set(read('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_TABLES_883.txt').decode().splitlines())
    chosen = []
    for dataset in ['arkitscenes','scannet','scannetpp']:
        eligible = [c for c in caps if c['canonical'].startswith(dataset+'/') and
                    any(r['id'] in train_ids for r in c['rows']) and
                    (SEL/'data/caps_iso'/(c['canonical'].replace('/','__')+'.json.gz')).is_file()]
        chosen.extend(sorted(eligible, key=lambda c:c['canonical'])[:15])
    assert len(chosen) >= 20 and all(c['k1_split']=='train' for c in chosen)
    write(OUT/'REPLAY_SAMPLE.json', dict(policy='First 15 canonical-sorted train table captures per dataset; all registered distance operand names with table inputs; fixed before replay',
        captures=[c['canonical'] for c in chosen]))
    loader, guard, _ = reviewed_loader()
    # Execute the table producer's exact geometry function, with only loader binding changed.
    table_functions = functions(PACK/'r1_src/b/heads/selector/sl118/sl_tables.py',
        ['g1','geometry_npz'], dict(np=np, camera_targets=camera_targets, load_geometry=loader, FrameMap=FrameMap))
    scales = json.loads(read(SEL/'sl118/SCALES_S4.json'))
    results, provenance = [], []
    for c in chosen:
        canonical = c['canonical']; key = digest(canonical)[:16]; slug = canonical.replace('/','__')
        rec = json.loads(gzip.decompress(read(SEL/'data/caps_iso'/(slug+'.json.gz'))))
        tower = npz(K1/'run_tower_sam_2'/key/'tower.npz')
        receipt = json.loads(read(K1/'run_tower_sam_2'/key/'PHASE_COMPLETE.json'))
        cache = json.loads(read(K1/'run_convert_2'/key/'candidates.json'))
        meta = json.loads(read(K1/'run_convert_2'/key/'CACHE_COMPLETE.json'))
        gdpath = K1/'run_convert_2'/key/'geometry.npz'
        gd_available = gdpath.is_file()
        gdarrays = npz(gdpath if gd_available else gdpath.with_name('REFUSED_GEOMETRY.npz'))
        own = npz(K1/'own_170235/native/probe'/key/'own.npz')
        own_receipt = json.loads(read(K1/'own_170235/native/probe'/key/'PHASE_COMPLETE.json'))
        assert own_receipt['capture_sha256'] == receipt['capture_sha256'] == meta['capture_sha256']
        assert PINS[str(K1/'own_170235/native/probe'/key/'own.npz')] == own_receipt['files']['own.npz']
        assert rec['tower_sha256'] == PINS[str(K1/'run_tower_sam_2'/key/'tower.npz')]
        assert rec['candidates_sha256'] == PINS[str(K1/'run_convert_2'/key/'candidates.json')]
        assert rec['scale'] == scales['captures'][canonical]['S4']
        gated, mask, threshold = tower_scale_rule.estimate(tower['depth_grid'],tower['depth_conf_grid'],own['depth'])
        serving = median_ratio(tower['depth_grid'],tower['depth_conf_grid'],own['depth'])
        serving_float = float(torch.tensor(float(np.log(serving))).exp())
        gd = None
        if gd_available:
            with guard.capture('train_debug_GD',canonical):
                gd = loader(gdpath, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
        with guard.capture('train_debug_table',canonical):
            export = ROOT/'work/table_geometry'/(slug+'.npz')
            tablegeo = table_functions['geometry_npz'](c,tower,receipt['source_hw'],table_functions['g1'](tower),rec['scale'],export)
        # Actual serving geometry entry point, replayed on cached checkpoint own outputs.
        livegeo = from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],
            tower['grid_uv'],own['gravity'],serving_float,receipt['source_hw'])
        same_scale_geo = from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],
            tower['grid_uv'],own['gravity'],float(gdarrays['scale']),receipt['source_hw'])
        recreate_sha = hashlib.sha256(export.read_bytes()).hexdigest()
        p = dict(capture=canonical, dataset=canonical.split('/')[0], digest=key,
            table_scale=rec['scale'], table_scale_rule='S4 train-fitted h_raw/span; no own-depth scale',
            table_geometry_sha256=rec['geometry_sha256'], recreated_table_geometry_sha256=recreate_sha,
            table_export_bytes_match=recreate_sha==rec['geometry_sha256'],
            gd_scale=float(gdarrays['scale']), own_gated_scale=gated, reader_ungated_scale=serving,
            reader_float32_scale=serving_float, gd_matches_gated=bool(np.isclose(float(gdarrays['scale']),gated,rtol=0,atol=1e-12)),
            relative_reader_scale_change=serving/float(gdarrays['scale'])-1,
            own_gravity=own['gravity'], table_gravity=table_functions['g1'](tower),
            gd_status='OK' if gd_available else 'MISSING',
            gd_missing_path=None if gd_available else str(gdpath),
            gd_refusal=meta.get('geometry_refusal'),
            gd_reader_camera_max_error=None if gd is None else float(np.max(np.abs(gd.C-same_scale_geo.C))),
            source_checkpoint=own_receipt['checkpoint'],
            own_depth_outside_gate=int(np.count_nonzero((own['depth']<=.1)|(own['depth']>=10))))
        old = K1/'run_convert_1'/key/'geometry.npz'
        if old.is_file():
            oldarr = npz(old); p['convert1_scale']=float(oldarr['scale']);p['convert1_equals_convert2']=PINS[str(old)]==PINS.get(str(gdpath))
        provenance.append(p)
        names = sorted({name for r in c['rows'] if r['id'] in train_ids for name in r['operands']} & {i['name'] for i in rec['inputs']})
        for geom_name, geo in [('GD_convert2',gd),('table_S4_G1',tablegeo),('reader_own_ungated',livegeo)]:
            stage = StageOne(cache_detect(cache), head, geo, rule='null_argmax') if geo is not None else None
            for name in names:
                inputs = [i for i in rec['inputs'] if i['name']==name]
                with torch.no_grad():
                    logits = head.with_null(torch.tensor([i['x'] for i in inputs],dtype=torch.float64),None,name)
                idx = int(torch.argmax(logits)); expected = None if idx==len(inputs) else inputs[idx]['candidate_id']
                accepted, vectors = stage.features(name) if stage is not None else ([],[])
                choice = stage.select(dict(x=torch.tensor(vectors,dtype=torch.float64),name=name)) if accepted else -1
                got = None if choice<0 else accepted[choice]['candidate_id']
                vector_map = {a['candidate_id']:x for a,x in zip(accepted,vectors)}
                shared = [i for i in inputs if i['candidate_id'] in vector_map]
                err = max([float(np.max(np.abs(np.array(i['x'])-vector_map[i['candidate_id']]))) for i in shared],default=None)
                results.append(dict(capture=canonical,dataset=canonical.split('/')[0],name=name,geometry=geom_name,
                    expected=expected,got=got,passed=got==expected and stage is not None,
                    refusal_code=meta.get('geometry_refusal',{}).get('code') if stage is None else None,
                    selected_frames=[] if choice<0 else sorted(accepted[choice]['masks']),
                    table_selected_members=[] if expected is None else next(r['members'] for r in rec['rows'] if r['name']==name and r['candidate_id']==expected),
                    max_feature_error=err, shared_candidates=len(shared), expected_candidates=len(inputs),
                    actual_candidates=len(accepted),candidate_id_set_equal=set(vector_map)=={i['candidate_id'] for i in inputs}))
        print(json.dumps(dict(capture=canonical,choices=len(names),gd=p['gd_scale'],reader=serving,table=p['table_scale'],table_bytes_match=p['table_export_bytes_match'])),flush=True)
    summary = {}
    for geom in ['GD_convert2','table_S4_G1','reader_own_ungated']:
        summary[geom] = {}
        for dataset in ['all','arkitscenes','scannet','scannetpp']:
            rows=[r for r in results if r['geometry']==geom and (dataset=='all' or r['dataset']==dataset)]
            n=len(rows); m=sum(r['passed'] for r in rows)
            summary[geom][dataset]=dict(matched=m,total=n,rate=m/n,passed=m/n>=.95,captures=len({r['capture'] for r in rows}),
                exact_feature_objects=sum(r['max_feature_error']==0 and r['candidate_id_set_equal'] for r in rows),
                max_feature_error=max(r['max_feature_error'] or 0 for r in rows))
    assert summary['GD_convert2']['all']['total']>=100
    sources()
    write(OUT/'REPLAY_EXPANDED.json',dict(summary=summary,rows=results,seconds=time.monotonic()-started,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
    write(OUT/'GEOMETRY_PROVENANCE.json',dict(captures=provenance,scale_provenance=scales['source'],coefficients=scales['coefficients']))
    (ROOT/'STATUS.md').write_text('Geometry diagnosis and expanded training replay are complete. The evidence files record table, convert, and serving-rule results, with input hashes. Pricing remains gated on A0 matching the serving reader; no held-out evaluation ran.\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__': main()
