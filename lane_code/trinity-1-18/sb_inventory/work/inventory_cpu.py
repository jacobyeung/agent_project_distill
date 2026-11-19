"""Reconstruct parameter membership without checkpoint IO or GPU allocation."""
import sys, json, hashlib, copy, ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT/'work/sealed/work/tree_r1'
sys.path.insert(0,str(TREE))
import torch
torch.set_num_threads(2)
from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
from student_pilot.carrier_c1 import CarrierC1, parameter_groups, load_depth_stage1
from student_pilot import tower_read, sam3_tower, c1r_ref, g3t_online
def pin(p):
    p=Path(p);return dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(name,data,inputs):
    imported=[Path(m.__file__) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_relative_to(TREE) and Path(m.__file__).is_file()]
    data.update(schema='sb-frozen-inventory-v1',inputs=[pin(p) for p in sorted(set(inputs+imported))])
    (ROOT/'out/inventories'/name).write_text(json.dumps(data,indent=2)+'\n')
cfgpath=ROOT/'work/sealed/work/build19/inputs/kit_config.json'
refpath=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json')
cfg=json.loads(cfgpath.read_text());ref=json.loads(refpath.read_text())
# Native tiny Qwen architecture from N's own test fixture; production head configuration retained.
text=dict(vocab_size=64,hidden_size=32,intermediate_size=64,num_hidden_layers=2,
          num_attention_heads=4,num_key_value_heads=2,head_dim=8,use_cache=False,
          layer_types=['linear_attention','full_attention'],linear_key_head_dim=4,
          linear_value_head_dim=4,linear_num_key_heads=4,linear_num_value_heads=4,
          pad_token_id=0,rope_parameters=dict(rope_type='default',rope_theta=10000.,mrope_section=[1,1,2],partial_rotary_factor=1.))
vision=dict(depth=3,hidden_size=32,intermediate_size=64,num_heads=4,out_hidden_size=32,
            num_position_embeddings=16,patch_size=2,temporal_patch_size=2,spatial_merge_size=2)
qcfg=Qwen3_5Config(text_config=text,vision_config=vision,image_token_id=60,video_token_id=61,vision_start_token_id=62,vision_end_token_id=63)
for item in (qcfg,qcfg.text_config,qcfg.vision_config):item._attn_implementation='sdpa'
camera={**ref['camera'],**cfg['camera_overrides']};depth=copy.deepcopy(ref['depth'])
# Layer selection must exist in the explicitly reduced vision architecture.
depth['vit_layers']=[1,2,3]
with torch.device('meta'):
    base=Qwen3_5ForConditionalGeneration(qcfg)
    model=CarrierC1(base,camera,depth,5,cfg['carrier_placement'],cfg['training_mode'],cfg['depth_enabled'],cfg['recipe'],
        cfg.get('skip_unsupervised_lm'),cfg['frame_layout'],cfg['depth_fov_source'],geometry_online=cfg.get('geometry_online'),frame_count=cfg['frame_count'])
# Execute only the freeze statements from the actual loader. Loading the missing
# depth checkpoint would falsely imply that we authenticated its identity.
source=Path(sys.modules[load_depth_stage1.__module__].__file__).read_text()
fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='load_depth_stage1')
freeze=next(n for n in fn.body if isinstance(n,ast.Expr) and ast.unparse(n)=='depth.model.visual.requires_grad_(False)')
exec(compile(ast.Module(body=[freeze],type_ignores=[]),str(TREE/'student_pilot/carrier_c1.py'),'exec'),{'depth':model.auxiliary_heads.depth})
model.train()
groups=parameter_groups(model,recipe=cfg['recipe'],inherited=(),pose_lr_scale=cfg['pose_lr_scale'],lm_lr_scale=cfg['lm_lr_scale'])
optimizer=torch.optim.AdamW(groups,weight_decay=cfg['recipe']['weight_decay'])
ids={id(p):g['name'] for g in optimizer.param_groups for p in g['params']}
def rows(module,group_ids):
    return [dict(name=n,shape=list(p.shape),numel=p.numel(),requires_grad=p.requires_grad,
                 device=str(p.device),optimizer_group=group_ids.get(id(p))) for n,p in module.named_parameters()]
