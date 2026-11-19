"""Fresh-process CPU admission, scorer parity and operator rehearsal."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run(work):
    w=Path(work);src=w/'src';sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
    import e2e_reader
    assert str(src/'b') in e2e_reader.__file__
    from h1eval.items import load_manifest
    from h1eval.h10.parity_adapter import map_items
    from h1eval.cli import code_hash
    from h1eval import scorers
    from h1eval.runner import measure
    from rows.expected_calls import expected_calls
    m=load_manifest(src/'items/HELDOUT_CAMERA_ITEMS.json')
    settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],
                  perception_memo_verify_ids=[],save_own_depth=False,arm='own_depth',
                  tasks=[str(src/'items/HELDOUT_NATIVE_TASKS.jsonl')],frames_root=str(w/'no_images'))
    settings['item_sets']={'heldout_camera_wording':dict(tasks=settings['tasks'])}
    mapped,mapping=map_items(m['items'],settings,name=m['name'])
    assert len(mapped)==len({i['key'] for i in mapping['items']})==900
    dev=load_manifest(src/'items/devs1_routed.json')
    a4mapped,a4mapping=map_items(dev['items'],dict(settings,tasks=[str(src/'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl'),str(src/'b/work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl')]),name=dev['name'])
    originals={i['id']:i for i in a4mapping['items']};hmap={i['id']:i for i in mapping['items']}
    twins=json.loads((src/'items/HELDOUT_CAMERA_TWINS.json').read_text())['twins']
    for t in twins:
        for key in ('native','layout_count','anchor_indices','dense_count','frame_binding_sha256'):
            assert hmap[t['original_id']][key]==hmap[t['reworded_id']][key]==originals[t['original_id']][key]
    old=module(w/'original_scorers.py','original_scorers')
    parity=0;original_calls=0
    for item in dev['items']:
        calls=expected_calls(item['question'],item['question_type'])
        if item['question_type'].startswith('camera_'):
            i,j=item['display_frame_pair'];assert calls==['<%s from=%d to=%d>'%('turn' if item['question_type']=='camera_rotation' else 'move',i,j)];original_calls+=1
        for cs,early in [(calls,False),([],False),(calls*2,False),(['<move from=1 to=2>'],False),(calls,True),(list(reversed(calls)),False)]:
            out=dict(calls=[dict(call=c,start_token=2,at_token=4) for c in cs],text=('</think>' if early else '')+''.join(cs)+'<answer>0</answer>',finish='eos')
            assert old.placement(out,item)==scorers.placement(out,item),(item['id'],cs)
            parity+=1
    stubs=0
    for item in m['items']:
        i,j=item['display_frame_pair'];call='<%s from=%d to=%d>'%('turn' if item['question_type']=='camera_rotation' else 'move',i,j)
        if item['question_type']=='camera_rotation':response='turn = %s deg'%item['answer']
        elif item['question_type']=='camera_displacement':response='dx = %s m, dy = 0 m, dz = 0 m, distance = %s m'%(item['answer'],item['answer'])
        else:
            label=item['options'][ord(item['answer'])-ord('A')].split('.')[-1].strip().lower()
            dx,dz={'backward':(0,-1),'right':(1,0),'left':(-1,0),'forward':(0,1)}[label]
            response='dx = %s m, dy = 0 m, dz = %s m, distance = 1 m'%(dx,dz)
        out=dict(calls=[dict(call=call,response=response,start_token=1,at_token=2)],text=call+'<answer>'+str(item['answer'])+'</answer>',finish='eos',scores={'answer':1.0})
        got=measure(out,item);assert got['M1']['exact'] and got['M2']['task_accuracy']==1.0
        assert len(got['M2']['calls'])==1 and got['M2']['error_calls']==0
        capped=measure(dict(out,finish='max_calls'),item);assert capped['M2']['task_accuracy']==0.0
        stubs+=1
    bad=[None,[],[1],[1,2,3],['1',2],[True,2],[1.0,2],[0,2],[2,2],[1,33]]
    for pair in bad:
        try:scorers.placement({},dict(m['items'][0],display_frame_pair=pair))
        except ValueError:pass
        else:raise AssertionError('Invalid pair admitted')
    op=module(w/'package/a/6.py','operator_h')
    (w/'settings.json').write_text(json.dumps(settings))
    conf=dict(package=str(src),output=str(w/'rehearsal'),settings=str(w/'settings.json'),plan_sha256='a'*64,
        inputs_sha256='b'*64,operator_sha256='c'*64,python=sys.executable,export=str(w/'export'),
        binding=str(w/'binding'),export_pin=str(w/'pin'),device='cpu',prefix=[])
    assert op.COUNTS==(300,300,300,0,0) and op.SCHEDULE==((0,0),(0,1),(0,2))
    rehearsal=op.rehearsal(conf)
    assert rehearsal[0]['expected']==900 and rehearsal[0]['types']==['camera_displacement','camera_rotation','camera_movement_direction']
    args=rehearsal[0]['args'];assert Path(args[args.index('--items')+1]).read_bytes()==(src/'items/HELDOUT_CAMERA_ITEMS.json').read_bytes()
    memory=op.memory_bound();assert memory['fits'] and memory['reads'][0]['captures']==52
    assert not op.memory_bound(allocation_bytes=1)['fits']
    summary=op.run(conf,100000,['0'],runner=lambda *a,**k:dict(completed=900,complete=True,failure=None),clock=lambda:0)
    assert summary['expected']==summary['completed']==900 and summary['complete']
    plan=json.loads((src/'9.json').read_text());assert code_hash()==plan['evaluator_code_sha256']
    assert code_hash(src/'b/e2e_reader')==plan['serving_pins']['reader_sha256']
    result=dict(passed=True,native_manifest_items=900,native_mapped_unique_keys=900,frame_mappings_equal=900,
        devs1_items=636,M1_parity_cases=parity,camera_original_expected_calls_equal=original_calls,
        heldout_stub_measure_scored=stubs,invalid_pairs_refused=len(bad),evaluator_code_sha256=code_hash(),
        memory=memory,summary=summary,rehearsal=rehearsal)
    (w/'PLANNING.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('H CPU admission passed: 900 mappings, 3816 parity cases, 900 measure stubs')

if __name__=='__main__':run(sys.argv[1])
