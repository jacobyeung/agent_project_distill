from copy import deepcopy
import hashlib, json, math, unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
from PIL import Image
import torch
from student_pilot import verify_pass as V,carrier_c1_decode as D
from student_pilot.scene_state import FrameMap
from student_pilot.ground_context import GroundContext
from student_pilot.p3_printed_calculator import PrintedPointRegistry as Reg
from verifykit.model import StubTokenizer
from verifykit.render import render
from tests.test_ground_r2 import geometry,backend,svp,batch,own_source,MaskProvider,ROOT

torch.set_num_threads(1)
KIT=Path('/scratch/jjyeung/orch_cd/verify_kit')

def rgb_hash(image):return hashlib.sha256(np.asarray(image).tobytes()).hexdigest()

def frame_data():
    y,x=np.indices((480,640))
    return {k:Image.fromarray(np.stack(((x+k*17)%256,(y*2+k*29)%256,(x+y*3+k*43)%256),-1).astype(np.uint8)) for k in range(1,33)}

def request(n=2,forms=('V1',)):
    frames=frame_data();mapping=FrameMap(tuple(range(32)),rgb_sha256=tuple(rgb_hash(frames[k]) for k in range(1,33)))
    candidates=[]
    for i in range(n):
        slot=i%32+1;m=np.zeros((480,640),bool);m[60+i*15:140+i*15,85+i*40:190+i*40]=True
        candidates.append(dict(candidate_id=str(i),slot=slot,mask=m,source_index=mapping.source_indices[slot-1],rgb_sha256=mapping.rgb_sha256[slot-1]))
    return dict(name='chair',candidates=candidates,forms=forms,frames=frames,frame_map=mapping,v3_slots=[1,2])


class Tokenizer(StubTokenizer):
    padding_side='right';eos_token_id=63;pad_token_id=0
    def decode(self,ids,**kw):
        if 50 in ids:return '[]'
        return ''.join(self.words[i] if i<len(self.words) else '' for i in ids)


class Processor:
    def __init__(self,tokenizer=None):self.tokenizer=tokenizer or Tokenizer();self.calls=[]
    def apply_chat_template(self,messages,**kw):
        assert kw==dict(tokenize=False,add_generation_prompt=True,enable_thinking=False)
        return messages[0]['content'][1]['text']
    def __call__(self,*,text,images,**kw):
        assert self.tokenizer.padding_side=='left'
        self.calls.append((text,images,kw))
        # Character IDs let prompt tests check every byte independently.
        ids=torch.tensor([[ord(c) for c in t] for t in text])
        pixels=torch.stack([torch.tensor(np.array(im.resize((16,16))),dtype=torch.float32) for im in images])
        return dict(input_ids=ids,attention_mask=torch.ones_like(ids),pixel_values=pixels,image_grid_thw=torch.tensor([[1,2,2]]*len(images)))


def pixel_score(pixels):
    weights=torch.arange(1,17,dtype=torch.float32)[None,None,:,None]
    channels=torch.tensor([.7,.2,.1])[None,None,None,:]
    return (pixels*weights*channels).mean((1,2,3))/255/3


class PixelModel(torch.nn.Module):
    def __init__(self):
        super().__init__();self.embedding=torch.nn.Embedding(256,4)
        self.model=NS(rope_deltas=torch.tensor([[123]]));self.config=NS(text_config=NS(max_position_embeddings=20000))
        self.generation_config=NS(eos_token_id=63,pad_token_id=0);self.calls=[];self.fail=None;self.eval()
    def get_input_embeddings(self):return self.embedding
    def forward(self,input_ids,attention_mask,pixel_values,image_grid_thw,**kw):
        assert self.model.rope_deltas is None
        from student_pilot.mdg_lora import _MASK
        assert _MASK.get() is None
        if self.fail:raise self.fail
        self.model.rope_deltas=torch.tensor([[-999]])
        self.calls.append(input_ids.tolist())
        scores=pixel_score(pixel_values)
        logits=torch.zeros((len(scores),1,64))
        logits[:,:,1:4]=scores[:,None,None]*3
        logits[:,:,4:7]=-scores[:,None,None]
        # The unconstrained argmax is number 5; a two-candidate sheet must choose 2.
        logits[:,:,7:13]=torch.arange(6)*2.
        return NS(logits=logits)
    def generate(self,**kw):
        assert kw['max_new_tokens']==128
        assert self.model.rope_deltas is None
        self.model.rope_deltas=torch.tensor([[-888]])
        return torch.cat((kw['input_ids'],torch.tensor([[50,63]]*len(kw['input_ids']))),1)


