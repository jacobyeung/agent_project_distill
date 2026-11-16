"""Restore the original proof checkpoint and independently serve its historical inputs."""
from pathlib import Path
from .c8 import install,Context,load_model
from .readers import HarnessReader,E2EReader
from .io import load,sha
from .paths import module


def factory(assets,kind):
    P=install()
    request=load(assets['request']['path'])
    import nomdg,gravity_guard
    from student_pilot import geometry_profiles as GP
    if not gravity_guard._installed:gravity_guard.install(GP,gravity_guard.Recorder())
    model,processor,info=load_model(request['config'],assets['artifact'],request['data_receipt'],assets.get('device','cuda:0'))
    tasks,captures=nomdg.tasks_and_captures(request['inputs'])
    tasks={ 'devrows:'+t['id']:dict(t,dataset=t['dataset'],scene_name=t['scene']) for t in tasks }
    if kind=='e2e':
        entry=assets['e2e_loaded_entry']
        if sha(entry['path'])!=entry['sha256']:raise ValueError('historical b04 entry differs')
        loaded=module('_native_b04_proof',entry['path']).load_original(model,processor,assets)
        reader=E2EReader(loaded,loaded.replay)
        return reader,loaded.frames_for,tasks
    from common import checked
    geometry=load(checked(request['grounding']['geometry_manifest']))
    masks=None if assets.get('proof_mode')=='reduced' else P.Masks(assets.get('mask_cache',request['mask_cache']))
    context=Context(processor,load(checked(request['config'])),captures,request['frames_root'],
                    geometry,masks,assets['audit_dir'],assets.get('device','cuda:0'))
    from .production import Unserved
    reader=HarnessReader(model,processor,context,Unserved(model,processor,context))
    return reader,lambda item:None,tasks


if __name__=='__main__':
    import sys
    from .proof import in_job
    from .io import dump
    assets,keys,kind,out=sys.argv[1:]
    reference,actual=in_job(factory,load(assets),load(keys),kind=kind)
    dump(out,{'reference':reference,'actual':actual})
