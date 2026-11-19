"""Real CPU admission functions with explicit external-byte boundaries."""
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_r2_data_path import directory, fixture, manifest, PROOFS, LANE


class Build5(unittest.TestCase):
    def test_materializer_refuses_invalid_pair_membership(self):
        from student_pilot.r2_materialize import materialize
        root=directory();row=fixture(root)
        rows=[{**deepcopy(row),'qid':str(i)} for i in range(3)]
        for name,assignment,reason in [('missing',dict(type='facing_pairs'),'pair identity'),
                                       ('overfull',dict(type='facing_pairs',pair='p'),'too many')]:
            mp=manifest(root/name,rows);value=load(mp)
            value['mix_cells']={r['qid']:assignment for r in rows};mp.write_text(json.dumps(value))
            with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
                with self.assertRaisesRegex(ValueError,reason):materialize([mp],root/(name+'_store'))

    def test_checklist_receipt_set_protocol(self):
        from launch_r2.checklist import Checklist, ITEMS
        root=directory();c=Checklist(root,{}, {})
        for item in ITEMS:
            c.step(item,lambda:dict(synthetic=True,purpose='receipt protocol only'))
        self.assertEqual(set(c.finish()),{str(i) for i in ITEMS})
        (c.output/'1.json').write_text(json.dumps(dict(item=1,status='REFUSE')))
        c.receipts[1]=file_pin(c.output/'1.json')
        with self.assertRaisesRegex(ValueError,'changed'):c.finish()

    def test_late_refusal_keeps_its_manifest_denominator(self):
        from student_pilot.r2_materialize import materialize
        root=directory();good=fixture(root);bad=deepcopy(good);bad['qid']='late-other-manifest'
        bad['student_input']['dense_source']['frames'][0]['sha256']='0'*64
        first=manifest(root/'first',[good],family='same')
        second=manifest(root/'second',[bad],family='same')
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            result=materialize([first,second],root/'store')
        counts=[r['counts']['object_rel_direction_easy'] for r in result['intake']]
        self.assertEqual([(c['seen'],c['admitted'],c['refused']) for c in counts],[(1,1,0),(1,0,1)])

    def test_published_missing_program_frames(self):
        from student_pilot.s1_routing import Frames
        from student_pilot.carrier_c1_routing import alias_of
        from student_pilot.r2_adapters import normalize
        from student_pilot.r2_contract import validate
        root=directory();examples=[json.loads(s) for s in (LANE/'rows/join_examples.jsonl').read_text().splitlines()]
        maps={};videos={};rates={}
        for row in examples:
            d,s=alias_of(row['canonical']).split('/',1)
            videos[s]=dict(g=d,raw_n=max(row['frame_indices'])+1);rates[d+'/'+s]=10
            for i in row['frame_indices']:
                h=hashlib.sha256((d+'/'+s+'/'+str(i)).encode()).hexdigest()
                maps[d,s,i]=dict(d=d,s=s,i=i,sha256=h,path='/data2/k6tk/'+h[:2]+'/'+h+'.png')
        with gzip.open(root/'map.jsonl.gz','wt') as f:
            for row in maps.values():f.write(json.dumps(row)+'\n')
        with gzip.open(root/'plan.json.gz','wt') as f:json.dump(dict(v=videos),f)
        write(root/'fps.json',dict(schema='s1-fps-authority-v1',by_scene=rates))
        resolver=Frames(file_pin(root/'map.jsonl.gz'),file_pin(root/'plan.json.gz'),fps_authority=file_pin(root/'fps.json'))
        records=[]
        for raw in examples:
            row=normalize(raw,resolver);validate(row,'routing')
            self.assertEqual(row['target'],raw['suffix'])
            records.append(dict(qid=raw['qid'],target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),spans=len(row['tool_output_spans'])))
        self.assertEqual(len(records),19)
        (PROOFS/'PUBLISHED_JOIN.json').write_text(json.dumps(dict(source=str(LANE/'rows/join_examples.jsonl'),rows=records,
            stand_in='synthetic content addresses, fixture FPS 10 and source-bound lower frame counts; real map remains on frame host',
            real_rgb_checked=False,scene_admission_checked=False)))

    def test_runtime_and_native_output_checklist(self):
        from launch_r2.checklist import Checklist
        from launch_r2 import staging, stdlib_probe
        root=directory();(root/'b').mkdir();(root/'k').mkdir();(root/'o').mkdir()
        (root/'b/t.py').write_text('value = 1\n')
        executable=root/'venvs/rwtrain_torch211_cu129/bin/python'
        executable.parent.mkdir(parents=True);executable.write_bytes(b'byte-boundary fixture')
        plan=dict(venv=dict(sha256='a'*64),bwrap=dict(sha256='b'*64))
        write(root/'plan.json',plan);write(root/'k/0.json',dict(staging=file_pin(root/'plan.json')))
        write(root/'o/01.json',dict(stdlib_version=[3,6],venv_sha256='a'*64,bwrap_sha256='b'*64,
                                   files={'t.py':file_pin(root/'b/t.py')['sha256']}))
        c=Checklist(root,{}, {})
        with patch.object(staging,'P',str(root)),patch.object(sys,'executable',str(executable)):
            c.step(1,c.runtime)
            with patch('torch.empty',return_value=SimpleNamespace(is_cuda=True)):
                with self.assertRaisesRegex(ValueError,'CPU check failed'):c.runtime()
            (root/'b/t.py').write_text('value = 2\n')
            with self.assertRaisesRegex(ValueError,'script proof differs'):c.runtime()
            (root/'b/t.py').write_text('value = 1\n')
        with self.assertRaisesRegex(ValueError,'runtime did not execute'):c.runtime()
        with patch.object(sys,'version_info',(3,6)):
            self.assertEqual(stdlib_probe.probe(root)['stdlib_version'],[3,6])
            with self.assertRaisesRegex(ValueError,'Missing bootstrap'):stdlib_probe.probe(directory())
            import runpy
            from contextlib import redirect_stdout
            output=io.StringIO()
            with patch.object(sys,'argv',['probe',str(root)]),redirect_stdout(output):
                runpy.run_path(stdlib_probe.__file__,run_name='__main__')
            self.assertEqual(json.loads(output.getvalue())['files'],{'t.py':file_pin(root/'b/t.py')['sha256']})
        with self.assertRaisesRegex(ValueError,'required version'):stdlib_probe.probe(root)
        # Minimal native-visible surface; the real scanner reads every file.
        from launch_r2.build import capsule_json
        for p in (root/'k/0.json',root/'plan.json',root/'o/01.json'):
            p.write_bytes(capsule_json(load(p)))
        (root/'b/wh.json').write_bytes((Path(__file__).parents[1]/'launch_s1/b/wh.json').read_bytes())
        (root/'job.sh').write_text('#!/bin/bash\ntrue\n')
        c.step(11,c.outputs)
        write(root/'o/leak.json',dict(value='benchmark'))
        with self.assertRaisesRegex(ValueError,'operational'):c.outputs()

    def test_vocabulary_reads_staged_export(self):
        from launch_r2.checklist import Checklist
        from tests.r2_init_fixture import INIT
        from student_pilot.p3_provenance import digest
        root=directory();tokens=dict(ids={'<move':3},constituents={'<move':[1,2]})
        vocab={'a':1,'b':2,'<move':3}
        recorded=dict(vocabulary_sha256=digest(vocab),tokens=tokens)
        # A derived export must carry the native source-seal lineage predicate.
        body=dict(schema='s1-run-seal-v1',tree_sha256='a'*64,config_sha256='b'*64,
                  archive=dict(path='/tiny/model-boundary',sha256='c'*64))
        seal={**body,'sha256':digest(body)}
        write(root/'artifact.json',dict(schema='carrier-c1-artifact-v1',r2_identity=dict(init=INIT),
            source_seal=seal,training_source_seal=seal,config_sha256='b'*64,routing_vocabulary=recorded))
        pin=file_pin(root/'artifact.json')
        write(root/'v.json',dict(artifact_sha256=pin['sha256'],lineage_sha256=INIT['artifact_sha256'],**recorded))
        cfg=dict(r2_identity=dict(init=INIT),init_artifact=dict(artifact=pin,lm='full'),routing_opener_init='keep',routing_vocabulary=file_pin(root/'v.json'))
        processor=SimpleNamespace(tokenizer=SimpleNamespace(get_vocab=lambda:vocab,convert_tokens_to_ids=lambda t:vocab[t]))
        c=Checklist(root,{},cfg)
        with patch('transformers.AutoProcessor.from_pretrained',return_value=processor) as loader:
            c.step(9,c.vocabulary)
            self.assertTrue(loader.call_args.kwargs['local_files_only'])
        processor.tokenizer.convert_tokens_to_ids=lambda t:99
        with patch('transformers.AutoProcessor.from_pretrained',return_value=processor):
            with self.assertRaisesRegex(ValueError,'IDs differ'):c.vocabulary()
        processor.tokenizer.convert_tokens_to_ids=lambda token:vocab[token]
        original=load(root/'v.json')
        with patch('transformers.AutoProcessor.from_pretrained',return_value=processor):
            for field,reason in [('lineage_sha256','lineage or vocabulary'),('vocabulary_sha256','differs from the witness')]:
                (root/'v.json').write_text(json.dumps({**original,field:'0'*64}))
                c.cfg['routing_vocabulary']=file_pin(root/'v.json')
                with self.assertRaisesRegex(ValueError,reason):c.vocabulary()
            artifact=load(root/'artifact.json');artifact['routing_vocabulary']={}
            (root/'artifact.json').write_text(json.dumps(artifact))
            c.cfg['init_artifact']['artifact']=file_pin(root/'artifact.json')
            with self.assertRaisesRegex(ValueError,'lacks its recorded'):c.vocabulary()

    def test_archive_disk_reservation(self):
        from student_pilot.checkpoint_space import Budget, check, plan
        root=directory()
        recipe=dict(wall_seconds=100,stop_before_seconds=10,resume_every_seconds=30,milestones=[1,2],export_at_stop=True)
        model=torch.nn.Linear(2,2)
        optimizer=torch.optim.AdamW(model.parameters())
        model(torch.ones(1,2)).sum().backward();optimizer.step()
        named=list(model.named_parameters())
        policy=plan(recipe,reserve_bytes=0,retained_archive_copies=1)
        native=check(root,named,optimizer,[],0,1,Budget(plan(recipe,reserve_bytes=0)))
        actual=check(root,named,optimizer,[],0,1,Budget(policy))
        self.assertGreater(actual['required_bytes'],native['required_bytes'])
        usage=os.statvfs(root)
        free=usage.f_bavail*usage.f_frsize
        reserve=free-(native['required_bytes']+actual['required_bytes'])//2
        self.assertGreater(reserve,0)
        # Reserve existing free space on paper, without allocating any file.
        # Native files fit, but retaining their archives must cross the real
        # available-space boundary. No filesystem reading is substituted.
        fits=check(root,named,optimizer,[],0,1,Budget(plan(recipe,reserve_bytes=reserve)))
        with self.assertRaisesRegex(ValueError,'Insufficient') as refused:
            check(root,named,optimizer,[],0,1,Budget(plan(recipe,reserve_bytes=reserve,retained_archive_copies=1)))
        (PROOFS/'DISK.json').write_text(json.dumps(dict(native=native,with_archives=actual,
            measured_free_bytes=free,reserve_bytes=reserve,native_fits=fits,refusal=str(refused.exception),
            stand_in='tiny synthetic model and optimizer; actual filesystem readings')))

    def test_pinned_native_frame_map_join(self):
        from student_pilot.r2_intake import intake
        root=directory();row=fixture(root)
        row['provenance']['alias']='d1/fixture_clean'
        original=deepcopy(row['student_input']);indices=original['frame_indices']
        row['student_input']={k:v for k,v in original.items() if k not in ('frames','dense_source')}
        mp=manifest(root/'m',[row]);value=load(mp)
        with gzip.open(root/'map.jsonl.gz','wt') as f:
            for i,p in zip(indices,original['frames']):
                h=p['sha256'];f.write(json.dumps(dict(d='d1',s='fixture_clean',i=i,sha256=h,
                    path='/data2/k6tk/'+h[:2]+'/'+h+'.png'))+'\n')
        with gzip.open(root/'plan.json.gz','wt') as f:json.dump(dict(v={'fixture_clean':dict(g='d1',raw_n=64)}),f)
        write(root/'fps.json',dict(schema='s1-fps-authority-v1',by_scene={'d1/fixture_clean':10}))
        value.update(frame_map=file_pin(root/'map.jsonl.gz'),frame_plan=file_pin(root/'plan.json.gz'),fps_authority=file_pin(root/'fps.json'))
        mp.write_text(json.dumps(value))
        accepted,report=intake(mp)
        self.assertEqual(len(accepted),1,report)
        self.assertEqual(accepted[0]['row']['student_input']['frame_indices'],indices)
        self.assertEqual(accepted[0]['row']['target'],row['target'])
        with gzip.open(root/'map.jsonl.gz','at') as f:f.write('{}\n')
        with self.assertRaisesRegex(ValueError,'changed pinned'):intake(mp)
        (PROOFS/'FRAME_JOIN.json').write_text(json.dumps(dict(schema='native d/s/i/path/sha256 gzip map',
            frames=len(indices),target_unchanged=True,stand_in='synthetic RGB content addresses; no real frame bytes')))

    def test_late_refusal_and_final_indices(self):
        from student_pilot.r2_materialize import materialize
        from student_pilot import r2_mix as M
        from student_pilot.carrier_c1_data import mixed_indices
        from tests.test_r2_sampling import binding
        root=directory();good=fixture(root);bad=deepcopy(good);bad['qid']='late'
        bad['student_input']['dense_source']['frames'][0]['sha256']='0'*64
        mp=manifest(root/'m',[bad,good])
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            report=materialize([mp],root/'store')
        self.assertEqual(report['intake'][0]['counts']['object_rel_direction_easy']['refused'],1)
        import sqlite3
        receipt=load(report['receipt']['path'])
        with sqlite3.connect(receipt['streams']['vqa']['database']['path']) as db:
            self.assertEqual([(i,json.loads(raw)['qid']) for i,raw in db.execute('SELECT i,row FROM rows')],[(0,'direct')])
        pins,counts,lookup=binding(root)
        # Admit one extra metadata row initially; its late frame refusal will
        # leave exactly the registered repeat-limit population for this cell.
        population=load(root/'population.json');population['cells']['direction']+=1
        (root/'population.json').write_text(json.dumps(population))
        count_record=load(root/'c.json');count_record['cells']['direction']+=1
        count_record['receipts']=[file_pin(root/'population.json')];(root/'c.json').write_text(json.dumps(count_record))
        indices=load(root/'i.json');indices['cells']['direction'].append(counts['vqa'])
        indices['counts_sha256']=file_pin(root/'c.json')['sha256'];(root/'i.json').write_text(json.dumps(indices))
        pins.update(counts=file_pin(root/'c.json'),indices=file_pin(root/'i.json'))
        counts['vqa']+=1
        before=next(M.plans(pins,counts,1))
        twin=deepcopy(good);twin['qid']='twin'
        small=manifest(root/'pair_m',[bad,good,twin]);value=load(small)
        value['mix_cells']={r['qid']:dict(type='facing_pairs',pair='p') for r in (good,twin)}
        value['mix_cells']['late']=dict(type='direction')
        small.write_text(json.dumps(value))
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            with self.assertRaisesRegex(ValueError,'missing or foreign cells'):
                materialize([small],root/'late_plan',mix_binding=dict(mix_pin=pins['mix'],counts_pin=pins['counts']))
        self.assertEqual(load(root/'late_plan/s/i.json')['cells']['facing_pairs'],[[0,1]])
        self.assertEqual(load(root/'late_plan/materialization.json')['status'],'refused')
        # Both producer and sampler use the post-refusal offsets. A bounded
        # slice cannot pass the registered repeat limit and must still refuse.
        value['mix_cells']['late']=dict(type='facing_pairs',pair='q')
        value['mix_cells']['twin']=dict(type='facing_pairs',pair='q')
        value['mix_cells']['direct']=dict(type='direction')
        small.write_text(json.dumps(value))
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            orphan=materialize([small],root/'orphan')
        self.assertEqual(orphan['intake'][0]['counts']['object_rel_direction_easy']['refused'],2)
        items=[];pair=0
        for cell in M.table()['cells']:
            kind,stream=cell['type'],cell['stream']
            n=load(pins['counts']['path'])['cells'][kind]
            for i in range(n):
                assignment=dict(type=kind)
                if kind=='facing_pairs':assignment['pair']=str(i//2)
                items.append(dict(stream=stream,mix_cell=assignment))
        refused_index=next(i for i,item in enumerate(items) if item['mix_cell']['type']=='direction')
        items=[item for i,item in enumerate(items) if i!=refused_index]
        counts['vqa']-=1
        # Metadata only: reverse native row order to force all offsets to change.
        items.reverse()
        merged=file_pin(LANE/'work/shared/dev_scene_exclusions_d0.json')
        write(root/'joined_counts.json',{**load(pins['counts']['path']),'merged_dev':merged})
        write(root/'presence.json',dict(schema='r2-frame-host-presence-v1',second_pose_source='present',synthetic=True))
        final=M.reindex(items,dict(mix_pin=pins['mix'],counts_pin=file_pin(root/'joined_counts.json'),
                                  source_presence=file_pin(root/'presence.json')),root/'final')
        self.assertEqual(load(final['counts']['path'])['merged_dev'],merged)
        self.assertEqual(load(final['counts']['path'])['cells']['direction'],count_record['cells']['direction']-1)
        self.assertEqual(final['source_presence'],file_pin(root/'presence.json'))
        totals=Counter();index_kind={};offsets=Counter();pairs={}
        for item in items:
            s=item['stream'];i=offsets[s];offsets[s]+=1;index_kind[s,i]=item['mix_cell']['type']
            if item['mix_cell']['type']=='facing_pairs':pairs[i]=item['mix_cell']['pair']
        for plan in mixed_indices(counts,1000,world=4,r2_sampling=final):
            twins=Counter()
            for stream,indices in plan:
                for index in indices:
                    kind=index_kind[stream,index];totals[kind]+=1
                    if kind=='facing_pairs':twins[pairs[index]]+=1
            self.assertTrue(all(n==2 for n in twins.values()))
        self.assertEqual(dict(totals),M.allocation(M.table()))
        self.assertNotEqual(before,next(M.plans(final,counts,1)))
        partial=[item for item in items if item.get('mix_cell',{}).get('pair')!='0']
        first=next(item for item in items if item.get('mix_cell',{}).get('pair')=='0')
        with self.assertRaisesRegex(ValueError,'incomplete facing'):
            M.reindex(partial+[first],dict(mix_pin=pins['mix'],counts_pin=pins['counts']),root/'partial')
        (PROOFS/'REINDEX.json').write_text(json.dumps(dict(late_refusals=1,draws=dict(totals),
            exact_totals=True,twins_together=True,initial_cells=count_record['cells'],
            final_cells=load(final['counts']['path'])['cells'],
            boundary='tiny real materializer and separate final-index metadata after the same one-row refusal; no full store')))

    def test_checklist_staging_banks_and_failures(self):
        from launch_r2.checklist import Checklist, ITEMS
        from launch_r2 import staging, build
        from student_pilot.r2_policy import seal_catalog
        root=directory();(root/'k').mkdir();raw=b'input';h=hashlib.sha256(raw).hexdigest()
        import base64
        entries={'u/'+h:dict(payload=base64.b64encode(raw).decode(),sha256=h)}
        staging.stage_inputs(entries,root)
        write(root/'plan.json',dict(entries=entries))
        write(root/'k/0.json',dict(staging=file_pin(root/'plan.json')))
        write(root/'bank.json',[dict(id='fixture',venue='clean')]);files={'dev-S1':file_pin(root/'bank.json')}
        write(root/'catalog.json',seal_catalog(files))
        cfg=dict(input=dict(path='u/'+h,sha256=h),r2_evaluation=dict(catalog=file_pin(root/'catalog.json')))
        c=Checklist(root,dict(checks=dict(bank_files=files)),cfg)
        c.step(2,c.staged);c.step(5,c.banks)
        c.packet['checks']['bank_files']={}
        with self.assertRaisesRegex(ValueError,'missing'):c.banks()
        c.packet['checks']['bank_files']=files
        write(root/'wrong_catalog.json',dict(items=[]))
        c.cfg['r2_evaluation']['catalog']=file_pin(root/'wrong_catalog.json')
        with self.assertRaisesRegex(ValueError,'membership'):c.banks()
        with self.assertRaisesRegex(ValueError,'incomplete'):c.finish()
        with self.assertRaisesRegex(ValueError,'repeated'):c.step(2,c.staged)
        for item in (1,4,9,11):
            with self.assertRaisesRegex(ValueError,'refused'):
                c.step(item,lambda:(_ for _ in ()).throw(ValueError('missing byte boundary')))
        self.assertTrue(all(load(c.output/(str(i)+'.json'))['status']=='REFUSE' for i in (1,4,9,11)))
        (root/'u'/h).write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'digest'):c.staged()

    def test_parent_writer_roundtrip_bytes(self):
        from launch_r2.checklist import Checklist
        root=directory();write(root/'sessions.json',{'j/fixture/01':'https://invalid.invalid/session'})
        (root/'b').mkdir()
        (root/'b/wh.json').write_bytes((Path(__file__).parents[1]/'launch_s1/b/wh.json').read_bytes())
        (root/'g.py').write_bytes((Path(__file__).parents[1]/'launch_s1/b/gcsput.py').read_bytes())
        cfg=dict(r2_persistence=dict(uploader=file_pin(root/'g.py')))
        packet=dict(checks=dict(roundtrip=dict(sessions=file_pin(root/'sessions.json'),prefix='j/fixture',
                    download_url='https://storage.googleapis.com/fixture/j/fixture/01')))
        payload=[]
        class Connection:
            def __init__(self,*args,**kwargs):self.data=b''
            def putrequest(self,*args):pass
            def putheader(self,*args):pass
            def endheaders(self):pass
            def send(self,block):self.data+=block
            def getresponse(self):
                import base64
                payload.append(self.data)
                data=json.dumps(dict(size=len(self.data),generation='1',md5Hash=base64.b64encode(hashlib.md5(self.data).digest()).decode())).encode()
                return SimpleNamespace(status=200,read=lambda:data)
        c=Checklist(root,packet,cfg)
        def response(raw,generation='1'):
            value=io.BytesIO(raw);value.headers={'x-goog-generation':generation};return value
        with patch('http.client.HTTPSConnection',Connection),patch('urllib.request.urlopen',side_effect=lambda *a,**k:response(payload[-1])):
            c.step(4,c.roundtrip)
        self.assertEqual(load(c.receipts[4]['path'])['status'],'PASS')
        with patch('http.client.HTTPSConnection',Connection),patch('urllib.request.urlopen',return_value=response(b'changed')):
            with self.assertRaisesRegex(ValueError,'Restored state differs'):c.roundtrip()
        with patch('http.client.HTTPSConnection',Connection),patch('urllib.request.urlopen',return_value=response(payload[-1],'2')):
            with self.assertRaisesRegex(ValueError,'generation differs'):c.roundtrip()
        from tests.test_r2_build5_faults import changed_on_read
        receipt=root/'sessions.json.receipts.jsonl'
        def bad_receipt():
            values=[json.loads(line) for line in receipt.read_text().splitlines()]
            for value in values:value['generation']=None
            receipt.write_text('\n'.join(json.dumps(value) for value in values))
        with patch('http.client.HTTPSConnection',Connection),changed_on_read(receipt,1,bad_receipt):
            with self.assertRaisesRegex(ValueError,'Upload generation'):c.roundtrip()
        bad_tool=root/'bad_writer.py';bad_tool.write_text('def main(args):\n return 1\n')
        c.cfg['r2_persistence']['uploader']=file_pin(bad_tool)
        with self.assertRaisesRegex(ValueError,'upload failed'):c.roundtrip()
        c.cfg['r2_persistence']['uploader']=file_pin(root/'g.py')
        c.packet['checks']['roundtrip']['download_url']='https://invalid.invalid/other'
        with self.assertRaisesRegex(ValueError,'uploaded object'):c.roundtrip()
        c.packet['checks']['roundtrip']['prefix']='j/benchmark'
        with self.assertRaisesRegex(ValueError,'not opaque'):c.roundtrip()
        c.packet['checks']['roundtrip']['prefix']='not-local'
        with self.assertRaisesRegex(ValueError,'job-local'):c.roundtrip()
        (PROOFS/'ROUNDTRIP.json').write_text(json.dumps(dict(parent_writer=True,restored=True,
            stand_in='Successful round trip uses HTTP byte stand-ins only and the real parent uploader; refusal tests also inject changed receipt bytes and an unsuccessful uploader fixture')))
