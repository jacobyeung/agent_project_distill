"""Native recovery producer, SQLite reader, RGB encoder and training forward."""
from copy import deepcopy
from pathlib import Path
import json,os,unittest
from unittest.mock import patch
import torch
from student_pilot import carrier_c1_run as run
from student_pilot.r2_materialize import materialize
from student_pilot.p3_provenance import load
from tests import test_r2_data_path as D
from tests.test_r2_families import ground


class RecoveryRGB(unittest.TestCase):
    def test_native_producer_reader_and_forward(self):
        from tests.test_carrier_c1 import fixture
        from student_pilot.carrier_c1 import CarrierC1
        from student_pilot.carrier_c1_sweep import recipe_for
        from transformers import Qwen3_5ForConditionalGeneration
        root=D.directory();row=ground(root,'recovery')
        from trace_format.ground_v313 import Session
        from student_pilot.ground_rows import pack
        # Empty provider output is the explicit simulated failure input.
        session=Session(None,None,None,instances=lambda name:[],program_version='3.14')
        record=deepcopy(row['ground_record']);call=record['events'][0]['call']
        self.assertEqual(session.execute(call),'ceiling lamp: not seen')
        event=session.events[0];event['audit'].update(simulated=True,status='not seen')
        record['suffix']=row['target'].replace(record['events'][0]['response'],event['response'])
        record['events']=[event]
        row.update(pack(record,row['provenance']))
        path=D.manifest(root/'manifest',[row],'routing','recovery')
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            produced=materialize([path],root/'store')
            self.assertEqual(produced['status'],'ready')
            receipt=load(produced['receipt']['path']);receipt['b7_inputs']={'fixture_binding':True}
            reader=run.Rows(receipt,D.TinyProcessor())
            try:batch,_,audit=reader.get('routing',0)
            finally:reader.close()
        original,_,_=fixture(depth_enabled=False)
        kit=Path(__file__).resolve().parents[2]/'work/build9/kits/a0'
        launch=load(kit/'k/launch.json')
        recipe_config=load(kit/launch['config']['file'])
        cfg=deepcopy(original.config);cfg.text_config.vocab_size=512
        model=CarrierC1(Qwen3_5ForConditionalGeneration(cfg).float(),dict(embed_dim=64,num_heads=4,
            trunk_depth=4,refine_iterations=4,weight_gravity=1.,weight_scale=1.,
            supervision={'path':'/fixture','sha256':'a'*64}),{},5,training_mode='final',depth_enabled=False,
            frame_layout='duplicate',frame_count=32,recipe=recipe_for(recipe_config))
        with torch.no_grad():result=model(batch,stream='routing')
        self.assertTrue(torch.isfinite(result['loss']))
        self.assertGreater(float(result['loss']),0.)
        self.assertGreater(float(result['components']['routing']),0.)
        self.assertGreater(audit['tool_spans'],0)
        (D.PROOFS/'RGB.json').write_text(json.dumps(dict(finite=True,loss=float(result['loss']),routing_loss=float(result['components']['routing']),supervised_tokens=int((batch['labels']!=-100).sum()),
            real_functions=['ground_v313.Session.execute','box_v313.ground','ground_rows.pack','r2_materialize.materialize','r2_intake.intake','carrier_c1_run.Rows.get','carrier_c1_routing.encode','CarrierC1.forward'],
            inputs='Synthetic RGB and an empty instance-provider result. The native formatter produces the failure event; no real-frame or deployment claim.',
            stand_ins='Tiny native Qwen and pose-head weights and lossless tokenizer/processor at the unavailable pretrained/GPU model boundary. Producers, SQLite reader, RGB loading, response masking and forward are real.',
            limitation='Training-path proof; frozen deployed towers and end-to-end product acceptance remain unqualified.'),indent=2)+'\n')
