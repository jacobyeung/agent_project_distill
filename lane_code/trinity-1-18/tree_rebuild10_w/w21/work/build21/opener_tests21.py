from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import unittest,json
from student_pilot import r2_openers as O,carrier_c1_run as C,r1_training as R
from student_pilot.p3_provenance import file_pin
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
class Opener21(unittest.TestCase):
 def fixture(self):
  cfg=json.loads((B/'proofs/capacity/400/q/h/config.json').read_text())
  receipt=json.loads(Path(cfg['preparation']['path']).read_text())
  receipt['_r1_start_config']=deepcopy(cfg)
  return cfg,receipt
 def test_context_identity_and_missing_refusals(self):
  cfg,receipt=self.fixture();self.assertEqual(O.start_context(receipt),cfg)
  self.assertIs(O.start_context(cfg),cfg)
  parent=deepcopy(receipt);parent['init_artifact']['artifact']['sha256']=R.PARENT
  parent.pop('_r1_start_config');self.assertIs(O.start_context(parent),parent)
  bad=deepcopy(receipt);bad.pop('_r1_start_config')
  with self.assertRaisesRegex(ValueError,'REQUIRED'):O.start_context(bad)
  for key in ('config_sha256','r1_training','init_artifact','routing_opener_init','routing_vocabulary','streams'):
   bad=deepcopy(receipt);bad[key]={} if isinstance(bad.get(key),dict) else 'altered'
   with self.assertRaisesRegex(ValueError,'MISMATCH'):O.start_context(bad)
  bad=deepcopy(receipt);bad['_r1_start_config']['lm_lr_scale']=0.25
  with self.assertRaisesRegex(ValueError,'MISMATCH'):O.start_context(bad)
 def test_initialize_uses_full_context_and_witness(self):
  cfg,receipt=self.fixture();w=json.loads(Path(receipt['routing_vocabulary']['path']).read_text())
  p=SimpleNamespace(tokenizer=SimpleNamespace(get_vocab=lambda:{}),_routing_tokens=w['tokens'])
  model=SimpleNamespace(init_report=dict(lm_tensors=1,r2_lineage=R.PARENT))
  with patch.object(O,'vocabulary',return_value={k:w[k] for k in ('vocabulary_sha256','tokens')}),patch.object(R,'start',return_value=400) as start:
   self.assertEqual(O.initialize(model,p,receipt),'kept');start.assert_called_once_with(cfg)
