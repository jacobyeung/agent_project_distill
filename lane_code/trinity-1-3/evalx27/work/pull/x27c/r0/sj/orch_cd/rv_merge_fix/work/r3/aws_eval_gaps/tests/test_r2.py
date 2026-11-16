"""Regression checks for the cross-family evaluation-kit review."""
import copy,hashlib,json,os,subprocess,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from test_eval_gaps import full,full_spec,pin
from test_routing import table
from test_frames import video
from evalpath.items import sha256,load_items,_trainer_row
from evalpath.official import build_prompt_context
from evalpath.sampling import _sample_floor_uniform_indices
from routing import *
from media import decode,load
from frame_stage import stage_one
from nested_sampling import nested_indices
from cells import frame_count
from worker import encoder_budget
from merge import merge
import bind_vl

def retained():return Path(tempfile.mkdtemp(dir=ROOT/'checks'))
def fixture_arms(directory):
    dev=ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl';rows=read_jsonl(dict(path=str(dev),sha256=DEV_SHA));pins=[]
    for selected in ('direct','routed'):
        p=directory/(selected+'.jsonl')
        out=[dict(t,benchmark='devrows',example_id=str(t['id']),status='complete',checkpoint_sha256=CP1_SHA,protocol=PROTOCOL,route_action=selected,layout='duplicate',frames=32,
                  raw_generation='</think>\n'+('invalid' if selected=='direct' else str(t['ground_truth'])),output_tokens=8,finish_reason='stop') for t in rows]
        p.write_text(''.join(json.dumps(r)+'\n' for r in out));pins.append(dict(path=str(p),sha256=sha256(p)))
    return dict(path=str(dev),sha256=DEV_SHA),pins

