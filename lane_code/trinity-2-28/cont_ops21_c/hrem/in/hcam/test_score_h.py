"""Synthetic H return and identity tests. These are not model measurements."""
import copy
import json
import os
import tempfile
from pathlib import Path
import score_h as s

def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True)+'\n')

def synthetic(root,build,m,twins,improved):
    binding=build['export_binding'];pins=build['serving_pins'];reworded={t['reworded_id'] for t in twins}
    settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],
        perception_memo_verify_ids=[],save_own_depth=False,tasks=['/synthetic/items/HELDOUT_NATIVE_TASKS.jsonl'])
    settings_sha=s.canonical(settings)
    identity=dict(plan=build['plan_sha256'],operator_sha256=build['changed_members']['a/6.py']['after'],inputs='1'*64,cards=1,
        reads=[dict(arm='tower',modes=['none'],types=[0,1,2],expected=900,stage1_select_rule='candidates_argmax',
        save_own_depth=False,perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[])],schedule=[[0,0],[0,1],[0,2]])
    meta=root/'metadata';rd=meta/'reads/0/metadata'
    dump(meta/'IDENTITY.json',identity)
    dump(rd/'READ_IDENTITY.json',dict(identity,read=0,settings_sha256=settings_sha))
    dump(rd/'IDENTITY.json',dict(plan=identity['plan'],inputs=identity['inputs'],settings_sha256=settings_sha))
    dump(meta/'EXPORT_PIN.json',dict(s.EXPORTS[binding['step']],schema='h1-export-pins-v1',config_sha256=binding['config_sha256'],
        preparation={k:dict(sha256=v) for k,v in binding['preparation_sha256'].items()}))
    for t,kind in enumerate(s.TYPES):
        items=[i for i in m['items'] if i['question_type']==kind]
        b=dict(schema='h10-shard-v1',arms=['tower'],modes=[{'name':'none'}],fixture=False,lineage='SFT',step=binding['step'],
            items_sha256=s.PINS[s.ITEM_NAMES[0]],item_set_sha256=m['item_set_sha256'],ids=[i['id'] for i in items],
            count=900,shard='0/1',r0_pin=m['r0_check']['pin'],reader_entry='e2e_reader.parity:make_real',maker_name='make_capped_real',
            export_sha256='2'*64,artifact_manifest_sha256='3'*64,settings_sha256=settings_sha,mapping_sha256='4'*64,r0_code_sha256='5'*64)
        b.update({k:v for k,v in settings.items() if k!='tasks'});b.update(pins)
        path=rd/('journals/%d/0'%t);dump(path/'environment.json',dict(binding=b,settings=settings))
        rows=[]
        for i in items:
            score=float(improved and i['id'] in reworded)
            rows.append(dict(id=i['id'],room_key=i['room_key'],type=kind,arm='tower',mode='none',intervention={'name':'none'},applied=False,complete=True,
                output=dict(calls=[{'call':'<move from=1 to=2>'}] if score else [],scores={'answer':score},finish='eos')))
        (path/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))

def run(m,twins):
    here=Path(__file__).resolve().parent
    work=Path(tempfile.mkdtemp(prefix='score_',dir=os.environ.get('H_TEST_TMPDIR','/dev/shm/c18h')))
    builds={};paths={};rows={};roots={}
    for step in (200,544):
        path=Path(os.environ.get('H_TEST_BUILD%d'%step,str(here/('evidence/H%d/BUILD.json'%step))))
        paths[step]=path;builds[step]=s.read(path)['H'];roots[step]=work/str(step)
        synthetic(roots[step],builds[step],m,twins,step==544)
        rows[step],meta=s.load_return(roots[step],path,m)
        assert len(rows[step])==900
    paired=s.paired(rows[544],m,twins)
    assert all(v['value']==1.0 and v['ci95']==[1.0,1.0] and v['n']==150 for cell in paired.values() for v in cell.values())
    comparison=s.compare(rows[544],rows[200],m,twins)
    for key,cell in comparison.items():
        want=1.0 if key.endswith('/reworded') else 0.0
        assert all(v['value']==want and v['ci95']==[want,want] for v in cell.values())
    self_comparison=s.compare(rows[200],rows[200],m,twins)
    assert all(v['value']==0 and v['ci95']==[0,0] for cell in self_comparison.values() for v in cell.values())
    capped=copy.deepcopy(next(iter(rows[544].values())));capped['output']['scores']['answer']=1;capped['output']['finish']='max_calls'
    assert s.metric(capped,'answer')==0
    missing=dict(rows[544]);key=twins[0]['original_id'];missing.pop(key)
    assert s.metrics(missing,[key])['completed']==0 and s.metrics(missing,[key])['answer'] is None
    negative=[]
    def mutation(path,keys,value,label):
        raw=path.read_bytes();v=json.loads(raw);obj=v
        for key in keys[:-1]:obj=obj[key]
        obj[keys[-1]]=value;dump(path,v)
        try:s.load_return(roots[544],paths[544],m)
        except (ValueError,KeyError,AssertionError):negative.append(label)
        else:raise AssertionError('Accepted '+label)
        finally:path.write_bytes(raw)
    meta=roots[544]/'metadata';env=meta/'reads/0/metadata/journals/0/0/environment.json'
    for key in ['plan','operator_sha256']:mutation(meta/'IDENTITY.json',[key],'f'*64,key)
    mutation(meta/'IDENTITY.json',['reads',0,'expected'],636,'read count')
    mutation(meta/'reads/0/metadata/READ_IDENTITY.json',['plan'],'f'*64,'read identity')
    mutation(meta/'reads/0/metadata/IDENTITY.json',['settings_sha256'],'f'*64,'reader settings')
    for key in ['run','step','member_directory','object','archive_sha256','config_sha256']:
        mutation(meta/'EXPORT_PIN.json',[key],'wrong','export '+key)
    mutation(meta/'EXPORT_PIN.json',['preparation','config','sha256'],'0'*64,'preparation')
    for key in s.SERVING_KEYS:
        mutation(env,['binding',key],'f'*64,'serving '+key)
    for key in ['export_sha256','artifact_manifest_sha256']:
        mutation(env,['binding',key],'0'*64,'zero '+key)
    for key,v in [('count',636),('items_sha256','f'*64),('item_set_sha256','f'*64),('fixture',True),('perception_memo','off')]:
        mutation(env,['binding',key],v,'binding '+key)
    journal=env.parent/'items.jsonl';raw=journal.read_bytes()
    for label,bad in [('duplicate',raw+raw.splitlines(True)[0]),('tail',raw[:-1]),('order',b''.join(reversed(raw.splitlines(True))))]:
        journal.write_bytes(bad)
        try:s.load_return(roots[544],paths[544],m)
        except ValueError:negative.append('journal '+label)
        else:raise AssertionError('Accepted '+label)
        finally:journal.write_bytes(raw)
    try:s.load_return(roots[544],paths[200],m)
    except ValueError:negative.append('other package/export')
    else:raise AssertionError('Accepted other package')
    return dict(passed=True,synthetic_only=True,completed_per_step=900,negative_cases=negative,
        reworded_minus_original=paired,step544_minus_step200=comparison,self_difference_zero=True,max_calls_zero=True,missing_reported=True)
