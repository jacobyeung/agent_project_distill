"""Faithful training preserves admitted answer envelopes and refuses wrong decisions."""
from copy import deepcopy
import json,os,unittest
from pathlib import Path
from student_pilot.h1_faithful import identity_check, answer_differs, canonical_row
from student_pilot.r2_intake import intake
from student_pilot.p3_provenance import digest
from tests.test_r2_data_path import directory, fixture, manifest, PROOFS
from tests.coverage_b8_rows import camera_row


class FaithfulIdentity(unittest.TestCase):
    def test_admitted_camera_and_real_mismatch(self):
        root=directory();base=fixture(root,stream='routing')
        raw=camera_row(base['student_input']['frames']);base.update(raw)
        base['student_input'].update(question=raw['question'],options=raw['options'])
        before=digest(base)
        path=manifest(root/'m',[base],'routing')
        admitted,report=intake(path)
        self.assertEqual(len(admitted),1,report)
        row=admitted[0]['row'];target=row['target'];answer=row['answer']
        self.assertTrue(answer.startswith('<answer>'))
        result=identity_check([row]);self.assertTrue(result['passes'],result)
        self.assertEqual(row['target'],target);self.assertEqual(digest(base),before)
        bad=deepcopy(row);bad['answer']='<answer>999</answer>'
        refused=identity_check([bad]);self.assertFalse(refused['passes'])
        self.assertEqual(refused['refusal_reasons'],{'gt_decision_mismatch':1})
        bad=deepcopy(row);next(e for e in bad['events'] if e['kind']=='decision')['result']='999'
        self.assertEqual(identity_check([bad])['refusal_reasons'],{'gt_decision_mismatch':1})
        from generator.derivgen_v7.derivgen.materialize import materialize
        raw=canonical_row(row);printed={e['call_id']:e for e in raw['events'] if e['kind']=='tool_response'}
        self.assertEqual(materialize(raw,printed)['target'],target)
        (PROOFS/'IDENTITY.json').write_text(json.dumps(dict(admitted=result,mismatched=refused,
            source_row_sha256=before,admitted_target_sha256=digest(target),bytes_preserved=True,
            scope='Synthetic camera geometry through native producer, admission and faithful materializer; production bound identity receipt remains absent.'),indent=2)+'\n')

    def test_existing_training_metric_reads_enveloped_content(self):
        for kind,a,b in (('camera_displacement','1.00','1.00'),('camera_rotation','359','-1'),('camera_movement_direction','A','A')):
            self.assertEqual(answer_differs(kind,'<answer>'+a+'</answer>','<answer>'+b+'</answer>'),answer_differs(kind,a,b))
        self.assertTrue(answer_differs('camera_displacement','<answer>2.0</answer>','<answer>1.0</answer>'))
