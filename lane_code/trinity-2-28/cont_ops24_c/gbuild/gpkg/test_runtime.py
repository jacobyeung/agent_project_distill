import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import build
sys.path.insert(0,str(build.ROOT))
from gpkg.runtime import w as worker
from gpkg.runtime import c as capture
from join_capture import score


def temp():return Path(tempfile.mkdtemp(prefix='a',dir=build.ROOT/'work/tests'))
def mod(name,**kwargs):
    m=types.ModuleType(name);m.__dict__.update(kwargs);return m

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


class RuntimeTests(unittest.TestCase):
    def test_complete_and_partial_worker_with_doubles(self):
        refs=json.loads((build.ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
        for fail_after in (None,5):
            root=temp();cfg=dict(output=str(root/'r'),stop_file=str(root/'r/metadata/STOP'),settings=str(root/'0.json'))
            settings=dict(stage1_select_rule='candidates_argmax',perception_memo='verify',perception_memo_modules=['g3t'],
                          save_own_depth=False,export_dir='e',artifact_manifest='b',frames_json='0',dense_manifest='1')
            memo=types.SimpleNamespace(modules=frozenset(['g3t']));gen=types.SimpleNamespace(perception=types.SimpleNamespace(memo=memo))
            made=types.SimpleNamespace(generator=gen,load_info={'export':{'step':544}})
            adapter=mod('h1eval.h10.parity_adapter',settings_for=lambda *a:settings,prepare_runtime=lambda x:None,
                        artifact_spec=lambda x:{},make_capped_real=lambda *a,**k:made)
            caps={r['task']['native']:{'pin':r['mapping']['frame_binding_sha256']} for r in refs}
            native=mod('e2e_reader.parity',FRAMES='0',DENSE='1',_captures=lambda x:caps,
                       bind_item=lambda task,settings:{'id':task['id']})
            items=mod('h1eval.items',digest=lambda v:v['anchors']['pin'] if 'anchors' in v else build.canonical(v))
            cuda=types.SimpleNamespace(synchronize=lambda:None,reset_peak_memory_stats=lambda:None,
                                      max_memory_allocated=lambda:11,max_memory_reserved=lambda:22)
            modules={'orchard_h10':mod('orchard_h10'),'orchard_h10.common':mod('orchard_h10.common',write=write),
                     'h1eval':mod('h1eval'),'h1eval.h10':mod('h1eval.h10'),'h1eval.h10.parity_adapter':adapter,
                     'h1eval.items':items,'e2e_reader':mod('e2e_reader',parity=native),'e2e_reader.parity':native,
                     'torch':mod('torch',cuda=cuda)}
            seen=[]
            def replay(g,b,r):
                if fail_after is not None and len(seen)==fail_after:raise RuntimeError('fixture interruption')
                fresh=len(seen)>=150
                self.assertEqual(memo.modules,frozenset() if fresh else frozenset(['g3t']))
                seen.append(r['item_id'])
                calls=copy.deepcopy(r['calls'])
                if len(seen)==20:calls[0]['served']=not calls[0]['served']
                return dict(schema='ground-capture-v1',item_id=r['item_id'],capture=r['capture'],
                            source_indices=r['source_indices'],objects=[],geometry=None,calls=calls,answer_pass=False)
            with patch.dict(sys.modules,modules),patch.object(worker,'load_rows',return_value=refs),patch.object(worker,'replay',side_effect=replay):
                result=worker.run(cfg,100,clock=lambda:0)
            receipt=json.loads((root/'r/metadata/PARITY.json').read_text())
            with gzip.open(root/'c/0.gz','rt') as f:rows=list(map(json.loads,f))
            if fail_after is None:
                self.assertTrue(result['complete']);self.assertEqual(len(rows),160)
                self.assertEqual(seen[:150],[r['item_id'] for r in refs])
                self.assertEqual(seen[150:],[r['item_id'] for r in refs if r['calls']][:10])
                self.assertEqual(receipt['discrete_matches'],149);self.assertTrue(receipt['trusted'])
                receipt['trusted']=False;write(root/'r/metadata/PARITY.json',receipt);write(root/'gt.json',{})
                score(root/'c/0.gz',root/'r/metadata/PARITY.json',root/'gt.json',root/'joined.jsonl')
                joined=[json.loads(x) for x in (root/'joined.jsonl').read_text().splitlines()]
                self.assertEqual(len(joined),150);self.assertTrue(all(x['trusted'] is False for x in joined))
            else:
                self.assertFalse(result['complete']);self.assertEqual(len(rows),5)
                self.assertFalse(receipt['trusted']);self.assertIn('fixture interruption',receipt['failure'])
            self.assertEqual(receipt['capture_records'],len(rows))
            self.assertEqual(receipt['capture_sha256'],worker.sha(root/'c/0.gz'))

    def test_exact_capped_hook_and_single_prefill(self):
        import ast
        from contextlib import ContextDecorator
        class Context(ContextDecorator):
            def __enter__(self):return self
            def __exit__(self,*args):return False
        torch=mod('torch',nn=types.SimpleNamespace(Module=object),no_grad=Context)
        modules={'torch':torch,'e2e_reader':mod('e2e_reader'),
                 'h1eval':mod('h1eval'),'h1eval.h10':mod('h1eval.h10'),
                 'h1eval.scorers':mod('h1eval.scorers',metadata=lambda x:x),
                 'student_pilot':mod('student_pilot')}
        with patch.dict(sys.modules,modules):
            def definitions(path,names,ns):
                tree=ast.parse(path.read_text())
                nodes=[n for n in tree.body if getattr(n,'name',None) in names]
                exec(compile(ast.fix_missing_locations(ast.Module(nodes,type_ignores=[])),str(path),'exec'),ns)
            path=build.ROOT/'work/payload/b/e2e_reader/callhook.py'
            spec=importlib.util.spec_from_file_location('e2e_reader.callhook',path)
            hookmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(hookmod)
            sys.modules[hookmod.__name__]=hookmod
            tok=types.SimpleNamespace(convert_tokens_to_ids=lambda s:0,encode=lambda s,**kw:[1])
            pm=mod('e2e_reader.parity',CallHook=hookmod.CallHook,ParityGenerator=object)
            pm.make_real=lambda *a,**kw:types.SimpleNamespace(hook=pm.CallHook(tok,[]))
            sys.modules['e2e_reader'].parity=pm;sys.modules['e2e_reader'].real=mod('e2e_reader.real')
            adapter=mod('h1eval.h10.parity_adapter',PER_READ_CALL_CAP={'object_abs_distance':6})
            definitions(build.ROOT/'work/payload/h1eval/h10/parity_adapter.py',{'make_capped_real','MaxCalls'},adapter.__dict__)
            sys.modules[adapter.__name__]=adapter
            capped=adapter.make_capped_real().hook
            class Model:
                def register_forward_pre_hook(self,fn,**kw):
                    self.fn=fn
                    return types.SimpleNamespace(remove=lambda:None)
                def __call__(self):
                    self.fn(self,(),{})
                    return object()
            model=types.SimpleNamespace(model=types.SimpleNamespace(language_model=Model()));prefills=[]
            def prepare(m,*args,**kwargs):prefills.append(1);return m.model.language_model()
            sys.modules['student_pilot.carrier_c1_decode']=mod('student_pilot.carrier_c1_decode',_prepare_decode=prepare)
            sys.modules['student_pilot.ground_context']=mod('student_pilot.ground_context',closed_adapters=lambda f:f)
            audit=type('Audit',(Context,),{'__init__':lambda self,a:None,'report':lambda self:{'entries':self.entries}})
            sys.modules['e2e_reader.artifact']=mod('e2e_reader.artifact',Audit=audit)
            generate=mod('e2e_reader.generate')
            definitions(build.ROOT/'work/payload/b/e2e_reader/generate.py',{'EntryCounter'},generate.__dict__)
            sys.modules[generate.__name__]=generate
            sys.modules['e2e_reader'].stage1=types.SimpleNamespace(StageOne=object)
            sys.modules['e2e_reader'].grounding=object()
            cap=type('Capture',(Context,),{'__init__':lambda self,*a:None,'geometry':None,'objects':[]})
            responded=[]
            def server(call):responded.append(call);return 'status',{}
            perception=types.SimpleNamespace(lazy=lambda *a:({'ground':server},{}))
            gen=types.SimpleNamespace(model=model,processor=None,device='cpu',artifact=None,hook=capped,
                                      perception=perception,prompt_batch=lambda *a:{})
            ref=dict(item_id='a',capture='x',source_indices=list(range(32)),mapping={'dense_count':64},
                     calls=[{'call':'<ground obj="x" mode="box">'}]*6)
            bound={'row':{},'frames':{'anchor_indices':list(range(32)),'native_frames':[0]*64,'dense_indices':list(range(64))}}
            with patch.object(worker,'Capture',cap):row=worker.replay(gen,bound,ref)
            self.assertEqual(len(prefills),1);self.assertEqual(row['prefills'],1);self.assertEqual(row['decode_steps'],0)
            self.assertEqual(len(responded),5);self.assertEqual(len(row['calls']),6)
            self.assertFalse(row['calls'][-1]['served']);self.assertEqual(gen.hook.servers,{})

    def test_stopped_worker_does_not_load_weights(self):
        refs=json.loads((build.ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
        root=temp();marker=root/'r/metadata/STOP';marker.parent.mkdir(parents=True);marker.write_text('stop')
        modules={'orchard_h10':mod('orchard_h10'),'orchard_h10.common':mod('orchard_h10.common',write=write)}
        with patch.dict(sys.modules,modules),patch.object(worker,'load_rows',return_value=refs):
            result=worker.run(dict(output=str(root/'r'),stop_file=str(marker)),100,clock=lambda:0)
        self.assertEqual(result['completed'],0);self.assertIsNone(result['failure'])
        self.assertEqual(gzip.decompress((root/'c/0.gz').read_bytes()),b'')
        self.assertFalse(json.loads((root/'r/metadata/PARITY.json').read_text())['trusted'])


if __name__=='__main__':unittest.main()
