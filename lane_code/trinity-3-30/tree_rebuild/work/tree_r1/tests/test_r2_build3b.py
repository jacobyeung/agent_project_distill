"""Native metadata rebuild, store producer and every-rank reader with synthetic RGB."""
from copy import deepcopy
import gzip
import json
import os
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

from student_pilot import r2_scene_bindings as S
from student_pilot import s1_exclusions as E
from student_pilot.p3_provenance import file_pin, load, pinned, write, digest
from student_pilot.r2_materialize import materialize
from student_pilot.r2_intake import intake
from student_pilot import s1_pool
from tests.test_r2_data_path import PROOFS, LANE, directory, fixture, manifest, TinyProcessor

META = LANE/'work/kit07ca49df_meta/m/k'
DEV = file_pin(Path(S.__file__).with_name('r2_dev_merged.json'))
OLD = file_pin(META/'dev_scene_exclusions.json')
BENCH = file_pin(META/'benchmark_scene_exclusions.json')
ROOMS = load(LANE/'work/shared/WITHHELD_ROOMS_80.json')
NATIVE = ROOMS['aliases'][ROOMS['rooms'][0]][0]
ALIAS = next(x for x in ROOMS['aliases'][ROOMS['rooms'][0]] if '/v' in x)


def at_scene(row, scene, qid):
    row = deepcopy(row)
    row.update(qid=qid, dataset=scene.split('/')[0], scene=scene.split('/')[1], canonical=scene)
    if row.get('ground_record'):
        row['ground_record']['qid']=qid
    row.setdefault('provenance', {}).update(canonical=scene, alias=scene)
    return row


def pool_fixture(root):
    root.mkdir()
    original = load(META/'pool_manifest.json')
    selection = load(META/'pool_selection.json')
    assert selection['schema'] == 's1-pool-selection-v1'
    assert all(type(i) is int for i in load(META/'pool_indices_2.json'))
    value = deepcopy(original)
    value['sets'] = []
    for name in ('T0_gen_r2', 'T0_room', 'ROUTE_direct'):
        entry = deepcopy(next(v for v in original['sets'] if v['name'] == name))
        rows = []
        for i, scene in enumerate(('d1/fixture_clean', NATIVE, ALIAS)):
            row = dict(qid=name+str(i), dataset='d1', scene=scene.split('/')[1],
                       question_type='route_planning', head_program=None, score_nomination_allowed=False,
                       answer='A', target='<think>\nThe doorway is visible in frame 1.\n</think>\n\nA')
            if name != 'ROUTE_direct':
                from student_pilot.ground_rows import pack
                if name == 'T0_room':
                    from generator.derivgen_v7.derivgen.room_rows_v314 import QUESTION
                    call = '<ground mode="room">'
                    response = '<tool_response>\nroom: frames 1,2\nfloor height 0.00 m\nfloor cells 400; supported cells 400; cell size 0.05 m; min frames 1\narea 1.00 m^2\n</tool_response>'
                    prefix = 'I will project the depth points onto the floor and measure their covered area.'
                    suffix = 'The covered floor area is 1.00 square meters.'
                    question, kind = QUESTION, 'room_size_estimation'
                else:
                    call = '<gap a="chair" b="table" rule="box_grid_5cm">'
                    response = '<tool_response>\ndistance 1.00 m\n</tool_response>'
                    prefix, suffix = 'Call: measure the gap.', 'Step: the printed distance is 1.00 m.'
                    question, kind = 'What is the distance between the chair and table?', 'object_abs_distance'
                record = dict(qid=row['qid'], candidate_id=row['qid'], spec_version='3.14', type=kind,
                              question=question, options=[], answer='1.00', gt_answer='1.00', answer_content='1.00',
                              events=[dict(call=call,response=response)], not_seen=False, gt_agrees=True, training_admitted=False,
                              suffix='<think>\n'+prefix+'\n'+call+'\n'+response+'\n'+suffix+'\n</think>\n<answer>1.00</answer>')
                row = {**pack(record,dict(canonical=scene)), 'dataset':'d1', 'scene':scene.split('/')[1]}
            rows.append(row)
        path = root/(name+'.jsonl.gz')
        with gzip.open(path, 'wt') as handle:
            handle.write(''.join(json.dumps(row)+'\n' for row in rows))
        entry.update(files={('rows' if name == 'ROUTE_direct' else 'packed'):{**file_pin(path), 'rows':len(rows), 'bytes':path.stat().st_size}},
                     rows_per_type=dict(__import__('collections').Counter(r['question_type'] for r in rows)),
                     after_exclusions=dict(rows=len(rows)))
        value['sets'].append(entry)
    for name in ('dev_s1', 'eval_rooms', 'room_release_gate'):
        path = root/(name+'.tsv'); path.write_text('')
        value['exclusions'][name].update(list=str(path), list_sha256=file_pin(path)['sha256'], rows=0)
    value['exclusions']['dev_s1'].update(withhold=OLD['path'], withhold_sha256=OLD['sha256'])
    value['exclusions']['eval_rooms'].update(v2=BENCH['path'], v2_sha256=BENCH['sha256'])
    write(root/'0.json', value)
    return file_pin(root/'0.json')


