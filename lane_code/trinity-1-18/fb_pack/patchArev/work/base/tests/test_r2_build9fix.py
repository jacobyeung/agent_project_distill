"""Input-only regression tests; all fabricated records below are test fixtures."""
import copy,json,os,sqlite3,unittest
from pathlib import Path
from student_pilot.row_text_audit import reasons,recorded_responses
from student_pilot.extent_receipt import Extents,content
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.carrier_c1_run import Rows
from student_pilot.scene_division_gate import check_rows


class Fixes(unittest.TestCase):
    def folder(self):
        p=Path(os.environ.get('R2_PROOFS',os.environ['TMPDIR']))/'b9fix';p.mkdir(parents=True,exist_ok=True);return p

    def response(self,text):
        value='<tool_response>\n'+text+'\n</tool_response>'
        return dict(target=value,events=[dict(kind='ground_response',text=value,call_id='a')],
                    tool_output_spans=[dict(start=0,end=len(value),call_id='a',event_index=0)])

    def reader(self,row,pin=None):
        reader=Rows(dict(streams={},extent_receipt=pin),None)
        conn=sqlite3.connect(':memory:');reader.connections['routing']=conn
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        conn.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
        try:return reader.row('routing',0)
        finally:reader.close()

    def test_status_authentication_and_whitespace(self):
        for whitespace in (' ','  ','\n','\u00a0','\u2003','\t'):
            for status in ('not'+whitespace+'seen','box'+whitespace+'unavailable','unresolved'):
                row=self.response(status);self.assertEqual(reasons(row),[])
                self.reader(row)
                for field in ('target','suffix','trace','response'):
                    forged={field:row['target']}
                    self.assertIn('runtime_box_status',reasons(forged))
                    with self.assertRaisesRegex(ValueError,'runtime_box_status'):self.reader(forged)
                bad=copy.deepcopy(row);bad['events'][0]['text']='edited'
                self.assertIn('runtime_box_status',reasons(bad))
                bad=copy.deepcopy(row);bad['tool_output_spans'][0]['start']=1
                self.assertIn('runtime_box_status',reasons(bad))
                bad=copy.deepcopy(row);bad['tool_output_spans'][0]['event_index']=99
                self.assertIn('runtime_box_status',reasons(bad))
        for text in ('<tool_response>not seen','<tool_response><tool_response>not seen</tool_response>'):
            self.assertFalse(recorded_responses({},text))

    def test_M02_interspan_status(self):
        a=self.response('a');b=self.response('b');text=a['target']+' not seen '+b['target']
        row=dict(target=text,events=a['events']+b['events'],tool_output_spans=a['tool_output_spans']+[
            dict(start=len(a['target'])+10,end=len(text),call_id='a',event_index=1)])
        self.assertTrue(recorded_responses(row,text))
        self.assertIn('runtime_box_status',reasons(row))
        import student_pilot.row_text_audit as audit
        namespace={'__name__':'student_pilot.mutant'}
        source=Path(audit.__file__).read_text().replace('[^<]*',r'[\s\S]*')
        exec(compile(source,str(self.folder()/'M02.py'),'exec'),namespace)
        self.assertEqual(namespace['reasons'](row),[])

    def test_extent_pin_and_reader(self):
        row=dict(qid='fixture',question_type='object_abs_distance',target='<think>fixture</think><answer>1</answer>',
            ground_record=dict(program_audit=dict(independent_ordered_boxes=[dict(axesLengths=[1,1,1])])),provenance={})
        p=self.folder()/'extent.json'
        entry=dict(content_sha256=digest(content(row)),box_statuses=['full'],repair_sha256=None)
        receipt=dict(schema='full-extent-receipt-v1',rows={row['qid']:entry})
        p.write_text(json.dumps(receipt));pin=file_pin(p)
        self.reader(row,pin)
        with self.assertRaisesRegex(ValueError,'REQUIRED'):self.reader(row)
        for status in ('half','unknown'):
            bad=copy.deepcopy(receipt);bad['rows']['fixture']['box_statuses']=[status];p.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'BOX_NOT_FULL'):self.reader(row,file_pin(p))
        p.write_text(json.dumps(receipt))
        changed=copy.deepcopy(row);changed['ground_record']['program_audit']['independent_ordered_boxes'][0]['axesLengths'][0]=.5
        with self.assertRaisesRegex(ValueError,'UNAUDITED'):self.reader(changed,file_pin(p))
        bad=copy.deepcopy(receipt);bad['rows']['fixture']['repair_sha256']='x';p.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError,'UNCERTIFIED'):self.reader(row,file_pin(p))
        p.write_text('{}')
        with self.assertRaisesRegex(ValueError,'SCHEMA'):Extents(file_pin(p))
        with self.assertRaises(ValueError):Extents(pin)

    def test_scene_gate(self):
        from student_pilot.row_removals import Removals
        p=self.folder()/'division.json';p.write_text(json.dumps(dict(train_scenes=['d/a'],heldout_scenes=['d/b'])))
        good=dict(qid='a',dataset='d',scene='a');bad=dict(qid='b',dataset='d',scene='b')
        self.assertEqual(check_rows([good],file_pin(p))['admitted'],1)
        with self.assertRaisesRegex(ValueError,'DIVISION_REFUSED'):check_rows([good,bad],file_pin(p))
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):check_rows([good,good],file_pin(p))
        r=self.folder()/'excluded.jsonl';r.write_text(json.dumps(dict(row_key='b'))+'\n')
        result=check_rows([good,bad],file_pin(p),removals=Removals([file_pin(r)]))
        self.assertEqual(result['removed'],1)

    def test_native_stream_and_bound_scene_gate(self):
        from student_pilot.carrier_c1_data import build_stream
        from student_pilot.scene_division_gate import check_bound
        from tests.test_r2_data_path import fixture,directory,RECORDS,SOURCES
        root=directory();row=fixture(root)
        for pin in row['student_input']['frames']:
            pin['path']=str(root/'frames'/Path(pin['path']).name)
        row['qid']='keep'
        division=root/'native_division.json';division.write_text(json.dumps(dict(schema='diagnostic-whole-scene-division-v1',training_only=True,train_scenes=['d1/fixture_clean'],heldout_scenes=[])))
        rejected=dict(qid='outside',dataset='d1',scene='outside')
        rows=root/'native_rows.jsonl';rows.write_text(json.dumps(rejected)+'\n'+json.dumps(row)+'\n')
        excluded=root/'native_excluded.jsonl';excluded.write_text(json.dumps(dict(row_key='outside'))+'\n')
        with self.assertRaisesRegex(ValueError,'scene division'):
            build_stream(file_pin(rows),file_pin(division),root/'without_list','vqa')
        result=build_stream(file_pin(rows),file_pin(division),root/'with_list','vqa',remove_files=[file_pin(excluded)])
        self.assertEqual(result['count'],1)
        stream=root/'stream.json';stream.write_text(json.dumps(result))
        cfg=dict(streams=dict(vqa=file_pin(stream),routing=file_pin(stream)),scene_division=file_pin(division),
            dev_scene_exclusions=file_pin(Path(__file__).parents[1]/'student_pilot/r2_dev_merged.json'),
            benchmark_scene_exclusions=file_pin(RECORDS/SOURCES['benchmark']),remove_files=[file_pin(excluded)])
        checked=check_bound(cfg);self.assertEqual(checked['vqa']['admitted'],1);self.assertEqual(checked['routing']['outside'],0)
        reader=Rows(dict(streams=dict(vqa=result)),None)
        try:self.assertEqual(reader.row('vqa',0)[0]['target'],row['target'])
        finally:reader.close()
