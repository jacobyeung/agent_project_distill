"""Small native numerical checks; the shipped implementation stays immutable."""
import hashlib
import math
import time

TOLERANCE=1e-5
REVISION='1db216004d1812ef86986ac3feb026905416e45a'


def admitted(guard,kernel,revision,config_sha256,placement):
    common=dict(status='PASS',source_revision=revision,config_sha256=config_sha256,
                placement=placement,device='cuda',base_dtype='bfloat16',head_dtype='float32',
                target_dtype='float32',master_dtype='float32',gpu_fit_measured=True,new_gpus=1,fixture=False)
    if revision!=REVISION or any(report.get(k)!=v for report in (guard,kernel) for k,v in common.items()):
        return False
    return (guard.get('mode')=='g' and guard.get('rows')==32 and guard.get('steps')==200
            and guard.get('frames_per_row')==32 and guard.get('threshold_deg')==30.
            and finite(guard.get('initial_rotation_deg')) and guard['initial_rotation_deg']>30
            and finite(guard.get('rotation_deg')) and 0<=guard['rotation_deg']<30
            and kernel.get('mode')=='h' and kernel.get('tolerance')==TOLERANCE
            and kernel.get('same_kernels') is True
            and paired_pass(kernel.get('deltas',{}),TOLERANCE))


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def paired_pass(values,tolerance):
    if set(values)!={'0','2'}: return False
    for arm,record in values.items():
        fields=('max_abs_delta','repeat_max_abs_delta','later_max_abs_delta')
        if any(not finite(record.get(k)) or record[k]<0 for k in fields): return False
        if record['repeat_max_abs_delta']>tolerance or record['later_max_abs_delta']<=tolerance: return False
    return values['0']['max_abs_delta']<=tolerance<values['2']['max_abs_delta']


def native(placement,device,dtype):
    import torch
    from tests.test_carrier_c1 import fixture
    model,batch,target=fixture(depth_labels=False,placement=placement,
                              training_mode='pose_only',depth_enabled=False)
    # The trainer keeps FP32 masters and heads, with bf16 base compute.
    # Functional casts below preserve those masters on this single-device check.
    model.to(device)
    model.model.language_model.gradient_checkpointing_disable()
    if model.model.language_model.config._attn_implementation!='sdpa':
        raise ValueError('Attention backend differs')
    if any(p.dtype!=torch.float32 for p in model.auxiliary_heads.parameters()):
        raise ValueError('Head precision differs')
    return model,batch,target


def move(values,device):
    return {k:v.to(device) for k,v in values.items()}


def native_call(model,batch,dtype,targets=None,hidden=False):
    import torch
    class View(torch.nn.Module):
        def __init__(self):
            super().__init__();self.native=model
        def forward(self,batch,targets,hidden):
            return self.native.hidden(batch) if hidden else self.native(batch,targets)
    view=View()
    # Cast only base parameters. Autograd returns FP32 gradients to the masters;
    # AdamW and the replicated pose head retain the guard's original FP32 math.
    parameters={name:p.to(dtype) for name,p in view.named_parameters()
                if name.startswith(('native.model.','native.lm_head.'))}
    return torch.func.functional_call(view,parameters,(batch,targets,hidden))


def observed(model,batch,dtype):
    """Observe native execution without replacing masks, forwards or kernels."""
    import torch
    dtypes=[]
    hooks=[layer.self_attn.q_proj.register_forward_hook(
        lambda m,a,o:dtypes.append(str(o.dtype).removeprefix('torch.')))
        for layer in model.model.language_model.layers if layer.layer_type=='full_attention']
    try:
        with torch.no_grad(),torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as profile:
            hidden=native_call(model,batch,dtype,hidden=True)
        operators=sorted({e.key for e in profile.key_averages() if 'scaled_dot_product' in e.key})
        expected=str(dtype).removeprefix('torch.')
        if (not dtypes or set(dtypes)!={expected} or not operators
                or hidden.dtype!=dtype or hidden.device!=batch['input_ids'].device):
            raise ValueError('Native attention was not observed')
        return hidden,dict(query_dtypes=sorted(set(dtypes)),sdpa_operators=operators,
                           hidden_dtype=str(hidden.dtype).removeprefix('torch.'),device=hidden.device.type)
    finally:
        for hook in hooks: hook.remove()


