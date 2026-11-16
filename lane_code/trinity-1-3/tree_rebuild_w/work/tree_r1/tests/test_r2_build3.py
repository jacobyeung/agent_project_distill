"""Build-three refusal, execution and retained-row proofs on bounded CPU fixtures."""
from copy import deepcopy
import hashlib
import importlib
import inspect
import io
import json
import os
import sys
from pathlib import Path
import tarfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch
from student_pilot.p3_provenance import file_pin, load, write, digest
from tests.r2_init_fixture import INIT
from student_pilot import r2_openers as O
from launch_r2 import host as H, parent, build as B, bootstrap
from tests.test_r2_data_path import PROOFS, directory, LANE, TinyProcessor, fixture, manifest
from tests.test_r2_build import inputs, dense


class Embeddings(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = torch.nn.Embedding(8, 3)
        self.head = torch.nn.Linear(3, 8, bias=False)
        self.carrier_placement = 'a'
        self.frame_layout = 'duplicate'
        self.carrier_position_policy = 'native_v1'
        self.geometry_online = None
    def get_input_embeddings(self):
        return self.embed
    def get_output_embeddings(self):
        return self.head


def tiny_export(root):
    body=dict(schema='s1-run-seal-v1',tree_sha256='a'*64,config_sha256='b'*64,
              archive=dict(path='/tiny/model-boundary',sha256='c'*64))
    seal={**body,'sha256':digest(body)}
    artifact=dict(schema='carrier-c1-artifact-v1',r2_identity=dict(init=INIT),synthetic=True,
                  source_seal=seal,training_source_seal=seal,config_sha256='b'*64)
    raw=json.dumps(artifact).encode()
    (root/'donor.json').write_bytes(raw)
    values={'m544/artifact.json':raw,'m544/heads.pt':b'tiny','m544/full_weights/a':b'tiny'}
    with tarfile.open(root/'donor.tar','w') as tar:
        for key,value in values.items():
            member=tarfile.TarInfo(key);member.size=len(value);tar.addfile(member,io.BytesIO(value))
    return dict(init_archive=file_pin(root/'donor.tar'),
                init_members={k:hashlib.sha256(v).hexdigest() for k,v in values.items()},init_member_limit=4096)


class Build3(unittest.TestCase):
    def test_native_prepare_and_every_rank_encode(self):
        from student_pilot import carrier_c1_run as R
        from tests.test_r2_preparation import PreparationProof
        from launch_r2.entry import execute
        captured = []
        original = R.prepare
        def record(cfg):
            captured.append(deepcopy(cfg))
            return original(cfg)
        with patch.object(R, 'prepare', side_effect=record):
            PreparationProof().test_native_preparation_membership()
        cfg = captured[0]
        root = Path(cfg['preparation_output']).parent
        native = load(root/'stores/receipt.json')
        pose = load(cfg['streams']['pose']['path'])
        cfg = H.native_config(cfg, native, pose, root/'bridge')
        env = dict(S1_CPU_REHEARSAL='1', STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')}))
        with patch.dict(os.environ, env), patch.object(R,'processor_for_receipt',return_value=TinyProcessor()):
            receipt = execute(cfg,'p')
            self.assertEqual(receipt['r2_membership'],native['r2_membership'])
            cfg['preparation']=file_pin(Path(cfg['preparation_output'])/'receipt.json')
            first = execute(cfg,'c')
            second = R.dryrun(cfg,root/'dry.json',encode_only=True)
            third = H.encode_first(cfg,H.Guard(root))
            self.assertEqual({(r['rank'],r['stream']) for r in first},
                             {(rank,stream) for rank in range(4) for stream in native['streams']})
            self.assertEqual(first,second)
            self.assertEqual(len(first),len(third))
            # The reader still runs; only a GPU-labelled value is injected at
            # its return boundary to prove the CPU host rejects it.
            previous_profile=sys.getprofile()
            def labelled_gpu(frame,event,arg):
                if event=='return' and frame.f_code is R.Rows.get.__code__:
                    arg[0]['boundary_probe']=SimpleNamespace(is_cuda=True)
            try:
                sys.setprofile(labelled_gpu)
                with self.assertRaisesRegex(ValueError,'CPU boundary received a GPU tensor'):
                    H.encode_first(cfg,H.Guard(root))
                with self.assertRaisesRegex(ValueError,'Encoding-only admission requires CPU tensors'):
                    R.first_batch_check(cfg,range(4),root/'labelled.json',encode_only=True)
            finally:sys.setprofile(previous_profile)
            with self.assertRaisesRegex(ValueError,'CPU'):
                R.first_batch_check(cfg,range(4),root/'bad.json',encode_only=True,device='cuda')
            pose_row = json.loads((root/'pose/rows.jsonl').read_text())
            pose_row['qid'] = 'pose_second'
            second_pose = manifest(root/'pose_second',[pose_row],'pose',family='pose_second')
            manifests = [root/name/'MANIFEST.json' for name in ('pose','vqa','routing','pointing')] + [second_pose]
            pose_sources=[]
            for index,path in enumerate((manifests[0],second_pose)):
                source=root/('pose_source_'+str(index)+'.json')
                write(source,dict(synthetic=True,source=index))
                pose_sources.append(file_pin(source))
                path.write_text(json.dumps({**load(path),'pose_source_sha256':file_pin(source)['sha256']}))
            write(root/'REAL_ROW_INPUTS.json',dict(schema='r2-real-proof-inputs-v1',synthetic=True,
                  expected_families=['pose','vqa','routing','pointing','pose_second'],manifests=[file_pin(p) for p in manifests]))
            write(root/'proof.json',dict(rows_dir=str(root),sealed_meta_dir=str(root),synthetic=True))
            write(root/'count.json',dict(synthetic=True))
            write(root/'template.json',captured[0]);write(root/'pose_template.json',pose)
            packet=dict(manifests=[file_pin(p) for p in manifests],
                pose_sources=pose_sources,
                configuration=file_pin(root/'template.json'),pose_template=file_pin(root/'pose_template.json'),
                real_proof=file_pin(root/'proof.json'),counts=file_pin(root/'count.json'),output='ee000005')
            packet.update(tiny_export(root))
            write(root/'packet.json',packet)
            write(root/'k/launch.json',dict(config=dict(file=str(root/'template.json'),sha256=packet['configuration']['sha256'])))
            host_result=H.run_packet(root,file_pin(root/'packet.json'),full=False)
            self.assertEqual(host_result['boundary'],'CPU tensors before model forward')
            self.assertEqual(host_result['schema'],'r2-host-preparation-v1')
            self.assertFalse(host_result['full_store'])
            self.assertEqual(host_result['packet_digest'],digest(packet))
            self.assertEqual(len(host_result['metadata']['results']),5)
            with self.assertRaisesRegex(ValueError,'Synthetic'):
                H.run_packet(root,file_pin(root/'packet.json'),full=True)
        with self.assertRaisesRegex(ValueError,'Unknown'):execute({},'x')
        (PROOFS/'B3_NATIVE_JOB_PROOF.json').write_text(json.dumps(dict(
            producer='r2_materialize.materialize',preparation='carrier_c1_run.prepare/prepared',
            reader='carrier_c1_run.Rows.get',records=first,
            packet=file_pin(root/'packet.json'),
            synthetic_rgb=True,stand_ins=['tiny base-model metadata in native CPU rehearsal',
                'TinyProcessor/TinyTokenizer at the pretrained processor boundary'],
            boundary='CPU tensors before model forward',native_forward=False),indent=2)+'\n')

    def test_opener_export_keep_and_reset(self):
        from student_pilot import carrier_c1_run as R, full_ft
        root = directory()
        model = Embeddings()
        with torch.no_grad():
            model.embed.weight.copy_(torch.arange(24).reshape(8,3))
            model.head.weight.copy_(100+torch.arange(24).reshape(8,3))
        state = {n:p.detach().clone() for n,p in model.named_parameters()}
        full_ft.save_export({k:v.to(torch.bfloat16) for k,v in state.items()}, root/'f', {}, {})
        write(root/'artifact.json', dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm',
              r2_identity=dict(init=INIT),
              placement='a', frame_layout='duplicate', carrier_position_policy='native_v1', step=544,
              full_weights=file_pin(root/'f/full_weights.json')))
        processor = SimpleNamespace(tokenizer=SimpleNamespace(get_vocab=lambda:{str(i):i for i in range(8)}),
            _routing_tokens=dict(ids={'<move':7}, constituents={'<move':[1,2]}))
        spec = dict(artifact=file_pin(root/'artifact.json'), lm='full', heads=[])
        witness = dict(artifact_sha256=spec['artifact']['sha256'], lineage_sha256=INIT['artifact_sha256'], **O.vocabulary(processor))
        write(root/'v.json', witness)
        receipt = dict(r2_identity=dict(init=INIT),init_artifact=spec, routing_vocabulary=file_pin(root/'v.json'))
        for policy in ('keep', 'reset'):
            live = Embeddings()
            live.init_report = R.init_from_artifact(live, spec, part='lm')
            self.assertEqual(O.initialize(live, processor, {**receipt,'routing_opener_init':policy}),
                             'kept' if policy=='keep' else 'reset')
            for attr, name in ((live.embed,'embed.weight'),(live.head,'head.weight')):
                expected = state[name][7] if policy=='keep' else state[name][[1,2]].mean(0)
                self.assertTrue(torch.equal(attr.weight[7], expected))
        with self.assertRaisesRegex(ValueError,'Unknown'): O.initialize(live,processor,{'routing_opener_init':'x'})
        with self.assertRaisesRegex(ValueError,'Missing'): O.initialize(live,processor,dict(init_artifact=spec,routing_opener_init='keep'))
        (root/'v.json').write_text(json.dumps({**witness,'lineage_sha256':'f'*64}))
        with self.assertRaisesRegex(ValueError,'vocabulary'):
            O.initialize(live,processor,{**receipt,'routing_opener_init':'keep','routing_vocabulary':file_pin(root/'v.json')})
        with self.assertRaisesRegex(ValueError,'full warm'):
            O.initialize(Embeddings(),processor,dict(routing_opener_init='keep'))

    def test_four_stream_record_identity(self):
        base = LANE/'work/kit07ca49df_meta/m'
        result = B.build(base, directory()/'a', overrides=False, init_pin=INIT_PIN)
        self.assertTrue(all(item['identical'] for item in result))
        (PROOFS/'B3_PARENT_REPRO.json').write_text(json.dumps(result,indent=2)+'\n')
        cfg = load(base/'k/b02e4385.json')
        self.assertEqual(parent.layout_config(cfg,{},'four')['streams'],cfg['streams'])
        model = dict(streams={},mix=[],mdg={})
        self.assertEqual(parent.layout_config({},model,'five'),model)
        for value,layout in (({},'four'),({},'six')):
            with self.assertRaises(ValueError): parent.layout_config(value,{},layout)
        bad = directory(); (bad/'k').mkdir()
        write(bad/'k/1.json',{'0':'a'});write(bad/'k/a.json',model)
        with self.assertRaises(ValueError):parent.reproduce(bad,bad/'b')

    def test_init_delivered_archive_mapping(self):
        root = directory()
        members = {'m544/artifact.json':b'{}','m544/heads.pt':b'tiny stand-in', 'm544/full_weights/a':b'tiny stand-in'}
        def archive(name, values):
            path=root/name
            with tarfile.open(path,'w') as tar:
                d=tarfile.TarInfo('m544');d.type=tarfile.DIRTYPE;tar.addfile(d)
                for key, raw in values.items():
                    info=tarfile.TarInfo(key);info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
            return file_pin(path)
        pin=archive('a.tar',members)
        hashes={k:hashlib.sha256(v).hexdigest() for k,v in members.items()}
        result=H.stage_init(pin,root/'s',hashes,max_member_bytes=100)
        self.assertEqual(result['m544/heads.pt'],'ap/'+pin['sha256'][:16]+'/e/heads.pt')
        self.assertEqual(result['m544/artifact.json'],'ap/'+pin['sha256'][:16]+'/a/artifact.json')
        for key,relative in result.items():self.assertEqual((root/'s'/relative).read_bytes(),members[key])
        with self.assertRaisesRegex(ValueError,'Unadmitted'):H.stage_init(pin,root/'b',hashes,max_member_bytes=1)
        with self.assertRaisesRegex(ValueError,'sha256'):H.stage_init(pin,root/'c',{k:'0'*64 for k in hashes},max_member_bytes=100)
        with self.assertRaisesRegex(ValueError,'incomplete'):
            H.stage_init(archive('b.tar',{'m544/heads.pt':members['m544/heads.pt']}),root/'d',hashes,max_member_bytes=100)

    def test_cpu_resource_mutations(self):
        hashes=load(B.TREE/'launch_s1/b/wh.json')
        H.cpu_guard(['b/e.py','a15_cot_apabcdef'],{'CUDA_VISIBLE_DEVICES':''},hashes)
        for args,env,reason in [(['--gpus=1'],{},'GPU'),([] ,{'SLURM_GPUS_ON_NODE':'1'},'GPU'),
                               (['k/vsibench'],{},'Forbidden'),(['--x=qwen'],{},'Forbidden'),
                               ([],{'X':'geometry'},'Forbidden')]:
            with self.assertRaisesRegex(ValueError,reason):H.cpu_guard(args,env,hashes)
        now=[0.]; guard=H.Guard(directory(),wall=10,idle=2,limits={'vqa':10},clock=lambda:now[0])
        guard.tick();guard.size('vqa',10)
        with self.assertRaisesRegex(ValueError,'Store'):guard.size('vqa',11)
        now[0]=3
        with self.assertRaisesRegex(ValueError,'Stalled'):guard.check()
        now[0]=11
        with self.assertRaisesRegex(ValueError,'Wall'):guard.check()
        with H.watchdog(H.Guard(directory())):pass
        self.assertEqual(H.estimate(2000,20000,200000)['extrapolated_bytes'],2000000)
        with self.assertRaises(ValueError):H.estimate(2001,10,2001)
        root=directory();write(root/'a.json',{})
        pin=file_pin(root/'a.json')
        packet={key:([pin] if key=='manifests' else pin) for key in ('manifests','configuration','pose_template','real_proof','counts')}
        with self.assertRaisesRegex(ValueError,'Missing pose'):H.input_paths(packet,root)
        packet['pose_sources']=[pin,pin]
        with self.assertRaisesRegex(ValueError,'distinct'):H.input_paths(packet,root)
        write(root/'b.json',{'source':2})
        packet['pose_sources']=[pin,file_pin(root/'b.json')]
        self.assertEqual(len(H.input_paths(packet,root)['pose_sources']),2)
        for change,reason in [({'counts':None},'Missing'),({'counts':{}},'Missing'),
                              ({'counts':dict(path='a.json',sha256='0'*64)},'sha256'),
                              ({'counts':dict(path='x',sha256='0'*64)},'Missing'),
                              ({'counts':dict(other=1)},'sha256')]:
            with self.assertRaisesRegex(ValueError,reason):H.input_paths({**packet,**change},root)

    def test_kits_real_entry_from_empty(self):
        results=[]
        for connector in ('none','gf1'):
            root=directory();dp=dense(root)
            kit=root/'a'
            result=B.build(LANE/'work/kit07ca49df_meta/m',kit,connector=connector,records=inputs(),
                           dense_manifest=dp if connector=='gf1' else None, init_pin=INIT_PIN)
            cfg=load(kit/result['config']['path'])
            self.assertEqual(cfg['routing_opener_init'],'keep')
            self.assertNotEqual(load(kit/'k/4.json')['modes'],[])
            with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):
                bootstrap.main(kit,'t',root/'b')
            with self.assertRaisesRegex(ValueError,'empty'):bootstrap.stage(kit,root/'b')
            results.append(dict(connector=connector,boundary='Missing component evidence: init_m544',
                                archive_verified=True,staged_from_empty=True,production_authorized=False))
        (PROOFS/'B3_JOB_PROOF.json').write_text(json.dumps(results,indent=2)+'\n')


class EvaluationEntrypoints(unittest.TestCase):
    pass


def refusal(entry):
    def test(self):
        with self.assertRaisesRegex(ValueError,'bank adapter'):
            invoke(entry)
    return test


def invoke(entry):
        module=importlib.import_module(entry['file'][:-3].replace('/','.'))
        function=getattr(module,entry['function'])
        sig=inspect.signature(function)
        args={name:None for name,p in sig.parameters.items() if p.default is inspect.Parameter.empty
              and p.kind not in (p.VAR_POSITIONAL,p.VAR_KEYWORD)}
        function(**args)


for number, entry in enumerate(load(LANE/'references/B3_BANK_ENTRYPOINTS.json')):
    setattr(EvaluationEntrypoints,'test_refusal_'+str(number),refusal(entry))

from tests.r2_init_fixture import PIN as INIT_PIN
