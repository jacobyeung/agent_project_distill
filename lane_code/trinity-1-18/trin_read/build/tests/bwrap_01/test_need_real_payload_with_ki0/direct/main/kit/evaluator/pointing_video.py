"""Video pointing prompts with source timing and an empty assistant think block."""
import json
import math
from pathlib import Path
import re
from evalpath.items import pinned

VARIANTS=('A','B','C')
EMPTY_THINK='<think>\n\n</think>\n\n'
QUESTION=('Point to the {obj} in frame {k}. Output the point as JSON {{"point_2d": [x, y]}} with integer '
          'coordinates on a 0-1000 grid of that frame. If there is no {obj} in frame {k}, output {{"point_2d": null}}.')


def question(item,variant):
    k=item['frame']
    if variant not in VARIANTS:raise ValueError('Unknown prompt variant')
    if variant!='C':return QUESTION.format(obj=item['obj'],k=k if variant=='A' else 2*k-1)
    when=f"{item['source_index']/item['fps']:.1f} s"
    return (f"Point to the {item['obj']} at {when}. Output the point as JSON {{\"point_2d\": [x, y]}} with integer "
            f"coordinates on a 0-1000 grid of that frame. If there is no {item['obj']} at {when}, "
            'output {"point_2d": null}.')


def tasks(spec,roots):
    value=json.loads(pinned(spec['membership']).read_text())
    rows=value['items']
    variants=spec.get('variants',list(VARIANTS))
    if variants!=list(VARIANTS):raise ValueError('Pointing video requires all three variants')
    if len(rows)!=1000 or len({r['id'] for r in rows})!=1000 or value['seed']!=17:
        raise ValueError('Require fixed 1000-item seed-17 pointing membership')
    result=[]
    for r in rows:
        indices=r['frame_indices'];k=r['frame']
        if (type(k) is not int or not 1<=k<=32 or len(indices)!=32 or indices!=sorted(indices)
                or indices[k-1]!=r['source_index'] or not math.isfinite(r['fps']) or r['fps']<=0
                or any(type(i) is not int or not 0<=i<r['total_num_frames'] for i in indices)):
            raise ValueError('Invalid pointing source selection')
        for variant in variants:
            result.append(dict(example_id=r['id']+':'+variant,membership_id=r['id'],variant=variant,
                benchmark='pointing_video',question_type='point',scene=r['scene'],scene_name=r['scene'],obj=r['obj'],
                question=question(r,variant),options=[],frame=k,source_index=r['source_index'],
                timestamp_seconds=r['source_index']/r['fps'],source_frame_indices=indices,
                video_path=str(Path(roots['pointing_video_root'])/r['video_rel']),
                fps=r['fps'],total_num_frames=r['total_num_frames']))
    return result


def video_prompt(processor,task):
    from trainer.trace_contract import ANSWER_FORMAT_INSTRUCTION
    text=task['question']+'\n\n'+ANSWER_FORMAT_INSTRUCTION
    messages=[{'role':'user','content':[{'type':'video'},{'type':'text','text':text}]}]
    value=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    if not value.endswith(EMPTY_THINK):raise ValueError('Empty think generation prefix changed')
    return value


def parse_output(text):
    """Parse one JSON object before applying any coordinate interpretation."""
    text=(text or '').strip()
    text=re.sub(r'^<think>\s*</think>\s*','',text)
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text)
        text=re.sub(r'\s*```$','',text)
    try:
        def unique(pairs):
            value={}
            for key,item in pairs:
                if key in value:raise ValueError('Duplicate JSON key')
                value[key]=item
            return value
        value=json.loads(text,object_pairs_hook=unique)
        if not isinstance(value,dict) or set(value)!={'point_2d'}:raise ValueError('Expected point_2d')
        point=value['point_2d']
        if point is None:return dict(point=None,none=True,parse_failed=False)
        if (not isinstance(point,list) or len(point)!=2
                or any(type(x) not in (int,float) or not math.isfinite(x) for x in point)):
            raise ValueError('Expected finite pair')
        return dict(point=point,none=False,parse_failed=False)
    except (ValueError,TypeError,OverflowError):
        return dict(point=None,none=False,parse_failed=True)


def processed_hw(processor,height,width,count):
    from transformers.models.qwen3_vl.video_processing_qwen3_vl import smart_resize
    from media import kwargs
    v=processor.video_processor;size=kwargs(count)['size']
    return list(smart_resize(num_frames=count,height=height,width=width,
                temporal_factor=v.temporal_patch_size,factor=v.patch_size*v.merge_size,
                min_pixels=size['shortest_edge'],max_pixels=size['longest_edge']))


def compare_video(processor,engine,task,arrays,meta,observed_ids,pixels):
    import torch
    from transformers.video_utils import VideoMetadata
    from media import kwargs
    from parity import processor_evidence
    from trainer.batches import training_text
    from trainer.pose_samples import encode_frames
    target=EMPTY_THINK+'{"point_2d": null}'
    prefix,suffix=training_text(processor,task['question'],[],target)
    expected_text=prefix+suffix[:suffix.index('{"point_2d"')]
    if expected_text!=video_prompt(processor,task):raise ValueError('Trainer empty-think bytes differ')
    kw=kwargs(len(arrays))
    batch=processor(text=[expected_text],videos=[arrays],video_metadata=[VideoMetadata(**meta)],
                    **kw,return_tensors='pt',return_metadata=True)
    expected=batch['input_ids'][0].tolist()
    result=dict(benchmark='pointing_video',example_id=task['example_id'],variant=task['variant'],
                prompt_equal=list(observed_ids)==expected,expected_tokens=len(expected),observed_tokens=len(observed_ids))
    if pixels:
        trainer,audit=encode_frames(processor,task['question'],[],arrays,VideoMetadata(**meta),target,max_length=131072)
        hf,evidence=processor_evidence(engine,kw)
        actual=hf if hf is not None else processor
        call=actual(text=[video_prompt(processor,task)],videos=[arrays],video_metadata=[VideoMetadata(**meta)],
                    **kw,return_tensors='pt',return_metadata=True)
        hw=processed_hw(processor,arrays.shape[1],arrays.shape[2],len(arrays))
        evidence.update(same_processor_class=type(actual) is type(processor),
            pixels_equal=torch.equal(trainer['pixel_values_videos'],call['pixel_values_videos']),
            grid_equal=torch.equal(trainer['video_grid_thw'],call['video_grid_thw']),
            grid_thw=call['video_grid_thw'].tolist(),processed_height_width=hw,
            processed_size_equal=hw==audit['processed_height_width'])
        evidence['pass']=all(evidence[k] for k in ('vllm_processor_class_verified','same_processor_class',
                                                  'pixels_equal','grid_equal','processed_size_equal'))
        result['pixels']=evidence
    return result