def scene_fixture(root, base_rows=None):
    pool = pool_fixture(root/'pool')
    specs, manifests = {}, []
    for name, stream in S.SOURCES.items():
        row = deepcopy(base_rows[stream]) if base_rows else fixture(root, stream=stream)
        row['qid'] = name
        values = [row, at_scene(row,NATIVE,name+'_native'), at_scene(row,ALIAS,name+'_alias')]
        path = manifest(root/name, values, stream, family=name)
        m = load(path)
        m.update(scene_source=name, dev_scene_exclusions=DEV,
                 mix_cells={r['qid']:dict(type={'vqa':'direction','routing':'camera_displacement'}.get(stream,stream)) for r in values})
        path.write_text(json.dumps(m))
        manifests.append(path)
        old_rule = E.Exclusions(OLD, BENCH)
        old_rule.expect(name, values)
        for r in values:old_rule.keep(r, name)
        old = root/name/'old.json'
        write(old, dict(schema='c1-stream-v1', source_scene_exclusions=old_rule.report(), count=len(values), rows_metadata=m['rows']))
        specs[name] = dict(receipt=file_pin(old), rows=m['rows'], count=len(values))
    return dict(pool_manifest=pool, sources=specs), manifests


class Build3b(unittest.TestCase):
    def test_merged_schema_and_every_alias(self):
        value = S.merge(OLD, file_pin(LANE/'work/shared/WITHHELD_ROOMS_80.json'))
        merged=load(pinned(DEV))
        self.assertEqual(value['rooms'], merged['rooms'])
        old_rule, merged_rule=E.Exclusions(OLD,BENCH), E.Exclusions(DEV,BENCH)
        derived_path=directory()/'derived.json';write(derived_path,value)
        derived_rule=E.Exclusions(file_pin(derived_path),BENCH)
        for aliases in ROOMS['aliases'].values():
            for alias in aliases:
                self.assertEqual(derived_rule.excluded(dict(scene=alias)),merged_rule.excluded(dict(scene=alias)))
        for field in ('natives','rooms','physical_groups'):
            self.assertLessEqual(set(load(pinned(OLD))[field]), set(value[field]))
        rule = E.Exclusions(DEV, BENCH)
        for room, aliases in ROOMS['aliases'].items():
            for name in [room, *aliases]:
                self.assertTrue(rule.excluded(dict(scene=name)))
                self.assertTrue(rule.excluded(dict(dataset='d1',scene='clean',provenance=dict(alias=name))))
        with self.assertRaisesRegex(ValueError,'Foreign sealed'):S.merge(DEV, file_pin(LANE/'work/shared/WITHHELD_ROOMS_80.json'))
        with self.assertRaisesRegex(ValueError,'foreign lists'):S.require_merged(OLD)
        with self.assertRaisesRegex(ValueError,'foreign lists'):S.require_merged(None)
        with self.assertRaisesRegex(ValueError,'Unknown'):rule.excluded(dict(scene='unknown/place'))
        S.verify({})
        with self.assertRaisesRegex(ValueError,'binding differs'):
            S.verify(dict(r2_identity=True))

    def test_pool_native_selection_and_old_pin_mutation(self):
        root = directory()
        pin = pool_fixture(root/'pool')
        result = S.rebuild_pool(pin, DEV, BENCH, root/'rebuilt')
        value = load(pinned(result))
        for name in value['sources']:
            self.assertEqual([r['qid'] for r in s1_pool.selected_rows(result,name)], [name+'0'])
            self.assertEqual(value['source_scene_exclusions']['sources'][name]['dev_matches'],2)
        with self.assertRaisesRegex(ValueError,'foreign lists'):
            E.totals(load(META/'pool_selection.json')['source_scene_exclusions'],E.Exclusions(DEV,BENCH))
        (PROOFS/'B3B_POOL_PROOF.json').write_text(json.dumps(dict(synthetic=True, input=pin, receipt=result,
            sources=value['sources'], standins='None; native metadata producer and reader'),indent=2)+'\n')

    def stream_proof(self, name):
        root = directory()
        spec, manifests = scene_fixture(root)
        path = manifests[list(S.SOURCES).index(name)]
        accepted, report = intake(path)
        self.assertEqual([x['row']['qid'] for x in accepted],[name])
        self.assertEqual(report['rows_withheld'],2)
        with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            native = load(pinned(materialize([path],root/'stores')['receipt']))
            from student_pilot.r2_contract import Admission
            guard = Admission(native['r2_membership'])
            store = native['streams'][S.SOURCES[name]]
            with sqlite3.connect(pinned(store['database'])) as connection:
                records = list(connection.execute('SELECT row,target FROM rows'))
            self.assertEqual(len(records),1)
            row, target = map(json.loads, records[0])
            for rank in range(4):
                self.assertEqual(guard.check(row,S.SOURCES[name],target)['qid'],name)
            # Re-sealing a leaked row does not bypass the reader's independent rule.
            for scene in (NATIVE,ALIAS):
                leaked = at_scene(row,scene,name+'_leak')
                member = dict(contract=load(pinned(native['r2_membership']))['contract'],
                              rows={leaked['qid']:digest(dict(row=leaked,target=target,stream=S.SOURCES[name]))})
                pin = root/(digest(scene)+'leak.json')
                write(pin,member)
                with self.assertRaisesRegex(ValueError,'withheld room'):
                    Admission(file_pin(pin)).check(leaked,S.SOURCES[name],target)
        result = S.rebuild_receipt({**spec['sources'][name],'source':name},DEV,BENCH,root/'receipt')
        self.assertEqual(load(pinned(result))['scene_rebuild']['rows_withheld'],2)

    def test_vqa(self):self.stream_proof('vqa')
    def test_camera(self):self.stream_proof('camera')
    def test_pose_a3v2(self):self.stream_proof('pose_a3v2')
    def test_pose_a2v3(self):self.stream_proof('pose_a2v3')
    def test_pointing(self):self.stream_proof('pointing')

    def test_host_metadata_counts_and_refusals(self):
        from student_pilot import r2_mix as M
        from launch_r2 import host as H
        root = directory()
        spec, manifests = scene_fixture(root)
        write(root/'mix.json',M.table())
        cfg = dict(dev_scene_exclusions=DEV,benchmark_scene_exclusions=BENCH,r2_all_stream_exclusions=True,
                   r2_build2=dict(mix=file_pin(root/'mix.json')))
        write(root/'spec.json',spec)
        packet = dict(scene_rebuild=file_pin(root/'spec.json'),output='o/x')
        rebound, paths, proof = S.prepare_host(root,packet,cfg,manifests)
        counts = load(pinned(proof['counts']))
        self.assertEqual(counts['cells'],dict(direction=1,camera_displacement=1,pose=2,pointing=1))
        self.assertEqual(load(pinned(proof['indices']))['cells']['pose'],[0,1])
        self.assertTrue(all(load(p)['dev_scene_exclusions']==DEV for p in paths))
        with self.assertRaisesRegex(ValueError,'missing or foreign cells'):
            M.preflight(file_pin(root/'mix.json'),proof['counts'])
        bad = deepcopy(rebound)
        bad['r2_sampling']['counts'] = OLD
        with self.assertRaisesRegex(ValueError,'Host counts'):S.verify(bad)
        with self.assertRaisesRegex(ValueError,'Missing all-stream'):S.prepare_host(root,{},cfg,manifests)
        with self.assertRaisesRegex(ValueError,'new folder'):S.prepare_host(root,packet,cfg,manifests)
        with self.assertRaisesRegex(ValueError,'escapes'):S.prepare_host(root,{**packet,'output':'../bad'},cfg,manifests)
        with self.assertRaisesRegex(ValueError,'sealed source'):
            S.prepare_host(root,{**packet,'output':'o/foreign','pose_sources':[OLD]},cfg,manifests,full=True)
        bad = deepcopy(spec);bad['sources'] = {}
        with self.assertRaisesRegex(ValueError,'every stream'):S.rebuild(bad,cfg,root/'bad')
        one = dict(spec['sources']['vqa'],source='vqa')
        with self.assertRaisesRegex(ValueError,'input receipt'):
            S.rebuild_receipt({**one,'count':4},DEV,BENCH,root/'bad_count')
        write(root/'incomplete.json',dict(count=4,rows_metadata=one['rows']))
        with self.assertRaisesRegex(ValueError,'incomplete'):
            S.rebuild_receipt({**one,'count':4,'receipt':file_pin(root/'incomplete.json')},DEV,BENCH,root/'incomplete')
        # Local metadata population limits fail before a store can exist.
        large = root/'large.jsonl'
        large.write_text('{}\n'*2001)
        with self.assertRaisesRegex(ValueError,'2000'):list(S.rows(file_pin(large)))
        result = load(pinned(rebound['r2_scene_rebuild']))
        for change in ('source','count','invalid','membership','cross','pair','pairs_ok','pool'):
            values = [load(p) for p in manifests]
            value = values[0]
            if change == 'source':value['scene_source']='unknown'
            if change == 'count':value['count'] += 1
            if change == 'invalid':value['row_bindings']={}
            if change == 'membership':value['scene_source']='pool'
            if change == 'cross':value['mix_cells']['vqa']['type']='pose'
            if change in ('pair','pairs_ok'):
                value['mix_cells']['vqa'] = dict(type='facing_pairs',pair='a')
                if change == 'pairs_ok':
                    raw = list(S.rows(value['rows']))
                    extra = deepcopy(raw[0]);extra['qid']='vqa_twin';extra['provenance']['source_qid']='vqa'
                    p = manifest(root/'twins',raw+[extra],family='vqa_twins')
                    value = {**load(p), 'scene_source':'vqa', 'mix_cells':dict(value['mix_cells'],vqa_twin=dict(type='facing_pairs',pair='a'))}
                    values[0]=value
            if change == 'pool':
                value['scene_source']='pool'
                raw = list(S.rows(value['rows']))
                raw[0]['provenance']['source_qid']='ROUTE_direct0'
                p = manifest(root/'pooled',raw,family='pooled')
                values[0]={**load(p),'scene_source':'pool','mix_cells':value['mix_cells']}
            selected=[]
            for i,value in enumerate(values):
                path = root/(change+str(i)+'.json');write(path,value);selected.append(path)
            dest=root/(change+'_out');dest.mkdir()
            if change in ('pairs_ok','pool','invalid'):
                _,c,idx=S.populations(selected,rebound,result,dest)
                if change=='pairs_ok':self.assertEqual(load(pinned(idx))['cells']['facing_pairs'],[[0,1]])
            else:
                with self.assertRaises(ValueError):S.populations(selected,rebound,result,dest)
        bad_result=deepcopy(result);bad_result['receipts']={}
        write(root/'bad_result.json',bad_result)
        with self.assertRaisesRegex(ValueError,'every stream'):
            S.verify({**rebound,'r2_scene_rebuild':file_pin(root/'bad_result.json')})
        bad_result=deepcopy(result)
        bad_ref=load(pinned(result['scene_coverage']['reference']));bad_ref['exact_rebuilt_population']=False
        write(root/'bad_ref.json',bad_ref)
        bad_result['scene_coverage']['reference']=file_pin(root/'bad_ref.json')
        write(root/'bad_reference_result.json',bad_result)
        with self.assertRaisesRegex(ValueError,'different withheld population'):
            S.verify({**rebound,'r2_scene_rebuild':file_pin(root/'bad_reference_result.json'),
                      'scene_coverage':bad_result['scene_coverage']})
        # Real execute_packet reaches the rebuild and repeat gate before any materialization.
        from tests.test_r2_policy import evidence
        cfg['r2_build2']['registry']=evidence(root/'e')
        write(root/'cfg.json',cfg)
        write(root/'proof.json',dict(synthetic=True))
        write(root/'pose.json',dict(synthetic=True))
        pose_sources=[]
        for i,name in enumerate(('pose_a3v2','pose_a2v3')):
            p=root/('ps'+str(i)+'.json');write(p,dict(source=name));pose_sources.append(file_pin(p))
            path=manifests[list(S.SOURCES).index(name)]
            value=load(path);value['pose_source_sha256']=file_pin(p)['sha256'];path.write_text(json.dumps(value))
        packet.update(configuration=file_pin(root/'cfg.json'),real_proof=file_pin(root/'proof.json'),
                      pose_template=file_pin(root/'pose.json'),pose_sources=pose_sources,
                      manifests=[file_pin(p) for p in manifests],output='o/y')
        write(root/'k/launch.json',dict(config=dict(file=str(root/'cfg.json'),sha256=packet['configuration']['sha256'])))
        with self.assertRaisesRegex(ValueError,'missing or foreign cells'):
            H.execute_packet(root,packet,H.Guard(root),full=False)
        self.assertFalse((root/'o/y/a').exists())
        (PROOFS/'B3B_COUNTS_PROOF.json').write_text(json.dumps(dict(synthetic=True,counts=proof['counts'],
             indices=proof['indices'],cells=counts['cells'],repeat_gate='refused incomplete fixture cells before materialization'),indent=2)+'\n')

    def test_pool_metadata_mutations(self):
        root = directory();pin=pool_fixture(root/'pool')
        for change in ('count','lost','invalid'):
            value=load(pinned(pin))
            if change=='count':value['sets'][0]['files']['packed']['rows']+=1
            if change=='lost':
                path=root/'lost.tsv';path.write_text('T0_gen_r2\tT0_gen_r20\n')
                value['exclusions']['dev_s1'].update(list=str(path),list_sha256=file_pin(path)['sha256'],rows=1)
            if change=='invalid':
                entry=value['sets'][0];metadata=entry['files']['packed']
                rr=list(S.rows({k:metadata[k] for k in ('path','sha256')}));rr[0]['gt_accepted']=False
                path=root/'invalid.gz'
                with gzip.open(path,'wt') as handle:handle.write(''.join(json.dumps(r)+'\n' for r in rr))
                entry['files']['packed']={**file_pin(path),'rows':len(rr),'bytes':path.stat().st_size}
            path=root/(change+'.json');write(path,value)
            with self.assertRaises(ValueError):S.rebuild_pool(file_pin(path),DEV,BENCH,root/change)

    def test_real_prepare_and_every_rank_encode(self):
        from student_pilot import carrier_c1_run as R
        from tests.test_r2_preparation import PreparationProof
        from launch_r2 import host as H
        captured = []
        original = R.prepare
        def capture(cfg):
            captured.append(deepcopy(cfg))
            return original(cfg)
        with patch.object(R,'prepare',side_effect=capture):
            PreparationProof().test_native_preparation_membership()
        cfg = captured[0]
        base = Path(cfg['preparation_output']).parent
        base_rows = {stream:json.loads((base/stream/'rows.jsonl').read_text()) for stream in ('vqa','routing','pose','pointing')}
        root = directory()
        spec, manifests = scene_fixture(root,base_rows)
        cfg.update(dev_scene_exclusions=DEV,benchmark_scene_exclusions=BENCH,r2_all_stream_exclusions=True)
        result = S.rebuild(spec,cfg,root/'scenes')
        cfg.update(scene_coverage=result['scene_coverage'],r2_scene_rebuild=file_pin(root/'scenes/2.json'))
        S.verify(cfg)
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(base/'frames')}),S1_CPU_REHEARSAL='1'), \
             patch.object(R,'processor_for_receipt',return_value=TinyProcessor()):
            report = materialize(manifests,root/'stores')
            native = load(pinned(report['receipt']))
            cfg = H.native_config(cfg,native,load(pinned(cfg['streams']['pose'])),root/'native')
            prepared = R.prepare(cfg)
            cfg['preparation'] = file_pin(Path(cfg['preparation_output'])/'receipt.json')
            first = H.encode_first(cfg,H.Guard(root))
            self.assertEqual({(r['rank'],r['stream']) for r in first},
                             {(r,s) for r in range(4) for s in native['streams']})
            self.assertEqual(prepared['scene_filter_report']['coverage']['status'],'PASS')
            for records in prepared['scene_filter_report']['coverage']['sources'].values():
                self.assertEqual(records['observed_dev_matches'],records['reference_dev_rows'])
        for change in ('config','upstream','pool','reference','counts','binding'):
            bad = deepcopy(cfg)
            if change == 'config':bad['dev_scene_exclusions'] = OLD
            else:
                result_bad = deepcopy(result)
                if change in ('upstream','pool'):
                    if change == 'pool':result_bad['pool_selection'] = file_pin(META/'pool_selection.json')
                    else:result_bad['receipts']['camera'] = spec['sources']['camera']['receipt']
                if change in ('reference','counts'):
                    ref = load(pinned(result['scene_coverage']['reference']))
                    if change == 'reference':ref['withhold_file'] = OLD
                    else:ref['withheld_training_rows']['camera']['rows_withheld'] += 1
                    write(root/(change+'.json'),ref)
                    result_bad['scene_coverage']['reference'] = file_pin(root/(change+'.json'))
                if change == 'binding':result_bad['files']['dev'] = OLD
                write(root/('result_'+change+'.json'),result_bad)
                bad['r2_scene_rebuild'] = file_pin(root/('result_'+change+'.json'))
                bad['scene_coverage'] = result_bad['scene_coverage']
            with self.assertRaises(ValueError):
                S.verify(bad)
                E.coverage_report(E.Exclusions(DEV,BENCH),{},bad['scene_coverage']) if change != 'counts' else E.verify(prepared,bad)
        (PROOFS/'B3B_NATIVE_PROOF.json').write_text(json.dumps(dict(synthetic=True,scene_receipt=cfg['r2_scene_rebuild'],
            preparation=cfg['preparation'], first_batch=first, mutations=['config','upstream','pool','reference','counts','binding'],
            standins='TinyProcessor/tokenizer and pretrained model metadata only; no producer, census, filter, store, sampler or reader replacement',
            boundary='CPU encoding before forward'),indent=2)+'\n')

    def test_bound_native_sqlite_and_opaque_metadata(self):
        root=directory()
        values=[dict(qid=str(i),canonical=scene) for i,scene in enumerate(('d1/clean',NATIVE,ALIAS))]
        path=root/'a.bin'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE rows (i INTEGER, row TEXT)')
            db.executemany('INSERT INTO rows VALUES (?,?)',[(i,json.dumps(row)) for i,row in enumerate(values)])
        self.assertEqual(list(S.rows(file_pin(path))),values)
        write(root/'receipt.json',dict(count=len(values),database=file_pin(path)))
        spec=dict(receipt=file_pin(root/'receipt.json'),rows=file_pin(path),count=len(values),source='vqa')
        pin=S.rebuild_receipt(spec,DEV,BENCH,root/'out')
        self.assertEqual(load(pinned(pin))['count'],1)
        self.assertEqual(load(pinned(load(pinned(pin))['indices'])),[0])
        zipped=root/'b.bin'
        with gzip.open(zipped,'wt') as handle:handle.write(''.join(json.dumps(r)+'\n' for r in values))
        self.assertEqual(list(S.rows(file_pin(zipped))),values)
        with self.assertRaisesRegex(ValueError,'not bound'):
            S.rebuild_receipt({**spec,'rows':file_pin(zipped)},DEV,BENCH,root/'bad')

    def test_pool_rows_cannot_reach_store_or_rank(self):
        from tests.test_r2_families import ground
        from student_pilot.carrier_c1_run import Rows
        from student_pilot.carrier_c1_data import mixed_indices
        root=directory()
        pool=S.rebuild_pool(pool_fixture(root/'pool'),DEV,BENCH,root/'selection')
        selected={name:{r['qid'] for r in s1_pool.selected_rows(pool,name)}
                  for name in ('T0_gen_r2','T0_room')}
        paths=[]
        for source,stream in (('T0_gen_r2','routing'),('T0_room','vqa')):
            row=ground(root,'absolute_distance') if stream=='routing' else fixture(root)
            if stream=='vqa':
                row.update(question_type='room_size_estimation',answer='1.00',
                           target='<think>\nStep: the question asks for the combined visible floor area.\n</think>\n1.00')
                row['question']=row['student_input']['question']='What is the combined room size in square meters?'
            values=[at_scene(row,scene,source+str(i)) for i,scene in enumerate(('d1/fixture_clean',NATIVE,ALIAS))]
            for value in values:value['provenance']['source_qid']=value['qid']
            path=manifest(root/source,values,stream,family=source)
            envelope=load(path);envelope['dev_scene_exclusions']=DEV
            path.write_text(json.dumps(envelope))
            admitted,_=intake(path)
            self.assertEqual({item['row']['qid'] for item in admitted},selected[source])
            paths.append(path)
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            store=materialize(paths,root/'stores')
            native=load(pinned(store['receipt']))
            reader=Rows(native,TinyProcessor())
            batches=[]
            try:
                counts={name:value['count'] for name,value in native['streams'].items()}
                self.assertEqual(counts,dict(vqa=1,routing=1))
                plan=next(mixed_indices(counts,1,training_mode='final',mix=['vqa','routing'],world=4))
                for stream,indices in plan:
                    for rank,index in enumerate(indices):
                        batch,_,_=reader.get(stream,index)
                        row,_=reader.row(stream,index)
                        self.assertTrue(row['qid'].endswith('0'))
                        self.assertGreater(int((batch['labels']!=-100).sum()),0)
                        batches.append(dict(rank=rank,stream=stream,qid=row['qid']))
            finally:reader.close()
        (PROOFS/'B3B_POOL_BATCH_PROOF.json').write_text(json.dumps(dict(synthetic=True,
            native_selection=pool,store=store['receipt'],batches=batches,
            standins='Synthetic RGB and TinyProcessor at the pretrained input boundary'),indent=2)+'\n')

    def test_pool_outputs_and_logs_are_opaque(self):
        import io
        from contextlib import redirect_stdout
        from launch_r2.build import bad_string
        root=directory();pin=pool_fixture(root/'pool')
        value=load(pinned(pin));value['sets'][0]['name']='ARKIT_gen_r2'
        write(root/'manifest.json',value)
        log=io.StringIO()
        with redirect_stdout(log):
            receipt=S.rebuild_pool(file_pin(root/'manifest.json'),DEV,BENCH,root/'opaque')
        self.assertNotIn('ARKIT',log.getvalue())
        hashes=load(Path(__file__).resolve().parents[1]/'launch_s1/b/wh.json')
        for path in (root/'opaque').rglob('*'):
            self.assertFalse(bad_string(str(path.relative_to(root/'opaque')),hashes))
        self.assertEqual([r['qid'] for r in s1_pool.selected_rows(receipt,'ARKIT_gen_r2')],['T0_gen_r20'])
        native=s1_pool.prepare(load(pinned(receipt))['manifest'],root/'native')
        self.assertEqual(native['selected_rows'],load(pinned(receipt))['selected_rows'])