params=rows(model,ids)
assert set(ids)=={id(p) for p in model.parameters() if p.requires_grad}
assert not any('gf1' in r['name'] or 'geometry_encoder' in r['name'] or 'sam3' in r['name'] for r in params)
initpath=ROOT/'work/sealed/work/n1fix2/inputs/init_artifact.json'
assert not json.loads(initpath.read_text()).get('head_init')
common=[Path(__file__),ROOT/'work/run_python.sh',cfgpath,refpath,initpath,ROOT/'work/sealed/out/TREE_SEAL.json',TREE/'tests/test_carrier_c1.py',TREE/'student_pilot/carrier_c1.py',TREE/'student_pilot/carrier_c1_run.py',TREE/'student_pilot/full_ft.py']
write('optimizer.json',dict(status='RECONSTRUCTED_META',configuration=cfg,torch_version=torch.__version__,parameters=params,
    groups=[dict(name=g['name'],lr=g['lr'],weight_decay=g['weight_decay'],parameter_tensors=len(g['params']),numel=sum(p.numel() for p in g['params'])) for g in optimizer.param_groups],
    reductions=dict(text=text,vision=vision,depth_vit_layers=[1,2,3]),
    limitations=['No pretrained weights loaded; no training step performed; no historical runtime certification.',
                 'Production head settings come from the C-prime reference receipt plus N camera_overrides.',
                 'Executed the real depth-loader freeze statement without loading unavailable checkpoint files.',
                 'inherited=() follows the pinned step-544 metadata: head_init is absent, so inherited_head_names returns an empty list.',
                 'Optimizer built on unwrapped model; FSDP not initialized because this sandbox has no loopback sockets.'],
    native_train_has_g3t=hasattr(model,'tower_read'),native_train_has_sam3=hasattr(model,'sam3_tower'),
    native_train_has_gf1=hasattr(model.auxiliary_heads,'gf1')),common)
print('student groups',[(g['name'],len(g['params'])) for g in optimizer.param_groups],flush=True)
# Full, un-reduced upstream G3T architecture, using the pinned vendor source.
cls=c1r_ref.source_import(g3t_online.VENDOR)
architecture=dict(embed_dim=1024,img_size=518,patch_size=14,enable_depth=True,enable_point=True,enable_gravity_camera_heads=True)
with torch.device('meta'), g3t_online._ScalarSchedule():tower_module=cls(**architecture)
owner=tower_read.attach_tower(model,dict(device='meta',dtype='fp32',dense_frames=64),module=tower_module)
model.train()
post=parameter_groups(model,recipe=cfg['recipe'],pose_lr_scale=cfg['pose_lr_scale'],lm_lr_scale=cfg['lm_lr_scale'])
after={id(p) for g in post for p in g['params']}
assert after==set(ids)
trows=rows(tower_module,ids)
assert not any(r['requires_grad'] or r['optimizer_group'] is not None for r in trows)
write('g3t_parameters.json',dict(status='RECONSTRUCTED_FULL_ARCHITECTURE_META',architecture=architecture,parameters=trows,
    source_digest_observed=g3t_online.vendor_digest(),source_digest_expected=tower_read.SOURCE_SHA256,
    parameter_tensors=len(trows),parameter_numel=sum(r['numel'] for r in trows),optimizer_parameter_tensors=0,
    parent_train_preserves_eval=not tower_module.training,all_submodules_eval=all(not m.training for m in tower_module.modules()),
    limitations=['Meta module injected through the real attachment interface; pretrained loader/checkpoint authentication was not executed.',
                 'N training constructor does not attach this owner. This is a structural inference-attachment probe, not a production run receipt.']),
    common+[TREE/'student_pilot/tower_read.py',TREE/'student_pilot/g3t_online.py',TREE/'student_pilot/c1r_ref.py',*sorted(g3t_online.VENDOR.rglob('*.py'))])
print('G3T tensors',len(trows),'numel',sum(r['numel'] for r in trows),'optimizer',0,flush=True)
# No fake SAM architecture: only test the disabled real attachment path here.
assert sam3_tower.attach_sam3_tower(model,enabled=False) is None
assert not hasattr(model,'sam3_tower')
Path(ROOT/'STATUS.md').write_text('CPU/meta optimizer reconstruction completed using sealed N code and C-prime head settings. No GF1, G3T or SAM3 parameters occur in the student optimizer. The full G3T architecture freezes all parameters through its real attachment interface; SAM3 upstream architecture remains unavailable in the supplied sources. Draft decisions and package validation are underway.\n')
