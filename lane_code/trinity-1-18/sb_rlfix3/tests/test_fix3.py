"""Regressions for the replay coverage, loader, INPUTS, refusal, resume and launcher contracts."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import torch
from rl_on_n import provenance as P
from rl_on_n import serving
from rl_on_n.serving import (load_binding, reader_runtime, require_replay, default_binding, PINS, PAYLOAD,
                             perception_pins, require_perception_pins, build_reader)
from rl_on_n.replay import (COUNTS, REQUIRED, DEVICE, export_identity, require_scratch, require_interpreter,
                            require_card, matched_items, append_item, selection)
from rl_on_n.reward import score
from rl_on_n.rollout import sample, SamplingProcessor
from rl_on_n.train import load_export, prompt_inputs, PromptRefusal
from rl_on_n.pool import RoomGate
from test_kit import ROOT, Tokenizer

KIT=Path(__file__).resolve().parents[1]
TMP=KIT/'out/tmp/fix3'
CODE=('rollout.py','serving.py','adapters.py','replay.py','choice.py','train.py')
BASE=ROOT.parents[1]/'work/build18/inputs'


def export_fixture(root,tag='m200'):
    """A restored export directory whose RESTORE.json names one original identity."""
    directory=root/('export_'+tag);directory.mkdir(parents=True,exist_ok=True)
    original={n:dict(path=f'/scratch/fixture/{tag}/{n}',sha256=hashlib.sha256((tag+n).encode()).hexdigest())
              for n in ('artifact','heads','full_weights','config')}
    (directory/'RESTORE.json').write_text(json.dumps(dict(original=original)))
    return directory


class ReplayGate(unittest.TestCase):
    """require_replay accepts only a full PASS receipt of the training export."""
    @classmethod
    def setUpClass(cls):
        cls.root=TMP/'gate';cls.root.mkdir(parents=True,exist_ok=True)
        cls.export=export_fixture(cls.root)
    def receipt(self,label,**changes):
        results=[]
        for group,n in COUNTS.items():
            ids=REQUIRED.get(group) or tuple(f'{group}_{i}' for i in range(n))
            results+=[dict(id=i,group=group,match=True) for i in ids]
        value=dict(status='PASS',counts=dict(COUNTS),mismatches=[],export_pin_sha256=PINS['export_pin'][1],
                   tree_root=str(ROOT.resolve()),export_identity=export_identity(self.export),results=results,
                   input_sha256={str(KIT/'overlay/rl_on_n'/n):P.sha(KIT/'overlay/rl_on_n'/n) for n in CODE})
        for key,change in changes.items():value[key]=change(copy.deepcopy(value[key])) if callable(change) else change
        path=self.root/f'receipt_{label}.json';path.write_text(json.dumps(value));return P.pin(path)
    def refuses(self,pattern,pin,export=None):
        with self.assertRaisesRegex(ValueError,pattern):require_replay(pin,ROOT,export or self.export)
    def test_full_pass_receipt_is_accepted(self):
        self.assertEqual(sum(COUNTS.values()),26)
        require_replay(self.receipt('pass'),ROOT,self.export)
    def test_missing_receipt_refuses(self):
        with self.assertRaisesRegex(ValueError,'MISSING greedy_replay'):require_replay(None,ROOT,self.export)
    def test_failed_status_refuses(self):
        self.refuses('did not pass every required item',self.receipt('fail',status='FAIL'))
    def test_listed_mismatch_refuses(self):
        self.refuses('did not pass every required item',self.receipt('mismatch',mismatches=['vsi590k_042674']))
    def test_three_per_type_refuses(self):
        drop=lambda rs:[r for r in rs if r['id']!='camera_rotation_3']
        self.refuses('did not pass every required item',
                     self.receipt('three',counts=dict(COUNTS,camera_rotation=3),results=drop))
        self.refuses('results do not all match',self.receipt('short',results=drop))
    def test_unmatched_item_refuses(self):
        def unmatch(rs):rs[-1]['match']=False;return rs
        self.refuses('results do not all match',self.receipt('unmatched',results=unmatch))
    def test_gap_and_forced_close_items_are_required(self):
        for group in REQUIRED:
            counts={k:v for k,v in COUNTS.items() if k!=group}
            self.refuses('did not pass every required item',self.receipt('no_'+group,counts=counts,
                         results=lambda rs:[r for r in rs if r['group']!=group]))
            def swap(rs):
                for r in rs:
                    if r['group']==group:r['id']+='_other'
                return rs
            self.refuses('lacks its required '+group+' items',self.receipt('swap_'+group,results=swap))
    def test_other_export_or_tree_refuses(self):
        self.refuses('MISSING deployed-reader replay of the training export',self.receipt('pass'),
                     export_fixture(self.root,'n_export'))
        self.refuses('different N training tree',self.receipt('tree',tree_root='/scratch/other_tree'))
    def test_changed_code_refuses(self):
        def change(pins):pins[str(KIT/'overlay/rl_on_n/train.py')]='0'*64;return pins
        self.refuses('MISSING or changed pinned input',self.receipt('code',input_sha256=change))


def artifact_fixture(root):
    """A tiny verified artifact with the deployed basenames of every frozen perception file."""
    load_binding()
    from e2e_reader.artifact import build_manifest, write_manifest
    layout=dict(checkpoint=('checkpoint',['ckpt/model.safetensors']),tokenizer=('tokenizer',['tok/tokenizer.json']),
                g3t=('g3t',['g/config.json','g/model.safetensors']),sam3=('sam3',['k/sam3.pt','k/SAM3_RECEIPT.json']),
                selector_head=('selector_head',['h/selector_head.json','h/selector_head.safetensors']))
    for _,rels in layout.values():
        for rel in rels:
            path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture '+rel)
    manifest=build_manifest(root,layout)
    path,sha=write_manifest(root,manifest)
    roots=dict(reader=str(PAYLOAD/'b/e2e_reader'),tree=str(PAYLOAD/'tree'),heads=str(PAYLOAD/'b/heads'),
               runner=str(PAYLOAD/'b/parity_kit'))
    spec=root/'binding.json';spec.write_text(json.dumps(dict(root=str(root),name=path.name,sha256=sha,code_roots=roots)))
    pins={c:{Path(e['rel']).name:e['sha256'] for e in manifest['components'][c]['files']} for c in serving.PERCEPTION}
    return manifest,P.pin(spec),pins


class Perception(unittest.TestCase):
    """The verified artifact must carry A4's INPUTS.json bytes for G3T, SAM 3 and the selector."""
    @classmethod
    def setUpClass(cls):
        cls.settings=load_binding()
        cls.root=TMP/'artifact';shutil.rmtree(cls.root,ignore_errors=True)
        cls.manifest,cls.spec,cls.fixture_pins=artifact_fixture(cls.root)
        cls.settings_fixture=dict(cls.settings,selector_head=str(cls.root/'h'),
            sam3=dict(cls.settings['sam3'],checkpoint_path=str(cls.root/'k/sam3.pt'),
                      receipt_path=str(cls.root/'k/SAM3_RECEIPT.json')))
    def binding(self):
        return dict(default_binding(),artifact_manifest=self.spec)
    def test_inputs_pin_two_files_per_component(self):
        pins=perception_pins(default_binding())
        inputs=P.load(serving.A4/PINS['inputs'][0])
        recorded={spec['sha256'] for spec in inputs['files'].values()}
        self.assertEqual({k:sorted(v) for k,v in pins.items()},
                         dict(g3t=['config.json','model.safetensors'],sam3=['SAM3_RECEIPT.json','sam3.pt'],
                              selector_head=['selector_head.json','selector_head.safetensors']))
        self.assertTrue(all(sha in recorded for files in pins.values() for sha in files.values()))
    def test_manifest_must_carry_inputs_bytes(self):
        pins=perception_pins(default_binding())
        manifest={'components':{c:{'files':[dict(rel='d/x/'+n,sha256=s) for n,s in files.items()]} for c,files in pins.items()}}
        manifest['components']['sam3']['files'].append(dict(rel='d/s/assets/bpe.txt.gz',sha256='0'*64))
        require_perception_pins(manifest,pins)
        for component,name in (('g3t','model.safetensors'),('sam3','sam3.pt'),('selector_head','selector_head.safetensors')):
            changed=copy.deepcopy(manifest)
            for entry in changed['components'][component]['files']:
                if entry['rel'].endswith('/'+name):entry['sha256']='f'*64
            with self.assertRaisesRegex(ValueError,f'Artifact {component}/{name} differs from A4 INPUTS.json'):
                require_perception_pins(changed,pins)
            missing=copy.deepcopy(manifest)
            missing['components'][component]['files']=[e for e in missing['components'][component]['files']
                                                       if not e['rel'].endswith('/'+name)]
            with self.assertRaisesRegex(ValueError,'differs from A4 INPUTS.json: None'):require_perception_pins(missing,pins)
    def test_build_reader_refuses_other_perception_bytes(self):
        with patch('rl_on_n.serving.load_binding',return_value=self.settings_fixture), \
             patch('e2e_reader.real.real_perception') as perception:
            with self.assertRaisesRegex(ValueError,'differs from A4 INPUTS.json'):
                build_reader(None,None,self.binding(),'cpu')
        perception.assert_not_called()
    def test_build_reader_binds_a4_signatures(self):
        # Signatures only: A4's real_perception, SAM 3 and selector loading stay unrun on CPU.
        with reader_runtime():
            import student_pilot.sam3_tower
            with patch('rl_on_n.serving.load_binding',return_value=self.settings_fixture), \
                 patch('rl_on_n.serving.perception_pins',return_value=self.fixture_pins), \
                 patch('student_pilot.sam3_tower.Sam3Tower',autospec=True) as tower, \
                 patch('e2e_reader.parity._head',autospec=True) as head, \
                 patch('e2e_reader.real.real_perception',autospec=True) as perception:
                reader=build_reader(None,None,self.binding(),'cpu')
        self.assertTrue(reader['artifact'].verified)
        tower.assert_called_once_with(dict(self.settings_fixture['sam3'],device='cpu'))
        head.assert_called_once_with(reader['artifact'],str(self.root/'h'),'selector_head')
        perception.assert_called_once_with(reader['artifact'],device='cpu',stage1_select_rule='candidates_argmax',
            perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
            sam3_tower=tower.return_value,selector_head=head.return_value)
        self.assertIs(reader['perception'],perception.return_value)
    def test_local_a4_staging_carries_inputs_bytes(self):
        spec=Path(self.settings['artifact_manifest'])
        if not spec.is_file():self.skipTest('A4 artifact staging absent on this node')
        spec=json.loads(spec.read_text());manifest=json.loads((Path(spec['root'])/spec['name']).read_text())
        require_perception_pins(manifest,perception_pins(default_binding()))