class PixelAndText(unittest.TestCase):
    def test_pixels_prompts_alignment_and_slot_identity(self):
        req=request();model=PixelModel();p=Processor();result=V.verify_pass(model,p,req)
        self.assertEqual(result['status'],'ok')
        expected=[]
        for c in req['candidates']:
            crop,meta=render(req['frames'][c['slot']],c['mask'],'outline')
            pixels=torch.tensor(np.array(crop.resize((16,16))),dtype=torch.float32)[None]
            expected.append(float(torch.sigmoid(pixel_score(pixels)*4)[0]))
            row=next(r for r in result['rows'] if r['candidate_id']==c['candidate_id'])
            self.assertEqual(row['image']['rgb_sha256'],meta['rgb_sha256'])
            self.assertEqual(row['prompt_tokens'],list(b'Is the object outlined in red a chair? Answer yes or no.'))
            self.assertAlmostEqual(row['p_yes'],expected[-1],places=6)
        self.assertNotAlmostEqual(expected[0],expected[1],places=5)

    def test_materialize_smoke_golden(self):
        from verifykit.io import rows,mask_for,frame_path
        golden=next(x for x in json.loads((KIT/'out/golden_hashes.json').read_text()) if x['variant']=='outline')
        group=next(g for g in rows(KIT/'out/smoke_candidates.jsonl') if g['object_id']==golden['object_id'])
        c=next(c for c in group['candidates'] if c['candidate_id']==golden['candidate'])
        with Image.open(frame_path(group,c['slot'])) as im:image=im.convert('RGB')
        slot=c['slot']+1;hashes=['0'*64]*32;hashes[slot-1]=rgb_hash(image)
        mapping=FrameMap(tuple(group['frame_indices']),rgb_sha256=tuple(hashes))
        candidate=dict(candidate_id=c['candidate_id'],slot=slot,source_index=mapping.source_indices[slot-1],rgb_sha256=hashes[slot-1],mask=mask_for(c))
        req=dict(name=group['name'],frames={slot:image},frame_map=mapping,candidates=[candidate])
        material=V._materialize(req,('V1',),[candidate],[])
        self.assertEqual(material['V1'][1][0][0]['rgb_sha256'],golden['rgb_sha256'])

    def test_bad_candidate_dropped_individually_and_frame_hash_checked(self):
        req=request();req['candidates'][0]['mask']=np.zeros((480,640),bool)
        result=V.verify_pass(PixelModel(),Processor(),req)
        self.assertEqual([r['candidate_id'] for r in result['rows']],['1']);self.assertEqual(len(result['dropped']),1)
        req=request();req['candidates'][0]['source_index']+=1
        result=V.verify_pass(PixelModel(),Processor(),req)
        self.assertEqual([r['candidate_id'] for r in result['rows']],['1'])
        req=request();req['frames'][1]=req['frames'][2]
        self.assertEqual([r['candidate_id'] for r in V.verify_pass(PixelModel(),Processor(),req)['rows']],['1'])

    def test_v2_restricts_to_sheet_and_v3_kit_budget(self):
        result=V.verify_pass(PixelModel(),Processor(),request(forms=('V2','V3')))
        self.assertEqual(result['rows'][0]['choice'],2)
        self.assertEqual(result['max_new_tokens'],128)
        self.assertEqual([r['parse_status'] for r in result['rows'][1:]],['null','null'])

    def test_padding_rope_gate_success_and_failure(self):
        from student_pilot.mdg_lora import _MASK
        for failure in (None,RuntimeError('test')):
            model=PixelModel();model.fail=failure;p=Processor();rope=model.model.rope_deltas
            mask=torch.ones((1,2),dtype=torch.bool);token=_MASK.set(mask)
            try:
                if failure:
                    with self.assertRaises(RuntimeError):V.verify_pass(model,p,request())
                else:V.verify_pass(model,p,request())
                self.assertIs(_MASK.get(),mask)
            finally:_MASK.reset(token)
            self.assertIs(model.model.rope_deltas,rope);self.assertEqual(p.tokenizer.padding_side,'right')

    def test_low_resolution_mask_rule(self):
        m=np.zeros((80,112),bool);m[10:20,30:40]=True
        expected=np.asarray(Image.fromarray(m).resize((640,480),Image.Resampling.NEAREST),bool)
        np.testing.assert_array_equal(V.native_mask(m),expected)


