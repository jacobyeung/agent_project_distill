"""Mechanical absence proofs for the two configuration-dependent head slots."""
from .p3_provenance import digest, load, pinned, file_pin

PREFIXES = {'heads_gf1_connector':('gf1.', 'pose.cam_token_connector.'),
            'heads_frame_embeddings':('frame_embeddings.',)}

def configuration(cfg,slot):
    from .carrier_c1_data import C1_A
    if slot not in PREFIXES:raise ValueError('NOT_PRESENT_SLOT_FORBIDDEN:'+slot)
    projection={k:cfg.get(k) for k in ('geometry_connector','geometry_online','carrier_placement','frame_embeddings')}
    if slot=='heads_gf1_connector':
        absent=projection['geometry_connector']=='none' and not projection['geometry_online']
    else:
        absent=projection['carrier_placement']==C1_A and not projection['frame_embeddings']
    if not absent:raise ValueError('NOT_PRESENT_CONFIG_NAMES_COMPONENT:'+slot)
    return projection

def clean(name):
    return name.removeprefix('module.').removeprefix('auxiliary_heads.')

def matches(name,slot):
    name=clean(name)
    return any(name==p.rstrip('.') or name.startswith(p) for p in PREFIXES[slot])

def prove(cfg,model,state,slot,inventory_pin):
    """Require a native-built module inventory and an authenticated state inventory."""
    from .carrier_c1 import CarrierC1
    import torch
    projection=configuration(cfg,slot)
    if not isinstance(model,CarrierC1):raise ValueError('NOT_PRESENT_NATIVE_BUILDER_REQUIRED')
    if (model.carrier_placement!=cfg['carrier_placement'] or model.geometry_online!=cfg.get('geometry_online')):
        raise ValueError('NOT_PRESENT_BUILDER_CONFIG_DIFFERS')
    modules=sorted(name for name,_ in model.named_modules())
    if any(matches(name,slot) for name in modules):raise ValueError('NOT_PRESENT_BUILT_MODULE:'+slot)
    tensors=sorted(name for name,value in state.items() if isinstance(value,torch.Tensor))
    if any(matches(name,slot) for name in tensors):raise ValueError('NOT_PRESENT_STATE_TENSOR:'+slot)
    import inspect
    builder=file_pin(inspect.getsourcefile(CarrierC1))
    return dict(status='NOT_PRESENT',record=dict(schema='r1-component-absence-v1',slot=slot,
        configuration=projection,builder=builder,entry='CarrierC1.__init__',modules=modules,
        inventory=inventory_pin,tensors=tensors,prefixes=list(PREFIXES[slot]),matching_tensors=0))

def build(cfg):
    """Exercise the actual constructor on meta tensors with the bound branch controls."""
    import torch
    from transformers import Qwen3_5Config,Qwen3_5ForConditionalGeneration
    from .carrier_c1 import CarrierC1
    text=dict(vocab_size=128,hidden_size=4,intermediate_size=8,num_hidden_layers=2,
        num_attention_heads=2,num_key_value_heads=1,head_dim=2,use_cache=False,
        layer_types=['linear_attention','full_attention'],linear_key_head_dim=2,
        linear_value_head_dim=2,linear_num_key_heads=2,linear_num_value_heads=2,
        rope_parameters=dict(rope_type='default',rope_theta=10000.,mrope_section=[0,0,1],partial_rotary_factor=1.))
    vision=dict(depth=3,hidden_size=4,intermediate_size=8,num_heads=1,out_hidden_size=4,
        num_position_embeddings=16,patch_size=2,temporal_patch_size=2,spatial_merge_size=2)
    config=Qwen3_5Config(text_config=text,vision_config=vision)
    for x in (config,config.text_config,config.vision_config):x._attn_implementation='sdpa'
    camera=dict(embed_dim=16,num_heads=2,trunk_depth=1,refine_iterations=1,weight_gravity=.05,weight_scale=.04,weight_focal=2.,
                supervision=cfg.get('scene_division',cfg.get('division')))
    depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=2,context_depth=1,vit_layers=[1,2,3],num_points_per_frame=1)
    with torch.device('meta'):
        base=Qwen3_5ForConditionalGeneration(config)
        return CarrierC1(base,camera,depth,2,cfg['carrier_placement'],cfg.get('training_mode','final'),
            cfg.get('depth_enabled',True),frame_layout=cfg.get('frame_layout','duplicate'),
            depth_fov_source=cfg.get('depth_fov_source','pose_head'),frame_count=cfg.get('frame_count',32),
            geometry_online=cfg.get('geometry_online'))

def evidence(cfg,artifact):
    """The persisted export pins the actual head payload; absence is never asserted from a list alone."""
    import torch
    slots=cfg.get('r1_training',{}).get('not_present_slots',[])
    if not slots:return {}
    if set(slots)!=set(PREFIXES) or len(slots)!=2:raise ValueError('NOT_PRESENT_SLOT_FORBIDDEN')
    for slot in slots:configuration(cfg,slot)
    pin=artifact.get('heads')
    if not pin:raise ValueError('NOT_PRESENT_STATE_INVENTORY_REQUIRED')
    state=torch.load(pinned(pin),map_location='meta',weights_only=True)
    if not isinstance(state,dict):raise ValueError('NOT_PRESENT_STATE_INVENTORY_INVALID')
    model=build(cfg)
    return {slot:prove(cfg,model,state,slot,pin) for slot in slots}

def verify(entry,cfg,slot):
    record=entry.get('record',{})
    if record.get('slot')!=slot or record.get('schema')!='r1-component-absence-v1':
        raise ValueError('NOT_PRESENT_RECORD_INVALID:'+slot)
    projected={**cfg,**record['configuration']}
    if any(k in cfg and cfg[k]!=v for k,v in record['configuration'].items()):
        raise ValueError('NOT_PRESENT_CONFIG_DIFFERS:'+slot)
    projected['r1_training']={**cfg.get('r1_training',{}),'not_present_slots':list(PREFIXES)}
    actual=evidence(projected,{'heads':record['inventory']})[slot]
    if actual!=entry:raise ValueError('NOT_PRESENT_PROOF_DIFFERS:'+slot)
    return entry
