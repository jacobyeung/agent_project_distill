"""Use N's native routed reader and preserve the provenance of each emitted token."""
from .choice import SamplingChoice, sampling_hooks, align

def sample(model,processor,batch,*,seed=17,max_tokens=1024,temperature=.7,prefix='',decode=None):
    from student_pilot.carrier_c1_decode import generate
    # Production uses no forced prefix. CPU integration fixtures may force call openers.
    choice=SamplingChoice(processor.tokenizer.encode(prefix,add_special_tokens=False),seed=seed,
                          temperature=temperature,top_p=1.,max_sampled_tokens=max_tokens,
                          eos_id=processor.tokenizer.eos_token_id)
    model.eval()
    from student_pilot.carrier_c1_batch_decode import RowRefusal
    from student_pilot.tower_errors import TowerError
    try:
        with sampling_hooks():
            record=generate(model,processor,batch,reference_trace=choice,**(decode or {}))
    except (RowRefusal, TowerError) as exc:
        return refused(exc)
    if record.get('tower_error'):
        return dict(record, refusal='TowerError: '+str(record['tower_error']),
                    kinds=[], logp_tempered=[], logp_raw=[])
    kinds,tempered,raw=align(record,choice)
    record.update(kinds=kinds,logp_tempered=tempered,logp_raw=raw,temperature=temperature,
                  top_p=1.,budget_hit=choice.budget_hit,seed=seed)
    return record


def native_kwargs(model,prompt,batch,artifact_pin,audit_dir,settings=None):
    from .serving import build_backend,POSE_SOURCE
    # N's LiveSession serves every 3.14 draw, including a camera/direct draw.
    backend=build_backend(model,prompt['row'],batch,artifact_pin,audit_dir,settings)
    return dict(pose_source=POSE_SOURCE,ground_backend=backend,mask_source=backend.mask_source,
                max_calls=200)


def tower_batch(row,batch):
    from student_pilot.tower_errors import tower_guard
    return tower_guard(_tower_batch)(row,batch)


def _tower_batch(row,batch):
    """Use only explicitly pinned native RGB frames and exact native-index matches."""
    from PIL import Image
    from student_pilot.r2_frames import verify_frame
    source=row['student_input'].get('geometry_dense',row['student_input'])
    indices=source['frame_indices']
    if len(indices)!=len(source['frames']) or len(indices) not in (32,64,96):
        raise ValueError('MISSING complete native tower frame selection')
    anchors=batch['frame_indices']
    if len(set(indices))!=len(indices) or any(i not in indices for i in anchors):
        raise ValueError('Native LM/tower frame indices disagree')
    images=[]
    for pin in source['frames']:
        with Image.open(verify_frame(pin)) as im:
            if im.mode!='RGB':raise ValueError('Native frame must be RGB')
            images.append(im.copy())
    return dict(batch,tower_native_frames=images,tower_frame_indices=list(indices),
                tower_anchor_slots=[indices.index(i) for i in anchors])


def refused(exc):
    return dict(text='', tokens=[], calls=[], kinds=[], logp_tempered=[], logp_raw=[],
                finish='refused', refusal=type(exc).__name__+': '+str(exc))


def diagnostic_own(model, processor, batch, **kwargs):
    """Print a separate own-head diagnostic; score() rejects this arm."""
    from student_pilot.carrier_c1_decode import generate
    record=generate(model, processor, batch, pose_source='own', **kwargs)
    record['diagnostic_arm']='own_heads'
    print({'diagnostic_arm':'own_heads', 'heads':record.get('heads')}, flush=True)
    return record