class TinyProcessor(Processor):
    def __call__(self,*,text,images,**kw):
        self.calls.append((text,images,kw))
        b=len(images);ids=torch.tensor([[2,62,60,63,10]]*b)
        return dict(input_ids=ids,attention_mask=torch.ones_like(ids),pixel_values=torch.zeros(b*4,24),
                    image_grid_thw=torch.tensor([[1,2,2]]*b),mm_token_type_ids=torch.where(ids==60,1,0))


def integration_fixture():
    from tests.test_grounding_decode import fixture,GroundTokenizer
    model,original,row=fixture()
    class RT(GroundTokenizer):
        padding_side='right';pad_token_id=0
        words={**GroundTokenizer.words,29:'<pose frame=2>',43:'<ground obj="table">',44:'<gap a="chair" b="table">',48:'<ground obj=" ">'}
        def __init__(self):self.responses={}
        def encode(self,text,**kw):
            values={'yes':20,'Yes':21,'YES':22,'no':23,'No':24,'NO':25}
            if '<tool_response>' in text:
                if text not in self.responses:
                    available=[i for i in list(range(3,20))+list(range(26,40))+list(range(51,59)) if i not in self.words]
                    self.responses[text]=available[len(self.responses)]
                return [self.responses[text]]
            return [values[text.strip()]] if text.strip() in values else super().encode(text,**kw)
        def decode(self,ids,**kw):
            values={20:'yes',21:'Yes',22:'YES',23:'no',24:'No',25:'NO'}
            response_ids={i:t for t,i in self.responses.items()}
            if any(i in response_ids for i in ids):
                return ''.join(response_ids[i] if i in response_ids else super(RT,self).decode([i],**kw) for i in ids)
            return ''.join(values[i] for i in ids) if ids and all(i in values for i in ids) else super().decode(ids,**kw)
    processor=TinyProcessor(RT());processor._routing_tokens=deepcopy(original._routing_tokens);processor._routing_tokens['ids']['fixture_pose']=29
    g=geometry();frames=frame_data()
    row.update(video_sha256='a'*64,frame_indices=list(g.frame_map.source_indices),hrp_frame_indices=list(g.frame_map.source_indices),
               ground_frames=frames,frame_rgb_sha256=[rgb_hash(frames[k]) for k in range(1,33)])
    return model,processor,row

def force(script):
    it=iter(script)
    def run(ids,logits):
        out=torch.full_like(logits,-1e9);out[:,next(it)]=0;return out
    return run

def make_backend(source):
    g=geometry()
    if source.startswith('svp'):
        def layout(name):return [(1,0,2,8,.9),(3,0,2,8,.9)] if name=='chair' else [(1,0,12,18,.9),(3,0,12,18,.9)]
        b=svp(g,own_source(g,layout),verify_threshold=0.)
        b.mask_source=source;b.config['mask_source']=source
        return b
    return backend(g,MaskProvider(lambda n:batch(g.frame_map.source_indices,x=2 if n=='chair' else 12),'test_'+source),mask_source=source,verify_threshold=0.)


