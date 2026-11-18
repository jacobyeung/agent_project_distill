"""Bind named producer metadata without reading or copying a full store."""
import hashlib, json, sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import file_pin,load,write,sha256,digest
from student_pilot.r1_training import STREAMS,PARENT
from student_pilot.r2_policy import slots
def write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
D=B/'inputs';D.mkdir(exist_ok=True)
(D/'v6_receipt.json').write_bytes(Path('/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/vqa/receipt.json').read_bytes())
base=L/'work/kit07ca49df_meta/m'
parent=load(base/'k/b02e4385.json')
source=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/next_leg/R1_CARD_v2.md')
(D/'R1_CARD_v2.md').write_bytes(source.read_bytes())
weights=[('direction',32.89),('facing_pairs',18.17),('relative_distance',22.74),
 ('object_size',0),('counting',10.87),('totals',3.39),('appearance_order',14.42),
 ('first_seen_frame',2),('box_3d',1.82),('route_planning',9.70),
 ('camera_object_rel_distance_v1',2),('camera_object_rel_distance_v2',2),('camera_object_rel_distance_v3',2),
 ('object_object_left_right',2),('object_object_near_far',2),('object_object_up_down',2),
 ('room_size',0),('camera_object_abs_distance',0)]
route=[('camera_displacement',17.42),('camera_movement_direction',15.15),('camera_rotation',11.96),
       ('absolute_distance',15.60),('recovery',1),('units',2.87)]
card=dict(schema='r1-card-v1',steps=1000,seed=17,quotas=STREAMS,world=4,global_batch=288,
          source=file_pin(D/'R1_CARD_v2.md'),size_rows_per_step=0,room_rows_per_step=0,
          room_rule='Only production-admitted traced rows can enter; initial cell zero until the loader audit binds them.',
          size_source=None,camera_object_abs_distance='excluded: no admitted source',
          cells=[dict(type=k,stream=s,rows_per_step=v) for s,items in [('vqa',weights),('routing',route),('pose',[('pose',64)]),('pointing',[('pointing',32)])] for k,v in items])
write(L/'out/MIX_A0.json',card);write(D/'mix.json',card)
receipt=load(D/'v7_receipt.json');validator=load(D/'v7_validator.json')
assert validator['status']=='PASS' and not validator['validator_failures_appended']
binding=dict(receipt=file_pin(D/'v7_receipt.json'),database=receipt['database'],count=receipt['count'],
             validator=file_pin(D/'v7_validator.json'),remote_source=None,
             remote_missing='JOB_PATHS.json is PROPOSAL_FOR_CONT_OPS, not a verified deployed source')
write(D/'store_parameter.json',binding)
over=load(D/'h1_over.json')
tar=next(v for v in over['deployment']['tars'] if any(h==PARENT for h in v['files'].values()))
init=dict(artifact_sha256=PARENT,metadata=file_pin(D/'init_artifact.json'),archive=tar,
          location=over['content'][PARENT],selected_by='NEXT_LEG_INIT_RULE_20261116',start_step=0)
assert sha256(D/'init_artifact.json')==PARENT
write(D/'init.json',init)
registry=slots();write(D/'registry.json',registry)
for name in ('init_m544','heads_pose','heads_depth','heads_frame_embeddings','depth_init_vc','data_rows_r2','geometry_tower','segmenter'):
    missing = ('Complete parent scene manifests, parent membership receipts and checked-bank intersections; inherited exposure must be disclosed.'
               if name.startswith(('init','heads','depth_init')) else
               'Complete post-filter production family manifests, independent scene coverage and frame-host membership.' if name=='data_rows_r2' else
               'Upstream release identity, weights/config identity and actual optimizer frozen inventory bound together.')
    write(D/('EVIDENCE_'+name+'.json'),dict(schema='r1-evidence-gap-v1',component=name,status='BLOCKED',
          available=[file_pin(D/'init_artifact.json'),file_pin(base/'k/b02e4385.json')],missing=missing))
cfg=dict(parent)
cfg.update(geometry_connector='none',frame_count=32,frame_layout='duplicate',frame_markers=True,
           all_frames=True,routing_opener_init='keep',steps=1000,milestones=[100,200,400,600,800,1000],
           world_size=4,max_pixels=None,min_pixels=None,gate_stop=False)
cfg.update(r2_all_stream_exclusions=True,r2_scene_rebuild=None,scene_coverage=None,
           dev_scene_exclusions=file_pin(T/'student_pilot/r2_dev_merged.json'))
