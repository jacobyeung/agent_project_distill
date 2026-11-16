"""Native tiny Qwen3.5 CPU encode/generate at the kit's production visual grid."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'evaluator'))
from cells import validate_token_budget
from parity import trainer_encode
from scoring import score_item

class LongContext(unittest.TestCase):
    def test_encode_generate_parse_96_128(self):
        from transformers import AutoProcessor,Qwen3_5Config,Qwen3_5ForConditionalGeneration,LogitsProcessor,LogitsProcessorList
        torch.set_num_threads(1);torch.manual_seed(17)
        p=AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',local_files_only=True)
        p._student_pilot_student='qwen35'
        # Width/layers match c1mix/tests/fullft_toys.py: tiny_base. Patch size
        # matches the real processor so the exact encoded visual grid is exercised.
        text=dict(vocab_size=64,hidden_size=16,intermediate_size=32,num_hidden_layers=2,
                  num_attention_heads=2,num_key_value_heads=1,head_dim=8,use_cache=True,pad_token_id=0,
                  layer_types=['linear_attention','full_attention'],linear_key_head_dim=4,
                  linear_value_head_dim=4,linear_num_key_heads=2,linear_num_value_heads=4,
                  max_position_embeddings=49152,
                  rope_parameters=dict(rope_type='default',rope_theta=10000.,mrope_section=[1,1,2],partial_rotary_factor=1.))
        patch=p.video_processor.patch_size;temporal=p.video_processor.temporal_patch_size
        vision=dict(depth=1,hidden_size=16,intermediate_size=32,num_heads=2,out_hidden_size=16,
                    num_position_embeddings=16,patch_size=patch,temporal_patch_size=temporal,spatial_merge_size=2)
        cfg=Qwen3_5Config(text_config=text,vision_config=vision,image_token_id=60,video_token_id=61,
                         vision_start_token_id=62,vision_end_token_id=63)
        for c in (cfg,cfg.text_config,cfg.vision_config):c._attn_implementation='sdpa'
        model=Qwen3_5ForConditionalGeneration(cfg).float().eval()
        task=dict(example_id='cpu',benchmark='devrows',question='Which object is closest?',options=['A. chair','B. desk'],ground_truth='A',question_type='object_rel_distance')
        evidence=[]
        for n,expected in ((96,30912),(128,35072)):
            cell=dict(frames=n,frame_set='uniform' if n==96 else 'nested',layout='spread',benchmarks=['devrows'])
            arrays=np.zeros((n,416,640,3),dtype=np.uint8)
            meta=dict(fps=10.,frames_indices=list(range(n)),total_num_frames=n,height=416,width=640)
            batch,audit=trainer_encode(p,task,arrays,meta,cell)
            start=audit['prompt_tokens']
            ids=batch['input_ids'][:,:start]
            tiny=torch.full_like(ids,10)
            for token,new in [('<|video_pad|>',61),('<|vision_start|>',62),('<|vision_end|>',63)]:
                tiny[ids==p.tokenizer.convert_tokens_to_ids(token)]=new
            native={k:v for k,v in batch.items() if k in ('pixel_values_videos','video_grid_thw')}
            native.update(input_ids=tiny,attention_mask=torch.ones_like(tiny),mm_token_type_ids=torch.where(tiny==61,2,0))
            self.assertEqual(int((tiny==61).sum()),int(batch['video_grid_thw'].prod()/4))
            self.assertEqual(validate_token_budget(cell),expected)
            self.assertGreaterEqual(start, n*60)
            encoded_start=start
            # Fill the conservative reserved prefill with ordinary text tokens.
            # The real processor merges temporal pairs; the budget remains 130/frame.
            start=expected-16384
            tiny=torch.cat([tiny,torch.full((1,start-encoded_start),10,dtype=tiny.dtype)],dim=1)
            native.update(input_ids=tiny,attention_mask=torch.ones_like(tiny),mm_token_type_ids=torch.where(tiny==61,2,0))
            self.assertEqual(start+16384,validate_token_budget(cell))
            self.assertLessEqual(start,n*130+2048)
            # Run actual generation and parse its unforced random answer. A second
            # decode constrains one token so the official valid-answer path is checked.
            with torch.inference_mode():
                out=model.generate(**native,max_new_tokens=2,do_sample=False,use_cache=True,pad_token_id=0,eos_token_id=1)
            self.assertGreater(out.shape[1],start)
            raw=p.tokenizer.decode(out[0,start:].tolist(),skip_special_tokens=False)
            result=score_item(task,raw,out.shape[1]-start)
            self.assertIn('parse_failed',result)
            class Answer(LogitsProcessor):
                def __call__(self,input_ids,scores):
                    scores.fill_(-float('inf'));scores[:,5]=0;return scores
            with torch.inference_mode():
                forced=model.generate(**native,max_new_tokens=1,do_sample=False,use_cache=True,pad_token_id=0,eos_token_id=1,
                                      logits_processor=LogitsProcessorList([Answer()]))
            # Tiny vocabulary's token 5 is the fixture's answer token A.
            decoded='</think>\n'+''.join('A' if x==5 else '?' for x in forced[0,start:].tolist())
            self.assertEqual(score_item(task,decoded,1)['score'],1)
            evidence.append(dict(frames=n,grid=batch['video_grid_thw'].tolist(),encoded_prompt_tokens=encoded_start,stress_prefill_tokens=start,
                                 visual_tokens=int((tiny==61).sum()),budget=expected,generated=out[0,start:].tolist(),
                                 raw_parse_failed=result['parse_failed'],forced_answer=decoded,device='cpu',
                                 tiny_parameters=sum(t.numel() for t in model.parameters())))
            (ROOT/'checks/LONG_CONTEXT.json').write_text(json.dumps(evidence,indent=2)+'\n')

if __name__=='__main__':unittest.main()
