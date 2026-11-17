"""Publish the R1 binding decision and its exact reader locations."""
import ast,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix';T=L/'work/tree_r1'
def symbol(path,name):
    nodes=ast.walk(ast.parse((T/path).read_text()))
    node=next(n for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
    return 'work/tree_r1/'+path+':'+str(node.lineno)
scope=symbol('student_pilot/r1_training.py','training_components')
admit=symbol('launch_r1/entry.py','admit')
reader=symbol('student_pilot/r1_training.py','row_check')
scene=symbol('student_pilot/r2_scene_bindings.py','verify')
rows=[]
facts=[
 (False,'No R1 fusion/cache path reads this; retained for A2.',scope),
 (True,'Selection and metadata/staging binding closed; actual remote asset verification remains host work.',symbol('student_pilot/r1_training.py','start')),
 (True,'V7 receipt selected; routing manifests, complete populations and verified remote sources remain missing.',admit),
 (False,'No R1 dense-fusion path reads this; retained for A2.',scope),
 (True,'Missing the actual D0 processor min/max pixel runtime values; defaults were not guessed.',admit),
 (True,'Text reader exercised; production formatter/provenance qualification remains missing.',reader),
 (True,'Rule-text checks bind; S2 minority-form populations do not bind with S2 off.',reader),
 (False,'No R1 launch path reads the frame-64 qualification; the config fixes frame count 32.',symbol('student_pilot/r1_training.py','validate')),
 (False,'No training launch gate reads this product-serving acceptance result; it remains a product blocker.',scope),
 (True,'Complete inventory and independent scene/alias coverage are missing.',scene),
 (True,'Real pointing-mask coordinate and portrait-layout proof is missing.',symbol('student_pilot/s1_admission.py','admit')),
 (False,'No R1 fusion encoder path reads this; retained for A2 and product qualification.',scope),
 (False,'No R1 launch path reads faithful-own identity; own rows and own response probability are disabled.',symbol('student_pilot/r1_training.py','validate')),
 (True,'Independent admission and legality review remains required.',admit),
 (True,'Every exclusion stays; full post-filter membership is not yet bound.',scene)]
carried=json.loads((L/'work/build9/CARRIED_BLOCKERS.json').read_text())
assert len(carried)==len(facts)
for item,(binds,disposition,path) in zip(carried,facts):
    rows.append(dict(kind='carried blocker',name=item['blocker'],binds=binds,reader=path,
        disposition=disposition,evidence=item['evidence']))
from_names=['init_m544','heads_pose','heads_depth','heads_frame_embeddings','depth_init_vc',
 'grounding_selector_deployed','box_policy','room_policy','alias_table','depth_cut',
 'geometry_tower','segmenter','data_rows_r2','heads_gf1_connector']
for name in from_names:
    required=name not in ('grounding_selector_deployed','box_policy','room_policy','alias_table','depth_cut','heads_gf1_connector')
    gap=B/'inputs'/('EVIDENCE_'+name+'.json')
    message=json.loads(gap.read_text())['missing'] if required else (
        'No R1 training launch reads this record; native-evaluation registry requirements are unchanged.' if name!='heads_gf1_connector'
        else 'No R1 training launch reads this record when the connector is absent; the full A2 registry still requires it.')
    rows.append(dict(kind='evidence record',name='EVIDENCE_'+name+'.json',binds=required,reader=scope,
        disposition=message,evidence=str(gap.relative_to(L)) if required else 'out/RECORDS_TO_REGENERATE.md'))
(B/'BINDING_TABLE.json').write_text(json.dumps(rows,indent=2)+'\n')
text='| Blocker or evidence record | Binds a launch without GF-1 | Reader or scoped omission | State / missing input | Evidence |\n|---|---|---|---|---|\n'
for r in rows:
    text+=f"| {r['name']} | {'yes' if r['binds'] else 'no'} | `{r['reader']}` | {r['disposition']} | `{r['evidence']}` |\n"
(B/'BINDING_TABLE.md').write_text(text)
remaining=[r for r in rows if r['binds'] and 'Selection and metadata/staging binding closed' not in r['disposition']]
(B/'CARRIED_BLOCKERS.json').write_text(json.dumps(dict(r1=remaining,a2_retained=[r for r in rows if not r['binds']],
 additional=[dict(name='R1_PRODUCTION_ROW_PLAN_MISSING',missing='Full filtered populations, all-stream store hashes, final native indices, continuation identity and P boundary sidecar'),
 dict(name='R1_ALL_STREAM_IDENTITIES_REQUIRED',missing='Authenticated pose, VQA, routing and pointing store identities from final native preparation'),
 dict(name='R1_CONTINUATION_IDENTITIES_REQUIRED',missing='Nonempty continuation configuration identity and final row-plan SHA'),
 dict(name='REMOTE_ROW_SOURCE_UNVERIFIED',missing='Verified deployed sources for v7, recovery-v2, room-v2, units and rebuilt routing'),
 dict(name='R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING',missing='Complete native sandbox/staging closure, regenerated selection pin and the CPU host proof'),
 dict(name='P_EXPORT_PROGRESS_RECEIPT_MISSING',missing='A real P R1 export plus authenticated config/store/row-plan/sampler-position receipt'),
 dict(name='ROUTING_VOCABULARY_WITNESS_MISSING',missing='An export-bound native tokenizer and routing-opener vocabulary witness'),
 dict(name='SCALE_WEIGHT_RUNTIME_UNVERIFIED',missing='The supplied config uses weight 1.0, inherited as GUESS from the prior kit; actual D0 runtime settings were not supplied'),
 dict(name='RECOVERY_ROWS_ABSENT / UNIT_ROWS_ABSENT',missing='Production-admitted recovery count and all required unit marginals; text-only sample counts do not close this')]),indent=2)+'\n')
print(json.dumps(dict(rows=len(rows),launch_binding=sum(r['binds'] for r in rows))))