cfg['camera_overrides']={**parent.get('camera_overrides',{}),'weight_scale':1.0}
cfg['scheduled_sampling']={**parent['recipe']['scheduled_sampling'],'max_own_probability':0,'force_from_step':None,
                           'exposure_probability':0.0,'exposure_from_step':None}
cfg['recipe']={**parent['recipe'],'milestones':cfg['milestones'],'scheduled_sampling':cfg['scheduled_sampling']}
cfg['init_artifact']=dict(artifact=dict(path=init['location'],sha256=PARENT),heads=['pose','depth','frame_embeddings'],lm='full')
metadata=load(D/'init_artifact.json')
cfg['r2_identity']=dict(init=dict(artifact_sha256=PARENT,parent_run='469ddece',parent_kit='07ca49df',step=544,
    parent_source_seal=metadata['source_seal']['tree_sha256'],parent_configuration_prefix=metadata['config_sha256']))
cfg['routing_vocabulary']=None
cfg['streams']={**parent['streams'],'vqa':file_pin(D/'v7_receipt.json'),
                'routing':dict(required_parameter='admitted_routing_receipt')}
cfg['route_table']={**parent.get('route_table',{}),'room_size_estimation':'direct','absolute_size_room':'direct','route_planning':'direct'}
write(D/'route_table.json',cfg['route_table'])
cfg['s1_route_policy']=dict(name='frozen-table-no-flag-v1',table=file_pin(D/'route_table.json'))
cfg['h1']={'faithful_own_camera_rows':False,'metrics':True}
cfg['r1_training']=dict(schema='r1-training-v1',s2=False,stop_after_step=None,mix=file_pin(D/'mix.json'),
      store_parameter=file_pin(D/'store_parameter.json'),store_hashes={'vqa':receipt['database']['sha256']},
      registry=file_pin(D/'registry.json'),host_receipt=None,review=None,row_plan_sha256=None,
      continuation_identity=None,continuation_receipt=None,donor_config_sha256=None,
      scale_initialization='Seeded native constructor only when the entire scale branch is absent; partial heads refuse.',
      scale_weight_basis='GUESS inherited from build 9; unchanged')
row_sources={}
for family,path in [('recovery',Path('/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v2/rows.jsonl')),
                    ('room',Path('/scratch/jjyeung/orch_n30/rows_r1/out/room_v2/rows.jsonl')),
                    ('room_programs_excluded',L/'work/rows_slices/slices_final/a0_room.jsonl'),
                    ('units',L/'work/rows_slices/slices_final/a0_units.jsonl'),
                    ('absolute_distance',L/'work/rows_slices/slices_final/a0_pool_abs_distance_reworded.jsonl')]:
    row_sources[family]=dict(source=file_pin(path),remote_source=None,
                            status='Requires admitted manifest and verified remote delivery')
row_sources['room_programs_excluded']['status']='Excluded from routing and the launch room cell; retained square-foot source binding only'
write(D/'row_sources.json',row_sources)
cfg['r1_training']['row_sources']=file_pin(D/'row_sources.json')
from student_pilot.r1_training import configure_store
cfg=configure_store(cfg,file_pin(D/'v7_receipt.json'))
from student_pilot.r2_config import refresh_recipe
cfg=refresh_recipe(cfg)
from student_pilot.r1_training import validate
validate(cfg)
write(D/'config.json',cfg)
write(B/'INPUT_BINDINGS.json',dict(init=init,store=binding,mix=file_pin(D/'mix.json'),
    absent=['processor runtime resolution','verified remote VQA/routing locations','independent full scene coverage',
            'post-filter full row plans','component lineage and frozen-source evidence','frame-host proof','independent review']))
with (B/'DECISIONS.md').open('a') as f:
    f.write('\n- The room-v2 text receipt and the v7 merge were produced at different revisions. Room starts at zero until the production loader binds eligible traced rows; freed room and size slots go to direction. No source row is rewritten.\n')
(B/'STATUS.md').write_text('# Build n1 status\n\nStep-544 metadata and H1 staging archive are bound. V7 is the receipt parameter; remote placement remains unverified. R1 switches and card are written. Evidence gaps, processor resolution and production row plans remain blockers. GO=false.\n')
print(json.dumps(dict(config=file_pin(D/'config.json'),mix=file_pin(D/'mix.json'),store=binding['count'])))
