"""Item-1 probe: run the tree's own resolution code up to the processor instantiation and report the directory."""
import json,os
from pathlib import Path
NAMED=('preprocessor_config.json','video_preprocessor_config.json','tokenizer.json','tokenizer_config.json',
       'chat_template.jinja','config.json','vocab.json','merges.txt')
TAPS=[]
def describe(root):
    root=Path(root);names=sorted(os.listdir(root)) if root.is_dir() else None
    return dict(directory=str(root),is_dir=names is not None,entries=None if names is None else len(names),
        processor_files_present=[n for n in NAMED if names and n in names],
        processor_files_missing=[n for n in NAMED if not names or n not in names],
        first_entries=None if names is None else names[:2])
def tap():
    import student_pilot.decoupled_v_run as d, student_pilot.carrier_c1_run as c
    if getattr(d.processor_for,'_tap',False):return
    native=d.processor_for
    def tapped(root):
        TAPS.append(dict(describe(root),pid=os.getpid()))
        return native(root)
    tapped._tap=True
    d.processor_for=tapped;c.processor_for=tapped
def _run(label,function):
    del TAPS[:]
    try:
        value=function();out=dict(ok=True,result=value)
    except Exception as error:
        out=dict(ok=False,error=type(error).__name__+':'+str(error)[:330])
    return dict(call=label,pid=os.getpid(),ppid=os.getppid(),**out,processor_for_called_with=list(TAPS))
def witness(config_pin):
    """production_proof._run lines 128-130: opener(cfg, v.json) -> p_opener_witness.prepared_vocabulary(source)."""
    tap()
    from student_pilot.p3_provenance import load,pinned
    from launch_r1.p_opener_witness import prepared_vocabulary
    def go():
        source=load(pinned(config_pin))
        value=prepared_vocabulary(source)
        return dict(vocabulary_keys=sorted(value)[:8],size=len(json.dumps(value)))
    return _run('witness',go)
def forward(preparation_pin):
    """first_batch_check: receipt, manifest = prepared(cfg) (manifest = load(pinned(receipt['model'])), line 792),
    then processor_for_receipt(manifest, receipt) (line 3143); load_model would follow and is not run."""
    tap()
    from student_pilot.p3_provenance import load,pinned
    import student_pilot.carrier_c1_run as c
    def go():
        receipt=load(pinned(preparation_pin));manifest=load(pinned(receipt['model']))
        processor=c.processor_for_receipt(manifest,receipt)
        root=Path(manifest['root'])
        return dict(manifest_root=manifest['root'],processor=type(processor).__name__,
            tokenizer=type(processor.tokenizer).__name__,vocab=len(processor.tokenizer),
            load_model_files={n:(root/n).is_file() for n in manifest['files']})
    return _run('forward',go)
