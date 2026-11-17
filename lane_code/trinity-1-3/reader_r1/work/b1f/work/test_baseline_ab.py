"""Deterministic CPU proof through generate_real, CallHook, StageOne and servers."""
import builtins,hashlib,io,json,sys,time,unittest
from contextlib import nullcontext,ExitStack
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];P=W/'out/baseline'
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P)]
import numpy as np
import torch
from PIL import Image
torch.set_num_threads(1)
import importlib.util
spec=importlib.util.spec_from_file_location('_testmemo',W/'out/src/b/e2e_reader/perception_memo.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
from e2e_reader import real
from e2e_reader.callhook import CallHook
from student_pilot.sam3_tower import ClipFeatures
from student_pilot import carrier_c1_decode as decode,tower_read
from h1eval.scorers import accuracy,answer_text

class G3T:
    calls=0
    def __init__(self,config):self.dense_frames=config['dense_frames']
    def run(self,b):
        G3T.calls+=1
        time.sleep(.002)  # labelled stub delay, never a GPU estimate
        c=b['tower_native_frames'][0].getpixel((0,0))[0]
        n=self.dense_frames
        pose=np.tile(np.array([0,0,0,0,0,0,1,1,1],np.float64),(n,1))
        pose[:,0]=np.linspace(0,.15,n)
        uv=np.linspace(0,1000,51,dtype=np.float32)
        yy,xx=np.meshgrid(uv,uv,indexing='ij')
        depth=np.broadcast_to(2+c*.1+xx/2000+yy/3000,(32,51,51)).copy().astype(np.float32)
        return NS(raw_pose9=pose,anchor_slots=np.asarray(b['tower_anchor_slots']),
                  frame_indices=np.asarray(b['tower_frame_indices']),depth_grid=depth,
                  depth_conf_grid=np.broadcast_to(xx,(32,51,51)).copy(),
                  points_grid=np.zeros((32,51,51,3),np.float32),grid_uv=uv)

class Sam:
    def __init__(self):
        self.calls=0;self.device=torch.device('cpu');self.precision='float32'
        self.image_batch_size=1;self.native_image_batch=False;self._owner=object()
        model=NS(backbone=NS(forward_text=lambda names,**k:dict(phrase=names[0])),
                 _get_dummy_prompt=lambda:None,forward_grounding=self.ground)
        self._backend=NS(model=model,find_stage=None)
    def _load(self):pass
    def _autocast(self):return nullcontext()
    def encode(self,images):
        self.calls+=1;time.sleep(.002)
        return ClipFeatures(tuple(dict(backbone_fpn=[torch.tensor([im.getpixel((0,0))[0]],dtype=torch.float32).reshape(1,1,1,1)],vision_pos_enc=[torch.ones(1,1,1,1)]) for im in images),tuple((im.height,im.width) for im in images),self._owner)
    def ground(self,backbone_out,**kw):
        mask=torch.full((1,1,24,32),-10.)
        # Different question names still execute the fresh text/grounding branch.
        if backbone_out['phrase']=='chair':mask[:,:,7:17,5:13]=10
        elif backbone_out['phrase']=='table':mask[:,:,7:17,20:28]=10
        return dict(pred_logits=torch.tensor([8.]),presence_logit_dec=torch.tensor([8.]),pred_masks=mask)

class Tokenizer:
    chunks=['<think>','<move from=1 to=9>','<ground obj="chair" mode="box">',
            '<ground obj="table" mode="box">','<gap a="chair" b="table" rule="box_grid_5cm">',
            '</think><answer>1.2</answer>']
    eos_token_id=2
    def convert_tokens_to_ids(self,t):return 3 if t=='<tool_response>' else 4
    def encode(self,s,**kw):return [1000+x for x in s.encode()]
    def decode(self,ids,**kw):
        return ''.join(self.chunks[i-10] if 10<=i<16 else chr(i-1000) if i>=1000 else '' for i in ids)

def artifact():
    return NS(manifest=dict(components={k:dict(files=[dict(rel=k+'/weights',sha256=hashlib.sha256(k.encode()).hexdigest(),bytes=1)]) for k in ('g3t','sam3')}),
              files=lambda k:[Path('model.safetensors'),Path('config.json')],
              allowed=set(),env_roots=(),write_roots=(),code=set())

def frames(c):
    return dict(native_frames=[Image.new('RGB',(64,48),(c,i,0)) for i in range(32)],
                dense_indices=list(range(32)),anchor_slots=list(range(32)),anchor_indices=list(range(32)))

def logits(i):
    z=torch.full((1,1,1300),-100.);z[0,0,10+i if i<6 else 2]=100.
    return NS(logits=z,past_key_values=None)

class Proof(unittest.TestCase):
    def setUp(self):M._sessions.clear();M._disabled=False
    def test_key_copies_no_io_eviction(self):
        memo=M.Memo();im=Image.new('RGB',(4,3),(1,2,3));count=[0]
        def fresh():
            count[0]+=1
            return dict(a=np.arange(12,dtype=np.float32).reshape(3,4),t=torch.arange(6,dtype=torch.bfloat16).reshape(2,3).t(),scalar=-0.,nested=[np.float32('nan')])
        # Warm torch's conversion machinery before denying all relevant IO.
        M.equal(fresh(),fresh());count[0]=0
        with patch.object(builtins,'open',side_effect=AssertionError('file IO')),patch.object(io,'open',side_effect=AssertionError('file IO')),patch.object(np,'load',side_effect=AssertionError('np.load')),patch.object(torch,'load',side_effect=AssertionError('torch.load')):
            a=memo.call('g3t',{'weight':'a'},[im],[0],fresh)
            a['a'][:]=42;a['t'].fill_(42)
            b=memo.call('g3t',{'weight':'a'},[im.copy()],[0],fresh)
            self.assertEqual(count[0],1);self.assertEqual(float(b['a'][0,0]),0);self.assertEqual(float(b['t'][0,0]),0)
            changed=im.copy();changed.putpixel((0,0),(9,2,3))
            memo.call('g3t',{'weight':'a'},[changed],[0],fresh)
            memo.call('g3t',{'weight':'a'},[im],[1],fresh)
            memo.call('g3t',{'weight':'b'},[im],[0],fresh)
            self.assertEqual(count[0],4)
            memo.call('sam3',{'weight':'a'},[im],[0],fresh)
            self.assertEqual(count[0],5)
        for field in ('dense_indices','anchor_slots','anchor_indices'):
            f=frames(1);a=M.key('g3t',{},f['native_frames'],M.frame_indices(f));f[field][1]+=2
            self.assertNotEqual(a,M.key('g3t',{},f['native_frames'],M.frame_indices(f)))
        self.assertNotEqual(M.key('g',{},[im],[]),M.key('g',{},[im.convert('RGBA')],[]))
        self.assertNotEqual(M.key('g',{},[im],[]),M.key('g',{},[im.resize((3,4))],[]))
        m=M.Memo(perception_memo_max_bytes=100)
        for i in range(3):m.call('g',i,[im],[],lambda:np.zeros(16,np.float32))
        self.assertEqual(m.evictions,2);self.assertLessEqual(m.bytes,100)
        m=M.Memo(perception_memo_max_bytes=1);m.call('g',0,[im],[],fresh)
        self.assertFalse(m.entries)
    def test_verify_mismatch_disables_entire_process(self):
        memo=M.process_memo({'perception_memo':'verify'});other=M.process_memo({'perception_memo':'on'})
        im=[Image.new('RGB',(1,1))]
        memo.call('g',{},im,[],lambda:np.array([0.],np.float64))
        other.call('s',{},im,[],lambda:torch.ones(1))
        got=memo.call('g',{},im,[],lambda:np.array([-0.],np.float64))
        self.assertTrue(np.signbit(got[0]));self.assertFalse(memo.events[-1]['equal'])
        self.assertEqual(memo.report()['effective'],'off');self.assertFalse(other.entries)
        self.assertEqual(other.call('s',{},im,[],lambda:torch.full((1,),7.)).item(),7)
        self.assertFalse(M.equal(np.array([1],np.int32),np.array([1],np.int64)))
        self.assertFalse(M.equal(torch.ones(1),torch.ones(1,1)))
        self.assertFalse(M.equal(-0.,0.))
    def test_verify_first_30_reads(self):
        m=M.Memo(perception_memo='verify',perception_memo_verify_reads=30)
        for i in range(35):m.begin_read();self.assertEqual(m.mode,'verify' if i<30 else 'on')
        for x in ({},{'perception_memo':'bad'},{'perception_memo':'on','perception_memo_verify_reads':30}):
            with self.assertRaises((ValueError,KeyError)):M.settings(x,required=True)
    def test_real_reader_ab(self):
        art=artifact();tok=Tokenizer();proc=NS(tokenizer=tok)
        baseline=None;reports={}
        for mode in ('off',):
            M._sessions.clear();M._disabled=False;G3T.calls=0;sam=Sam()
            head=NS(with_null=lambda x,*a:torch.cat((torch.arange(len(x),dtype=torch.float64)+1,torch.tensor([-10.]))))
            perception=real.real_perception(art,device='cpu',sam3_tower=sam,selector_head=head)
            sequence=[0]
            def prefill(*args,**kw):
                sequence[0]=0
                heads=NS(pose9=np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.],(32,1)),gravity=np.array([0.,-1.,0.]),
                         depth_map=torch.ones(32,1,1,1),depth_head=NS(query=lambda d,uv:torch.full(uv.shape[:2],3.)))
                return NS(heads=heads,native=NS(generation_config=NS(eos_token_id=2)),cap=10000,stream=None,output=logits(0))
            def consume(*args,**kw):sequence[0]+=1;return logits(sequence[0]),None
            outputs=[];elapsed=[]
            with patch.object(tower_read,'FrozenG3TTower',G3T),patch.object(decode,'_prepare_decode',prefill),patch.object(decode,'consume_cache_tokens',consume):
                for i in range(30):
                    hook=CallHook(tok,[11,12,13,14])
                    t=time.perf_counter()
                    result=real.generate_real(NS(),proc,dict(input_ids=torch.ones(1,1,dtype=torch.long),attention_mask=torch.ones(1,1,dtype=torch.long)),
                                             frames(i//6),hook,perception,artifact=art,enforce_audit=False)
                    elapsed.append(time.perf_counter()-t)
                    scores=accuracy(result,dict(question_type='object_abs_distance',question='How far in meters?',ground_truth=1.2,answer_type='numeric'))
                    outputs.append(dict(text=result['text'],tokens=result['tokens'],responses=result['calls'],answer=answer_text(result),scores=scores))
            raw=json.dumps(outputs,sort_keys=True,allow_nan=False).encode()
            if baseline is None:baseline=raw
            self.assertEqual(raw,baseline)
            self.assertTrue(all(r['responses']['calls']==dict(move=1,ground=2,gap=1) for r in outputs))
            self.assertTrue(any('distance ' in c['response'] for r in outputs for c in r['responses']['records'] if c['family']=='gap'))
            expected=5 if mode=='on' else 30
            self.assertEqual(G3T.calls,expected);self.assertEqual(sam.calls,expected)
            events=[] if mode=='off' else perception.memo.events
            if mode=='verify':self.assertEqual(len(events),50);self.assertTrue(all(e['equal'] for e in events))
            print('Completed A/B mode:',mode,flush=True)
            reports[mode]=dict(reads=30,captures=5,seconds_per_read=sum(elapsed)/30,g3t_calls=G3T.calls,sam_encode_calls=sam.calls,
                               output_sha256=hashlib.sha256(raw).hexdigest(),events=events)
        (W/'out/BASELINE_AB.json').write_text(json.dumps(dict(passed=True,timings='CPU deterministic stubs with 2 ms fresh-module delays; not GPU performance',modes=reports),indent=2)+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