class R2(unittest.TestCase):
    def test_release_manifest_and_reencode_refused(self):
        rows=full();self.assertEqual(len({r['scene_name'] for r in rows}),312)
        self.assertTrue(all(len(r['video_sha256'])==64 for r in rows))
        root=retained();a=root/'release.mp4';b=root/'reencoded.mp4';video(a,40,10);video(b,40,12)
        task=dict(rows[0],video_path=str(b),video_sha256=sha256(a))
        with self.assertRaisesRegex(ValueError,'Video pin'):decode(task,'duplicate')
        with self.assertRaisesRegex(ValueError,'Video SHA'):_trainer_row(task,root/'trainer')
        cache=root/'cache';cache.mkdir();receipt,error=stage_one(task,'duplicate',cache)
        self.assertTrue(error);self.assertIn('Video pin',json.loads((cache/receipt['path']).read_text())['error'])
        spec=full_spec();spec.pop('videos')
        with self.assertRaisesRegex(ValueError,'release videos'):load_items(spec,{'video_root':'/unused'})

    def test_real_journal_450_replay(self):
        p=ROOT/'tests/fixtures/vsti_real450.jsonl';provenance=json.loads(p.with_name('vsti_real450_pin.json').read_text())
        self.assertEqual(sha256(p),provenance['fixture_sha256'])
        rows=[json.loads(s) for s in p.read_text().splitlines()];new={r['example_id']:r for r in full()};comp=[];tasks=[]
        self.assertEqual(len(rows),450)
        for r in rows:
            t=new[str(r['example_id'])]
            for f in ('question','options','question_type'):self.assertEqual(r.get(f) or [],t.get(f) or [])
            self.assertEqual(str(r['ground_truth']),str(t['ground_truth']))
            self.assertEqual(Path(r['video_path']).name,Path(t['video_path']).name)
            self.assertEqual(build_prompt_context({**r,'text':None},'ours').encode(),build_prompt_context(t,'ours').encode())
            s=score_item(t,r['raw_generation'],r['output_tokens'],cap=r['max_new_tokens'],finish=r['finish_reason'])
            self.assertEqual((s['score'],s['response_text']),(r['score'],r['response_text']))
            comp.append(dict(t,status='complete',**s));tasks.append(t)
        self.assertEqual(round(benchmark_summary(comp,tasks,True)['overall_score'],5),0.39187)

    def test_layout_defaults_duplicate64_and_mixed_merge(self):
        c={'benchmarks':['vstifull']};self.assertEqual(frame_count(c),32);self.assertEqual(c['layout'],'duplicate')
        for l in ('duplicate','spread'):self.assertEqual(frame_count(dict(c,layout=l)),32)
        root=retained();p=root/'video.mp4';video(p,140,10)
        arr,audit=decode(dict(benchmark='devrows',video_path=str(p)),'duplicate',64,'nested')
        self.assertEqual(len(arr),128);self.assertTrue((arr[::2]==arr[1::2]).all())
        out=root/'out/0';out.mkdir(parents=True);t=dict(benchmark='devrows',example_id='1',question_type='object_abs_distance')
        cfg=dict(cells=[dict(model='base',layout='duplicate',benchmarks=['devrows'])],output=str(root/'out'),datasets=[],roots={},binding='b',gpus=2)
        from evalpath.items import digest
        for rank,layout in enumerate(['duplicate','spread']):
            r=dict(t,key='devrows:1',status='error',frames=32,layout=layout,binding=digest(dict(request='b',cell=0)))
            (out/f'g{rank}.jsonl').write_text(json.dumps(r)+'\n')
        with patch('merge.tasks_for',return_value=[t]):
            cfg['datasets']=[{'benchmark':'devrows'}]
            with self.assertRaisesRegex(ValueError,'layout'):merge(cfg,0,'test')

    def test_frame_cells_and_uniform96_quarters(self):
        cells=json.loads((ROOT/'inputs/cells_frames1.json').read_text())
        self.assertEqual([(c['frames'],c['layout']) for c in cells],[(32,'duplicate'),(64,'spread'),(64,'duplicate'),(96,'spread'),(128,'spread')])
        for c in cells:frame_count(c)
        fixed=[{k:v for k,v in c.items() if k not in ('frames','layout','frame_set','name')} for c in cells]
        self.assertTrue(all(x==fixed[0] for x in fixed))
        self.assertIn('uniform',cells[3]['name']);self.assertEqual(cells[3]['frame_set'],'uniform')
        for n in (900,1234,1800,3000):
            for count in (64,96):
                ids=nested_indices(n,count) if count==64 else _sample_floor_uniform_indices(n,count)
                quarters=[sum(i*4//n==q for i in ids) for q in range(4)]
                self.assertLessEqual(max(quarters)-min(quarters),2)
        root=retained();p=root/'video.mp4';video(p,200,10)
        a,m=decode(dict(benchmark='devrows',video_path=str(p)),'spread',96,'uniform')
        self.assertEqual(m['anchor_indices'],_sample_floor_uniform_indices(200,96))

    def test_encoder_budget_covers_128_spread_and_64_duplicate(self):
        for c in json.loads((ROOT/'inputs/cells_frames1.json').read_text()):
            pairs=c['frames'] if c['layout']=='duplicate' else c['frames']//2
            self.assertGreaterEqual(encoder_budget(c),pairs*130+2048)
        self.assertGreater(encoder_budget(dict(frames=128,layout='spread',frame_set='nested',benchmarks=['devrows'])),8320)

    def test_noRevsi_overlap_pins_counts(self):
        p=ROOT/'inputs/SOURCE_PINS.json';pins=json.loads(p.read_text());meta=pins['DEV_ITEMS_noReVSI.jsonl']
        self.assertEqual(meta['sha256'],DEV_SHA);self.assertEqual(meta['counts_per_type'],dict(object_rel_direction_medium=195,object_rel_direction_hard=200,object_abs_distance=208,object_rel_distance=138))
        dev=read_jsonl(dict(path=str(ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl'),sha256=DEV_SHA))
        self.assertEqual(len(dev),741);self.assertEqual(len({r['scene_name'] for r in dev}),73)
        self.assertEqual([pins['dev_overlap'][b]['overlap_scenes'] for b in ['VSI-5130','VSTI','ReVSI']],[0,84,11])
        self.assertFalse({r['scene_name'] for r in dev}&{r['scene'] for r in json.loads((ROOT/'inputs/revsi999_rows_t32.json').read_text())})
        self.assertEqual(bind_vl.parser().get_default('dev_rows'),ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl')

    def test_handwritten_table_and_changed_freeze_rejected(self):
        hand=table();hand['routes']={'camera_displacement':{'action':'routed','ci95':[.1,.2]},'object_counting':{'action':'routed','ci95':[.1,.2]}}
        with self.assertRaisesRegex(ValueError,'types'):validate_table(hand)
        for field in ['direct_pin','routed_pin']:
            bad=table();bad.pop(field)
            with self.assertRaisesRegex(ValueError,'pin'):validate_table(bad)
        dev,pins=fixture_arms(retained());frozen=freeze(dev,*pins);verify_freeze(frozen,dev)
        changed=copy.deepcopy(frozen);changed['routes'][next(iter(DEV_TYPES))]['delta']=99
        with self.assertRaisesRegex(ValueError,'recomputed'):verify_freeze(changed,dev)

    def test_absent_types_report_and_direct_reuse(self):
        tasks=[dict(benchmark=b,example_id=str(i),question_type=typ,question='How many?',options=[],ground_truth=1) for i,(b,typ) in enumerate([('official5130','object_counting'),('revsi','object_abs_distance')])]
        policy=table();policy['routes']['object_abs_distance']=dict(action='routed',ci95=[.1,.2])
        report=route_report(policy,tasks)
        self.assertEqual(report['absent_types'],{'official5130':['object_counting'],'revsi':[]})
        self.assertEqual(report['route_actions']['official5130']['object_counting'],dict(action='direct',items=1))
        p=retained()/'direct.jsonl';r=dict(tasks[0],status='complete',checkpoint_sha256=CP1_SHA,frames=32,layout='duplicate',raw_generation='</think>\n1',output_tokens=3,finish_reason='stop')
        p.write_text(json.dumps(r)+'\n');pin=dict(path=str(p),sha256=sha256(p));reused=reuse_direct(tasks,pin,policy)
        self.assertEqual(set(reused),{'official5130:0'});self.assertEqual(reused['official5130:0']['score'],1.)
        for change in ({'checkpoint_sha256':'0'*64},{'layout':'spread'},{'ground_truth':2}):
            p.write_text(json.dumps(dict(r,**change))+'\n')
            with self.assertRaises(ValueError):reuse_direct(tasks,dict(path=str(p),sha256=sha256(p)),policy)

    def test_launcher_dry_values_never_launch(self):
        candidates=[ROOT.parent/'trin_vl/go_cp1_official.sh',ROOT.parents[1]/'out/r2/kits/trin_vl/go_cp1_official.sh']
        script=next(p for p in reversed(candidates) if p.exists())
        root=retained();(root/'trin_vl').mkdir();table_path=root/'table.json';table_path.write_text('{}')
        (root/'trin_vl/go_f1.sh').write_text('printf "%s" "${DRY-unset}"\n')
        for value,expected in [(None,'unset'),('','unset'),('0','unset'),('1','1'),('yes','1'),('true','1'),('unknown','1'),('false','1')]:
            env=dict(os.environ,EVAL_WORK=str(root));env.pop('DRY',None)
            if value is not None:env['DRY']=value
            result=subprocess.run(['bash',str(script),str(table_path)],env=env,text=True,capture_output=True,check=True)
            self.assertEqual(result.stdout,expected)

    def test_bind_recomputes_table_and_reports_actions(self):
        root=retained();dev,pins=fixture_arms(root);policy=freeze(dev,*pins)
        path=root/'table.json';path.write_text(json.dumps(policy))
        models=json.loads((ROOT/'inputs/MODELS.json').read_text());models['cp1m200']=dict(kind='c1_export',path='/fixture/artifact.json',sha256=CP1_SHA)
        mp=root/'models.json';mp.write_text(json.dumps(models))
        args=['--preset','custom','--cells',str(ROOT/'inputs/cells_cp1_official.json'),'--models',str(mp),'--gpu-cap','2','--gpus','2',
              '--build-only','--artifact-dir',str(root/'bind'),'--engine','native_routed','--route-table',str(path)+'@'+sha256(path),
              '--official-rows',str(ROOT/'inputs/meta_5130.jsonl'),'--revsi-set','official999']
        cfg=bind_vl.bind(bind_vl.parser().parse_args(args))
        self.assertEqual(cfg['routing']['absent_types']['revsi'],sorted(set(cfg['routing']['route_actions']['revsi'])-DEV_TYPES))
        self.assertEqual(cfg['routing']['route_actions']['official5130']['object_counting']['action'],'direct')
        policy['routes']['object_abs_distance']['delta']=999;path.write_text(json.dumps(policy))
        args[args.index('--route-table')+1]=str(path)+'@'+sha256(path)
        with self.assertRaisesRegex(ValueError,'recomputed'):bind_vl.bind(bind_vl.parser().parse_args(args))

    def test_media_stage_skips_reused_direct_and_native_duplicate_row(self):
        from frame_stage import stage
        from native_routed import row_from_cache
        root=retained();v=root/'video.mp4';video(v,40,10)
        base=dict(benchmark='devrows',video_path=str(v),dataset='scannet',scene_name='scene',question='How far?',options=[],ground_truth=1)
        tasks=[dict(base,example_id='1',question_type='object_abs_distance'),dict(base,example_id='2',question_type='object_counting')]
        policy=table();policy['routes']['object_abs_distance']=dict(action='routed',ci95=[.1,.2])
        tp=root/'table.json';tp.write_text(json.dumps(policy))
        direct=root/'direct.jsonl';direct.write_text(json.dumps(dict(tasks[1],status='complete',checkpoint_sha256=CP1_SHA,frames=32,layout='duplicate',raw_generation='</think>\n1',output_tokens=3,finish_reason='stop'))+'\n')
        cfg=dict(binding='x',source_sha256='s',roots={},datasets=[dict(benchmark='devrows')],cells=[dict(layout='duplicate',benchmarks=['devrows'])],routing=dict(table=dict(path=str(tp),sha256=sha256(tp)),direct_answers={'devrows':dict(path=str(direct),sha256=sha256(direct))}))
        cp=root/'cfg.json';cp.write_text(json.dumps(cfg))
        with patch('frame_stage.tasks_for',return_value=tasks):index=stage(cp,root/'cache',1)
        self.assertEqual(len(index['items']),1);self.assertEqual(index['errors'],0)
        row,_=row_from_cache(tasks[0],root/'cache',sha256(root/'cache/0.json'))
        self.assertEqual(len(row['student_input']['frames']),32)
        self.assertEqual(len(set(row['student_input']['frame_indices'])),32)

    def test_legacy_direct_request_authenticates_checkpoint(self):
        root=retained();t=dict(benchmark='official5130',example_id='1',question_type='object_counting',ground_truth=1,options=[],question='How many?')
        request=dict(binding='old',models={'cp1':{'sha256':CP1_SHA}},cells=[dict(model='cp1',layout='duplicate',benchmarks=['official5130'])])
        rp=root/'request.json';rp.write_text(json.dumps(request))
        r=dict(t,binding=digest(dict(request='old',cell=0)),status='complete',raw_generation='</think>\n1',output_tokens=3,finish_reason='stop')
        p=root/'direct.jsonl';p.write_text(json.dumps(r)+'\n');pin=dict(path=str(p),sha256=sha256(p))
        reused=reuse_direct([t],pin,table(),dict(path=str(rp),sha256=sha256(rp)))
        self.assertEqual(reused['official5130:1']['checkpoint_sha256'],CP1_SHA)
        request['models']['cp1']['sha256']='0'*64;rp.write_text(json.dumps(request))
        with self.assertRaisesRegex(ValueError,'checkpoint'):reuse_direct([t],pin,table(),dict(path=str(rp),sha256=sha256(rp)))

    def test_release_list_and_erratum_provenance(self):
        pins=json.loads((ROOT/'inputs/SOURCE_PINS.json').read_text())['vsti_release']
        for label,name in [('corrected_list','vstibench_test.json'),('erratum','vstibench_erratum_dropped_items.json')]:
            self.assertEqual(sha256(ROOT/'inputs'/name),pins[label]['upstream_release_sha256'])
            self.assertTrue(pins[label]['upstream_release_file'].endswith('/vsti_upstream_labelfix_20260715/'+name))
        kept=json.loads((ROOT/'inputs/vstibench_test.json').read_text());dropped=json.loads((ROOT/'inputs/vstibench_erratum_dropped_items.json').read_text())
        self.assertEqual({r['id'] for r in dropped},set(range(6042))-{r['id'] for r in kept})
        self.assertEqual(Counter(r['drop_reason'] for r in dropped),dict(ambiguous_after_fix=202,closest_below_min_dist=98,out_of_range=6))

    def test_deadline_and_official_split(self):
        self.assertTrue(deadline_reached({'until':'1970-01-01T00:00:01Z'},now=1))
        self.assertFalse(deadline_reached({'until':'1970-01-01T00:00:01Z'},now=0))
        with self.assertRaises(ValueError):deadline_reached({})
        cells=json.loads((ROOT/'inputs/cells_cp1_official.json').read_text())
        self.assertEqual([c['benchmarks'] for c in cells],[['official5130'],['revsi']])

# The user explicitly requires unchanged 128 sampling AND balance <=2; keep each contradiction visible.
class Preserved128Balance(unittest.TestCase):pass
for total in (900,1234,1800,3000):
    def check(self,n=total):
        ids=nested_indices(n,128);q=[sum(i*4//n==k for i in ids) for k in range(4)]
        self.assertLessEqual(max(q)-min(q),2,f'Preserved 128 sampler: N={n}, quarters={q}')
    setattr(Preserved128Balance,f'test_quarters_128_N{total}',unittest.expectedFailure(check))

if __name__=='__main__':unittest.main()
