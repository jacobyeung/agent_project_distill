"""Review A regressions and common recorded-layout/provenance contracts."""
from copy import deepcopy
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from provenance import annotate,verify_annotation,request,sha,VERSION
from evalpath.items import digest
from worker import read_journal,append
from journal import records,retain
from cells import check_layout,check_pinned_frames


def retained():return Path(tempfile.mkdtemp(dir=ROOT/'checks'))


class ReviewA(unittest.TestCase):
    def bundle(self):
        d=retained();archive=d/'code.tar';archive.write_bytes(b'sealed evaluator fixture')
        cfg=dict(cells=[dict(model='t0m800',layout='duplicate',benchmarks=['revsi'],decoding='greedy')],
            thinking=True,max_tokens=16384,source_sha256=sha(archive),datasets=[],models={},roots={},gpus=1)
        cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest();cfg['output']='original-output'
        p=d/'request.json';p.write_text(json.dumps(cfg))
        r=dict(key='revsi:1',binding=digest(dict(request=cfg['binding'],cell=0)),status='error')
        j=d/'original.jsonl';j.write_text(json.dumps(r)+'\n')
        return d,p,archive,j,cfg,r

    def test_A3_recompute_request_binding(self):
        d,p,a,j,c,r=self.bundle();c['thinking']=False;p.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError,'recomputed'):annotate(p,a,j,d/'copy.jsonl',0)
        self.assertFalse((d/'copy.jsonl').exists())

    def test_A4_native_annotation_provenance_and_original_bytes(self):
        d,p,a,j,c,r=self.bundle();before=j.read_bytes();out=d/'copy.jsonl'
        meta=annotate(p,a,j,out,0);row=json.loads(out.read_text())
        self.assertEqual(j.read_bytes(),before);self.assertEqual(row['layout'],'duplicate')
        self.assertEqual(row['layout_source'],'bound_config');self.assertEqual(row['original_journal_sha256'],sha(j))
        self.assertEqual(row['annotation_version'],VERSION)
        self.assertEqual(verify_annotation(out,c,0).metadata,meta)

    def test_A4_annotation_checks_source_archive(self):
        d,p,a,j,c,r=self.bundle();a.write_bytes(b'different code')
        with self.assertRaisesRegex(ValueError,'archive'):annotate(p,a,j,d/'copy.jsonl',0)

    def test_A4_annotation_refuses_each_wrong_binding_including_errors(self):
        d,p,a,j,c,r=self.bundle();j.write_text(json.dumps(r)+'\n'+json.dumps(dict(r,key='revsi:2',binding='wrong'))+'\n')
        with self.assertRaisesRegex(ValueError,'binding'):annotate(p,a,j,d/'copy.jsonl',0)

    def test_A4_annotation_layout_comes_only_from_cell(self):
        d,p,a,j,c,r=self.bundle();j.write_text(json.dumps(dict(r,layout='spread'))+'\n')
        with self.assertRaisesRegex(ValueError,'layout'):annotate(p,a,j,d/'copy.jsonl',0)

    def test_A4_annotation_refuses_in_place_and_changed_copy(self):
        d,p,a,j,c,r=self.bundle()
        with self.assertRaisesRegex(ValueError,'new output'):annotate(p,a,j,j,0)
        out=d/'copy.jsonl';annotate(p,a,j,out,0);out.write_text(out.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'hash'):verify_annotation(out,c,0)

    def test_A6_never_resume_annotated_journal(self):
        d,p,a,j,c,r=self.bundle();r.update(status='complete');j.write_text(json.dumps(r)+'\n')
        out=d/'copy.jsonl';annotate(p,a,j,out,0)
        with self.assertRaisesRegex(ValueError,'never be resumed'):read_journal(out,r['binding'],'duplicate')

    def test_A1_B5_shared_exact_expansion_and_missing_layout(self):
        t=dict(benchmark='revsi',source_frame_indices=[1,3,9]);r=dict(key='revsi:1',status='complete',layout='duplicate',media={'metadata':{'frames_indices':[1,1,3,3,9,9]}})
        check_layout(r,'duplicate');check_pinned_frames(r,t,'duplicate')
        for indices in ([1,3,9],[1,3,9,1,3,9],[1,1,3,3,9],[1,1,9,9,3,3]):
            bad=deepcopy(r);bad['media']['metadata']['frames_indices']=indices
            with self.assertRaises(ValueError):check_pinned_frames(bad,t,'duplicate')
        for row in (dict(key='x',status='error'),dict(key='x',status='error',layout='spread')):
            with self.assertRaises(ValueError):check_layout(row,'duplicate')

    def test_A1_B5_resume_error_requires_layout(self):
        d=retained();p=d/'g.jsonl';p.write_text(json.dumps(dict(key='a',binding='b',status='error'))+'\n')
        with self.assertRaisesRegex(ValueError,'layout'):read_journal(p,'b','duplicate')

    def test_B6_resume_514_plus_485_rebind_and_conflicts(self):
        d=retained();p=d/'g.jsonl'
        rows=[dict(key=str(i),binding='b',layout='duplicate',status='complete',answer=str(i)) for i in range(999)]
        p.write_text(''.join(json.dumps(r)+'\n' for r in rows[:514]))
        self.assertEqual(len(read_journal(p,'b','duplicate')),514)
        with p.open('a') as f:
            for r in rows[514:]+rows[:1]:f.write(json.dumps(r)+'\n')
        self.assertEqual(set(read_journal(p,'b','duplicate')),{str(i) for i in range(999)})
        with self.assertRaisesRegex(ValueError,'binding'):read_journal(p,'new','duplicate')
        append(p,dict(rows[0],answer='conflicting'))
        with self.assertRaisesRegex(ValueError,'Conflicting'):read_journal(p,'b','duplicate')

    def test_B6_merge_duplicate_policy(self):
        rows={};r=dict(key='a',status='complete',answer='A');retain(rows,r);retain(rows,dict(r));self.assertEqual(len(rows),1)
        with self.assertRaisesRegex(ValueError,'Conflicting'):retain(rows,dict(r,answer='B'))
        retain(rows,dict(key='a',status='error'));self.assertEqual(rows['a'],r)

    def test_B9_interrupted_journal_resume_append(self):
        d=retained();p=d/'g.jsonl';r=dict(key='1',binding='b',layout='duplicate',status='complete')
        p.write_text(json.dumps(r)+'\n{"key":')
        self.assertEqual(len(read_journal(p,'b','duplicate')),1)
        append(p,dict(r,key='2'));self.assertEqual(len(read_journal(p,'b','duplicate')),2)
        p2=d/'bad.jsonl';p2.write_text('{bad\n'+json.dumps(r)+'\n')
        with self.assertRaisesRegex(ValueError,'Broken'):list(records(p2))

    def test_A8_isolated_python_storage_boundary(self):
        self.assertTrue(sys.flags.isolated);self.assertTrue(sys.flags.no_user_site)
        self.assertFalse(any(str(p).startswith(('/home/','/data')) for p in sys.path))
        self.assertEqual(sys.executable,'/scratch/jjyeung/envs/p1cpu/bin/python')

    @unittest.skipUnless(ROOT.name=='aws_vl64o','vl64o bind restriction only')
    def test_A5_vl64o_refuses_revsi_at_bind(self):
        import bind_vl
        d=retained();p=d/'cells.json';p.write_text(json.dumps([dict(model='base',layout='duplicate',benchmarks=['revsi'])]))
        args=bind_vl.parser().parse_args(['--preset','custom','--cells',str(p),'--models',str(ROOT/'inputs/MODELS.example.json'),'--gpu-cap','1','--gpus','1','--build-only','--artifact-dir',str(d/'bind')])
        with self.assertRaisesRegex(ValueError,'pinned-tier'):bind_vl.bind(args)

    @unittest.skipUnless(ROOT.name=='aws_eval_gaps','routing kit only')
    def test_A2_legacy_direct_request_pin_and_unpinned_refusal(self):
        from routing import reuse_direct,CP1_SHA
        from test_routing import table
        d=retained();t=dict(benchmark='official5130',example_id='1',question_type='object_counting',ground_truth=1,question='How many?',options=[])
        req=dict(binding='bound',models={'cp':dict(sha256=CP1_SHA)},cells=[dict(model='cp',layout='duplicate',benchmarks=['official5130'])])
        p=d/'request.json';p.write_text(json.dumps(req));pin=dict(path=str(p),sha256=sha(p))
        r=dict(t,binding=digest(dict(request='bound',cell=0)),status='complete',raw_generation='</think>\n1',output_tokens=3,finish_reason='stop')
        j=d/'direct.jsonl';j.write_text(json.dumps(r)+'\n');jp=dict(path=str(j),sha256=sha(j))
        self.assertEqual(reuse_direct([t],jp,table(),pin)['official5130:1']['score'],1)
        with self.assertRaises(ValueError):reuse_direct([t],jp,table())
        req['models']['cp']['sha256']='0'*64;p.write_text(json.dumps(req))
        with self.assertRaises(ValueError):reuse_direct([t],jp,table(),dict(path=str(p),sha256=sha(p)))
    def test_rebind_reviewed_builds_fresh_stage_preserves_protocol(self):
        import rebind_reviewed,tarfile
        stage={'aws_vl64rt':'checks/TR_rv999_cp1on/kit','aws_eval_gaps':'checks/TR_vstifull_r2/kit'}.get(ROOT.name,'kit')
        source=Path('/scratch/jjyeung/orch_cd/evalx/work')/ROOT.name/stage
        before=sha(source/'k/1.tar')
        with tarfile.open(source/'k/1.tar') as archive:old=json.load(archive.extractfile('0.json'))
        out=retained()/'fresh'
        cfg=rebind_reviewed.rebind(source,out,build_only=True)
        self.assertNotEqual(cfg['binding'],old['binding']);self.assertNotEqual(cfg['output'],old['output'])
        self.assertNotEqual(cfg['source_sha256'],old['source_sha256'])
        for field in ('cells','models','datasets','roots','gpus'):self.assertEqual(cfg[field],old[field])
        self.assertEqual(sha(source/'k/1.tar'),before)
        with tarfile.open(out/'kit/k/0.tar') as archive:self.assertIn('provenance.py',archive.getnames())
        with self.assertRaisesRegex(ValueError,'new stage'):rebind_reviewed.rebind(source,out,build_only=True)
        request(out/'inputs/REQUEST.json',out/'kit/k/0.tar')
        from seal import seal
        seal(out)
        self.assertEqual(json.loads((out/'SEALED.json').read_text())['status'],'CLEAN')

