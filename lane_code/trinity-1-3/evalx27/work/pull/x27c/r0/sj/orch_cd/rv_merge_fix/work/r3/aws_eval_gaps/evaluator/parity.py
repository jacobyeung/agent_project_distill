"""Compare independent trainer encoding against native vLLM processing."""
import hashlib
import json
from evalpath.official import build_prompt_context
from media import kwargs
from cells import frame_count


def prompt(processor, task):
    if task.get('benchmark')=='pointing_video':
        from pointing_video import video_prompt
        return video_prompt(processor,task)
    if task.get('benchmark')=='pointing':
        from pointing import image_prompt
        return image_prompt(processor,task)
    text=build_prompt_context(task,'ours')
    messages=[{'role':'user','content':[{'type':'video'},{'type':'text','text':text}]}]
    value=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    if not value.endswith('<think>\n'):
        raise ValueError('Thinking generation prefix changed')
    return value


def trainer_encode(processor, task, arrays, meta, cell=None):
    cell=cell or dict(layout='spread',benchmarks=[task['benchmark']])
    frames=frame_count(cell)
    expected=frames if cell['layout']=='spread' else frames*2
    if len(arrays)!=expected or len(meta['frames_indices'])!=expected:
        raise ValueError(f'Cell requires exactly {expected} input frames')
    from transformers.video_utils import VideoMetadata
    from trainer.batches import training_text
    from trainer.pose_samples import encode_frames
    class Capture:
        def __call__(self,*args,**kw):
            return processor(*args,**kw)
        def __getattr__(self,k):
            return getattr(processor,k)
        def apply_chat_template(self,messages,**kw):
            text=messages[0]['content'][1]['text']
            if text.encode()!=build_prompt_context(task,'ours').encode():
                raise AssertionError('Trainer prompt bytes differ')
            return processor.apply_chat_template(messages,**kw)
    p=Capture()
    training_text(p,task['question'],task['options'],'0\n')
    batch,audit=encode_frames(p,task['question'],task['options'],arrays,VideoMetadata(**meta),
                             '0\n',max_length=131072)
    return batch,audit


def processor_evidence(engine, size_kwargs):
    """Obtain the HF processor through vLLM's multimodal registry, or fail the gate."""
    evidence={'requested_kwargs':size_kwargs,'fallback':'HF same-call pixel/grid comparison',
              'vllm_processor_class_verified':False}
    try:
        from vllm.multimodal import MULTIMODAL_REGISTRY
        config=getattr(engine,'model_config',None)
        if config is None:
            config=engine.vllm_config.model_config
        mm=MULTIMODAL_REGISTRY.create_processor(config)
        hf=mm.info.get_hf_processor(**size_kwargs)
        evidence.update(vllm_processor_class=type(hf).__module__+'.'+type(hf).__qualname__,
                        registry_class=type(mm).__module__+'.'+type(mm).__qualname__,
                        vllm_processor_class_verified=True)
        return hf,evidence
    except Exception as exc:
        evidence['probe_error']=type(exc).__name__
        return None,evidence


def compare(processor, engine, task, arrays, meta, observed_ids, pixels=False, cell=None):
    if cell is not None:frame_count(cell)
    if task.get('benchmark')=='pointing_video':
        from pointing_video import compare_video
        return compare_video(processor,engine,task,arrays,meta,observed_ids,pixels)
    if task.get('benchmark')=='pointing':
        from pointing import compare_image
        return compare_image(processor,engine,task,arrays,observed_ids,pixels)
    import torch
    batch,audit=trainer_encode(processor,task,arrays,meta,cell)
    expected=batch['input_ids'][0,:audit['prompt_tokens']].tolist()
    r=dict(example_id=task['example_id'],benchmark=task['benchmark'],prompt_equal=list(observed_ids)==expected,
           expected_tokens=len(expected),observed_tokens=len(observed_ids),
           expected_ids_sha256=hashlib.sha256(json.dumps(expected).encode()).hexdigest(),
           observed_ids_sha256=hashlib.sha256(json.dumps(list(observed_ids)).encode()).hexdigest())
    if not r['prompt_equal']:
        r['first_difference']=next((i for i,(a,b) in enumerate(zip(expected,observed_ids)) if a!=b),
                                    min(len(expected),len(observed_ids)))
    if pixels:
        from transformers.video_utils import VideoMetadata
        kw=kwargs(len(arrays))
        hf,evidence=processor_evidence(engine,kw)
        # If registry introspection fails, still compare the same HF call and record its limit.
        actual=hf if hf is not None else processor
        call=actual(text=[prompt(processor,task)],videos=[arrays],video_metadata=[VideoMetadata(**meta)],
                    **kw,return_tensors='pt',return_metadata=True)
        evidence['trainer_processor_class']=type(processor).__module__+'.'+type(processor).__qualname__
        evidence['same_processor_class']=type(actual) is type(processor)
        evidence['pixels_equal']=torch.equal(batch['pixel_values_videos'],call['pixel_values_videos'])
        evidence['grid_equal']=torch.equal(batch['video_grid_thw'],call['video_grid_thw'])
        evidence['grid_thw']=call['video_grid_thw'].tolist()
        evidence['pixel_shape']=list(call['pixel_values_videos'].shape)
        evidence['pass']=all(evidence[k] for k in ('vllm_processor_class_verified','same_processor_class',
                                                 'pixels_equal','grid_equal'))
        r['pixels']=evidence
    return r


def probe_tasks(cfg,tasks):
    if cfg.get('parity_per_benchmark'):
        return [(t,i) for b in sorted({t['benchmark'] for t in tasks})
                for i,t in enumerate([t for t in tasks if t['benchmark']==b][:16])]
    return [(t,i) for i,t in enumerate(tasks[:16])]
