from pathlib import Path
import json
import hashlib
import sys
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build9'
sys.path.insert(0,str(B))
# Reuse only the edit helper, without executing its edit program.
namespace={}
exec((B/'edit_core.py').read_text().split("edit('student_pilot")[0],{'__file__':str(B/'edit_core.py')},namespace)
# The helper's globals must hold the same fixed lane roots.
edit=namespace['edit'];edit.__globals__.update(namespace)
q=json.loads((L/'work/design/KIT_INPUT_QUALIFICATION.json').read_text())
mapping={}
for entry in q:
    if entry['kit']!='a0':continue
    h=entry['sha256'];member=entry.get('member','')
    parent=entry.get('parent_source') or []
    if parent and 'package_source' in parent[0]:
        p=parent[0]
        mapping[h]=dict(archive=dict(parts=[p['package_source']],sha256=p['package_sha']),member=p['name'],sha256=h)
    elif 'frame_map' in member or 'frame_plan' in member or 'input_source_tokenizer' in member:
        mapping[h]=dict(parts=['/home/jjyeung/okit/x/07ca49df/k/'+member.split('/')[-1]],sha256=h)
    elif 'vxm_m4/receipt.json' in member:
        mapping[h]=dict(parts=['/project/community/jjyeung/distill/okit/in/cr/524b14f9f180.p00'],sha256=h)
    elif '7c9f2d84' in member:
        mapping[h]=dict(parts=['/project/community/jjyeung/okh7/7c9f2d84/receipt.json'],sha256=h)
inventory={e['member']:h for h,e in mapping.items() if 'archive' in e}
for e in mapping.values():
    if 'archive' in e:e['archive']['inventory']=inventory
