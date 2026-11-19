"""Offline planning test using the unchanged A4 reader environment (CPU only)."""
import importlib.util
import json
import sys
from pathlib import Path


def run(work):
    w=Path(work);src=w/'src';sys.path[:0]=[str(src),str(src/'b'),str(src/'tree')]
    from h1eval.items import load_manifest
    sys.path.insert(0,str(src/'b'))
    import e2e_reader
    from h1eval.h10.launch import selected,select_types
    sys.path.insert(0,str(src/'b'))
    m=load_manifest(src/'items/devs1_routed.json')
    items=select_types(m['items'],selected(m['items'],'0/1'),'object_abs_distance')
    assert len(items)==150
    spec=importlib.util.spec_from_file_location('operator_e',str(w/'package/a/6.py'))
    op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
    settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],
                  perception_memo_verify_ids=[],save_own_depth=False)
    (w/'settings.json').write_text(json.dumps(settings))
    conf=dict(package=str(src),output=str(w/'rehearsal'),settings=str(w/'settings.json'),plan_sha256='a'*64,
              inputs_sha256='b'*64,operator_sha256='c'*64,python=sys.executable,
              export=str(w/'export'),binding=str(w/'binding'),export_pin=str(w/'pin'),device='cpu',prefix=[])
    assert op.COUNTS==(0,0,0,150,0) and op.SCHEDULE==((0,3),)
    configs=op.prepare(conf);assert configs[0]['types']==['object_abs_distance']
    assert op.descriptors(str(src))[0]['types']==[3]
    rehearsal=op.rehearsal(conf);assert len(rehearsal)==1
    assert rehearsal[0]['types']==['object_abs_distance'] and rehearsal[0]['expected']==150
    args=rehearsal[0]['args'];assert args[args.index('--types')+1]=='object_abs_distance'
    assert Path(args[args.index('--items')+1]).read_bytes()==(src/'items/devs1_routed.json').read_bytes()
    memory=op.memory_bound();assert memory['fits'] and memory['reads'][0]['captures']==84
    assert not op.memory_bound(allocation_bytes=1)['fits']
    summary=op.run(conf,100000,['0'],runner=lambda *a,**k:dict(completed=150,complete=True,failure=None),clock=lambda:0)
    assert summary['expected']==summary['completed']==150 and summary['complete']
    from h1eval.h10.parity_adapter import map_items
    mapped,mapping=map_items(items,{'frames_root':str(w/'no_images')},name=m['name'])
    assert list(mapped)==[r['id'] for r in items]
    result=dict(passed=True,rehearsal=rehearsal,memory=memory,summary=summary,ids=list(mapped),
                mapped=len(mapped),settings_unchanged=True)
    (w/'PLANNING.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('Offline E planning passed; 150 distance items')

if __name__=='__main__':run(sys.argv[1])
