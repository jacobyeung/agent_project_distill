"""Stat named local inputs and verify the six SAM source pins; no downloads or copies."""
import collections,json
from pathlib import Path
from provenance import sha256,write_json
from probe_common import ROOT,O

def run():
    rows=[json.loads(s) for s in (ROOT/'out/b2_manifest.jsonl').read_text().splitlines()]
    tuning=[json.loads(s) for s in (ROOT/'out/tuning_manifest.jsonl').read_text().splitlines()]
    from probe_common import candidate_inputs
    groups,_,_,_=candidate_inputs();categories=collections.defaultdict(set)
    for r in rows:
        categories['Training RGB'].add(r['rgb_path']);categories['Training rasters'].add(r['raster_path'])
    for r in tuning:categories['Tuning frames32 RGB'].add(r['rgb_path'])
    for g in groups:
        categories['Tuning GT'].add(str(O/'toolprog/work/gt/scannet'/(g['scene'].split('/')[1]+'.npz')))
        categories['Linked candidates'].add(str(O/'ofs_e1/out/e1/candidates'/(g['scene'].replace('/','__')+'.json')))
        for c in g['candidates']:
            for m in c['members']:categories['SAM candidate caches'].add(m['mask_ref']['path'])
    weights=json.loads((ROOT/'out/WEIGHTS.example.json').read_text());t0=Path(weights['qwen_vit']['path']);index=t0/'model.safetensors.index.json'
    weightmap=json.loads(index.read_text())['weight_map'];categories['T0 required shards'].update(str(t0/f) for key,f in weightmap.items() if key.startswith('model.visual.') or key=='model.language_model.embed_tokens.weight');categories['T0 metadata'].add(str(index))
    categories['T0 config and tokenizer'].update(str(p) for p in (O/'mdg_build/work/t0bundle/base').glob('*') if p.is_file() and p.suffix in ('.json','.txt','.model'))
    for key,cfg in weights.items():
        if key=='qwen_vit':continue
        for field in ['path','receipt']:
            if field in cfg:categories[key].add(cfg[field])
    for category,files in {
        'Runtime helper source':[O/'ttower/work/sam3/common.py',O/'toolprog/work/tp/tplib.py',O/'mdg_build/work/cfg/confusers.json',O/'mdg_build/work/c1mix_mdg/scripts/mdg_env.sh'],
        'Label metadata':[O/'verify_kit/out/e1_k5_candidates.jsonl',O/'verify_kit/out/e1_k5_tuning_labels.jsonl',O/'label_ops/out/p2/p2_identity_labels.jsonl'],
        'O5 pending':['/scratch/jjyeung/ownenc_inputs/o5_agreement.jsonl'],
        'Lane code and manifests':list((ROOT/'work').glob('*.py'))+list((ROOT/'work/own_feats').glob('*.py'))+[ROOT/'work/RULES.json',ROOT/'work/RULES.sha256',ROOT/'work/FIT_CONFIG.json',ROOT/'out/room_gate.py',ROOT/'out/EVAL_ROOMS.json',ROOT/'out/EVAL_ROOMS.sha256',ROOT/'out/b2_manifest.jsonl',ROOT/'out/tuning_manifest.jsonl']
    }.items():categories[category].update(map(str,files))
    # Local source/environment inventories contain metadata only, never file contents.
    roots={ 'G3T source':Path(weights['g3t']['source_root']), 'SAM source':Path(weights['sam3_pe']['source_root']),
        'Environment sam3_capretry_native_v1':Path('/scratch/jjyeung/envs/sam3_capretry_native_v1'),
        'Environment p1cpu':Path('/scratch/jjyeung/envs/p1cpu'),
        'Environment fla site':O/'mdg_build/work/fla/site' }
    for cat,root in roots.items():
        if root.exists():categories[cat].update(str(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts)
        else:categories[cat].add(str(root))
    summary={};inventory=[]
    for category,paths in categories.items():
        files=[]
        for filename in sorted(paths):
            p=Path(filename);exists=p.is_file();n=p.stat().st_size if exists else None
            files.append(dict(path=filename,bytes=n,status='present' if exists else 'missing'))
        summary[category]=dict(files=len(files),present=sum(f['status']=='present' for f in files),bytes=sum(f['bytes'] or 0 for f in files),missing=[f['path'] for f in files if f['status']=='missing'])
        inventory.extend(dict(category=category,**f) for f in files)
    receipt=json.loads(Path(weights['sam3_pe']['receipt']).read_text());src=Path(weights['sam3_pe']['source_root']);checks=[]
    for filename,expected in receipt['source_files'].items():
        p=src/filename;actual=sha256(p) if p.is_file() else None
        checks.append(dict(path=str(p),expected=expected,actual=actual,status='PASS' if actual==expected else 'MISSING' if actual is None else 'FAIL'))
    assert len(checks)==6
    geometry=dict(source_host='trinity-2-18',source='/dev/shm/jjyeung_mdg_next/g3t',
        target_host='trinity-1-18',target='/dev/shm/jjyeung_evalx/g3t',
        reviewer_reported_bytes_approx=5_500_000_000,
        source_visible_in_this_namespace=Path(weights['g3t']['path']).is_file(),
        note='Review2 confirms 5.5 GB on the source host; a private RAM-disk namespace may hide it. Verify target staging before A4.')
    write_json(ROOT/'out/STAGING_INVENTORY.json',dict(summary=summary,files=inventory,geometry_weights=geometry,scope='Named local inputs, source and environment metadata only; no copies'))
    write_json(ROOT/'out/SAM_SOURCE_CHECK.json',dict(source_root=str(src),six_files=checks,ready=all(c['status']=='PASS' for c in checks)))
    lines=['# Staging inventory','', 'Exact byte counts from local stat; missing inputs have no invented size. Preserve absolute paths on the GPU node.','', '| Group | Files present / required | Bytes present |', '|---|---:|---:|']
    for key,v in summary.items():lines.append(f"| {key} | {v['present']} / {v['files']} | {v['bytes']:,} |")
    lines+=['','G3T weights: `/dev/shm/jjyeung_mdg_next/g3t` on trinity-2-18 → `/dev/shm/jjyeung_evalx/g3t` on trinity-1-18. Review2 reports approximately 5.5 GB; visibility in this private RAM-disk namespace does not establish host-wide absence. `WEIGHTS.gpu.json` uses the target path.']
    lines+=['','Every path and byte count is in `STAGING_INVENTORY.json`. Missing source and weights must be recorded in each arm’s `SKIPPED.json`.','', '| T0 shard | Exact bytes |','|---|---:|']
    for f in inventory:
        if f['category']=='T0 required shards':lines.append(f"| `{f['path']}` | {f['bytes']:,} |")
    (ROOT/'out/STAGING_INVENTORY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary))
if __name__=='__main__':run()