class Payload(unittest.TestCase):
    def test_one_flipped_payload_byte_refuses(self):
        load_binding()
        import e2e_reader.real
        farm=(TMP/'payload').resolve();shutil.rmtree(farm,ignore_errors=True)
        for path in PAYLOAD.rglob('*'):
            if path.is_file():
                target=farm/path.relative_to(PAYLOAD);target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(path)
        tampered=farm/'b/e2e_reader/real.py';data=bytearray(tampered.read_bytes());tampered.unlink()
        data[len(data)//2]^=1;tampered.write_bytes(bytes(data))
        paths=list(sys.path)
        try:
            with patch.object(serving,'PAYLOAD',farm),patch.object(serving,'_VERIFIED',False):
                with self.assertRaisesRegex(ValueError,'MISSING or changed pinned input.*b/e2e_reader/real.py'):
                    load_binding()
        finally:
            sys.path[:]=paths
            for key in [k for k in P.INPUTS if k.startswith(str(farm))]:del P.INPUTS[key]
            shutil.rmtree(farm)


class Rewards(unittest.TestCase):
    def test_correct_answer_after_max_calls_scores_zero(self):
        prompt=dict(type='room_size_estimation',gt_answer='10',options=[])
        record=dict(text='room</think>10',calls=[],finish='eos')
        self.assertGreater(score(prompt,record,Tokenizer(),{prompt['type']:'direct'})['correct'],0)
        for changes in (dict(finish='max_calls'),dict(strict_no_answer=True)):
            r=score(prompt,dict(record,**changes),Tokenizer(),{prompt['type']:'direct'})
            self.assertEqual((r['total'],r['correct']),(0,0),changes)


class Sampling(unittest.TestCase):
    def test_reader_value_errors_refuse_but_alignment_errors_raise(self):
        load_binding()
        with reader_runtime():
            from student_pilot.geometry_profiles import GeometryError
        tok=SimpleNamespace(encode=lambda *a,**k:[],eos_token_id=1)
        for failure in (ValueError('no_scale_points'),GeometryError('reference_camera_up_opposes_gravity')):
            with patch('e2e_reader.real.generate_real',side_effect=failure), \
                 patch('rl_on_n.serving.budget',return_value=Mock()), patch('rl_on_n.rollout.align') as aligned:
                record=sample(Mock(),SimpleNamespace(tokenizer=tok),{},decode={})
            aligned.assert_not_called()
            self.assertEqual(record['finish'],'refused');self.assertIn(str(failure),record['refusal'])
        decoded=dict(tokens=[5],text='x',finish='eos',calls=dict(records=[]))
        with patch('e2e_reader.real.generate_real',return_value=decoded), patch('rl_on_n.serving.budget',return_value=Mock()), \
             patch('rl_on_n.rollout.align',side_effect=ValueError('kit misalignment')):
            with self.assertRaisesRegex(ValueError,'kit misalignment'):
                sample(Mock(),SimpleNamespace(tokenizer=tok),{},decode={})
    def test_behaviour_logp_is_tempered(self):
        class Budget:
            forced_tokens=0
            def __call__(self,ids,logits):return logits
        s=SamplingProcessor(Budget(),seed=3,temperature=.7)
        logits=torch.tensor([[0.,1.,2.,3.]]);s([],logits);token=s.chosen[0]
        self.assertAlmostEqual(s.logp_tempered[0],float(torch.log_softmax(logits[0]/.7,-1)[token]),places=6)
        self.assertAlmostEqual(s.logp_raw[0],float(torch.log_softmax(logits[0],-1)[token]),places=6)
        self.assertGreater(abs(s.logp_tempered[0]-s.logp_raw[0]),1e-3)


class GateLayers(unittest.TestCase):
    """Each room-gate layer refuses on its own, with the other layers disabled."""
    @classmethod
    def setUpClass(cls):
        cls.gate=RoomGate(P.load(BASE/'config.json'))
        reserve=BASE/'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3.json'
        cls.reserve=sorted(n.strip() for n in reserve.read_text().splitlines() if n.strip())
        cls.withheld=sorted(P.load(ROOT/'student_pilot/r2_withheld.json')['rooms'])
    def row(self,name):
        ds,scene=name.split('/',1)
        return dict(qid='probe',dataset=ds,scene=scene,question_type='object_counting',answer='2',
                    student_input=dict(question='How many chairs?',frame_indices=list(range(32))))
    def test_reserve_layer_alone(self):
        with patch.object(self.gate.rooms,'admit'):
            for name in self.reserve[:20]:
                with self.assertRaisesRegex(ValueError,'r0_room_refused:rl'):self.gate.admit(self.row(name))
    def test_withheld_layer_alone(self):
        refused=0
        with patch.object(self.gate.rooms,'admit'),patch.object(self.gate.reserve,'check'), \
             patch.object(self.gate.removals,'assert_clean'),patch.object(self.gate.exclusions,'excluded',return_value=False):
            for name in self.withheld[:20]:
                with self.assertRaisesRegex(ValueError,'RL_WITHHELD_ROOM_REFUSED'):self.gate.admit(self.row(name))
                refused+=1
        self.assertEqual(refused,min(20,len(self.withheld)))


class Loader(unittest.TestCase):
    """Training loads and prompts the policy with A4's deployed functions."""
    def test_load_export_calls_a4_load_native(self):
        root=TMP/'loader';root.mkdir(parents=True,exist_ok=True)
        restore=root/'export/RESTORE.json';restore.parent.mkdir(exist_ok=True);restore.write_text('{}')
        config=root/'config.json';config.write_text('{}');seen={}
        def native(export_dir,*,device,settings,artifact=None):
            import student_pilot
            seen.update(export_dir=export_dir,device=device,settings=settings,tree=student_pilot.__file__)
            return 'model','processor',dict(config={'tool_mode_flag':False,'source':'loader'})
        load_binding()
        import e2e_reader.parity
        with patch('e2e_reader.parity.load_native',side_effect=native):
            model,processor,info=load_export(P.pin(restore),P.pin(config),'cpu')
        self.assertEqual((model,processor,info['config']['source']),('model','processor','loader'))
        self.assertEqual((seen['export_dir'],seen['device']),(str(restore.parent),'cpu'))
        self.assertEqual((seen['settings']['config'],seen['settings']['export_dir'],seen['settings']['tree']),
                         (str(config),str(restore.parent),str(PAYLOAD/'tree')))
        self.assertTrue(seen['tree'].startswith(str(PAYLOAD/'tree')))
        with patch('e2e_reader.parity.load_native',return_value=('m','p',dict(config={'tool_mode_flag':True}))):
            with self.assertRaisesRegex(ValueError,'unflagged config'):load_export(P.pin(restore),P.pin(config),'cpu')
    def test_prompt_inputs_use_a4_prompt_batch(self):
        load_binding();seen=[]
        with reader_runtime():
            import evalpath.runtime as runtime
            from student_pilot.tower_errors import TowerError
        from student_pilot.tower_errors import TowerError as NativeTowerError
        self.assertTrue(runtime.__file__.startswith(str(PAYLOAD/'tree')))
        self.assertIsNot(TowerError,NativeTowerError)
        def build(processor,row,config,mode):
            seen.append((row,config,mode));return dict(input_ids=torch.ones(1,2,dtype=torch.long),kind='routed')
        with patch.object(runtime,'prompt_batch',side_effect=build):
            batch=prompt_inputs('processor',{'qid':'row'},{'source':'loader'},'cpu')
        self.assertEqual(seen,[({'qid':'row'},{'source':'loader'},'routed')])
        self.assertEqual((batch['kind'],batch['input_ids'].device.type),('routed','cpu'))
        with patch.object(runtime,'prompt_batch',side_effect=TowerError('fixture')):
            with self.assertRaisesRegex(PromptRefusal,'TowerError: fixture'):prompt_inputs('p',{},{},'cpu')
        with patch.object(runtime,'prompt_batch',side_effect=ValueError('Prompt exhausts context')):
            with self.assertRaises(ValueError) as caught:prompt_inputs('p',{},{},'cpu')
        self.assertNotIsInstance(caught.exception,PromptRefusal)


class ReplayHelpers(unittest.TestCase):
    def test_card_scratch_and_interpreter(self):
        require_card(DEVICE)
        with self.assertRaisesRegex(ValueError,'NVIDIA H100 80GB HBM3'):require_card('NVIDIA A100-SXM4-80GB')
        require_scratch(dict(out=str(TMP)))
        for path in ('/home/jjyeung/x','/data2/x','/tmp/x'):
            with self.assertRaisesRegex(ValueError,'must be under /scratch'):require_scratch(dict(path=path))
        link=TMP/'tmp_link';link.unlink(missing_ok=True);link.symlink_to('/tmp')
        with self.assertRaisesRegex(ValueError,'must be under /scratch'):require_scratch(dict(link=str(link)))
        link.unlink()
        require_interpreter()
        with patch.object(sys,'executable','/home/jjyeung/env/bin/python'):
            with self.assertRaisesRegex(ValueError,'RL_PYTHON must be under /scratch'):require_interpreter()
    def test_item_journal_resume(self):
        path=TMP/'items.jsonl';path.unlink(missing_ok=True)
        append_item(path,dict(key='k',id='a',match=True));append_item(path,dict(key='k',id='b',match=False))
        append_item(path,dict(key='other',id='c',match=True))
        with path.open('a') as stream:stream.write('{"key": "k", "id": "d", "ma')
        self.assertEqual(set(matched_items(path,'k')),{'a'})
        self.assertEqual(matched_items(TMP/'absent.jsonl','k'),{})
    def test_replay_uses_the_training_loader(self):
        tree=ast.parse((KIT/'scripts/greedy_replay.py').read_text())
        imported={a.name for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) for a in n.names}
        called={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertNotIn('load_native',imported);self.assertNotIn('prompt_batch',imported)
        self.assertLessEqual({'load_export','prompt_inputs','require_card','require_scratch','require_interpreter',
                              'matched_items','append_item'},called)


class GreedyReplayRun(unittest.TestCase):
    """greedy_replay.main on CPU with mocked CUDA, weights and decoding; real selection, mapping and receipt."""
    @classmethod
    def setUpClass(cls):
        cls.root=TMP/'replay_run';shutil.rmtree(cls.root,ignore_errors=True);cls.root.mkdir(parents=True)
        cls.export=export_fixture(cls.root)
        cls.config=cls.root/'config.json';cls.config.write_text('{}')
        _,cls.spec,_=artifact_fixture(cls.root/'artifact')
        spec=importlib.util.spec_from_file_location('greedy_replay_fixture',KIT/'scripts/greedy_replay.py')
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
        selected=selection();cls.expected={r['item']['id']:r['expected'] for r in selected}
        # The real mapping runs once; the patched bind_item below would otherwise feed it.
        with reader_runtime():
            import h1eval.h10.parity_adapter as adapter
            cls.mapped=adapter.map_items([r['item'] for r in selected],load_binding())
        cls.adapter=adapter
    def run_main(self,out,wrong=(),crash_after=None):
        info=dict(config={'source':'loader'});decoded=[];module=self.module
        def prompts(processor,row,config,device):
            if config is not info['config']:raise AssertionError('replay prompt config is not the loader info config')
            return {}
        def decode(model,processor,batch,*,decode,greedy):
            self.assertTrue(greedy)
            if crash_after is not None and len(decoded)==crash_after:raise RuntimeError('fixture interruption')
            identifier=decode['id'];decoded.append(identifier);output=dict(self.expected[identifier])
            if identifier in wrong:output['tokens']=output['tokens'][:-1]
            return output
        pin=dict(preparation=dict(config=dict(sha256=P.sha(self.config))))
        argv=['greedy_replay.py','--export-dir',str(self.export),'--config',str(self.config),
              '--artifact-binding',self.spec['path'],'--artifact-binding-sha256',self.spec['sha256'],'--out',str(out)]
        with patch.object(sys,'argv',argv),patch.dict(os.environ,{'REPLAY_CARD':'3'}), \
             patch('torch.cuda.is_available',return_value=True),patch('torch.cuda.device_count',return_value=1), \
             patch('torch.cuda.get_device_name',return_value=DEVICE), \
             patch.object(module,'check_export',return_value=pin), \
             patch.object(self.adapter,'map_items',return_value=self.mapped), \
             patch('e2e_reader.parity.bind_item',return_value=dict(row=dict(student_input={}),
                                                                   frames=dict(native_frames=[],dense_indices=[]))), \
             patch('rl_on_n.train.load_export',return_value=('model','processor',info)) as load, \
             patch('rl_on_n.train.prompt_inputs',side_effect=prompts), \
             patch('rl_on_n.adapters.install',return_value=['adapter']), \
             patch.object(module,'build_reader',return_value={}), \
             patch('rl_on_n.rollout.native_kwargs',side_effect=lambda processor,prompt,batch,reader:dict(id=prompt['prompt_id'])), \
             patch('rl_on_n.rollout.sample',side_effect=decode):
            module.main()
        return load,decoded
    def test_interrupted_replay_resumes_and_passes_the_training_gate(self):
        out=self.root/'GREEDY_REPLAY.json'
        with self.assertRaisesRegex(RuntimeError,'fixture interruption'):self.run_main(out,crash_after=10)
        self.assertFalse(out.exists())
        self.assertEqual(len(out.with_suffix('.items.jsonl').read_text().splitlines()),10)
        load,decoded=self.run_main(out)
        load.assert_called_once();self.assertEqual(len(decoded),16)
        receipt=P.load(out)
        self.assertEqual((receipt['status'],receipt['counts'],len(receipt['results'])),('PASS',COUNTS,26))
        self.assertTrue(receipt['command'].startswith('bash scripts/run_greedy_replay.sh 3 --export-dir'))
        require_replay(P.pin(out),ROOT,self.export)
        load,decoded=self.run_main(out)
        load.assert_not_called();self.assertEqual(decoded,[])
        with self.assertRaisesRegex(ValueError,'MISSING deployed-reader replay'):
            require_replay(P.pin(out),ROOT,export_fixture(self.root,'n_export'))
    def test_one_wrong_gap_token_fails_the_gate(self):
        out=self.root/'GREEDY_REPLAY_wrong.json'
        with self.assertRaisesRegex(SystemExit,'FAILED'):self.run_main(out,wrong=('vsi590k_042690',))
        receipt=P.load(out)
        self.assertEqual((receipt['status'],receipt['mismatches']),('FAIL',['vsi590k_042690']))
        with self.assertRaisesRegex(ValueError,'did not pass every required item'):require_replay(P.pin(out),ROOT,self.export)


class Launcher(unittest.TestCase):
    """scripts/run_greedy_replay.sh with fake nvidia-smi, hostname, vnice and interpreter."""
    @classmethod
    def setUpClass(cls):
        cls.bin=TMP/'launcher_bin';shutil.rmtree(cls.bin,ignore_errors=True);cls.bin.mkdir(parents=True)
        fakes={'nvidia-smi':'[[ $FAKE_USED == fail ]] && exit 1; echo "$FAKE_USED"',
               'hostname':'echo "$FAKE_HOST"',
               'vnice':'echo "$*" > "$FAKE_OUT.vnice"; exec "$@"',
               'python':'{ echo "args:$*"; echo "cuda:$CUDA_VISIBLE_DEVICES"; echo "nice:$(nice)";'
                        ' echo "parent:$(ps -o comm= -p $PPID)"; } > "$FAKE_OUT"'}
        for name,body in fakes.items():
            path=cls.bin/name;path.write_text('#!/bin/bash\n'+body+'\n');path.chmod(0o755)
    def launch(self,card,used='17',host='orchard-community-4',python=None,args=('--export-dir','/scratch/x')):
        out=TMP/'launcher.out';out.unlink(missing_ok=True)
        env=dict(os.environ,PATH=f'{self.bin}:{os.environ["PATH"]}',FAKE_USED=used,FAKE_HOST=host,FAKE_OUT=str(out),
                 RL_PYTHON=python or str(self.bin/'python'),RL_VNICE=str(self.bin/'vnice'))
        p=subprocess.run(['bash','scripts/run_greedy_replay.sh',card,*args],cwd=KIT,env=env,capture_output=True,text=True,timeout=60)
        lines=dict(l.split(':',1) for l in out.read_text().splitlines()) if out.exists() else {}
        vnice=Path(str(out)+'.vnice')
        return p,lines,vnice
    def test_refusals(self):
        for card,used,python,code,message in (('a','17',None,2,'numeric'),('0','fail',None,2,'Cannot check'),
                                              ('0','',None,2,'Invalid memory'),('0','1025',None,3,'busy'),
                                              ('0','17','/tmp/python',2,'under /scratch')):
            p,lines,_=self.launch(card,used=used,python=python)
            self.assertEqual(p.returncode,code,p.stderr);self.assertIn(message,p.stderr);self.assertEqual(lines,{})
        p,lines,_=self.launch('0',host='trinity-1-18',args=('--export-dir','/scratch/a b'))
        self.assertEqual(p.returncode,2);self.assertIn('plain arguments',p.stderr)
    def test_idle_card_runs_niced_under_timeout(self):
        base=os.nice(0)
        p,lines,vnice=self.launch('3',used='1024')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(lines['args'],'-B scripts/greedy_replay.py --export-dir /scratch/x')
        self.assertEqual((lines['cuda'],lines['nice'],lines['parent']),('3',str(min(19,base+10)),'timeout'))
        self.assertFalse(vnice.exists())
        p,lines,vnice=self.launch('5',host='trinity-1-18')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(vnice.read_text().split(),['nice','-n','10',str(self.bin/'python'),'-B','scripts/greedy_replay.py',
                                                    '--export-dir','/scratch/x'])
        self.assertEqual((lines['cuda'],lines['parent']),('5','timeout'))
        vnice.unlink()
