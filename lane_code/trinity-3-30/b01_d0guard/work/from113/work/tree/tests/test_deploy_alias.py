"""Deployment aliases preserve canonical pins and reject changed warm-start content."""
import copy
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from student_pilot import students, full_ft, orchard_paths
from student_pilot.common import digest_json
from student_pilot.opaque_logs import console


class DeployAliasTests(unittest.TestCase):
    def test_unset_runtime_keeps_canonical_behavior(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(students.runtime_student(), 'qwen35')
            original = students.get_student('qwen35')
            alias = students.get_student('m8a9e')
            self.assertEqual({k:v for k,v in alias.items() if k != 'snapshot_dir'}, original)
            self.assertNotIn('snapshot_dir', original)
            model = SimpleNamespace(config=SimpleNamespace(model_type='qwen3_5',
                text_config=SimpleNamespace(num_hidden_layers=32, hidden_size=4096)))
            self.assertEqual(students.student_for_model(model), 'qwen35')
            value = {'event':'native', 'value':[1,2]}
            self.assertIs(console(value), value)
            with patch.dict(os.environ, {'R1_STUDENT_HEX':'6d38613965'}):
                self.assertEqual(students.student_for_model(model), 'm8a9e')
                self.assertEqual(students.runtime_student(), 'm8a9e')
            for invalid in ('zz', '756e6b6e6f776e'):
                with patch.dict(os.environ, {'R1_STUDENT_HEX':invalid}), self.assertRaises(ValueError):
                    students.runtime_student()

    def test_opaque_snapshot_and_identity(self):
        with patch.dict(os.environ, {'STUDENT_MODEL_ROOT':'/tmp/jjyeung/models'}), patch.object(orchard_paths,'owned',return_value=True):
            spec=students.STUDENTS['m8a9e']
            self.assertEqual(orchard_paths.snapshot(spec), Path('/tmp/jjyeung/models/a32330d0/snapshots') / spec['snapshot'].name)
        self.assertTrue(students.same_student('m8a9e','qwen35'))
        self.assertFalse(students.same_student('m8a9e','qwen36_27b'))
        self.assertFalse(students.same_student(None,None))

    def test_relocated_export_requires_complete_identical_content(self):
        names=['config.json','model.safetensors.index.json','tokenizer.json','tokenizer_config.json']
        base={'revision':students.STUDENTS['qwen35']['snapshot'].name,
              'files':[{'path':'/old/'+n,'sha256':str(i)*64} for i,n in enumerate(names)],
              'weight_shards':[{'path':'/old/weights.safetensors','sha256':'a'*64}]}
        current=copy.deepcopy(base)
        for values in (current['files'], current['weight_shards']):
            for p in values: p['path']=p['path'].replace('/old/','/new/')
        recorded={'student':'qwen35','base':base,'base_sha256':digest_json(base)}
        self.assertTrue(full_ft.init_base_matches(recorded,digest_json(current),current,'m8a9e'))
        self.assertFalse(full_ft.init_base_matches(recorded,digest_json(current),current,'qwen35'))
        self.assertTrue(full_ft.init_base_matches(recorded,digest_json(base)))
        current['weight_shards'][0]['sha256']='b'*64
        self.assertFalse(full_ft.init_base_matches(recorded,digest_json(current),current,'m8a9e'))
        recorded['student']='qwen36_27b'
        self.assertFalse(full_ft.init_base_matches(recorded,digest_json(current),current,'m8a9e'))

    def test_rgb_only_wrapper_uses_native_session(self):
        from tools import run_gate_eval_pdg as wrapper
        model=SimpleNamespace(auxiliary_heads=SimpleNamespace(camera=SimpleNamespace(has_g3t_prior=False)))
        processor=SimpleNamespace(tokenizer=object())
        with patch.object(wrapper.ge,'load_full_ft_checkpoint',return_value=(model,processor,{})):
            backend=wrapper.FullFTCheckpointHeads('m8a9e','f','h','p',device='cpu',rgb_only=True)
            self.assertIsNone(backend.store)
            self.assertIsNone(backend.geometry)
            self.assertEqual(backend.load_report['input_mode'],'rgb')
            model.auxiliary_heads.camera.has_g3t_prior=True
            with self.assertRaises(ValueError):
                wrapper.FullFTCheckpointHeads('m8a9e','f','h','p',device='cpu',rgb_only=True)

    def test_alias_preserves_generation_stop(self):
        from student_pilot.batches import training_stop_token
        tokenizer=SimpleNamespace(eos_token_id=248046, eos_token='<|im_end|>', encode=lambda *a,**kw:[248044])
        for name in ('qwen35','m8a9e'):
            processor=SimpleNamespace(_student_pilot_student=name, tokenizer=tokenizer)
            self.assertEqual(training_stop_token(processor), ('<|endoftext|>',248044))

    def test_training_only_division_is_explicit_and_retains_authority(self):
        from student_pilot.division import make_inherited_division
        row={'qid':'q','dataset':'d1','scene':'v1','category':'camera_pose_only'}
        record={'train_scenes':['d1/v1'],'heldout_scenes':['d1/v2']}
        with self.assertRaises(ValueError): make_inherited_division([row],[row],record)
        value=make_inherited_division([row],[row],{**record,'training_only':True})
        self.assertEqual(value['train_candidate_qids'],['q'])
        self.assertEqual(value['heldout_qids'],[])
        for invalid in ({**row,'scene':'v2'},{**row,'scene':'v3'}):
            with self.assertRaises(ValueError):
                make_inherited_division([invalid],[invalid],{**record,'training_only':True})
        with self.assertRaises(ValueError):
            make_inherited_division([row],[row],{'train_scenes':['d1/v1'],'training_only':True})