(T/'launch_r2/staging_sources.json').write_text(json.dumps(mapping,indent=2)+'\n')
raw=(L/'work/design/R0_SCENES.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479'
(T/'student_pilot/r0_scenes.json').write_bytes(raw)
edit('launch_r2/plan.py', "    metadata = {sha256(p):p", "    verified_sources = load(Path(__file__).with_name('staging_sources.json'))\n    metadata = {sha256(p):p")
edit('launch_r2/plan.py', "        elif original in extras:", "        elif expected in verified_sources:\n            entries[name] = verified_sources[expected]\n        elif original in extras:")
edit('launch_r2/plan.py', "entries[name] = dict(parts=['/tmp/jjyeung/in/'+expected], sha256=expected)", "entries[name] = dict(required_parameter='artifact_'+expected, sha256=expected)")
edit('launch_r2/staging.py', "        if not e.get('sha256') or not any(k in e for k in ('payload', 'parts', 'archive', 'directory')):", "        if not e.get('sha256') or not any(k in e for k in ('payload', 'parts', 'archive', 'directory', 'required_parameter')):")
edit('launch_r2/checklist.py', "        stage_inputs(plan['entries'], self.root)", "        from .input_check import sources\n        source_proof = sources(plan)\n        if 'b7_inputs' in self.cfg:\n            from student_pilot.b7_inputs import validate\n            validate(self.cfg['b7_inputs'], 'a2' if self.cfg['geometry_connector']=='gf1' else 'a0', verify=True)\n        stage_inputs(plan['entries'], self.root)")
edit('student_pilot/r2_config.py', 'overrides=True, init_pin=None):', 'overrides=True, init_pin=None, launch_inputs=None):')
edit('student_pilot/r2_config.py', '    init = selected_init(init_pin)', "    init = selected_init(init_pin) if launch_inputs is None or init_pin else None")
edit('student_pilot/r2_config.py', '        if not dense_manifest:', '        if not dense_manifest and launch_inputs is None:')
edit('student_pilot/r2_config.py', "        dense = load(pinned(dense_manifest))\n        if dense.get('schema')", "        dense = load(pinned(dense_manifest)) if dense_manifest else {'schema':'r2-dense-manifest-v1', 'reconstruct_then_subsample':True, 'clips':['required input']}\n        if dense.get('schema')")
edit('student_pilot/r2_config.py', '    return refresh_recipe(cfg)\n\n\ndef refresh_recipe', "    if launch_inputs is not None:\n        from .b7_inputs import configure as bind_inputs\n        cfg = bind_inputs(cfg, launch_inputs, 'a2' if geometry_connector=='gf1' else 'a0')\n    return refresh_recipe(cfg)\n\n\ndef refresh_recipe")
edit('launch_r2/build.py', 'overrides=True, init_pin=None):', 'overrides=True, init_pin=None, launch_inputs=None):')
edit('launch_r2/build.py', "    if not init_pin:\n        raise ValueError('Missing pinned init selection')\n    pins['init_selection'] = capsule(pinned(init_pin))", "    if not init_pin and launch_inputs is None:\n        raise ValueError('Missing pinned init selection')\n    if init_pin:\n        pins['init_selection'] = capsule(pinned(init_pin))")
edit('launch_r2/build.py', 'cfg = configure(cfg, connector, dense_manifest=dense_manifest, init_pin=init_pin)', 'cfg = configure(cfg, connector, dense_manifest=dense_manifest, init_pin=init_pin, launch_inputs=launch_inputs)')
edit('launch_r2/build.py', "    cfg['init_artifact'] = dict(artifact=dict(path='u/'+cfg['r2_identity']['init']['artifact_sha256'],\n                                            sha256=cfg['r2_identity']['init']['artifact_sha256']),\n                                heads=['pose','depth','frame_embeddings'], lm='full')", "    if cfg['r2_identity']['init'] is not None:\n        cfg['init_artifact'] = dict(artifact=dict(path='u/'+cfg['r2_identity']['init']['artifact_sha256'],\n                                                sha256=cfg['r2_identity']['init']['artifact_sha256']),\n                                    heads=['pose','depth','frame_embeddings'], lm='full')\n    else:\n        cfg['init_artifact'] = None")
edit('launch_r2/build.py', "    staging_pin = put(make(cfg, paths, base))", "    plan = make(cfg, paths, base)\n    if launch_inputs and launch_inputs.get('init') and cfg.get('init_artifact'):\n        spec = launch_inputs['init']\n        plan['entries'][cfg['init_artifact']['artifact']['path']] = dict(parts=[spec['location']],sha256=spec['sha256'])\n    staging_pin = put(plan)")
edit('launch_r2/build.py', "    (output/'BUILD.json').write_bytes(capsule_json(result))", "    if launch_inputs is not None:\n        result['blockers'] += cfg['b7_blockers']\n        result['claim_reader'] = cfg['claim_reader']\n        result['read_order'] = cfg['read_order']\n        result['launch_inputs'] = launch_inputs\n    (output/'BUILD.json').write_bytes(capsule_json(result))")
edit('student_pilot/carrier_c1_run.py', 'def validate(cfg):\n', "def validate(cfg):\n    if 'b7_inputs' in cfg:\n        from .b7_inputs import validate as validate_inputs\n        validate_inputs(cfg['b7_inputs'], 'a2' if cfg.get('geometry_connector')=='gf1' else 'a0')\n")
edit('student_pilot/carrier_c1_routing.py', "'object_size_estimation', 'object_rel_dist',", "'object_size_estimation', 'absolute_size_object', 'object_rel_distance', 'relative_distance_object',")
edit('student_pilot/carrier_c1_routing.py', "              'object_abs_dist')", "              'object_abs_distance', 'absolute_distance_object')")
edit('student_pilot/routing_type_gate.py', "{'object_size_estimation', 'object_rel_direction_easy'}", "{'object_size_estimation', 'absolute_size_object', 'object_rel_direction_easy'}")
with (B/'STATUS.md').open('a') as f:f.write('\nLaunch-input contracts and source authentication are integrated. R0 authority is pinned locally. Full row-store and frame inventories are still missing; they cannot be qualified from slices.\n')
print(json.dumps(dict(source_mappings=len(mapping),archive_members=len(inventory))))