class Integration(unittest.TestCase):
    def test_b4_equals_singles_all_sources_and_replay_gap(self):
        summary=[]
        for source in ('gt','mdg','svp_sam3','svp_own'):
            model,p,row=integration_fixture();rows=[deepcopy(row) for _ in range(4)]
            scripts=[[29,40,43,44,1],[43,40,44,1],[40,40,1],[40,48,1]]
            backends=[make_backend(source) for _ in rows]
            singles=[D.generate(model,p,r,mask_source=source,ground_backend=b,verify=V.Config(b),logits_processor=force(s)) for r,b,s in zip(rows,backends,scripts)]
            backends=[make_backend(source) for _ in rows]
            records=D.generate(model,p,rows,mask_source=source,ground_backend=backends,verify=[V.Config(b) for b in backends],logits_processor=[force(s) for s in scripts])
            self.assertEqual(records,singles)
            for rec in records:
                self.assertEqual(rec['text'].count('\n<tool_response>'),len(rec['calls']))
                self.assertTrue(D.replay(rec)['byte_equal'],D.replay(rec))
            self.assertNotEqual(next(c['response'] for c in records[0]['calls'] if c['kind']=='gap'),'not seen',source)
            self.assertIn('P2',records[2]['calls'][1]['response'])
            summary.append(dict(mask_source=source,rows=4,records_equal=True,bytes_equal=True,replay=True,leading_lf=True))
        (ROOT/'out/BATCH_PROOF.json').write_text(json.dumps(summary,indent=2)+'\n')

    def test_frame_binding_and_begin_question(self):
        model,p,row=integration_fixture();b=make_backend('gt')
        b.queries.append(dict(name='stale'));bad=dict(row,frame_indices=list(range(32)))
        with self.assertRaisesRegex(ValueError,'source_frame'):
            D.generate(model,p,bad,mask_source='gt',ground_backend=b,logits_processor=force([1]))
        rec=D.generate(model,p,row,mask_source='gt',ground_backend=b,logits_processor=force([29,40,1]))
        self.assertEqual([q['name'] for q in rec['heads']['ground_queries']],['chair'])
        self.assertEqual(rec['text'].count('\n<tool_response>'),2)

    def test_callback_errors_oom_and_budget_are_row_local(self):
        model,p,row=integration_fixture();rows=[deepcopy(row) for _ in range(4)];bs=[make_backend('gt') for _ in rows]
        bs[0].verify_request=lambda *a:(_ for _ in ()).throw(RuntimeError('tower failure'))
        real_accept=bs[1].accept_verify
        def bad_accept(name,result,context):
            if name=='table':return real_accept(name,result,context)
            context.registry.register(camera=[1.,2.,3.],f1=[1.,2.,3.],spread=0.,requested_frame=1)
            raise ValueError('accept failure')
        bs[1].accept_verify=bad_accept
        bs[2].verify_request=lambda *a:(_ for _ in ()).throw(torch.cuda.OutOfMemoryError('fixture OOM'))
        accepted=[]
        bs[3].accept_verify=lambda *a:accepted.append(True) or 'invalid acceptance'
        configs=[V.Config(b,max_queries=0 if i==3 else 256) for i,b in enumerate(bs)]
        results=D.generate(model,p,rows,mask_source='gt',ground_backend=bs,verify=configs,
            logits_processor=[force([40,43,1] if i==1 else [40,1]) for i in range(4)])
        self.assertEqual([r['errors'] for r in results],[1,1,1,0])
        self.assertEqual(results[2]['calls'][0]['response'],'error: verify_out_of_memory')
        self.assertEqual(results[3]['calls'][0]['verify']['status'],'budget_exceeded')
        self.assertNotIn('chair',bs[1].results)
        self.assertIn('P1',results[1]['calls'][1]['response'])
        self.assertEqual(accepted,[])

    def test_main_per_step_logits_and_final_cache_equal(self):
        from student_pilot.ground_replay import pack_array
        def run(enabled):
            model,p,row=integration_fixture();b=make_backend('gt');logs=[];cache_hash={};consume=D.consume_cache_tokens
            def spy(native,ids,mask,cache,*a,**kw):
                out,cache=consume(native,ids,mask,cache,*a,**kw);logs.append(out.logits[:,-1].detach().clone())
                for i,layer in enumerate(cache.layers):
                    for key in ('keys','values','conv_states','recurrent_states'):
                        value=getattr(layer,key,None)
                        if isinstance(value,torch.Tensor):cache_hash[i,key]=hashlib.sha256(value.detach().numpy().tobytes()).hexdigest()
                return out,cache
            with patch.object(D,'consume_cache_tokens',side_effect=spy):
                rec=D.generate(model,p,row,mask_source='gt',ground_backend=b,verify=V.Config(b) if enabled else None,logits_processor=force([42,40,42,42,1]))
            return rec,logs,cache_hash
        off,a,ca=run(False);on,b,cb=run(True)
        self.assertEqual(on['tokens'],off['tokens']);self.assertEqual(ca,cb)
        self.assertEqual(len(a),len(b));self.assertTrue(all(torch.equal(x,y) for x,y in zip(a,b)))

    def test_reread_fallback_priority_and_one_based_slots(self):
        from student_pilot.hrp_reread import Config
        model,p,row=integration_fixture();b=make_backend('gt');calls=[]
        reread=Config(frames={1:row['ground_frames'][1]},frame_indices=tuple(row['hrp_frame_indices']))
        b.verify_request=lambda *args:None
        with patch('student_pilot.hrp_reread.Backend.ground',side_effect=lambda n,r:calls.append(n) or n+': not seen'):
            rec=D.generate(model,p,row,mask_source='gt',ground_backend=b,verify=V.Config(b),reread=reread,logits_processor=force([40,1]))
        self.assertEqual(calls,['chair']);self.assertEqual(rec['calls'][0]['response'],'chair: not seen')


if __name__=='__main__':unittest.main(verbosity=2)