def learning(placement,device,dtype):
    import torch
    from student_pilot.carrier_c1 import parameter_groups
    torch.manual_seed(31)
    model,single,target=native(placement,device,dtype)
    # Same construction, seeds, objective and optimizer as the shipped guard.
    generator=torch.Generator().manual_seed(29)
    projection=torch.randn(4,24,generator=generator)
    pixels,quaternions=[],[]
    for offset in (0.,.12):
        yaw=torch.linspace(-1.4,1.4,16)+offset
        for origin in range(16):
            angles=yaw[torch.roll(torch.arange(16),-origin)]
            signal=torch.stack((angles.sin(),angles.cos(),(2*angles).sin(),(2*angles).cos()),-1)
            pixels.append((signal@projection).repeat_interleave(4,dim=0))
            relative=(angles[0]-angles).repeat_interleave(2)
            q=torch.zeros(32,4);q[:,1]=torch.sin(relative/2);q[:,3]=torch.cos(relative/2)
            quaternions.append(q)
    batch={k:torch.cat([v]*32,dim=0) for k,v in single.items()}
    batch['pixel_values_videos']=torch.cat(pixels)
    targets={k:torch.cat([v]*32,dim=0) for k,v in target.items()}
    targets['aux_camera_target'][...,3:7]=torch.stack(quaternions)
    targets['aux_gravity_mask'].fill_(False)
    targets['aux_camera_scale'].fill_(0.)
    batch,targets=move(batch,device),move(targets,device)
    optimizer=torch.optim.AdamW(parameter_groups(model),weight_decay=.01)
    for group in optimizer.param_groups: group['lr']=1e-3
    def measure():
        model.eval()
        with torch.no_grad():
            hidden=native_call(model,batch,dtype,hidden=True).float()
            head=model.auxiliary_heads.pose
            states=head.carrier_states(hidden,batch['aux_camera_positions'])
            pred=head.predict(states)[-1]
            q=torch.nn.functional.normalize(pred[...,3:7],dim=-1)
            error=2*torch.acos((q*targets['aux_camera_target'][...,3:7]).sum(-1).abs().clamp(max=1))*180/math.pi
            if not torch.isfinite(error).all(): raise ValueError('Nonfinite metric')
        return float(error.mean()),float(error.mean(-1).max())
    initial,_=measure();started=time.perf_counter()
    for step in range(200):
        model.train();optimizer.zero_grad(set_to_none=True)
        result=native_call(model,batch,dtype,targets)
        if not torch.isfinite(result['loss']): raise ValueError('Nonfinite objective')
        result['loss'].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step()
    final,worst=measure()
    _,execution=observed(model,batch,dtype)
    ok=finite(initial) and initial>30 and finite(final) and 0<=final<30
    return dict(status='PASS' if ok else 'FAIL',rows=32,steps=200,frames_per_row=32,
                initial_rotation_deg=initial,rotation_deg=final,worst_rotation_deg=worst,
                threshold_deg=30.,seed=31,pixel_seed=29,guard_lr=1e-3,weight_decay=.01,
                grad_clip=1.,seconds=time.perf_counter()-started,execution=execution)


def reach(device,dtype):
    import torch
    from student_pilot.carrier_c1_data import C1_A,C1_C
    deltas={}
    for arm,placement in (('0',C1_A),('2',C1_C)):
        model,batch,_=native(placement,device,dtype)
        model.eval();batch=move(batch,device)
        changed={**batch,'pixel_values_videos':batch['pixel_values_videos'].clone()}
        # Four patches form the final temporal group, representing frames 31/32.
        # Both its image placeholder and its CAM states follow the first CAM.
        changed['pixel_values_videos'][-4:]*=-4
        first=int(batch['aux_camera_positions'][0,0]);last=int(batch['aux_camera_positions'][0,-1])
        token_positions=(batch['input_ids'][0]==model.config.video_token_id).nonzero().flatten()
        if len(token_positions)!=16 or not first<int(token_positions[-1])<last:
            raise ValueError('Perturbation order differs')
        before,execution=observed(model,batch,dtype)
        with torch.no_grad():
            repeat=native_call(model,batch,dtype,hidden=True)
            after=native_call(model,changed,dtype,hidden=True)
        if any(not torch.isfinite(state).all() for state in (before,repeat,after)):
            raise ValueError('Nonfinite hidden state')
        deltas[arm]=dict(max_abs_delta=float((before[:,first].float()-after[:,first].float()).abs().max()),
                        repeat_max_abs_delta=float((before[:,first].float()-repeat[:,first].float()).abs().max()),
                        later_max_abs_delta=float((before[:,last].float()-after[:,last].float()).abs().max()),
                        earlier_frame=1,later_frames=[31,32],earlier_cam=first,
                        later_image_token=int(token_positions[-1]),later_cam=last,execution=execution)
    same=deltas['0']['execution']==deltas['2']['execution']
    return dict(status='PASS' if same and paired_pass(deltas,TOLERANCE) else 'FAIL',same_kernels=same,
                tolerance=TOLERANCE,deltas=deltas,frames_per_row=32,rows=1)


def compute(mode,placement,device,dtype,fixture=False):
    import torch
    import transformers
    if mode not in ('g','h'): raise ValueError('Unknown check')
    device=torch.device(device)
    if not fixture:
        if (device.type!='cuda' or dtype!=torch.bfloat16 or not torch.cuda.is_available()
                or torch.cuda.device_count()!=1 or not torch.cuda.is_bf16_supported(including_emulation=False)):
            raise ValueError('One native bf16 device required')
        torch.cuda.set_device(device);torch.cuda.reset_peak_memory_stats(device)
    report=(learning(placement,device,dtype) if mode=='g' else reach(device,dtype))
    report.update(mode=mode,device=device.type,base_dtype=str(dtype).removeprefix('torch.'),
                  head_dtype='float32',target_dtype='float32',master_dtype='float32',fixture=fixture,
                  gpu_fit_measured=device.type=='cuda',new_gpus=int(device.type=='cuda'),
                  versions=dict(torch=str(torch.__version__),transformers=transformers.__version__,
                                cuda=torch.version.cuda))
    if device.type=='cuda':
        report['peak_allocated_bytes']=torch.cuda.max_memory_allocated(device)
        report['peak_reserved_bytes']=torch.cuda.max_memory_reserved(device)
    return report


def execute(out,mode,cfg,cur):
    import torch
    from i import identity
    from v import write
    report=dict(status='FAIL',mode=mode,source_revision=cur['commit'],
                config_sha256=identity(cfg),placement=cfg['carrier_placement'])
    path=out.with_suffix('.6.json' if mode=='g' else '.7.json')
    try:
        if cur['commit']!=REVISION: raise ValueError('Revision differs')
        report.update(compute(mode,cfg['carrier_placement'],'cuda:0',torch.bfloat16))
    except Exception as error:
        report['error_sha256']=hashlib.sha256((type(error).__name__+':'+str(error)).encode()).hexdigest()
        write(path,report)
        raise ValueError('Numerical check failed') from None
    write(path,report)
    if report['status']!='PASS': raise ValueError('Numerical check failed')
