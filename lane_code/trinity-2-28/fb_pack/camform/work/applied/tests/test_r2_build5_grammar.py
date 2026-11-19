"""Numeric and streaming boundaries of the pinned grammar, without contract edits."""
from contextlib import redirect_stdout, redirect_stderr
from decimal import Decimal
import io
import json
import runpy
import sys
import unittest
from unittest.mock import patch
from tests.test_r2_data_path import directory
from student_pilot import trace_grammar as G


class Grammar(unittest.TestCase):
    def test_bounded_numeric_literals_and_units(self):
        for text in ('1/0','NaN','1e100','２','1'*101,'garbage'):
            self.assertIsNone(G._value(text))
            self.assertFalse(G._equal(text,'1'))
        self.assertEqual(G._value('1/4'),Decimal('.25'))
        self.assertEqual(G._value('25%'),Decimal('.25'))
        self.assertEqual([m.group() for m in G._tokens('2 m² and 3 m^2')],['2','3'])
        self.assertEqual(G._word_errors('one is closer; the other one is behind; halfway between chairs',''),[])
        self.assertEqual(G._word_errors('three dimensions','length width height'),[])
        self.assertEqual(G._word_errors('twice','2'),[])
        self.assertTrue(G._word_errors('frame IV; II meters',''))

    def test_distinct_object_citations(self):
        cases=[('Locate: chair in frame 1; chair in frame 2.',True),
               ('Locate: chair in frame 1; table in frame 2.',False),
               ('Locate: first chair in frame 1; second chair in frame 2.',False),
               ('Locate: in frame 1; in frame 2.',True),
               ('Locate: distinct chair instances in frame 1; chair in frame 2.',False),
               ('Locate: chair and table in frames 1 and 2.',False)]
        for text,expected in cases:
            self.assertEqual(G._exhaustive(text,list(G.FRAME.finditer(text))),expected,text)
        text='Locate: distinct instances: chair in frame 1; chair in frame 2.'
        self.assertEqual(G._list_count(text,list(G.FRAME.finditer(text))),2)
        self.assertEqual(G._citation_names('Find the first frame showing each object: chair frame 1; table frame 2.'),['chair','table'])
        for name in ('chair a','chairs','the first chair'):
            self.assertTrue(G._named_in_question(name,'Which chair(s)?',[]))
        self.assertEqual(G._kind('The turns are: left, right.',entity=False,frames=[],printed=[],program=False),'Step')
        self.assertEqual(G._kind('second chair',entity=True,frames=[],printed=[],program=False),'Step')

    def test_row_and_cli_failure_boundaries(self):
        root=directory();path=root/'rows.jsonl'
        for row in ([],dict(target=1),dict(form='invalid'),{},dict(target='<think>\n\n</think>',answer='A')):
            self.assertTrue(G.validate_row(row))
        with self.assertRaises(ValueError):G.validate_trace('x',form='invalid')
        with self.assertRaises(ValueError):G.validate_trace('x',form='direct',n_frames=-1)
        self.assertEqual({v.rule_id for v in G.validate_trace('',form='direct')},{'empty_think','no_evidence'})
        path.write_text('x'*(4*1024*1024+30)+'\n'+json.dumps({})+'\n')
        output=io.StringIO()
        with redirect_stdout(output):self.assertEqual(G.main(['--jsonl',str(path)]),1)
        self.assertEqual(json.loads(output.getvalue())['rows'],2)
        with redirect_stdout(io.StringIO()):self.assertEqual(G.main(['--jsonl',str(path),'--limit','0']),0)
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            G.main(['--jsonl',str(path),'--limit','-1'])
        with patch.object(sys,'argv',['grammar','--jsonl',str(path),'--limit','0']),redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:runpy.run_path(G.__file__,run_name='__main__')
            self.assertEqual(result.exception.code,0)

    def test_arithmetic_refusals_and_structural_labels(self):
        texts=['<think>chair</think>', 'Step 1: Locate: chair in frame 1.\nStep 3: chair is left of table.',
               'Step: 1e60 + 1 = 1.', 'Step: 1 / 0 = 0.', 'Step: 1e49 * 1e49 = 1e49.',
               'Step: 4 - 2 = 2.', 'Step: list [chair;table]; count = 3.',
               'Locate: chair in frame 1.\nRelate: chair is absent in frame 2.',
               'Step 1: I look at the video.', '<tool_response>2</tool_response><tool_response>',
               'Locate: chair in frame 1.\nThe count is 2.']
        found=set()
        for text in texts:
            found.update(v.rule_id for v in G.validate_trace(text,form='direct',question='Where are chair and table? 1 2 4',answer='2'))
        self.assertTrue({'layout','number_not_allowed','absence_claim','direct_call','filler_only'}<=found)
