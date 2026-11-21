"""Debug partition: submission flags, queue admission, exclusive-node routing and deadlines."""
import os
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE/'tests'))
import ast
import json
import re
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
import test_fixes as F
import test_bootstrap as BT
import debug_partition as DP

BOOT=re.compile(r"\nexec\(bytes\.fromhex\('[0-9a-f]+'\)\.decode\(\),_a0:=\{\}\);_a0\['install'\]\(\)\n")


class DebugPartitionTests(unittest.TestCase):
    setUpClass=classmethod(F.FixTests.setUpClass.__func__)
    @classmethod
    def tearDownClass(cls):
        import j
        keys=('submission','launcher','operator_queue_check','exclusive_node','time_guard')
        cls.evidence['passed']=all(cls.evidence.get(k,{}).get('passed') is True for k in keys)
        (HERE/'out/DEBUG_PARTITION_CHECKS.json').write_text(j.wire_dumps(cls.evidence,indent=2)+'\n')

    def previous_argv(self,token):
        # The placed a4282fee306d6 contract, read from its sealed common.py.
        prior=HERE/'tmp/prev_a428b/out/delivery.tgz'
        outer={m.name:d for m,d in F.BD.B.read_tar(prior.read_bytes())}
        payload={m.name:d for m,d in F.BD.B.read_tar(outer['0.tgz'])}
        source=BOOT.sub('\n',payload['orchard_h10/common.py'].decode())
        scope={'__name__':'previous_common'};exec(compile(source,'previous_common.py','exec'),scope)
        return scope['submit_argv'](token,1,'00:50:00')

    def test_submission_flags(self):
        from orchard_h10 import common
        token=self.info['token']
        self.assertEqual((common.PARTITION,common.QOS),(DP.PARTITION,DP.QOS))
        self.assertEqual((DP.PARTITION,DP.QOS),('debug','debug_qos'))
        argv=common.submit_argv(token,1,'00:50:00')
        old=self.previous_argv(token)
        i=old.index('--partition=general')
        self.assertEqual(argv,old[:i]+['--partition=debug','--qos=debug_qos']+old[i+1:])
        self.assertFalse(any('general' in a for a in argv))
        for flag in ('--account=mt01','--nodes=1','--ntasks=1','--cpus-per-task=16','--mem=200G','--exclude=orchard-community-4',
                     '--time=00:50:00','--signal=B:USR1@120','--no-requeue','--export=NONE','--chdir=/tmp','--open-mode=append',
                     '--job-name=a15_cot_ap'+token,'--output=/project/community/jjyeung/'+token+'/a/19',
                     '--error=/project/community/jjyeung/'+token+'/a/24'):
            self.assertEqual(argv.count(flag),1,flag)
        # Debug's MaxTime is one hour; the 50-minute allocation fits.
        self.assertLessEqual(common.seconds('00:50:00'),3600)
        # Both allocations go through the packaged submit; only --gres differs.
        m=types.ModuleType('submission');m.__file__=str(self.package/'8.py')
        exec(self.files['8.py'],m.__dict__)
        from orchard_h10 import job
        cfg=json.loads(self.files['9.json']);cfg.update(json.loads((self.package/'0.json').read_bytes()))
        receipt=dict(plan=cfg['plan_sha256'],inputs=m.digest(self.package/'a/1.json'),package=m.digest(self.package/'PACKAGE.json'),gpus=1,time='00:50:00')
        (self.package/'2.json').write_text(json.dumps(receipt))
        calls=[]
        def submitted(argv,**kw):calls.append((argv,kw));return types.SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
        with patch.object(m,'load_helpers',return_value=cfg),patch.object(job,'check_inputs'),patch.object(m.subprocess,'run',side_effect=submitted):
            self.assertEqual(m.submit(self.package,1,'00:50:00',cpu_only=True),0)
            self.assertEqual(m.submit(self.package,1,'00:50:00'),0)
        cpu,gpu=calls
        self.assertEqual(gpu[0],argv)
        self.assertEqual(cpu[0],[a for a in argv if a!='--gres=gpu:1'])
        self.assertEqual(cpu[1],gpu[1])
        self.evidence['submission']=dict(passed=True,gpu_argv=gpu[0],cpu_argv=cpu[0],previous_argv=old,
            changed=['--partition=general -> --partition=debug --qos=debug_qos'],cpu_gpu_difference=['--gres=gpu:1'])

    def test_retained_launcher(self):
        from orchard_h10.vendor import orchard_launcher as L
        from orchard_h10 import common
        self.assertEqual((L.PARTITION,L.QOS,L.LANE_JOB_PREFIX),(DP.PARTITION,DP.QOS,DP.LANE_JOB_PREFIX))
        self.assertEqual((L.PARTITION,L.QOS),(common.PARTITION,common.QOS))
        token=self.info['token']
        for proof in (False,True):
            argv=L.submit_argv(None,token,proof=proof)
            self.assertEqual((argv.count('--partition=debug'),argv.count('--qos=debug_qos')),(1,1))
            self.assertFalse(any('general' in a for a in argv))
        source=(self.payload/'orchard_h10/vendor/orchard_launcher.py').read_text()
        self.assertNotIn('general',source);self.assertIn("['squeue', '-p', PARTITION, '-h',",source)
        user='jjyeung';lane='a15_cot_ap'+token
        allowed={'empty':'',
                 'other_project_gpu':'1|x7job|jjyeung|RUNNING|gres/gpu:1',
                 'lane_cpu_check':'2|'+lane+'|jjyeung|RUNNING|N/A',
                 'other_user_lane_gpu':'3|a15_cot_apa4282fee306d6|someone|RUNNING|gres/gpu:1'}
        refused={'own_gpu':'4|'+lane+'|jjyeung|PENDING|gres/gpu:1',
                 'lane_gpu':'5|a15_cot_apa4282fee306d6|jjyeung|RUNNING|gres:gpu:1',
                 'lane_gpu_with_others':'1|x7job|jjyeung|RUNNING|gres/gpu:8\n6|a15_cot_apx|jjyeung|RUNNING|gpu:1'}
        for name,text in allowed.items():L.queue_admission(text,user)
        for name,text in refused.items():
            with self.assertRaisesRegex(ValueError,'already on the debug partition'):L.queue_admission(text,user)
        with self.assertRaisesRegex(ValueError,'malformed'):L.queue_admission('1|2|3',user)
        self.evidence['launcher']=dict(passed=True,allowed=sorted(allowed),refused=sorted(refused))

    def body(self,name):
        text=(HERE/'orchard'/name).read_text()
        return text.split("<<'BODY'\n",1)[1].split('\nBODY\n',1)[0]

    def test_operator_queue_check(self):
        scripts=sorted((HERE/'orchard').glob('*.sh'))
        for path in scripts:self.assertNotIn('general',path.read_text(),path.name)
        self.assertEqual((HERE/'orchard/o_check_sub.sh').read_bytes(),(HERE/'orchard/o_sub_hand.sh').read_bytes())
        body=self.body('o_check_sub.sh')
        self.assertEqual(body.count(DP.QUEUE),1)
        lines=body.splitlines();start=next(i for i,l in enumerate(lines) if l.startswith('squeue '))
        # The queue check sits after the receipt and package checks and before submit.
        self.assertTrue(lines[start-2].startswith('/usr/bin/python3 -I -s -B a/9.py'))
        self.assertTrue(lines[start+2].startswith('reply=$(/usr/bin/python3 -I -s -B 3.py submit'))
        snippet='\n'.join(lines[start:start+2])
        token=self.info['token']
        cases={'empty':('',0),'other_project_gpu':('x7job|gres/gpu:1',0),'lane_cpu_check':('a15_cot_ap'+token+'|N/A',0),
               'own_gpu':('a15_cot_ap'+token+'|gres/gpu:1',1),'lane_gpu':('a15_cot_apa4282fee306d6|gres:gpu:1',1),
               'lane_gpu_upper':('a15_cot_apa4282fee306d6|GPU:1',1),'squeue_failure':(None,1)}
        results={}
        for name,(rows,expected) in cases.items():
            work=Path(tempfile.mkdtemp(dir=HERE.parent/'r1_fixtures_old',prefix='queue_'))
            (work/'a').mkdir()
            # A shell function stands in for the scheduler; functions take precedence over PATH.
            fake='squeue(){ printf "%s\\n" "$@" > "$Q_ARGS"; '+('return 2; }' if rows is None else 'printf "%s" "$Q_ROWS"; }')
            env=dict(PATH='/usr/bin:/bin',Q_ARGS=str(work/'args'),Q_ROWS=(rows or '')+('\n' if rows else ''))
            got=subprocess.run(['bash','--noprofile','--norc','-c','set -euo pipefail\n'+fake+'\n'+snippet+'\necho admitted\n'],cwd=work,env=env,capture_output=True,text=True)
            self.assertEqual(got.returncode!=0,expected==1,(name,got.stdout,got.stderr))
            self.assertEqual(got.stdout.strip()=='admitted',expected==0,name)
            self.assertEqual((work/'args').read_text().splitlines(),['-u','jjyeung','-p','debug','-h','-o','%j|%b'])
            results[name]='refused' if got.returncode else 'admitted'
        self.evidence['operator_queue_check']=dict(passed=True,command=snippet,cases=results,scripts=['o_check_sub.sh','o_sub_hand.sh'])

    def test_exclusive_node_routes(self):
        exclusive=dict(CUDA_VISIBLE_DEVICES='0,1,2,3',SLURM_JOB_GPUS='0,1,2,3',SLURM_GPUS_ON_NODE='4',SLURM_JOB_PARTITION='debug')
        # CPU check (no --gres) on a whole debug node that exposes its GPUs.
        root,p,pub,env,argv=BT.BootstrapTests.setup_case(self,'write_success')
        (p/'a/c').rename(p/'a/c0')
        env.update(SLURM_JOB_ID='174101',**exclusive)
        result=subprocess.run(argv,env=env,capture_output=True,text=True)
        diagnostic=BT.decoded((p/'a/14.json').read_bytes()) if (p/'a/14.json').exists() else {}
        self.assertEqual((result.returncode,result.stdout+result.stderr),(0,''),diagnostic)
        proof=BT.decoded((p/'a/c/CPU.json').read_bytes())
        self.assertTrue(proof['passed'] and proof['bundle_guard_passed'] and proof['entry_sequence_passed'] and proof['real_unit_passed'])
        seen=json.loads((root/'work'/('a174101'+pub['token'])/'gpu_env.json').read_text())
        self.assertEqual(seen,dict(SLURM_JOB_GPUS=None,SLURM_STEP_GPUS=None,SLURM_GPUS_ON_NODE=None,GPU_DEVICE_ORDINAL=None,
                                   CUDA_VISIBLE_DEVICES='',dispatch_cuda_visible=''))
        checked=subprocess.run([sys.executable,'-I','-s','-B','a/9.py',str(p)],cwd=p,env=env,capture_output=True,text=True)
        self.assertEqual((checked.returncode,checked.stdout.strip()),(0,'All CPU receipt checks passed'),checked.stderr)
        # The previous mode test would have sent this CPU check down the GPU route.
        self.assertIn(b"if not os.environ.get('SLURM_JOB_GPUS') and not os.environ.get('CUDA_VISIBLE_DEVICES'):",DP.BOOT_OLD)
        self.assertFalse(not exclusive.get('SLURM_JOB_GPUS') and not exclusive.get('CUDA_VISIBLE_DEVICES'))
        # GPU job (CPU receipt present) on the same kind of node: real job.main with A_N=1.
        root2,p2,pub2,env2,argv2=BT.BootstrapTests.setup_case(self,'clean')
        env2.update(**exclusive)
        gpu=subprocess.run(argv2,env=env2,capture_output=True,text=True)
        self.assertEqual((gpu.returncode,gpu.stdout+gpu.stderr),(1,''))
        self.assertTrue((root2/'work'/('a173925'+pub2['token'])/'17.json').exists())
        from orchard_h10.job import select_cards
        self.assertEqual(select_cards('0,1,2,3',1),['0'])
        self.assertEqual(select_cards('GPU-a,GPU-b',1),['GPU-a'])
        self.assertEqual(select_cards('3',1),['3'])
        self.assertEqual(select_cards('',1),[''])
        self.assertEqual(select_cards('0,,1',1),['0','','1'])
        source=(self.payload/'orchard_h10/job.py').read_text()
        self.assertIn("cards=select_cards(assigned,n)\n        if len(cards)!=n or not all(cards)",source)
        self.evidence['exclusive_node']=dict(passed=True,cpu_check_route='cpu',cpu_check_gpu_env=seen,cpu_receipt_check='passed',
            gpu_job_route='job.main',card_selection={'0,1,2,3':['0'],'3':['3'],'':'refused by the GPU/hour contract'})

    def test_time_guard_on_debug(self):
        source=(self.package/'a/5.py').read_text()
        tree=ast.parse(source)
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='unit_config')
        scope={'os':os};exec(compile(ast.Module(body=[node],type_ignores=[]),'a/5.py','exec'),scope)
        cfg=json.loads(self.files['9.json']);self.assertEqual(cfg['budget_gpu_seconds'],3000)
        cases={}
        start=1_800_000_000
        for name,end in (('debug_50_min',start+3000),('debug_max_time',start+3600),('no_end',None),('early_end',start+2000)):
            env={'SLURM_JOB_START_TIME':str(start),'SLURM_CPUS_PER_TASK':'16'}
            if end:env['SLURM_JOB_END_TIME']=str(end)
            with patch.dict(os.environ,env,clear=False):
                if not end:os.environ.pop('SLURM_JOB_END_TIME',None)
                unit=scope['unit_config'](cfg)
            limit=min(start+3000,end or start+3000)
            self.assertEqual((unit['allocation_end'],unit['end'],unit['kill_at']),(limit,limit-360,limit-330))
            # The operator kill (E-330) precedes Slurm's USR1 (E-120), so CPU.json is written first.
            self.assertLess(unit['kill_at'],limit-120)
            cases[name]=dict(allocation_end_s=unit['allocation_end']-start,worker_stop_s=unit['end']-start,kill_s=unit['kill_at']-start)
        self.evidence['time_guard']=dict(passed=True,cases=cases,usr1_before_end_s=120,
            note='The guard reads SLURM_JOB_START_TIME and SLURM_JOB_END_TIME, which Slurm sets the same way on every partition.')


if __name__=='__main__':unittest.main(verbosity=2)
