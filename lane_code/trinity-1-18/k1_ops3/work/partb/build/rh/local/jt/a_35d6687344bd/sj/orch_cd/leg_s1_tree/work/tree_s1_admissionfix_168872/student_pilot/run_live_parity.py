"""Independent kit parity. Run --processor-only before scheduling the live read.

The adapter must expose load_processor(inputs), load(inputs,device), routed,
score_routed, addressing, video_address, and score_addressing. Inputs name the
local HF T0 checkpoint in hf_checkpoint. Reference weights live in a separate
serial subprocess; the reference is the kit's actual HFBackend constructor.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,math,os,subprocess,sys,time
from collections import Counter

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def numerical_provenance(model):
    import torch
    device=next(model.parameters()).device
    return dict(gpu_name=torch.cuda.get_device_name(0) if device.type=='cuda' else None,
                cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                parameter_dtype=str(next(model.parameters()).dtype), device=str(device))

from student_pilot.precision_parity import probability_parity, capture_inputs, check_probabilities
from student_pilot.acceptance_evidence import stage_assertions, addressing_evidence, check_addressing, save


def reference_predictions(reference, crops, images):
    from verifykit.render import prompt
    def predict(indices):
        requests=[dict(form='V1',name=crops[i]['request']['name'],
                       prompt=prompt('V1',crops[i]['request']['name'])) for i in indices]
        ims=[images[i] for i in indices]
        with capture_inputs(reference.model,reference.processor,ims) as evidence:
            predictions=reference.predict(requests,ims)
        return [dict(index=i,rgb_sha256=crops[i]['rgb_sha256'],name=crops[i]['request']['name'],
                     p_yes=r['probabilities'][0],token_groups=r['token_groups'],inputs=e)
                for i,r,e in zip(indices,predictions,evidence)]
    started=time.monotonic()
    mixed=predict(list(range(len(crops))))
    mixed_seconds=time.monotonic()-started
    started=time.monotonic()
    grouped=[]
    for name in dict.fromkeys(c['request']['name'] for c in crops):
        grouped.extend(predict([i for i,c in enumerate(crops) if c['request']['name']==name]))
    reference.parity_seconds=dict(mixed=mixed_seconds,grouped=time.monotonic()-started)
    return mixed,grouped


def routed_predictions(native,processor,crops,images,references):
    import torch
    from student_pilot import verify_pass as V
    from student_pilot.reread_isolation import isolated
    keyed={r['index']:r for r in references['rows']}
    grouped={r['index']:r for r in references['grouped_rows']}
    results=[]
    for name in dict.fromkeys(c['request']['name'] for c in crops):
        indices=[i for i,c in enumerate(crops) if c['request']['name']==name]
        ims=[images[i] for i in indices];meta=[[dict(candidate_id=str(i))] for i in indices]
        with torch.inference_mode(),capture_inputs(native,processor,ims) as evidence:
            actual=isolated(native,lambda:V._forward_form(native,processor,name,'V1',ims,meta))
        for i,row,audit in zip(indices,actual,evidence):
            expected=keyed[i];repeat=grouped[i]
            results.append(dict(index=i,rgb_sha256=crops[i]['rgb_sha256'],name=name,
                inside=row['p_yes'],reference=expected['p_yes'],reference_grouped=repeat['p_yes'],
                absolute_error=abs(row['p_yes']-expected['p_yes']),
                reference_inputs=expected['inputs'],grouped_inputs=repeat['inputs'],inside_inputs=audit,
                reference_token_groups=expected['token_groups'],inside_token_groups=row['token_groups']))
    return sorted(results,key=lambda r:r['index'])


def cpu_matched_rows(results):
    """Isolate implementation parity from the reference's own fp32 batch rounding."""
    return [dict(r, mixed_reference=r['reference'], mixed_reference_inputs=r['reference_inputs'],
        mixed_absolute_error=abs(r['inside']-r['reference']),
        reference=r['reference_grouped'], reference_inputs=r['grouped_inputs'],
        absolute_error=abs(r['inside']-r['reference_grouped'])) for r in results]

def check_membership(routed,addressing):
    required={'direction_medium','direction_hard','relative_distance','absolute_distance'}
    counts=Counter(r['type'] for r in routed)
    if set(counts)!=required or any(n!=8 for n in counts.values()):raise ValueError('Require eight routed rows per type')
    if len({r['id'] for r in routed})!=32 or len(addressing)!=48 or len({r['id'] for r in addressing})!=48:
        raise ValueError('Require 32 routed and 48 distinct addressing rows')

