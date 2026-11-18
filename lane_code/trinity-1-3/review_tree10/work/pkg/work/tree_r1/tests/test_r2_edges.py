"""Focused failures around native adapters and content closures."""
from copy import deepcopy
import contextlib
import hashlib
import json
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from launch_r2 import build as B
from student_pilot import r2_grammar as G, r2_contract as C, r2_policy as P
from student_pilot.p3_provenance import file_pin, load
from tests.test_r2_data_path import directory, fixture, LANE
from tests.test_r2_families import ground
from tests.test_r2_build import inputs
from tests.test_r2_policy import evidence
from tests.test_r2_sampling import binding


class Edges(unittest.TestCase):
    def test_wrapper_refusals_and_shared_cli(self):
        root=directory(); path=root/'changed.py';path.write_text('changed')
        with patch.object(G.shared,'__file__',str(path)),self.assertRaises(ValueError):G.check_shared()
        with self.assertRaises(ValueError):G.validate_direct('A','chair',32)
        with self.assertRaises(ValueError):G.validate_direct('<think>\nThe chair is seen in frame 2 seconds.\n</think>\nA','Where is the chair?',32)
        with self.assertRaises(ValueError):G.validate_program({**ground(root,'units'),'response_source':'deployed'})
        with self.assertRaises(ValueError):C.event_row({**ground(root,'units'),'response_source':'deployed'})
        row=fixture(root,stream='routing')
        changed=deepcopy(row);changed['events'][0]['text']='Call: invented 800.'
        from student_pilot.carrier_c1_routing import render
        changed['target'],changed['tool_output_spans']=render(changed['events'],changed['answer'])
        with self.assertRaises(ValueError):G.validate_program(changed)
        direct=fixture(root);direct['question_type']='route_planning'
        with self.assertRaisesRegex(ValueError,'D0'):C.validate(direct,'routing')
        for text in ['A','<think>\nRelate: chair is right.\n</think>\n<call>',
                     '<think>\nUnknown line\n</think>\nA']:
            with self.assertRaises(ValueError):G.legacy_direct(text,'Where is the chair?',32)
        row=fixture(root);row['provenance']['alias']='d1/scene0161_00'
        from student_pilot.p3_provenance import digest,write
        write(root/'membership.json',dict(contract=C.CONTRACT,rows={row['qid']:digest(dict(row=row,stream='vqa',target=None))}))
        with self.assertRaisesRegex(ValueError,'withheld'):C.Admission(file_pin(root/'membership.json')).check(row,'vqa')
        path=root/'empty.jsonl';path.write_text('')
        with patch.object(sys,'argv',['g','--jsonl',str(path)]),contextlib.redirect_stdout(__import__('io').StringIO()),self.assertRaises(SystemExit) as result:
            runpy.run_path(str(Path(__file__).resolve().parents[1]/'student_pilot/trace_grammar.py'),run_name='__main__')
        self.assertEqual(result.exception.code,0)

    def test_missing_evidence_reaches_native_preparation(self):
        root=directory();pins,counts,_=binding(root)
        registry=evidence(root/'e')
        relative=lambda p:dict(path=str(Path(p['path']).relative_to(root)),sha256=p['sha256'])
        b=dict(registry=relative(registry),mix=relative(pins['mix']),counts=relative(pins['counts']))
        with contextlib.chdir(root):
            with self.assertRaisesRegex(ValueError,'r2_sampling'):
                C.preparation(dict(geometry_connector='none',r2_build2=b))
        value=load(registry['path']);value['init_m544']['record']=None
        Path(registry['path']).write_text(json.dumps(value));b['registry']=relative(file_pin(registry['path']))
        with contextlib.chdir(root),self.assertRaisesRegex(ValueError,'Missing component'):
            C.preparation(dict(geometry_connector='none',r2_build2=b))

    def test_builder_guard_branches(self):
        root=directory();base=LANE/'work/kit07ca49df_meta/m'
        source=inputs();bad=root/'foreign.json';bad.write_text('{}')
        with self.assertRaises(ValueError):B.build(base,root/'x',connector='none',records={**source,'withheld':bad}, init_pin=INIT_PIN)
        real=B.sha256
        def stale(path):
            return '0'*64 if Path(path).name=='trace_grammar.py' else real(path)
        with patch.object(B,'sha256',side_effect=stale),self.assertRaisesRegex(ValueError,'grammar'):
            B.build(base,root/'y',connector='none',records=source, init_pin=INIT_PIN)
        with patch.object(B,'tree_files',return_value={'student_pilot/__init__.py':'0'*64}),self.assertRaisesRegex(ValueError,'Source changed'):
            B.build(base,root/'z',connector='none',records=source, init_pin=INIT_PIN)
        old_load=B.load
        def no_pose(path):
            result=old_load(path)
            if Path(path)==base/'k/0.json':result={**result,'extra':[]}
            return result
        with patch.object(B,'load',side_effect=no_pose),patch.object(B,'tree_files',return_value={}),self.assertRaisesRegex(ValueError,'pose sources'):
            B.build(base,root/'w',connector='none',records=source, init_pin=INIT_PIN)
        hashes=dict(word=[hashlib.sha256(b'sensitive').hexdigest()],substr={'3':[hashlib.sha256(b'bad').hexdigest()]})
        self.assertTrue(B.bad_string('sensitive',hashes));self.assertTrue(B.bad_string('xxbadxx',hashes))

from tests.r2_init_fixture import PIN as INIT_PIN
