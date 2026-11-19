"""Original/default-OFF production launcher bytes, including real code hashes."""
import hashlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
import uuid
from contextlib import redirect_stdout
from unittest.mock import patch

SRC=Path(__file__).resolve().parents[2]
L=SRC.parent.parent
INPUT=Path(os.environ['READ_INPUT_SRC'])

class RefuseExtensions(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if ('read_cache' in fullname or fullname in tuple('a'+str(i) for i in range(11))+('u0',) or fullname.startswith('u0.')):
            raise AssertionError('OFF attempted extension import: '+fullname)


def generator_factory(export,artifact,items,**kwargs):
    def generate(item):
        return dict(text='</think> 1',tokens=[1],finish='eos',scale=None,
                    heads={'pose9':[[0.]*9],'gravity':[[0.,0.,1.]]},
                    calls={'records':[],'calls':{},'unserved':{}},scores={'answer':1.})
    return generate


def child(source,root):
    sys.path[:0]=[str(source),str(source/'b'),str(INPUT/'tree'),str(INPUT)]
    sys.meta_path.insert(0,RefuseExtensions())
    import torch
    torch.set_num_threads(8)
    from e2e_reader import parity
    from h1eval.h10 import launch
    from h1eval.items import digest
    from datetime import datetime,timezone
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return cls(2026,11,19,0,0,0,tzinfo=timezone.utc)
    counter=iter(range(100000))
    out=root/'output'
    args=types.SimpleNamespace(items=str(root/'items.json'),shard='0/1',types=None,arms='tower',modes='none',
          reader_root=str(SRC/'b'),reader_entry=launch.ENTRY,settings=str(root/'settings.json'),export=str(root/'export'),
          artifact_manifest=str(root/'artifact.json'),export_pin=str(root/'pin.json'),out=str(out),device='cpu',
          stop_at=None,finish_by=None,stop_file=None)
    captured=io.StringIO()
    with patch.object(launch.time,'perf_counter',side_effect=lambda:float(next(counter))), \
         patch.object(launch,'datetime',Clock),redirect_stdout(captured):
        result=launch.run(args,make_real=generator_factory)
    files={str(p.relative_to(out)):p.read_bytes().hex() for p in sorted(out.rglob('*')) if p.is_file()}
    env=json.loads((out/'environment.json').read_text())
    expected_hashes=('reader_sha256','maker_sha256','evaluator_code_sha256','expected_calls_sha256','r0_code_sha256',
                     'parity_code_sha256','settings_sha256','mapping_sha256')
    assert all(len(env['binding'][k])==64 for k in expected_hashes)
    assert not any('read_cache' in k or k=='a8' or k.startswith('u0') for k in sys.modules)
    # Exercise the production make_real initializer with poisoned new settings.
    # Any new import is rejected by RefuseExtensions in this fresh process.
    from e2e_reader import parity
    class PoisonSettings(dict):
        def get(self,key,*args):
            if key.startswith('read_'):raise AssertionError('OFF parsed new settings: '+key)
            return super().get(key,*args)
        def __getitem__(self,key):
            if key.startswith('read_'):raise AssertionError('OFF parsed new settings: '+key)
            return super().__getitem__(key)
        def __contains__(self,key):
            if key.startswith('read_'):raise AssertionError('OFF parsed new settings: '+key)
            return super().__contains__(key)
    class Artifact:
        def __init__(self,*args,**kwargs):pass
        def verify(self):return self
    class Generator:
        def __init__(self,*args,**kwargs):pass
    runtime=types.ModuleType('evalpath.runtime');runtime.prompt_batch=lambda *args:None
    package=types.ModuleType('evalpath');package.runtime=runtime
    settings=PoisonSettings(arm='own_depth',frames_json={'captures':{}},dense_manifest={'captures':{}},
              perception_memo='off',perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
    from contextlib import ExitStack
    with ExitStack() as stack:
        stack.enter_context(patch.dict(sys.modules,{'evalpath':package,'evalpath.runtime':runtime}))
        replacements=dict(Artifact=Artifact,install=lambda *a:None,
            load_native=lambda *a,**k:(object(),types.SimpleNamespace(tokenizer=object(),_routing_tokens={'ids':{}}),
                                      {'config':{},'export':{'frame_layout':'spread'}}),
            install_hook=lambda *a:object(),CallHook=lambda *a:object(),
            ParityGenerator=Generator,policy=lambda:object())
        for name,value in replacements.items():stack.enter_context(patch.object(parity,name,value))
        parity.make_real('unused',{'root':'unused','name':'u0','sha256':'0'*64},[],
                         perception_factory=lambda **kwargs:None,settings=settings)
    assert not any('read_cache' in k or k=='a8' or k.startswith('u0') for k in sys.modules)
    print(json.dumps(dict(files=files,stdout=captured.getvalue(),result=result,hashes={k:env['binding'][k] for k in expected_hashes}),sort_keys=True))


class OffContractTests(unittest.TestCase):
    def test_every_output_byte_and_source_hash_matches_original(self):
        root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True)
        sys.path[:0]=[str(INPUT),str(INPUT/'tree')]
        from h1eval.items import digest
        sample=json.loads((SRC/'u0/tests/u0.json').read_text())
        sample['items']=sample['items'][:3];sample['count']=3;sample['r0_check']['checked']=3
        sample['item_set_sha256']=digest(sample['items'])
        sample['r0_check']['pin']['path']=str(INPUT/'auth/R0_ROOMS.txt')
        (root/'items.json').write_text(json.dumps(sample))
        (root/'pin.json').write_text(json.dumps({'lineage':'SFT','step':600}))
        artifact={'root':str(root/'export'),'name':'u0','sha256':'0'*64}
        (root/'artifact.json').write_text(json.dumps(artifact))
        (root/'export').mkdir();(root/'export/u0').write_bytes(b'fixture')
        # Real reviewed binding/mapping uses tiny manifests and unopened frame paths.
        (root/'tasks.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in sample['items']))
        captures={};dense={}
        for row in sample['items']:
            anchors=row.get('source_frame_indices',list(range(32)))
            frames=[{'index':index,'path':str(number)+'.png','sha256':'0'*64}
                    for number,index in enumerate(anchors)]
            captures[row['native']]={'native':row['native'],'frames':frames,'anchor_indices':anchors,
                'timestamps':list(range(32)),'fps':row.get('fps',1.),'total_num_frames':row.get('total_num_frames',32)}
            dense[row['native']]={'native':row['native'],'frames':frames,'anchor_slots':list(range(32))}
        (root/'frames.json').write_text(json.dumps({'captures':captures}))
        (root/'dense.json').write_text(json.dumps({'captures':dense}))
        settings={'export_dir':str(root/'export'),'artifact_manifest':str(root/'artifact.json'),
                  'tasks':[str(root/'tasks.jsonl')],'frames_json':str(root/'frames.json'),
                  'dense_manifest':str(root/'dense.json'),'frames_root':str(root/'pixels'),
                  'perception_memo':'off','perception_memo_modules':['g3t'],'perception_memo_verify_ids':[],
                  'stage1_select_rule':'null_argmax'}
        (root/'settings.json').write_text(json.dumps(settings))
        results=[]
        for index,source in enumerate((INPUT,SRC)):
            process=subprocess.run([sys.executable,'-I','-s','-B',__file__,'--child',str(source),str(root)],
                                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertEqual(process.returncode,0,process.stderr)
            results.append(process.stdout.encode())
            (root/'output').rename(root/('saved'+str(index)))
        self.assertEqual(results[0],results[1])
        receipt=json.loads(results[0]);self.assertGreaterEqual(len(receipt['files']),3)
        proof=json.dumps({'passed':True,'files':list(receipt['files']),
              'source_hashes':receipt['hashes'],'exclusions':[],'clock':'controlled; no timing fields removed',
              'production_launcher':True,'model_generation':'CPU fixture'},indent=2)+'\n'
        (root/'byte_comparison.json').write_text(proof)
        if os.environ.get('READ_OFF_RECEIPT'):Path(os.environ['READ_OFF_RECEIPT']).write_text(proof)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),Path(sys.argv[3]))
    else:unittest.main(verbosity=2)
