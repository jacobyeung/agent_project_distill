"""Review regressions use published slices and real admission/staging functions."""
from copy import deepcopy
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import unittest
from unittest.mock import patch
from tests.test_r2_data_path import directory, fixture, manifest, LANE, PROOFS
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot import r2_contract as C, r2_grammar as G, r2_openers as O
from student_pilot.r2_exclusions import Exclusions
from student_pilot.r2_intake import intake
from student_pilot.r2_materialize import materialize
from launch_r2 import staging, persistence, build as B, host


class ReviewGuards(unittest.TestCase):
    def test_isolated_mutation_guards(self):
        target='<think>\nLocate: the chair is seen in frame 1.\nRelate: the chair is to the right; the answer is A.\n</think>\nA'
        with self.assertRaisesRegex(ValueError,'Answer restatement'):
            G.legacy_direct(target,'Which side?',32)
        row=fixture(directory(),stream='routing');row['response_source']='deployed'
        with self.assertRaisesRegex(ValueError,'Deployed selector'):
            G.validate_program(row)
        from tests.test_r2_families import ground
        from student_pilot.ground_rows import render_ground
        row=ground(directory(),'recovery')
        row['events'][-1]['text']='\nI estimate the visible gap.\n</think>\n<answer>'+row['answer']+'</answer>'
        row['target'],row['tool_output_spans'],_=render_ground(row['events'],row['answer'])
        with self.assertRaisesRegex(ValueError,'located direct continuation'):
            C.event_row(row)
        row=ground(directory(),'recovery')
        row['events'][4:4]=[dict(row['events'][2],call_id='g2'),dict(row['events'][3],call_id='g2')]
        row['ground_record']['events'].append(deepcopy(row['ground_record']['events'][0]))
        row['target'],row['tool_output_spans'],_=render_ground(row['events'],row['answer'])
        with self.assertRaisesRegex(ValueError,'calls again'):
            C.event_row(row)

    def test_duplicate_row_and_repeat_limit(self):
        root=directory();row=fixture(root)
        admitted,report=intake(manifest(root/'duplicate',[row,row]))
        self.assertEqual(len(admitted),1)
        self.assertIn('Duplicate QID',report['refusals'][0]['reason'])
        from tests.test_r2_sampling import binding
        from student_pilot import r2_mix as M
        pins,_,_=binding(root)
        pop=load(root/'population.json');counts=load(root/'c.json')
        pop['cells']['pose']=(M.allocation(M.table())['pose']+4)//5
        (root/'population.json').write_text(json.dumps(pop))
        counts['cells']=pop['cells'];counts['receipts']=[file_pin(root/'population.json')]
        (root/'c.json').write_text(json.dumps(counts))
        with self.assertRaisesRegex(ValueError,'repeats'):
            M.preflight(pins['mix'],file_pin(root/'c.json'))

    def test_raw_published_pool_masks_printed_responses(self):
        from student_pilot.r2_adapters import normalize
        raw=json.loads(next((LANE/'rows/slices_final/a0_pool_abs_distance_reworded.jsonl').open()))
        indices=raw['frame_indices']
        from student_pilot.carrier_c1_routing import alias_of
        fps=load(LANE/'work/kit07ca49df_meta/m/k/frame_rates.json')['by_scene'][alias_of(raw['canonical'])]
        # Only RGB metadata stands in; printed text and GT provenance are real.
        frame_map={raw['qid']:dict(fps=fps,total_num_frames=indices[-1]+1,
            frames=[dict(path='/fh/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
        row=normalize(raw,frame_map)
        self.assertEqual(row['target'],raw['suffix'])
        C.validate(row,'routing')
        self.assertEqual(len(row['tool_output_spans']),raw['suffix'].count('<tool_response>'))

    def test_direct_route_in_wrong_stream(self):
        row=fixture(directory());row['question_type']='route_planning'
        with self.assertRaisesRegex(ValueError,'VQA only'):
            C.validate(row,'routing')

    def test_wrong_independent_scene(self):
        root=directory();row=fixture(root);m=load(manifest(root/'m',[row]))
        rule=Exclusions(m['exclusions'])
        with self.assertRaisesRegex(ValueError,'independent coverage'):
            rule.check(row,dict(status='known',names=['d1/other']))

    def test_distinct_pose_sources(self):
        root=directory();p=root/'input.json';write(p,dict(test=True));pin=file_pin(p)
        packet={k:pin for k in ('configuration','pose_template','real_proof','counts')}
        packet.update(manifests=[pin],pose_sources=[pin,pin])
        with self.assertRaisesRegex(ValueError,'distinct pose'):
            host.input_paths(packet,root)

    def test_manifest_contract_and_validator(self):
        root=directory();row=fixture(root);row.pop('trace_contract')
        path=manifest(root/'m',[row]);original=load(path)
        self.assertEqual(len(intake(path)[0]),1)
        for key in ('trace_contract','validator_sha256'):
            path.write_text(json.dumps({**original,key:'wrong'}))
            with self.assertRaisesRegex(ValueError,'validator pin'):
                intake(path)

    def test_published_ground_and_selector_provenance(self):
        from student_pilot.r2_adapters import normalize
        for family in ('a0_units','a0_recovery'):
            raw=json.loads(next((LANE/'rows/slices_final'/(family+'.jsonl')).open()))
            indices=raw['frame_indices']; fps=raw['provenance']['fps_source']['value']
            frames={raw['qid']:dict(fps=fps,total_num_frames=indices[-1]+1,
                frames=[dict(path='/fh/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
            row=normalize(raw,frames)
            C.validate(row,'routing')
            self.assertTrue(row['tool_output_spans'])
            for change in (dict(mask_source='deployed_selector_v3'),dict(mask_source='sam3_fitted_selector'),
                           dict(geometry_source='deployed'),dict(gt_authority='selector')):
                changed=deepcopy(row);changed['ground_record'].update(change)
                with self.assertRaisesRegex(ValueError,'lineage'):
                    C.event_row(changed)
            with self.assertRaisesRegex(ValueError,'lineage'):
                C.event_row({**row,'response_source':None})

    def test_keep_preparation_never_resets(self):
        cfg=dict(routing_opener_init='keep',init_artifact=dict(lm='full',artifact=dict(sha256=C.INIT['artifact_sha256'])))
        with self.assertRaisesRegex(ValueError,'vocabulary witness'):
            O.preparation(cfg)
        with self.assertRaisesRegex(ValueError,'full warm'):
            O.preparation({**cfg,'init_artifact':dict(lm='heads')})
        with self.assertRaisesRegex(ValueError,'init artifact'):
            O.preparation({**cfg,'init_artifact':dict(lm='full',artifact={})})
        root=directory();p=root/'v.json'
        write(p,dict(artifact_sha256=C.INIT['artifact_sha256'],lineage_sha256=C.INIT['artifact_sha256'],
                     vocabulary_sha256='a'*64,tokens={'<move':1}))
        O.preparation({**cfg,'routing_vocabulary':file_pin(p)})
        O.preparation(dict(routing_opener_init='reset'))

    def test_missing_sampler_refuses(self):
        from student_pilot.carrier_c1_data import mixed_indices
        with self.assertRaisesRegex(ValueError,'r2_sampling'):
            next(mixed_indices({'vqa':1},1,require_r2=True))

    def test_bad_row_keeps_denominator(self):
        root=directory();good=fixture(root);bad={**good,'qid':'bad','target':'A'}
        m=manifest(root/'m',[good,bad])
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            result=materialize([m],root/'store')
        counts=result['intake'][0]['counts']['object_rel_direction_easy']
        self.assertEqual((counts['seen'],counts['admitted'],counts['refused']),(2,1,1))
        self.assertEqual(load(result['receipt']['path'])['streams']['vqa']['count'],1)

    def test_relative_plan_assembly_and_corruption(self):
        root=directory();raw=b'fixture';h=hashlib.sha256(raw).hexdigest()
        cfg=dict(input=dict(path='u/'+h,sha256=h))
        entries={'u/'+h:dict(payload=base64.b64encode(raw).decode(),sha256=h)}
        self.assertEqual(staging.validate_plan(cfg,entries),['u/'+h])
        staging.stage_inputs(entries,root)
        self.assertEqual((root/'u'/h).read_bytes(),raw)
        with self.assertRaisesRegex(ValueError,'absent'):
            staging.validate_plan(cfg,{})
        with self.assertRaisesRegex(ValueError,'digest'):
            staging.assemble({**entries['u/'+h],'sha256':'0'*64},root/'bad')
        archive=root/'a.tar'
        with tarfile.open(archive,'w') as handle:
            m=tarfile.TarInfo('../escape');m.size=1;handle.addfile(m,io.BytesIO(b'x'))
        with self.assertRaisesRegex(ValueError,'escaped'):
            staging.unpack(archive,root/'unpacked')

    def test_all_json_fields_and_outputs_scanned(self):
        hashes=load(B.TREE/'launch_s1/b/wh.json')
        for v in ({'note':'MindCube'},{'dataset':'x'},{'other':['ARKIT_frames']}):
            with self.assertRaises(ValueError):B.scan_value(v,hashes)
        v=json.loads(B.capsule_json({'note':'MindCube'}));B.scan_value(v,hashes)
        v['sha256']='0'*64
        with self.assertRaises(ValueError):B.scan_value(v,hashes)

    def test_parent_configuration_path(self):
        from student_pilot.r2_config import configure
        parent=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        self.assertEqual(configure(parent,None,overrides=False),parent)
        with self.assertRaisesRegex(ValueError,'Invalid'):
            configure({'streams':{s:{} for s in ('pose','vqa','pointing','routing')}},None,overrides=False)

    def test_bank_caller_catalog_refuses(self):
        from student_pilot import r2_policy as P
        for item in ({'source':'MindCube','id':'mindcube_1'}, {'id':'vsibench_1','question_type':'camera_displacement'},
                     {'id':'revsi_1','question_type':'object_abs_distance'}):
            root=directory();p=root/'bank.json';write(p,[item])
            cat=P.seal_catalog({'dev-S1':file_pin(p)})
            c=root/'cat.json';write(c,cat)
            with self.assertRaisesRegex(ValueError,'sealed kit'):
                P.read_bank(file_pin(p),file_pin(c),choices=(),camera_routing=True)

    def test_persistence_survives_project_full(self):
        from student_pilot.r2_config import configure
        parent=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        cfg=configure(parent,'none');root=directory();cfg['output']=str(root)
        cfg['r2_persistence']={"test":True}
        # Only the network transport stands in. Real archive creation, hashing,
        # receipt checks and ordering run on tiny synthetic export bytes.
        uploaded=[]
        def uploader(path,key):
            raw=path.read_bytes();width=(len(raw)+3)//4
            records=[]
            for i in range(4):
                block=raw[i*width:(i+1)*width]
                records.append(dict(generation=str(i+1),offset=i*width,bytes=len(block),
                                    sha256=hashlib.sha256(block).hexdigest()))
            uploaded.append(key)
            return records
        def full(*args):
            raise OSError(28,'full')
        for step in cfg['recipe']['milestones']:
            d=root/('m'+str(step));d.mkdir();write(d/'artifact.json',dict(step=step,synthetic=True))
            (d/'weights.dat').write_bytes(b'tiny export boundary')
            receipt=persistence.upload(cfg,d,'export',uploader,full)
            self.assertTrue(receipt['durable'])
        self.assertEqual(len(uploaded),len(cfg['recipe']['milestones']))
        (PROOFS/'PERSISTENCE.json').write_text(json.dumps(dict(plan=persistence.plan(cfg),milestones=len(uploaded),
            stand_in='network uploader, tiny export bytes',checkpoint_restore_checked=False)))
