from pathlib import Path
L=Path(__file__).resolve().parents[2]
p=L/'work/tree_r1/tests/test_r2_build3b.py'
s=p.read_text()+'''
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
                           target='<think>\\nLocate: the floor is seen in frame 1.\\n</think>\\n1.00')
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
        (LANE/'out/B3B_POOL_BATCH_PROOF.json').write_text(json.dumps(dict(synthetic=True,
            native_selection=pool,store=store['receipt'],batches=batches,
            standins='Synthetic RGB and TinyProcessor at the pretrained input boundary'),indent=2)+'\\n')
'''
p.write_text(s)
