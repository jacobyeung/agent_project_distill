from pathlib import Path
import sys, json, gzip, hashlib, ast, importlib.util, unittest, time
from unittest.mock import patch
from types import SimpleNamespace
L=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path[:0]=[str(L/'out/rcj'),str(L/'out/kit_qd/b'),str(L/'work/tree_r1c')]
import x,nd,z
R=L.parent/'work/d173725/173725'
F=D/('new_'+str(time.time_ns()));F.mkdir()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=module('old_x',L/'attic/build24m4u/out/rcj/x.py')
class Tests(unittest.TestCase):
    def test_authentic_publication_fail_before_and_pass_after(self):
        before=z.load(R/'timings.json')
        self.assertEqual(before['aggregate_limit_status'],'FAIL')
        self.assertEqual(before['aggregate_publication_bytes'],8419362)
        self.assertEqual(before['publication_errors'],[dict(error='ValueError',file='live')])
        result=z.load(D/'publication_result/timings.json')
        total=sum(p.stat().st_size for p in (D/'publication_result').rglob('*') if p.is_file())
        self.assertLess(total,x.LIMIT);self.assertEqual(total,result['aggregate_publication_bytes'])
        self.assertEqual(result['publication_selection']['rd0/rdiff.json.gz']['status'],'OMITTED')
        self.assertEqual(result['publication_selection']['rd0/rdiff.json.gz']['sha256'],z.sha(R/'rd0/rdiff.json.gz'))
        for name in ('chain.json','cand_cmp.json','rd0/rdiff_summary.json'):
            self.assertEqual((R/name).read_bytes(),(D/'publication_result'/name).read_bytes())
    def test_real_processor_pass_summaries_and_failed_ids(self):
        payload=(R/'proc_check.json').read_bytes();value=json.loads(payload)
        value['rows'][0]['status']='FAIL'
        short=json.loads(x.publication_payload('proc_check.json',x.compact(value)))
        self.assertEqual(short['rows'][0],value['rows'][0])
        for row,full in zip(short['rows'][1:],value['rows'][1:]):
            self.assertEqual(row['key'],full['key']);self.assertEqual(row['status'],full['status'])
            for side in ('n','p'):
                for field in ('prompt_ids','target_ids','combined_ids'):
                    expected=full[side]['values'][field]
                    self.assertEqual(row[side]['values'][field],dict(count=len(expected),sha256=hashlib.sha256(x.compact(expected)).hexdigest()))
    def test_real_sample_preserves_every_class_and_original_identity(self):
        payload=(R/'p_sample.json').read_bytes();short=x.publication_payload('p_sample.json',payload)
        full=json.loads(payload);value=json.loads(short)
        self.assertLessEqual(len(short),200000)
        self.assertEqual({r['class'] for r in value['rows']},{r['class'] for r in full['rows']})
        self.assertTrue(all(r in full['rows'] for r in value['rows']))
        self.assertEqual(value['publication']['full_sha256'],hashlib.sha256(payload).hexdigest())
    def test_child_subtype_and_exception_line_survive(self):
        failure=SimpleNamespace(returncode=1,stdout='Traceback (most recent call last):\nValueError: E96:rd\n')
        # The input is an injected child failure to test transport, not a production reproduction.
        with patch.object(old.subprocess,'run',return_value=failure):
            with self.assertRaisesRegex(ValueError,'^E96:1$'):old.type_counts(Path('n'),Path('o'))
        with patch.object(x.subprocess,'run',return_value=failure):
            with self.assertRaisesRegex(ValueError,'E96:rd'):x.type_counts(Path('n'),Path('o'))
    def test_worker_result_and_refusal_transport(self):
        for action in ('types','nsample'):
            root=F/action;root.mkdir();out=root/('nt' if action=='types' else 'ns')
            method='publish_types' if action=='types' else 'publish'
            with patch.object(nd,method,side_effect=ValueError('E96:rd')):
                self.assertEqual(x.nd_worker(L/'out/kit_qd',root,action),1)
            record=z.load(out/'result.json')
            self.assertEqual(record['exception_line'],'ValueError: E96:rd')
            self.assertIn('ValueError: E96:rd',record['traceback'])
            with patch.object(x,'launch',return_value=1) as launch:
                with self.assertRaisesRegex(ValueError,'E96:rd'):x.nd_result(L/'out/kit_qd',root,action,out)
                self.assertEqual(launch.call_args.kwargs['action'],action)
    def test_comparisons_and_mode_b_commands_unchanged(self):
        def funcs(path):
            return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)}
        a=funcs(L/'out/rcj/nd.py');b=funcs(L/'attic/build24m4u/out/rcj/nd.py')
        for name in ('fields','exact_fields','tokens','attribution','native_rules','type_table','publish_types','listings'):
            self.assertEqual(a[name],b[name],name)
        a=funcs(L/'out/rcj/x.py');b=funcs(L/'attic/build24m4u/out/rcj/x.py')
        for name in ('launch','host_root','stage','plan_r','run_r','run','sample','rdiff'):
            self.assertEqual(a[name],b[name],name)
    def test_real_absence_and_extent_evidence(self):
        value=json.loads(gzip.decompress((D/'observations/na.json.gz').read_bytes()))
        self.assertEqual(value['count'],4797);self.assertEqual(value['unattributed'],0)
        self.assertEqual(value['counts_by_attribution'],dict(scene=4768,list=29))
        ext=z.load(D/'EXTENT_EVIDENCE.json');self.assertEqual(ext['normalized_missing'],2368)
        from student_pilot.extent_receipt import Extents,required
        rows=[json.loads(r['row']) for r in z.load(R/'p_sample.json')['rows']]
        required_rows=[r for r in rows if required(r,'routing')]
        self.assertTrue(required_rows)
        for row in required_rows:
            with self.assertRaisesRegex(ValueError,'EXTENT_RECEIPT_REQUIRED'):Extents(None).check(row,'routing')
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    z.write(D/'U_TESTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),real_inputs=str(R),
        limitations='Child error transport tests inject a failure; the opaque original helper exception is not recoverable. No production SQL stores were reconstructed.'))
    raise SystemExit(not result.wasSuccessful())
