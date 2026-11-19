"""The 27 literal calls found in the v3.12.2 fixture stay open vocabulary."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from student_pilot import mdg_decode as D, mdg_features as F, mdg_stream
from student_pilot.ground_admission import LABELS, qualification, normalized_name
from student_pilot.p3_printed_calculator import PrintedPointRegistry
from tests.test_ground_backend import Geometry, masks


def calls():
    return json.loads((Path(__file__).parent/'fixtures/v3122_open_vocabulary_calls.json').read_text())['calls']


class OpenVocabulary(unittest.TestCase):
    def test_all_27_complete_literal_names_reach_the_query_pass(self):
        cases=calls();self.assertEqual(len(cases),27)
        model=SimpleNamespace(mdg_head=object(),mdg_meta={'tau':.5})
        backend=D.Backend(model,object(),Geometry(),batch={})
        sentinel=object()
        with mock.patch.object(F,'_tokenizer',return_value=object()), \
             mock.patch.object(F,'suffix_tokens',return_value=([7,8],slice(0,1))), \
             mock.patch.object(mdg_stream,'stream_suffix_states',return_value=sentinel) as query:
            for case in cases:
                self.assertFalse(qualification(case['name']),case)
                self.assertIs(backend.query(case['name']),sentinel)
            self.assertEqual(query.call_count,27)
            self.assertEqual([c.args[3] for c in query.call_args_list],[[c['name']] for c in cases])

    def test_unknown_name_flag_changes_no_response_bytes(self):
        values=dict(mask=masks()[None],prob=np.ones((1,32))*.8)
        for name in sorted({case['name'] for case in calls()}):
            with self.subTest(name=name), mock.patch.object(D,'predict',return_value=(values,None)):
                unknown=D.Backend(SimpleNamespace(mdg_head=object(),mdg_meta={'tau':.5}),None,Geometry())
                known=D.Backend(SimpleNamespace(mdg_head=object(),mdg_meta={'tau':.5,'labels':[*LABELS,name]}),None,Geometry())
                a=unknown.ground(name,None,PrintedPointRegistry())
                b=known.ground(name,None,PrintedPointRegistry())
                self.assertEqual(a,b)
                self.assertNotIn('not seen',a)
                self.assertEqual(unknown.queries[0]['name_outside_decoder_vocabulary'],
                                 normalized_name(name) not in {normalized_name(label) for label in LABELS})
                self.assertFalse(known.queries[0]['name_outside_decoder_vocabulary'])
                self.assertFalse(unknown.queries[0]['qualified'])
