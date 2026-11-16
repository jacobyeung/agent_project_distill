"""Use the exact acceptance bundle for live parity; delegate all inference callbacks."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'inputs/gv_fix/live_parity_adapter.py').is_file():
    ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('_acceptance_delivered_adapter',ROOT/'inputs/gv_fix/live_parity_adapter.py')
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def load_processor(inputs):
    from student_pilot.mdg_runtime import _bundle
    from student_pilot.carrier_c1_run import processor_for_receipt
    root,_,cfg,receipt,manifest,_,_=_bundle(inputs['bundle'])
    base._inputs=inputs
    base._cfg=cfg
    processor=processor_for_receipt({**manifest,'root':str(root/'base')},receipt)
    from acceptance_model_contract import check_runtime_binding
    if inputs.get('call_mode')=='scripted':check_runtime_binding(inputs,processor.tokenizer)
    return processor


def load(inputs,device):
    from student_pilot.mdg_runtime import load_runtime
    from transformers import GenerationConfig
    model,processor,cfg=load_runtime(dict(bundle=inputs['bundle'],c1_config=inputs['carrier_config'],base_artifact=inputs['artifact'],trace_program_version=inputs.get('trace_program_version')),device)
    base._inputs=inputs
    base._cfg=cfg
    model.generation_config=GenerationConfig.from_pretrained(inputs['hf_checkpoint'],local_files_only=True)
    from acceptance_model_contract import check_runtime_binding
    if inputs.get('call_mode')=='scripted':check_runtime_binding(inputs,processor.tokenizer)
    model.eval().requires_grad_(False)
    return model,processor

def routed(row,model,processor):
    from student_pilot.live_trace313 import LiveSession
    from student_pilot.trace_version import model_version
    batch,config,kwargs=base.routed(row,model,processor)
    kwargs['trace_session']=LiveSession(kwargs['ground_backend'],program_version=model_version(model,base._inputs.get('trace_program_version')))
    if base._inputs.get('call_mode')=='scripted':kwargs['reference_trace']=base.document(row['row'])['reference_trace']
    return batch,config,kwargs

score_routed=base.score_routed
def addressing(row,model,processor):
    image,batch,config,kwargs=base.addressing(row,model,processor)
    # This assay compares two executions of one image query. The routed rows
    # measure free calling when requested; this identity probe must run its call.
    call='<ground obj="'+row['name']+'">'
    kwargs['reference_trace']=dict(schema='addressing-call-v1',free_answer=True,name=row['name'],
        segments=[dict(text='<think>\n'+call,call=call)])
    return image,batch,config,kwargs
video_address=base.video_address
score_addressing=base.score_addressing
