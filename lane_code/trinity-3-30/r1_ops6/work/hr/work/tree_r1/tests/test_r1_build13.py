"""R1 population and composition refusals on retained synthetic CPU fixtures."""
from collections import Counter
from copy import deepcopy
import json,os,sqlite3,unittest
from pathlib import Path
from unittest.mock import patch
from student_pilot.p3_provenance import digest,file_pin,load
from student_pilot.r1_population import Membership,produce,scene_receipt,family,TYPES
from student_pilot.r1_mix import plans,validate_binding
from student_pilot.r1_training import STREAMS


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['R2_PROOFS'])/'population13'/self._testMethodName
        self.root.mkdir(parents=True,exist_ok=True)
        self.open=Path.open
        original=self.open
        root=self.root
        def opened(p,mode='r',*args,**kwargs):
            return original(p,mode.replace('x','w') if p.is_relative_to(root) else mode,*args,**kwargs)
        self.patch=patch.object(Path,'open',opened);self.patch.start()
        self.card=dict(schema='r1-card-v1',steps=1000,quotas=STREAMS,seed=17,cells=[
            dict(type=k,stream=s,rows_per_step=n) for s,k,n in
            [('pose','pose',64),('vqa','direction',128),('routing','camera_displacement',64),('pointing','pointing',32)]])
        self.cardpin=self.write('card.json',self.card)
        self.source=self.write('source.json',{})
        self.member=self.write('member.json',dict(schema='r1-source-membership-v1',sources={}))

    def tearDown(self):
        self.patch.stop()

    def write(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value));return file_pin(p)

    def binding(self):
        counts={c['type']:STREAMS[c['stream']]*250 for c in self.card['cells']}
        pop=self.write('pop.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,
            card_sha256=self.cardpin['sha256'],counts=counts,evidence=[self.source]))
        idx=self.write('idx.json',dict(population_sha256=pop['sha256'],cells={k:list(range(n)) for k,n in counts.items()}))
        return dict(schema='r1-sampling-v1',card=self.cardpin,population=pop,indices=idx)

    def test_unassigned_type(self):
        class Reader:
            def count(self,s):return int(s=='vqa')
            def row(self,s,i):return dict(qid='unknown',question_type='new_type'),{}
        with self.assertRaisesRegex(ValueError,"R1_UNASSIGNED_TYPES:.*new_type.*1"):
            produce(Reader(),self.cardpin,self.member,[self.source],self.root/'out')

    def test_absent_card_cell(self):
        class Reader:
            def count(self,s):return int(s=='vqa')
            def row(self,s,i):return dict(qid='unknown',question_type='box_3d'),{}
        with self.assertRaisesRegex(ValueError,"R1_UNASSIGNED_TYPES:.*box_3d.*1"):
            produce(Reader(),self.cardpin,self.member,[self.source],self.root/'out')

    def test_slice_identity(self):
        r=dict(qid='r1rec2_fixture',question_type='object_abs_distance',
               r1_source=dict(family='recovery',sha256=self.source['sha256']))
        pin=self.write('member.json',dict(schema='r1-source-membership-v1',sources={
            'recovery':dict(source=self.source,rows={r['qid']:digest(r)})}))
        m=Membership(pin)
        self.assertEqual(m.cell(r,'routing'),'recovery')
        for change in ({'r1_source':None},{'qid':'unknown'},{'question_type':'camera_rotation'}):
            with self.assertRaisesRegex(ValueError,'R1_SLICE_ROW_MISFILED'):
                m.cell({**r,**change},'routing')

    def test_base_cells_refused(self):
        m=Membership(self.member)
        for r in (dict(qid='base',question_type='object_abs_distance'),
                  dict(qid='a0_units_fixture',question_type='object_abs_distance')):
            with self.assertRaisesRegex(ValueError,'R1_BASE_DISTANCE_OR_UNIT_RETAINED'):
                m.cell(r,'routing')

    def test_overlap(self):
        b=self.binding();idx=load(b['indices']['path']);idx['cells']['direction'][1]=0
        b['indices']=self.write('idx.json',idx)
        with self.assertRaisesRegex(ValueError,'R1_INDEX_OVERLAP_OR_COUNT'):
            next(plans(b,{s:n*250 for s,n in STREAMS.items()},1))

    def test_binding_changed(self):
        b=self.binding();pop=load(b['population']['path']);pop['complete']=False
        self.write('pop.json',pop)
        with self.assertRaises(ValueError):validate_binding(b)
        from student_pilot.r1_loader import production_audit
        from student_pilot import carrier_c1_run as C
        cfg=dict(r1_training=dict(row_plan_sha256='0'*64),r2_sampling=b)
        with patch('os.uname',return_value=type('Host',(),dict(nodename='fixture-host'))()),\
             patch.object(C,'prepared',return_value=(dict(streams={}),None)):
            with self.assertRaisesRegex(ValueError,'R1_PRODUCTION_ROW_PLAN_CHANGED'):
                production_audit(cfg,self.root/'audit')

    def test_trinity_full_audit_refusal(self):
        from student_pilot.r1_loader import production_audit
        with patch('os.uname',return_value=type('Host',(),dict(nodename='trinity-1-3'))()):
            with self.assertRaisesRegex(ValueError,'R1_FULL_AUDIT_REQUIRES_FRAME_HOST'):
                production_audit({},self.root/'audit')

    def test_scene_subset(self):
        p=self.write('original.json',[2,4,7]);q=self.write('subset.json',[2,7])
        original=dict(indices=p,count=3,receipt=self.source)
        self.assertEqual(scene_receipt(dict(streams=dict(vqa=original)))['streams']['vqa'],original)
        value=dict(original,reader_source=deepcopy(original),indices=q,count=2)
        self.assertEqual(scene_receipt(dict(streams=dict(vqa=value)))['streams']['vqa'],original)
        value['indices']=self.write('subset.json',[2,9])
        with self.assertRaisesRegex(ValueError,'R1_READER_SELECTION_DIFFERS'):
            scene_receipt(dict(streams=dict(vqa=value)))

    def test_type_table_and_single_facing(self):
        for typ,cell in TYPES.items():
            self.assertEqual(family(dict(question_type=typ),'vqa'),cell)
        self.assertEqual(family(dict(question_type='object_rel_direction_easy',facing='away'),'vqa'),'facing_pairs')
        self.assertEqual(family(dict(question_type='object_counting',count_kind='total'),'vqa'),'totals')
        self.assertEqual(family(dict(qid='x',routing=dict(question_type='camera_rotation')),'routing'),'camera_rotation')
        self.assertEqual(family(dict(qid='x',routing=dict(question_type='odd')),'routing'),'unassigned:odd')
        self.assertEqual(family(dict(qid='a0_recovery_x'),'routing'),'recovery')

    def test_membership_refusals(self):
        bad=self.write('bad.json',dict(schema='wrong'))
        with self.assertRaisesRegex(ValueError,'R1_SOURCE_MEMBERSHIP_INVALID'):Membership(bad)
        bad=self.write('bad.json',dict(schema='r1-source-membership-v1',sources={'odd':{}}))
        with self.assertRaisesRegex(ValueError,'R1_SLICE_CELL_INVALID'):Membership(bad)
        bad=self.write('bad.json',dict(schema='r1-source-membership-v1',sources={
            k:dict(source=self.source,rows=dict(duplicate='a'*64)) for k in ('recovery','units')}))
        with self.assertRaisesRegex(ValueError,'R1_SLICE_QID_OVERLAP'):Membership(bad)

    def composition(self, rows):
        from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
        db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for i,r in enumerate(rows):db.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(r),'{}'))
        db.commit();(self.root/'base.sqlite').write_bytes(db.serialize());db.close()
        division=self.write('division.json',dict(train_scenes=['d1/fixture_clean'],heldout_scenes=['d1/held']))
        base=self.write('base.json',dict(schema=ROUTING_SCHEMA,stream='routing',database=file_pin(self.root/'base.sqlite'),
            count=len(rows),division=division,scene_role='train',heldout_overlap=0))
        dev=self.write('dev.json',dict(schema='dev_s1_withhold_v1',natives=['d1/dev'],rooms=['d1/dev'],
            physical_groups=['scannet/dev'],canonical={'d1/dev':['scannet/dev']},aliases={'d1/dev':['d1/vdev']}))
        bench=self.write('bench.json',dict(schema='benchmark_scene_exclusions_v1',scenes=['d1/benchmark']))
        cfg=dict(r1_training=dict(schema='r1-training-v1'),dev_scene_exclusions=dev,benchmark_scene_exclusions=bench)
        return base,cfg,{k:self.source for k in ('recovery','absolute_distance','units')}

    def test_composition_replaces_base(self):
        from student_pilot.r1_routing import compose
        row=dict(qid='camera',dataset='d1',scene='fixture_clean',question_type='camera_displacement',
            target='<think>The camera moves right between the shown frames.</think><answer>right</answer>')
        base,cfg,sources=self.composition([row,{**row,'qid':'old_distance','question_type':'object_abs_distance'},
                                         {**row,'qid':'a0_units_old','question_type':'object_abs_distance'}])
        batches=[(k,p,[dict(row={**row,'qid':'slice_'+k},target={})],self.source) for k,p in sources.items()]
        result=compose(base,sources,batches,cfg,self.root/'out')
        self.assertEqual(result['count'],4)
        self.assertEqual(result['per_source'],dict(base=1,recovery=1,absolute_distance=1,units=1))
        self.assertEqual(result['refused']['base:replaced_cell'],2)
        m=Membership(result['source_membership'])
        con=sqlite3.connect('file:'+result['database']['path']+'?mode=ro',uri=True)
        self.assertEqual(Counter(m.cell(json.loads(r),'routing') for (r,) in con.execute('SELECT row FROM rows')),
                         Counter(dict(camera_displacement=1,recovery=1,absolute_distance=1,units=1)))
        con.close()

    def test_composition_refusals(self):
        from student_pilot.r1_routing import compose,Filters
        row=dict(qid='camera',dataset='d1',scene='fixture_clean',question_type='camera_displacement',target='<think>visible</think>A')
        base,cfg,sources=self.composition([row])
        with self.assertRaisesRegex(ValueError,'R1_ROUTING_SLICES_REQUIRED'):
            compose(base,{},[],cfg,self.root/'bad1')
        with self.assertRaisesRegex(ValueError,'R1_SLICE_SOURCE_DIFFERS'):
            compose(base,sources,[('recovery',dict(self.source,sha256='f'*64),[],self.source)],cfg,self.root/'bad2')
        with self.assertRaisesRegex(ValueError,'R1_ROUTING_DUPLICATE_QID'):
            compose(base,sources,[('recovery',self.source,[dict(row=row)],self.source)],cfg,self.root/'bad3')
        value=load(base['path']);value['heldout_overlap']=None
        bad=self.write('invalid.json',value)
        with self.assertRaisesRegex(ValueError,'R1_ROUTING_BASE_INVALID'):
            compose(bad,sources,[],cfg,self.root/'bad4')
        f=Filters(cfg,value['division'])
        self.assertEqual(f.reason({**row,'scene':'held'},'routing'),'division_heldout')
        self.assertEqual(f.reason({**row,'scene':'outside'},'routing'),'division_outside')
        f.train.add('d1/dev');self.assertEqual(f.reason({**row,'scene':'dev'},'routing'),'scene_exclusion')
        f.qids={'routing':{'camera'}};self.assertEqual(f.reason(row,'routing'),'exclude_qids')
        f.qids={};f.cfg['route_table']={'camera_displacement':'route'}
        self.assertEqual(f.reason(row,'vqa'),'routed_type')
        f.benchmark={'d1/fixture_clean'};self.assertEqual(f.reason(row,'routing'),'benchmark_exclusion')
        base,cfg,sources=self.composition([dict(row,target='answer only'),dict(row,qid='outside',scene='outside')])
        result=compose(base,sources,[],cfg,self.root/'empty')
        self.assertEqual(result['count'],0)
        self.assertEqual(sum(result['refused'].values()),2)

    def test_native_mixture_and_bound_producer(self):
        from student_pilot.carrier_c1_run import Rows
        from student_pilot.r1_population import bind_prepared
        from student_pilot import carrier_c1_run as C
        streams={};pins={}
        for stream,quota in STREAMS.items():
            n=quota*250
            db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            for i in range(n+(stream=='vqa')):
                row=dict(qid=stream+'_'+str(i),question_type='camera_displacement' if stream=='routing' else 'object_rel_direction_easy',
                    target='<think>The frames show the object to the right.</think><answer>right</answer>')
                if i==n:row['target']='answer only'
                db.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
            db.commit();p=self.root/(stream+'.sqlite');p.write_bytes(db.serialize());db.close()
            receipt=dict(database=file_pin(p),count=n+(stream=='vqa'))
            if stream=='routing':receipt['source_membership']=self.member
            pin=self.write(stream+'.json',receipt);pins[stream]=pin
            streams[stream]=dict(receipt=pin,**receipt)
            if stream=='pose':
                order=self.write('order.json',[[0,i] for i in range(n)])
                streams[stream]=dict(receipt=pin,kind='mix',count=n,order=order,
                    sources=[dict(kind='rows',database=file_pin(p))])
        receipt=dict(streams=streams,r1_training=dict(schema='r1-training-v1'),depth=dict(num_points_per_frame=1))
        from student_pilot.source_seal import SCHEMA
        cfg=dict(r1_training=dict(schema='r1-training-v1',mix=self.cardpin),streams=pins,
                 preparation=self.write('preparation.json',receipt),code=self.write('code.json',
                    dict(schema=SCHEMA,tree_sha256='0'*64,archive=self.source)))
        reader=Rows(receipt,None)
        self.assertEqual(reader.row('pose',3)[0]['qid'],'pose_3')
        real=reader.mixes['pose'].sources[0]
        reader.mixes['pose'].sources[0]=object()
        with self.assertRaisesRegex(ValueError,'R1_POPULATION_POSE_SOURCE_NOT_ROWS'):reader.row('pose',0)
        reader.mixes['pose'].sources[0]=real;reader.close()
        # Only authentication of the unavailable host preparation stands in.
        # Filtering, native readers, mixture order, producer and pins are real.
        with patch.object(C,'prepared',return_value=(receipt,None)):
            config_pin=bind_prepared(cfg,self.root/'produced')
        bound=load(config_pin['path']);prepared=load(bound['preparation']['path'])
        self.assertEqual(bound['r1_training']['row_plan_sha256'],digest(bound['r2_sampling']))
        self.assertEqual(scene_receipt(prepared)['streams'],streams)
        reader=Rows(prepared,None)
        self.assertEqual(reader.count('vqa'),32000)
        self.assertEqual(reader.row('pose',3)[0]['qid'],'pose_3')
        _,indices,proof=validate_binding(bound['r2_sampling'])
        self.assertEqual(proof['draws'],{c['type']:STREAMS[c['stream']]*1000 for c in self.card['cells']})
        self.assertEqual(len(indices['cells']['direction']),32000)
        reader.close()

    def test_native_composition_envelopes(self):
        from student_pilot.r1_routing import compose_native
        from tests.test_r2_data_path import manifest
        row=dict(qid='camera',dataset='d1',scene='fixture_clean',question_type='camera_displacement',target='<think>visible</think>A')
        base,cfg,_=self.composition([row])
        manifests={};sources={}
        for k in ('recovery','absolute_distance','units'):
            path=manifest(self.root/k,[],stream='routing',family=k)
            manifests[k]=file_pin(path);sources[k]=dict(source=load(path)['rows'])
        cfg['r1_training'].update(row_sources=self.write('sources.json',sources),routing_inputs=manifests,
            source_membership=self.write('catalog.json',dict(schema='r1-source-catalog-v1',sources={
                k:dict(source=v['source'],qids=[]) for k,v in sources.items()})))
        with patch('os.uname',return_value=type('Host',(),dict(nodename='fixture-host'))()),\
             patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1',STUDENT_R2_LOCAL_NODE='0'):
            result=compose_native(cfg,base,self.root/'native')
        self.assertEqual(result['count'],1)
        bad=deepcopy(cfg);bad['r1_training']['row_slice_inputs']={}
        with self.assertRaisesRegex(ValueError,'R1_SLICE_SOURCE_DIFFERS'):compose_native(bad,base,self.root/'badstaged')
        bad=deepcopy(cfg);bad['r1_training']['source_membership']=self.source
        with self.assertRaisesRegex(ValueError,'R1_SOURCE_CATALOG_INVALID'):compose_native(bad,base,self.root/'badcatalog')
        catalog=load(cfg['r1_training']['source_membership']['path']);catalog['sources']['units']['source']['sha256']='0'*64
        bad=deepcopy(cfg);bad['r1_training']['source_membership']=self.write('badcatalog.json',catalog)
        with self.assertRaisesRegex(ValueError,'R1_SOURCE_CATALOG_DIFFERS'):compose_native(bad,base,self.root/'badpin')
        bad=deepcopy(cfg);mp=load(manifests['units']['path']);mp['family']='recovery'
        bad['r1_training']['routing_inputs']['units']=self.write('badmanifest.json',mp)
        with patch('os.uname',return_value=type('Host',(),dict(nodename='fixture-host'))()),\
             patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1',STUDENT_R2_LOCAL_NODE='0'):
            with self.assertRaisesRegex(ValueError,'R1_SLICE_MANIFEST_DIFFERS'):compose_native(bad,base,self.root/'badmanifest')
        from tests.test_r2_data_path import fixture
        extra=manifest(self.root/'extra',[fixture(self.root,qid='extra',stream='routing')],stream='routing',family='units')
        bad=deepcopy(cfg);bad['r1_training']['routing_inputs']['units']=file_pin(extra)
        sources['units']['source']=load(extra)['rows'];bad['r1_training']['row_sources']=self.write('extra_sources.json',sources)
        catalog=load(cfg['r1_training']['source_membership']['path']);catalog['sources']['units']['source']=sources['units']['source']
        bad['r1_training']['source_membership']=self.write('extra_catalog.json',catalog)
        with patch('os.uname',return_value=type('Host',(),dict(nodename='fixture-host'))()),\
             patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1',STUDENT_R2_LOCAL_NODE='0'):
            with self.assertRaisesRegex(ValueError,'R1_SLICE_ROW_MISFILED'):compose_native(bad,base,self.root/'extra_out')


if __name__=='__main__':unittest.main()
