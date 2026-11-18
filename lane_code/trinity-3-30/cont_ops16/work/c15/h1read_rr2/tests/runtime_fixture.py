"""CPU integration: actual worker, budget derivation, token audit and mergers; fake engine/model/parity probe."""
import offline_guard
import asyncio
import importlib
import json
from pathlib import Path
import sys
import tarfile
import types
import uuid
from unittest.mock import patch
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit/reader'))
import x7 as X
work=ROOT/'evidence'/('runtime_'+uuid.uuid4().hex)
work.mkdir()
all_rows=[json.loads(l) for l in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()]
rows=[next(r for r in all_rows if r['question_type']==t) for t in ('object_counting','object_abs_distance','object_rel_direction_easy','obj_appearance_order')]
reg=json.loads((ROOT/'kit/launcher/EXTRA.json').read_text())
# Extract only these fixture rows' real RGB frames from the already pinned local asset.
froot=work/'f';froot.mkdir();need={n for r in rows for n in r['frame_refs']}
with tarfile.open(ROOT/'assets/d81f4a26.tar') as tf:
    for m in tf:
        if m.name in need:
            p=froot/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(m).read())

class Tokenizer:
    def encode(self,text,add_special_tokens=False):
        result=[]
        while text:
            if text.startswith('</think>'):result.append(999999);text=text[8:]
            else:result.append(ord(text[0]));text=text[1:]
        return result
    def decode(self,ids,skip_special_tokens=True):return ''.join('</think>' if i==999999 else chr(i) for i in ids)
class Processor:
    tokenizer=Tokenizer()
    video_processor=None
    @classmethod
    def from_pretrained(cls,*a,**kw):return cls()
    def apply_chat_template(self,messages,**kw):return messages[0]['content'][1]['text']+'<think>\n'
class Engine:
    @classmethod
    def from_engine_args(cls,*a):return cls()
    async def generate(self,req,params,request_id):
        row=next((r for r in rows if r['id'] in request_id),rows[0])
        if params.max_tokens==1:text='p'
        elif params.max_tokens==64:text=row['ground_truth']
        else:text='t'*2050+'</think>\n'+row['ground_truth']
        ids=Processor.tokenizer.encode(text)
        prompt_ids=req.get('prompt_token_ids',Processor.tokenizer.encode(req.get('prompt','')))
        yield NS(outputs=[NS(text=text,token_ids=ids,finish_reason='stop')],prompt_token_ids=prompt_ids)
    def shutdown(self):pass

def module(name,**values):
    m=types.ModuleType(name);m.__dict__.update(values);sys.modules[name]=m;return m
module('transformers',AutoProcessor=Processor)
module('vllm',__version__='0.32.0',SamplingParams=lambda **kw:NS(**kw))
module('vllm.engine');module('vllm.engine.arg_utils',AsyncEngineArgs=lambda **kw:NS(**kw))
module('vllm.sampling_params',RequestOutputKind=NS(FINAL_ONLY='final'))
module('vllm.v1');module('vllm.v1.engine');module('vllm.v1.engine.async_llm',AsyncLLM=Engine)
sys.path.insert(0,str(ROOT/'kit/reader/out'))
import direct
# The candidate requires the accepted runtime digest, including its input filter.
# The packaged optional filter differs; it is not the runtime executed by the job.
runtime=ROOT/'readk/evidence/test_fix2_bind_main1000/a0/kit'
sys.path.insert(0,str(runtime/'evaluator'))
import parity,stage,token_audit
manifest=work/'manifest.json';manifest.write_text(json.dumps(dict(files=[dict(bytes=1)])))
models=json.loads((ROOT/'kit/launcher/MODELS.json').read_text())
models['base']['manifest']['path']=str(manifest)
models['cp1m200']=dict(kind='c1_export',path=str(work/'artifact.json'),sha256='a'*64)
cfg=dict(spec=dict(run=str(work/'r'),step=200,models=models,artifact=models['cp1m200']),extra=reg)

def assets(reg,w):
    Path(w).mkdir(parents=True)
    return rows,froot

def compare(processor,engine,task,arrays,meta,ids,pixels=False,cell=None):
    import numpy as np
    assert cell==json.loads((ROOT/'kit/reader/e193_contract.json').read_text())['main']['cells'][0]
    assert len(arrays)==64 and np.array_equal(arrays[::2],arrays[1::2])
    assert meta['frames_indices']==[i for i in task['source_frame_indices'] for _ in range(2)]
    value=dict(example_id=task['example_id'],benchmark=task['benchmark'],prompt_equal=True)
    if pixels:value['pixels']=dict(pass_=True,**{'pass':True})
    return value

class LocalLoop(asyncio.SelectorEventLoop):
    def _make_self_pipe(self):pass
    def _close_self_pipe(self):pass
    def _write_to_self(self):pass
async def local_thread(fn,*args,**kwargs):return fn(*args,**kwargs)

with patch('asyncio.events.new_event_loop',LocalLoop),patch('asyncio.to_thread',local_thread),\
     patch.object(X,'stage_assets',assets),patch.object(direct,'check_export',return_value=dict(status='VERIFIED')),\
     patch.object(stage,'prepare',return_value=work/'model'),patch.object(token_audit,'load_tokenizer',return_value=Processor.tokenizer),\
     patch.object(parity,'compare',compare):
    X.run(cfg,reader=ROOT/'kit/reader',runtime=runtime)
for name in ('think_settings','budget','budget_merge'):
    module=sys.modules[name]
    assert Path(module.__file__).read_bytes()==(ROOT/'kit/reader/evaluator'/(name+'.py')).read_bytes()
    for value in vars(module).values():
        if isinstance(value,types.FunctionType) and value.__module__==name:
            assert 'spread' not in value.__code__.co_consts, name
result=[json.loads(l) for l in (work/'r/a7/ITEMS.jsonl').read_text().splitlines()]
assert len(result)==4 and all(r['score']==1 for r in result),result
sys.path.insert(0,str(ROOT))
from tools.item_ids import decode_inventories, load_map
mapping=load_map()
decode_inventories(work/'r')
decoded=[json.loads(l) for l in (work/'r/a7/ITEMS.jsonl').read_text().splitlines()]
assert [r['id'] for r in decoded]==[mapping[r['id']]['id'] for r in result]
assert all(r['source_qid'] and r['source_line'] for r in decoded)
for arm in ('0','budget_2048/0','budget_4096/0'):
    directory=work/'r/a7/a0/results'/arm
    assert (directory/'items_a0.jsonl').is_file()
    summary=json.loads((directory/'summary_a0.json').read_text())
    for record in map(json.loads,(directory/'items_a0.jsonl').read_text().splitlines()):
        assert record['layout']=='duplicate' and record['frames']==32
    assert summary['parity_pass']
    assert summary['benchmarks']['devrows']['missing']==0
value=dict(status='PASS',items=4,work=str(work),candidate_reader=True,accepted_pinned_runtime=True,actual_worker=True,actual_budget_derivation=True,
 actual_mergers=True,actual_rgb=True,trained_duplicate_64_frames=True,unpatched_layout_modules=True,logical_ids_on_trinity=True,fake_engine=True,fake_model=True,fake_parity_probe=True)
(ROOT/'evidence/RUNTIME_FIXTURE.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
