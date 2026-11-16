"""Measure the real SQLite producer on a synthetic bounded family slice."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from launch_r2.host import estimate
from student_pilot.r2_materialize import materialize
from student_pilot.p3_provenance import load, file_pin
from tests.test_r2_data_path import directory, fixture, manifest, LANE


class Estimator(unittest.TestCase):
    def test_production_slice_extrapolation(self):
        root=directory()
        base=fixture(root)
        base['student_input']={k:v for k,v in base['student_input'].items() if k!='dense_source'}
        rows=[{**base,'qid':'s'+str(i)} for i in range(2000)]
        mp=manifest(root/'m',rows)
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            report=materialize([mp],root/'s',dense=False)
        store=load(report['receipt']['path'])['streams']['vqa']
        self.assertEqual(store['count'],2000)
        measured=Path(store['database']['path']).stat().st_size
        projection=estimate(2000,measured,200000)
        self.assertEqual(projection['extrapolated_bytes'],measured*100)
        proof=dict(**projection,synthetic=True,full_rows_source='synthetic extrapolation fixture; not a real census',
            source_manifest=file_pin(mp),store=store,producer='student_pilot.r2_materialize.materialize',
            note='This validates estimator arithmetic against a real produced slice; it does not estimate a real population.')
        (LANE/'out/B3_ESTIMATOR_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n')
        print(json.dumps(proof))
