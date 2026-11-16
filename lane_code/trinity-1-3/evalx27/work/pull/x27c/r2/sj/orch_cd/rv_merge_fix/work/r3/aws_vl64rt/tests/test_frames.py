"""CPU regression tests for independent decoding, PNG pins, and retained deploys."""
from copy import deepcopy
import datetime as dt
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import av
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from common import archive,sha
from frame_env import unpack
from frame_stage import stage
from media import decode,load,item_key
from remote import DEPLOY,SUBMIT


def retained():
    return Path(tempfile.mkdtemp(dir=ROOT/'checks'))


def video(path,count,rate):
    with av.open(str(path),'w') as container:
        stream=container.add_stream('mpeg4',rate=rate)
        stream.width=48;stream.height=32;stream.pix_fmt='yuv420p'
        y,x=np.indices((32,48))
        for i in range(count):
            pixels=np.stack(((x*7+i*3)%256,(y*11+i*5)%256,(x+y+i*9)%256),axis=-1).astype(np.uint8)
            frame=av.VideoFrame.from_ndarray(pixels,format='rgb24')
            for packet in stream.encode(frame):container.mux(packet)
        for packet in stream.encode():container.mux(packet)


class Frames(unittest.TestCase):
    def test_launch_stages_frames_once_before_workers(self):
        import launch
        d=retained();config=d/'0.json'
        cfg=dict(gpus=2,models={'base':{}},cells=[dict(model='base'),dict(model='base')])
        config.write_text(json.dumps(cfg));events=[]
        def frames(*args):events.append('frames');return 'pinned'
        def model(*args):events.append('model');return d/'model'
        def child(argv,**kw):
            events.append('worker')
            self.assertEqual(argv[argv.index('--frames-sha256')+1],'pinned')
            return SimpleNamespace(wait=lambda:0)
        with patch.dict(sys.modules,{'vllm':SimpleNamespace(__version__='0.32.0')}),\
             patch.dict('os.environ',{'SLURM_JOB_ID':'job','CUDA_VISIBLE_DEVICES':'0,1'}),\
             patch('launch.prepare_frames',side_effect=frames) as staged,\
             patch('launch.prepare',side_effect=model),patch('launch.subprocess.Popen',side_effect=child),\
             patch('token_audit.load_tokenizer',return_value=object()),patch('launch.merge') as merged:
            launch.main(str(config),d)
        self.assertEqual(events,['frames','model','worker','worker','worker','worker'])
        self.assertEqual(staged.call_count,1);self.assertEqual(merged.call_count,2)

    def test_two_videos_original_decoder_and_png_worker(self):
        spec=importlib.util.spec_from_file_location('original_media',ROOT/'tests/fixtures/media_before_x5.py')
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        self.assertEqual(sha(ROOT/'tests/fixtures/media_before_x5.py'),
                         'f6b8ead54ea38b621d6caaa1d249c3cfa96142c2b99081a2741db7f262680e84')
        d=retained();videos=[d/'0.mp4',d/'1.mp4']
        video(videos[0],67,Fraction(30000,1001));video(videos[1],32,1)
        normal=[dict(benchmark='vsi500',example_id=str(i),video_path=str(p),video_sha256=sha(p))
                for i,p in enumerate(videos)]
        # Two questions share the exact video/layout cache.
        normal.append({**normal[0],'example_id':'shared'})
        source=[k*319//31 for k in range(32)]
        revsi=[dict(benchmark='revsi',example_id='r',video_path=str(videos[1]),source_frame_indices=source)]
        layouts=('spread','duplicate','P0.5','P0.2')
        cfg=dict(binding='bound',source_sha256='source',roots={},datasets=[dict(benchmark=b) for b in ('vsi500','revsi')],
                 cells=[dict(layout=l,benchmarks=['vsi500']) for l in layouts]+
                       [dict(layout=l,benchmarks=['revsi']) for l in ('spread','duplicate')])
        cfg['cells'].append(deepcopy(cfg['cells'][0]))  # Another model shares frames too.
        config=d/'0.json';config.write_text(json.dumps(cfg))
        tasks={'vsi500':normal,'revsi':revsi}
        with patch('frame_stage.tasks_for',side_effect=lambda s,r:tasks[s['benchmark']]):
            index=stage(config,d/'cache',4)
        self.assertEqual(index['decodes'],10);self.assertEqual(index['errors'],0)
        self.assertEqual(len(index['items']),14)
        self.assertEqual(index['items'][item_key(normal[0],'spread')],
                         index['items'][item_key(normal[2],'spread')])
        pin=sha(d/'cache/0.json')
        expected={}
        for cell in cfg['cells'][:-1]:
            layout=cell['layout']
            for task in tasks[cell['benchmarks'][0]]:
                before,audit=original.load(task,layout,d/'original')
                direct,observed=decode(task,layout)
                self.assertTrue(np.array_equal(before,direct));self.assertEqual(audit,observed)
                expected[item_key(task,layout)]=(before,audit)
        # The vLLM entry point must work with neither PyAV nor the source videos.
        for p in videos:p.rename(p.with_suffix('.retained.mp4'))
        with patch.dict(sys.modules,{'av':None}),patch('media.decode',side_effect=AssertionError('worker decoded')):
            for cell in cfg['cells'][:-1]:
                for task in tasks[cell['benchmarks'][0]]:
                    arrays,audit=load(task,cell['layout'],d/'cache',pin)
                    before,previous=expected[item_key(task,cell['layout'])]
                    self.assertTrue(np.array_equal(before,arrays))
                    self.assertEqual(previous,{k:v for k,v in audit.items() if k!='frame_receipt'})
                    self.assertIn('sha256',audit['frame_receipt'])
        receipt=json.loads((d/'cache'/index['items'][item_key(normal[0],'duplicate')]['path']).read_text())
        self.assertEqual(receipt['frames'][0],receipt['frames'][1])
        png=d/'cache'/receipt['frames'][0]['path']
        png.write_bytes(png.read_bytes()+b'corrupt')
        with self.assertRaisesRegex(ValueError,'PNG pin differs'):load(normal[0],'duplicate',d/'cache',pin)
        with self.assertRaisesRegex(ValueError,'index pin differs'):load(normal[0],'spread',d/'cache','0'*64)
        # Receipt edits cannot silently repin altered pixels or indices.
        receipt_path=d/'cache'/index['items'][item_key(normal[0],'spread')]['path']
        receipt_path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'receipt pin differs'):load(normal[0],'spread',d/'cache',pin)

    def test_smoke_selection_and_decode_error_receipt(self):
        d=retained();config=d/'0.json'
        tasks=[dict(benchmark='vsi500',example_id=str(i),video_path=str(d/(str(i)+'.mp4'))) for i in range(20)]
        config.write_text(json.dumps(dict(binding='b',source_sha256='s',roots={},smoke_items=16,
            datasets=[dict(benchmark='vsi500')],cells=[dict(layout='spread',benchmarks=['vsi500'])])))
        with patch('frame_stage.tasks_for',return_value=tasks),patch('frame_stage.decode',side_effect=ValueError('bad source')):
            index=stage(config,d/'cache',2)
        self.assertEqual(index['errors'],16);self.assertEqual(len(index['items']),16)
        selected=sorted(tasks,key=lambda t:(t['benchmark'],t['example_id']))[:16]
        self.assertEqual(set(index['items']),{item_key(t,'spread') for t in selected})
        with self.assertRaisesRegex(ValueError,'CPU frame stage: ValueError: bad source'):
            load(selected[0],'spread',d/'cache',sha(d/'cache/0.json'))

    def test_environment_archive_pin_and_shebangs(self):
        d=retained();name='rwtrain_torch211_cu129'
        blobs={name+'/bin/python3':b'fixture interpreter',name+'/lib/python3.12/site-packages/av/__init__.py':b'',
               name+'/bin/tool':b'#!/project/community/jjyeung/opaque/venvs/rwtrain_torch211_cu129/bin/python\nprint(1)\n'}
        archive(d/'e.tar',blobs)
        python=unpack(d/'e.tar',sha(d/'e.tar'),d/'e')
        self.assertEqual(python,d/'e'/name/'bin/python3')
        self.assertEqual((python.parent/'tool').read_text().splitlines()[0],'#!'+str(python))
        with self.assertRaisesRegex(ValueError,'pin/extraction differs'):unpack(d/'e.tar','0'*64,d/'bad')

    def test_deploy_retains_model_manifest_outputs_and_previous_tree(self):
        d=retained();root=d/'90da7ac2';(root/'m').mkdir(parents=True);(root/'o').mkdir()
        (root/'m/base_manifest.json').write_text('model pin');(root/'o/110500.out').write_text('old output')
        blobs={'b/0.sh':b'new launcher','b/1.py':b'new bootstrap','k/0.tar':b'code','k/1.tar':b'request','k/2.json':b'auth'}
        blobs['SHA256SUMS.txt']=''.join(hashlib.sha256(v).hexdigest()+'  '+n+'\n' for n,v in blobs.items()).encode()
        archive(d/'incoming.tar',blobs)
        def deploy():
            return subprocess.run([sys.executable,'-I','-s','-B','-',str(root),str(d/'incoming.tar'),sha(d/'incoming.tar')],
                                  input=DEPLOY,text=True,capture_output=True)
        first=deploy();self.assertEqual(first.returncode,0,first.stderr)
        (root/'b/0.sh').write_text('previous launcher')
        (root/'k/1.tar').write_bytes(b'previous request')
        previous_manifest=(root/'SHA256SUMS.txt').read_bytes()
        second=deploy();self.assertEqual(second.returncode,0,second.stderr)
        retained_trees=[p for p in (root/'.retained').iterdir() if p.is_dir()]
        self.assertEqual(len(retained_trees),1)
        self.assertEqual((retained_trees[0]/'b/0.sh').read_text(),'previous launcher')
        self.assertEqual((retained_trees[0]/'k/1.tar').read_bytes(),b'previous request')
        self.assertEqual((retained_trees[0]/'SHA256SUMS.txt').read_bytes(),previous_manifest)
        self.assertEqual((root/'b/0.sh').read_bytes(),blobs['b/0.sh'])
        self.assertEqual((root/'m/base_manifest.json').read_text(),'model pin')
        self.assertEqual((root/'o/110500.out').read_text(),'old output')
        (root/'unexpected').write_text('keep')
        refused=deploy();self.assertNotEqual(refused.returncode,0);self.assertIn('E02',refused.stderr)
        self.assertEqual((root/'unexpected').read_text(),'keep')
        self.assertEqual(len([p for p in (root/'.retained').iterdir() if p.is_dir()]),1)

    def test_submit_keeps_parent_cpu_skip_and_explicit_resources(self):
        d=retained();(d/'o').mkdir();(d/'b').mkdir();(d/'k').mkdir()
        (d/'b/0.sh').write_text('#SBATCH --job-name=a15_cot_ap90da7ac2\n')
        (d/'k/2.json').write_text(json.dumps(dict(build_only=False,gpus=4,gpu_cap=1,
            until=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())))
        (d/'SHA256SUMS.txt').write_text(''.join(sha(d/n)+'  '+n+'\n' for n in ('b/0.sh','k/2.json')))
        queue='/other|N/A|1|a15_cot_ap12345678\n/other2|gres/gpu:h100:8|2|a15_cot_ap87654321\n'
        def command(argv,**kw):
            if argv[0]=='squeue':return queue
            self.assertEqual(argv[0],'sbatch')
            for flag in ('--account=av_alpamayo_aml','--partition=batch','--qos=normal'):self.assertIn(flag,argv)
            return '1234\n'
        with patch.object(sys,'argv',['submit',str(d),sha(d/'SHA256SUMS.txt')]),\
             patch('subprocess.check_output',side_effect=command) as calls:
            exec(SUBMIT,{})
        self.assertEqual(calls.call_count,2)
        self.assertEqual(json.loads((d/'o/s1234.json').read_text())['gpus'],4)


if __name__=='__main__':unittest.main(verbosity=2)
