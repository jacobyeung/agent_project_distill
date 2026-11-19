"""B44's full-count prefix regression, retained against the integrated trainer."""
import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PIL import Image
from student_pilot import carrier_c1_data as data, carrier_c1_run as native
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.p3_provenance import file_pin, pinned, write

candidate = native

def save(path, value):
    write(path, value)
    return file_pin(path)

def sampler_ids(indices, recipe):
    return [indices[i] for plan in data.mixed_indices({'pose':len(indices)},880,
        seed=recipe['seed'],training_mode='pose_only') for _,batch in plan for i in batch]

runtime = SimpleNamespace(pin=file_pin,checked=pinned,write=save,sampler_ids=sampler_ids)

def config(manifest, readout, output, gap):
    cfg = dict(schema='carrier-c1-run-v1', init='base', parallel='fsdp', all_frames=True,
        training_mode='pose_only', depth_enabled=False, base_identity='fixture',
        frame_layout='paired', frame_pair_gap_seconds=gap, carrier_placement=data.C1_A,
        streams={'pose':manifest}, readout=readout, preparation_output=str(output),
        schedule=dict(startup_seconds=1, p95_step_seconds=1, checkpoint_seconds=1, export_seconds=1))
    cfg['recipe'] = recipe_for(cfg)
    return cfg


class PrefixTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='c1_prefix_',dir=os.environ['LANE_TEST_OUTPUT']))
        Image.new('RGB',(8,8)).save(self.root/'rgb.png')
        rgb=file_pin(self.root/'rgb.png')
        ids=list(range(0,96,3))
        self.row=dict(qid='fixture',category='camera_pose_only',
            pose_sample=dict(recording=dict(sampling=dict(variant='all_frames32'))),
            student_input=dict(frames=[rgb]*32,frame_indices=ids,timestamps=[i/24 for i in ids],
                fps=24.,total_num_frames=150,question='',options=[]))
        self.target=dict(camera=[[0.]*9]*32,camera_mask=[True]*32,gravity=[0.,1.,0.],
            gravity_mask=True,trajectory_scale=1.,point_depth=dict(uv=[],depth=[],mask=[]))
        model=save(self.root/'model.json',dict(kind='base',base_identity='fixture',root='/snapshot',files={'config.json':'fixture'}))
        parent=dict(settings=dict(anchors=list(range(1,33)),temporal_grouping='fused_pairs_all_frames',camera={'point_depth':{}}),
            inputs={'division':{}},model=model,schema='decoupled-v-preparation-v1')
        self.cfg={'preparation':save(self.root/'parent.json',parent)}
        readout={k:save(self.root/(k+'.json'),{}) for k in ('bank','training_scenes','rows_inventory')}
        self.report={'manifests':[]}
        for j,gap in enumerate((.5,1.)):
            row=copy.deepcopy(self.row)
            row['student_input'].update(recording_id='fixture',partner_frames=[dict(**rgb,
                recording_id='fixture',frame_index=i+round(gap*24),timestamp=i/24+gap) for i in ids])
            db=self.root/('seed%d.db'%j)
            with sqlite3.connect(db) as conn:
                conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
                conn.execute('INSERT INTO rows VALUES(0,?)',(json.dumps(row),))
            manifest=dict(schema='c1-paired-prefix-v2',database=file_pin(db),readout=readout,
                frame_layout='paired',frame_pair_gap_seconds=gap,**{k:parent[k] for k in ('settings','inputs','model')})
            self.report['manifests'].append(save(self.root/('seed%d.json'%j),manifest))

    def test_06_full_scale_virtual_store_native_prepare(self):
        # Full production counts use SQLite views over one shared RGB row: small local files,
        # real source IDs and sampler, and no repeated PNG generation or network reads.
        root=self.root/'full';root.mkdir()
        recipe=recipe_for(config(None,None,root/'unused',.5))
        indices=list(range(100,283300));order=runtime.sampler_ids(indices,recipe)
        dense=runtime.write(root/'dense.json',indices)
        def database(path, ids, row):
            with sqlite3.connect(path) as conn:
                conn.execute('CREATE TABLE ids(i INTEGER PRIMARY KEY)')
                conn.executemany('INSERT INTO ids VALUES(?)',((i,) for i in ids))
                conn.execute('CREATE TABLE payload(row TEXT,target TEXT)')
                conn.execute('INSERT INTO payload VALUES(?,?)',(json.dumps(row),json.dumps(self.target)))
                conn.execute("CREATE VIEW rows AS SELECT i,CASE WHEN i>=283300 THEN json_set(row,'$.category','other') ELSE row END AS row,target FROM ids CROSS JOIN payload")
            return runtime.pin(path)
        parent=json.loads(runtime.checked(self.cfg['preparation']).read_text())
        parent.update(count=321152,database=database(root/'source.db',range(321152),self.row))
        parent_pin=runtime.write(root/'parent.json',parent)
        sampler=dict(training_mode='pose_only',recipe=recipe,streams={'pose':dict(database=parent['database'],receipt=parent_pin,count=283200,indices=dense)})
        sampler_pin=runtime.write(root/'sampler.json',sampler)
        for j,gap in enumerate((.5,1.)):
            manifest=json.loads(runtime.checked(self.report['manifests'][j]).read_text())
            with native.connect(manifest['database']) as conn:row=json.loads(conn.execute('SELECT row FROM rows LIMIT 1').fetchone()[0])
            manifest.update(count=28160,database=database(root/('%d.db'%j),order,row),parent=parent_pin,
                source_database=parent['database'],sampler_preparation=sampler_pin,source_indices=order,sampler_indices=order,
                dense_indices=dense,dense_count=283200,required_steps=800,margin_steps=80,recipe=recipe)
            manifest_pin=runtime.write(root/('%d.json'%j),manifest)
            cfg=config(manifest_pin,manifest['readout'],root/('prep%d'%j),gap)
            with patch.object(candidate,'authenticate',return_value='fixture-source-only'),patch('student_pilot.students.get_student',return_value=dict(snapshot=Path('/snapshot'),config_sha256='fixture')):
                prepared=candidate.prepare(cfg)
                self.assertEqual(prepared['streams']['pose']['count'],283200)
                cfg['preparation']=runtime.pin(Path(cfg['preparation_output'])/'receipt.json')
                restored,_=candidate.prepared(cfg)
                self.assertEqual(restored,prepared)
                rows=candidate.Rows(prepared,None)
                try:
                    with patch.object(data,'encode',side_effect=lambda processor,row,target,*args,**kwargs:(row,target,kwargs)):
                        for index in [v-100 for v in (order[0],order[31],order[25599],order[-1])]:
                            actual,target,options=rows.get('pose',index)
                            self.assertEqual(actual,row);self.assertEqual(target,self.target)
                            self.assertEqual(options['frame_layout'],'paired')
                        outside=next(i for i in indices if i not in set(order))
                        with self.assertRaisesRegex(ValueError,'Missing planned'):rows.get('pose',outside-100)
                finally:rows.close()
            broken={**manifest,'sampler_indices':list(reversed(order))}
            with self.assertRaisesRegex(ValueError,'sampler order'):candidate.paired_prefix(cfg,broken)
            broken={**manifest,'source_indices':order[1:],'count':len(order)-1}
            with self.assertRaisesRegex(ValueError,'sampler order'):candidate.paired_prefix(cfg,broken)
            with self.assertRaisesRegex(ValueError,'sampler order'):
                candidate.paired_prefix(cfg,{**manifest,'source_indices':order+[321151],'count':len(order)+1})
            with self.assertRaisesRegex(ValueError,'prefix identity'):
                candidate.paired_prefix({**cfg,'frame_pair_gap_seconds':2.},manifest)
            outside = next(i for i in indices if i not in set(order))
            extra = database(root/('extra%d.db'%j),order+[outside],row)
            with self.assertRaisesRegex(ValueError,'database coverage'):
                candidate.paired_prefix(cfg,{**manifest,'database':extra})
            badpath=root/('bad%d.db'%j)
            database(badpath,order,row)
            changed=copy.deepcopy(self.target);changed['camera'][0][0]=99.
            with sqlite3.connect(badpath) as conn:conn.execute('UPDATE payload SET target=?',(json.dumps(changed),))
            broken={**manifest,'database':runtime.pin(badpath)}
            with self.assertRaisesRegex(ValueError,'changed targets'):candidate.paired_prefix(cfg,broken)