def images_for(crops):
    from PIL import Image
    images=[]
    for c in crops:
        if sha(c['path'])!=c['file_sha256']:raise ValueError('Crop file hash differs')
        with Image.open(c['path']) as image:images.append(image.convert('RGB'))
        if hashlib.sha256(images[-1].tobytes()).hexdigest()!=c['rgb_sha256']:raise ValueError('Crop RGB hash differs')
    return images


def materialize_check(manifest,crops):
    """Compare actual bound source-frame/mask rendering with frozen kit crops."""
    from PIL import Image
    from verifykit.io import rows,frame_path,mask_for
    from student_pilot import verify_pass as V
    from student_pilot.scene_state import FrameMap
    if sha(manifest['source'])!=manifest['source_sha256']:
        raise ValueError('Pinned crop source manifest differs')
    groups={g['object_id']:g for g in rows(manifest['source'])}
    images=[];checks=[]
    for crop in crops:
        request=crop['request'];group=groups[request['object_id']]
        if len(request['candidate_ids'])!=1:raise ValueError('Require single-candidate V1 crops')
        c=next(c for c in group['candidates'] if c['candidate_id']==request['candidate_ids'][0])
        with Image.open(frame_path(group,c['slot'])) as source:image=source.convert('RGB')
        slot=c['slot']+1;rgb=hashlib.sha256(image.tobytes()).hexdigest()
        hashes=['0'*64]*32;hashes[slot-1]=rgb
        mapping=FrameMap(tuple(group['frame_indices']),rgb_sha256=tuple(hashes))
        candidate=dict(candidate_id=c['candidate_id'],slot=slot,mask=mask_for(c),
                       source_index=mapping.source_indices[slot-1],rgb_sha256=rgb)
        bound=dict(name=group['name'],frame_map=mapping,frames={slot:image},candidates=[candidate])
        material=V._materialize(bound,('V1',),[candidate],[])
        if material['_dropped'] or len(material['V1'][0])!=1:raise AssertionError('Source crop failed materialization')
        actual=material['V1'][0][0]
        digest=hashlib.sha256(actual.tobytes()).hexdigest()
        if digest!=crop['rgb_sha256']:raise AssertionError('Materialized crop differs from pinned kit crop')
        images.append(actual);checks.append(dict(candidate_id=c['candidate_id'],slot=slot,
            source_index=candidate['source_index'],frame_rgb_sha256=rgb,crop_rgb_sha256=digest,equal=True))
    return images,checks

def processor_check(routed,reference,crops,images):
    import torch
    from verifykit.model import HFBackend
    from verifykit.render import prompt
    checks=[]
    old=routed.tokenizer.padding_side
    try:
        for processor in (routed,reference):processor.tokenizer.padding_side='left'
        for c,image in zip(crops,images):
            values=[]
            for processor in (routed,reference):
                text=processor.apply_chat_template([dict(role='user',content=[dict(type='image'),
                    dict(type='text',text=prompt('V1',c['request']['name']))])],
                    tokenize=False,add_generation_prompt=True,enable_thinking=False)
                values.append(processor(text=[text],images=[image],return_tensors='pt',padding=True,size=HFBackend.size('V1')))
            check={k:torch.equal(values[0][k],values[1][k]) for k in ('input_ids','pixel_values','image_grid_thw')}
            if not all(check.values()):raise AssertionError('Independent processor mismatch: '+str(check))
            checks.append(dict(rgb_sha256=c['rgb_sha256'],**check))
    finally:routed.tokenizer.padding_side=old
    return checks

def cache_hash(cache):
    import torch
    result={}
    for i,layer in enumerate(cache.layers):
        for field in ('keys','values','conv_states','recurrent_states'):
            value=getattr(layer,field,None)
            if isinstance(value,torch.Tensor):
                result[f'{i}:{field}']=hashlib.sha256(value.detach().contiguous().view(torch.uint8).cpu().numpy().tobytes()).hexdigest()
    return result

