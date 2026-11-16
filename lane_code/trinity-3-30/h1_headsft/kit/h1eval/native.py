"""Load a native trainer export and bind it to the unchanged reader core."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from .items import pin, sha
from .perception import perception, Heads
from .runner import H1Generator


def checked(value, root):
    path = Path(value['path'])
    if not path.is_absolute():path=root/path
    path=path.resolve()
    if path.parts[1] != 'scratch':raise ValueError('Native inputs must be staged on /scratch')
    if sha(path)!=value['sha256']:raise ValueError('Native input pin mismatch: '+str(path))
    return path


def json_pin(value,root):return json.loads(checked(value,root).read_text())


def head_loader(name):
    path=Path(__file__).parent/'reader_core/heads'/name/(name+'_head.py')
    spec=importlib.util.spec_from_file_location('h1_'+name+'_head',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.load_head


def gt_arrays(directory,item):
    """GT filenames use SHA256(item ID); no path traversal or pickle loading."""
    from .items import digest
    path=Path(directory)/(digest(item['id'])+'.npz')
    with np.load(path,allow_pickle=False) as value:
        result={k:value[k].copy() for k in value.files}
    if 'gt_depth' in result:
        grid=result['gt_depth'];axis=result.get('grid_uv',np.linspace(0,1000,grid.shape[-1]))
        if grid.ndim!=3 or grid.shape[0]!=32 or grid.shape[1:]!=(len(axis),len(axis)):
            raise ValueError('GT depth must be [32,N,N] with a square UV grid')
        def depth(frame,uv):
            from scipy.interpolate import RegularGridInterpolator
            interp=RegularGridInterpolator((axis,axis),grid[frame-1],bounds_error=True)
            return interp(np.asarray(uv)[:,::-1])
        result['depth']=depth
    return result


def load(root,settings,*,frames,gt,items):
    """h1eval.json pins config, model manifest, receipt, checkpoint, reader and media."""
    import torch
    from PIL import Image
    from student_pilot import carrier_c1_run as trainer
    from student_pilot.h1_r0 import room_key
    from evalpath.runtime import prompt_batch, check_init_spec
    from e2e_reader.artifact import Artifact
    from e2e_reader.callhook import CallHook, install
    cfg=json_pin(settings['config'],root);receipt=json_pin(settings['receipt'],root)
    manifest=json_pin(settings['model_manifest'],root)
    checkpoint=pin(checked(settings['checkpoint'],root))
    artifact_json=json_pin(settings['checkpoint'],root)
    if artifact_json.get('step')!=settings['step']:raise ValueError('Checkpoint step differs')
    check_init_spec(receipt,checkpoint)
    device=settings.get('device','cpu')
    reader=settings['reader'];reader_path=checked(reader,root)
    artifact=Artifact(reader_path.parent,reader_path.name,reader['sha256'],code_roots=settings['code_roots']).verify()
    processor=trainer.processor_for_receipt(manifest,receipt)
    loading={k:v for k,v in receipt.items() if k!='init_artifact'}
    model=trainer.load_model(manifest,loading,processor,evaluation=True)
    trainer.load_artifact(model,checkpoint);model.to(device).eval().requires_grad_(False)
    hook=install(model,CallHook(processor.tokenizer,processor._routing_tokens['ids'].values()))
    sam=selector=scale=None
    if 'sam3' in settings:
        from student_pilot.sam3_tower import Sam3Tower
        sam=Sam3Tower({**settings['sam3'],'device':device})
        selector,_=head_loader('selector')(artifact.path('selector_head','selector_head/selector_head.json').parent)
        if selector.cfg['name_mode']=='sam3':
            raise ValueError('Reader socket requires selector name_mode none/trigram; SAM text embeddings are not bound')
    if settings.get('scale_head'):
        scale,_=head_loader('scale')(artifact.path('scale_head','scale_head/scale_head.json').parent)
    media=json_pin(settings['media'],root)
    if set(media)!=set(i['id'] for i in items):raise ValueError('Media IDs differ from pinned item set')
    last={}
    def bind(item):
        entry=media[item['id']]
        if entry['room_key']!=item['room_key']:raise ValueError('Media room differs')
        if last.get('id')!=item['id']:
            row=json_pin(entry['row'],root)
            if room_key(row)!=item['room_key']:raise ValueError('Trainer row room differs')
            inputs=row['student_input']
            if inputs['question']!=item['question'] or (inputs.get('options') or [])!=(item.get('options') or []):
                raise ValueError('Media prompt differs from pinned item')
            native=[]
            for file in entry['frames']['native_frames']:
                with Image.open(checked(file,root)) as image:native.append(image.convert('RGB'))
            frame_data={**entry['frames'],'native_frames':native}
            if len(frame_data['anchor_indices'])!=frames:raise ValueError('Media frame count differs')
            last.clear();last.update(id=item['id'],row=row,frames=frame_data)
        return dict(last)

    def factory(arm,mode,item):
        donor=None
        if mode['name']=='donor':
            capture=media[item['id']]['frames']['capture_id']
            candidate=next((other for other in items if media[other['id']]['frames']['capture_id']!=capture),None)
            if candidate is None:raise ValueError('Donor mode requires another capture in the pinned set')
            source=bind(candidate)
            from student_pilot.carrier_c1_decode import _prepare_decode
            from student_pilot.ground_context import closed_adapters
            from e2e_reader.artifact import Audit
            batch=prompt_batch(processor,source['row'],cfg,'routed')
            batch={k:(v.to(device) if hasattr(v,'to') else v) for k,v in batch.items()}
            with torch.no_grad(),Audit(artifact):
                state=closed_adapters(_prepare_decode)(model,processor,batch)
                donor=Heads.prefill(state,str(source['frames']['capture_id']))
        current=bind(item)
        gt_value=gt_arrays(gt,item) if gt is not None else None
        if gt_value:
            for key in ('gt_pose9','gt_up','gt_depth'):
                if key in gt_value:item[key]=gt_value[key].tolist()
        if mode['name']=='gt' and gt_value is None:raise ValueError('GT intervention requires --gt')
        p=perception(arm,artifact=artifact,device=device,sam3_tower=sam,selector_head=selector,scale_head=scale,
                     **({'mode':mode,'gt':gt_value,'donor':donor} if arm=='own' else {}))
        gen=H1Generator(model,processor,artifact,p,hook,dict(frames=dict(layout=settings['export_layout']['layout'],count=frames)),
                        export_layout=settings['export_layout'],prompt_batch=lambda processor,row:prompt_batch(processor,row,cfg,'routed'),device=device)
        def generate(_):
            bound={**item,'row':current['row'],'frames':current['frames']}
            return gen(bound)
        return generate
    return factory