@stage_assertions(4)
def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--tree',required=True);p.add_argument('--kit',default='/scratch/jjyeung/orch_cd/verify_kit/work')
    p.add_argument('--adapter',required=True);p.add_argument('--adapter-sha256',required=True)
    p.add_argument('--inputs',required=True);p.add_argument('--inputs-sha256',required=True)
    p.add_argument('--crops',default='/scratch/jjyeung/orch_cd/verify_gen/out/PARITY_CROPS_20.json')
    p.add_argument('--out',required=True);p.add_argument('--processor-only',action='store_true')
    p.add_argument('--reference-worker',action='store_true');p.add_argument('--max-seconds',type=int,default=3600)
    p.add_argument('--start-check',action='store_true')
    p.add_argument('--cpu-fp32',action='store_true',help='Compare full checkpoint P(yes) on CPU and stop before routed generation')
    a=p.parse_args()
    cpu=getattr(sys, "_acceptance_cpu_e2e", None)
    if a.start_check:
        from acceptance_start_check import begin
        begin(1 if a.processor_only else 4, a)
    sys.path[:0]=[a.kit,a.tree]
    if sha(a.adapter)!=a.adapter_sha256 or sha(a.inputs)!=a.inputs_sha256:raise ValueError('Input pin differs')
    inputs=json.loads(Path(a.inputs).read_text());crop_manifest=json.loads(Path(a.crops).read_text());crops=crop_manifest['crops']
    if len(crops)!=20:raise ValueError('Require exactly twenty crops')
    if cpu: crops=crops[:4]
    images=images_for(crops);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    import torch
    from verifykit.model import HFBackend
    from verifykit.render import prompt
    import inspect
    kit_source=Path(inspect.getfile(HFBackend)).resolve()
    if not kit_source.is_relative_to(Path(a.kit).resolve()):
        raise ValueError('Reference must import the standalone kit')
    if a.reference_worker and a.start_check:
        from acceptance_start_check import reference_constructor, finish
        reference_constructor(inputs, a.kit)
        finish('reference-constructor')
        return
    if a.reference_worker:
        reference=HFBackend(inputs['hf_checkpoint'],device='cpu' if a.cpu_fp32 or cpu else 'cuda:0',max_new_tokens=128)
        rows,grouped_rows=reference_predictions(reference,crops,images)
        (out/'reference.json').write_text(json.dumps(dict(runner='verifykit.model.HFBackend',checkpoint=inputs['hf_checkpoint'],
            model_type=type(reference.model).__name__,kit_source=str(kit_source),kit_source_sha256=sha(kit_source),rows=rows,grouped_rows=grouped_rows,processor_parity=reference.parity,
            numerical_provenance=numerical_provenance(reference.model),reference_seconds=reference.parity_seconds),indent=2)+'\n')
        return
    spec=importlib.util.spec_from_file_location('live_adapter',a.adapter);adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    images,render_checks=materialize_check(crop_manifest,crops)
    if not a.start_check: (out/'MATERIALIZE_PARITY.json').write_text(json.dumps(render_checks,indent=2)+'\n')
    from transformers import AutoProcessor
    routed_processor=adapter.load_processor(inputs)
    hf_processor=AutoProcessor.from_pretrained(inputs['hf_checkpoint'],local_files_only=True)
    checks=processor_check(routed_processor,hf_processor,crops,images)
    if not a.start_check: (out/'PROCESSOR_PARITY.json').write_text(json.dumps(dict(device='cpu',count=len(checks),checks=checks),indent=2)+'\n')
    if a.start_check:
        from acceptance_start_check import live_check
        live_check(a, inputs, adapter)
        return
    if a.processor_only:return
    check_membership(inputs['routed'],inputs['addressing'])
    if not a.cpu_fp32 and not cpu and torch.cuda.device_count()!=1:raise ValueError('Expose one assigned GPU')
    # A nonzero or killed worker terminates the driver; there is no retry path.
    worker=[sys.executable,'-B',str(Path(__file__).resolve()),*sys.argv[1:],'--reference-worker']
    if cpu: worker=cpu.worker(worker)
    subprocess.run(worker,check=True)
    references=json.loads((out/'reference.json').read_text())
    from student_pilot import carrier_c1_decode as D,verify_pass as V
    from student_pilot.reread_isolation import isolated
    from unittest.mock import patch
    start=time.monotonic();model,processor=adapter.load(inputs,device='cpu' if a.cpu_fp32 or cpu else 'cuda:0')
    if a.cpu_fp32 or cpu:model.float()
    native=V.native_view(model)
    if model.training:raise ValueError('Require eval model')
    if not a.cpu_fp32 and not cpu:torch.cuda.reset_peak_memory_stats()
    def deadline():
        if time.monotonic()-start>a.max_seconds:raise TimeoutError('Live parity budget exhausted')
    results=routed_predictions(native,processor,crops,images,references)
    if a.cpu_fp32:
        (out/'BATCH_SHAPE_DIAGNOSTICS.json').write_text(json.dumps(results,indent=2)+'\n')
        results=cpu_matched_rows(results)
    from student_pilot.ground_v3 import GroundV3
    threshold=inspect.signature(GroundV3).parameters['verify_threshold'].default
    numeric=check_probabilities(out,results,references['numerical_provenance'],numerical_provenance(model),threshold=threshold)
    if a.cpu_fp32:return
    if cpu: inputs=dict(inputs,routed=cpu.routed_rows(inputs['routed'])[:1],addressing=inputs['addressing'][:1])
    active=[None];consume=D.consume_cache_tokens;verify=V.verify_pass;cache_checks=[]
    def capture(native,ids,attention,cache,*args,**kwargs):
        value,new=consume(native,ids,attention,cache,*args,**kwargs);active[0]=new;return value,new
    def guarded(native,*args,**kwargs):
        if active[0] is None:raise AssertionError('Require a prefix token before the first ground')
        before=cache_hash(active[0]);rope=native.model.rope_deltas
        result=verify(native,*args,**kwargs)
        after=cache_hash(active[0]);rope_restored=native.model.rope_deltas is rope
        if after!=before or not rope_restored:raise AssertionError('Main state changed')
        cache_checks.append(dict(hash=before,rope_identity_restored=True));return result
    routed=[]
    for row in inputs['routed']:
        deadline();batch,config,kwargs=adapter.routed(row,model,processor)
        if config.backend.config['verify_threshold']!=threshold:raise AssertionError('Routed verification threshold differs from parity threshold')
        baseline=D.generate(model,processor,batch,verify=None,**kwargs)
        batch,config,kwargs=adapter.routed(row,model,processor);active[0]=None;first=len(cache_checks)
        with patch.object(D,'consume_cache_tokens',side_effect=capture),patch.object(V,'verify_pass',side_effect=guarded):
            enabled=D.generate(model,processor,batch,verify=config,**kwargs)
        if len(cache_checks)==first or enabled['errors']:raise AssertionError('Required successful verification did not run')
        from student_pilot.live_trace313 import check_record
        check_record(baseline,kwargs.get('reference_trace'));check_record(enabled,kwargs.get('reference_trace'))
        if not D.replay(enabled)['byte_equal']:raise AssertionError('Verified record fails replay')
        routed.append(dict(id=row['id'],video_only=baseline,video_verify=enabled,cache_checks=cache_checks[first:],score=adapter.score_routed(row,baseline,enabled)))
    (out/'routed.json').write_text(json.dumps(routed,indent=2)+'\n')
    addressing=[]
    from student_pilot.hrp_reread import read_image
    import numpy as np
    for row in inputs['addressing']:
        deadline();image,batch,config,kwargs=adapter.addressing(row,model,processor)
        digest=hashlib.sha256(np.asarray(image).tobytes()).hexdigest();slot=row['anchor_slot']
        if digest!=row['frame_rgb_sha256'] or config.frame_indices[slot-1]!=row['source_index']:raise AssertionError('Addressed frame mismatch')
        image_only=read_image(model,processor,image,row['name'],config)
        video_only=adapter.video_address(row,model,processor,batch)
        if cpu: batch['_cpu_address_name']=row['name']
        enabled=D.generate(model,processor,batch,reread=config,verify=None,**kwargs)
        evidence=addressing_evidence(row,image,config,enabled,image_only,video_only)
        save(out/'addressing_records'/f'{len(addressing):03d}.json',evidence)
        sub=check_addressing(evidence)
        if cpu: cpu.replay_card_generations(model,processor,batch,config,kwargs,row,image,out)
        addressing.append(dict(id=row['id'],call_mode='scheduled_identity_probe',score=adapter.score_addressing(row,image_only,video_only,sub)))
    (out/'addressing.json').write_text(json.dumps(addressing,indent=2)+'\n')
    result=dict(status='PASS',call_mode=inputs.get('call_mode','free'),addressing_call_mode='scheduled_identity_probe',response_parse_and_replay=True,all_eos=True,zero_errors=True,crops=len(crops),routed=len(routed),addressing=len(addressing),reference='separate HFBackend checkpoint process',
        p_yes_parity=numeric,max_p_yes_error=max(r['absolute_error'] for r in results),processor_checks=len(checks),seconds=time.monotonic()-start,
        gpu_peak_allocated_bytes=0 if cpu else torch.cuda.max_memory_allocated(),inputs_sha256=a.inputs_sha256,adapter_sha256=a.adapter_sha256)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
