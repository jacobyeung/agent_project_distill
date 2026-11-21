"""Preempt partition: submission flags, queue admission, preemption receipts, exclusive-node routing and deadlines."""
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
        keys=('submission','launcher','operator_queue_check','exclusive_node','time_guard','preemption_trap','preempted_fetch')
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
        self.assertEqual((DP.PARTITION,DP.QOS,DP.EXCLUDE),('preempt','preempt_qos','orchard-community-4,orchard-flame-[0-31]'))
        self.assertEqual(common.EXCLUDE,DP.EXCLUDE)
        argv=common.submit_argv(token,1,'00:50:00')
        old=self.previous_argv(token)
        i=old.index('--partition=general')
        expected=old[:i]+['--partition=preempt','--qos=preempt_qos']+old[i+1:]
        expected[expected.index('--exclude=orchard-community-4')]='--exclude=orchard-community-4,orchard-flame-[0-31]'
        self.assertEqual(argv,expected)
        self.assertFalse(any('general' in a or 'debug' in a for a in argv))
        for flag in ('--account=mt01','--nodes=1','--ntasks=1','--cpus-per-task=16','--mem=200G','--exclude=orchard-community-4,orchard-flame-[0-31]',
                     '--time=00:50:00','--signal=B:USR1@120','--no-requeue','--export=NONE','--chdir=/tmp','--open-mode=append',
                     '--job-name=a15_cot_ap'+token,'--output=/project/community/jjyeung/'+token+'/a/19',
                     '--error=/project/community/jjyeung/'+token+'/a/24'):
            self.assertEqual(argv.count(flag),1,flag)
        # preempt's MaxTime is two days; the 50-minute allocation fits.
        self.assertLessEqual(common.seconds('00:50:00'),2*86400)
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
            changed=['--partition=general -> --partition=preempt --qos=preempt_qos','--exclude=orchard-community-4 -> --exclude=orchard-community-4,orchard-flame-[0-31]'],cpu_gpu_difference=['--gres=gpu:1'])

    def test_retained_launcher(self):
        from orchard_h10.vendor import orchard_launcher as L
        from orchard_h10 import common
        self.assertEqual((L.PARTITION,L.QOS,L.LANE_JOB_PREFIX),(DP.PARTITION,DP.QOS,DP.LANE_JOB_PREFIX))
        self.assertEqual((L.PARTITION,L.QOS),(common.PARTITION,common.QOS))
        token=self.info['token']
        for proof in (False,True):
            argv=L.submit_argv(None,token,proof=proof)
            self.assertEqual((argv.count('--partition=preempt'),argv.count('--qos=preempt_qos')),(1,1))
            self.assertFalse(any('general' in a for a in argv))
        source=(self.payload/'orchard_h10/vendor/orchard_launcher.py').read_text()
        self.assertNotIn('general',source)
        self.assertIn("['squeue', '-u', 'jjyeung', '-h', '-t', 'all', '-o', '%i|%j|%u|%T|%b']",source)
        self.assertIn("queue_admission(queue.stdout, 'jjyeung', LANE_JOB_PREFIX+config['token'])",source)
        user='jjyeung';name='a15_cot_ap'+token
        allowed={'empty':'',
                 'other_project_general':'1|x7job|jjyeung|RUNNING|gres/gpu:1',
                 'other_lane_package_advanced':'3|a15_cot_apa4282fee306d6|jjyeung|RUNNING|gres/gpu:4',
                 'other_user_same_name':'2|'+name+'|someone|RUNNING|N/A'}
        refused={'own_pending':'4|'+name+'|jjyeung|PENDING|gres/gpu:1',
                 'own_completed':'5|'+name+'|jjyeung|COMPLETED|N/A',
                 'own_preempted':'1|x7job|jjyeung|RUNNING|gres/gpu:8\n6|'+name+'|jjyeung|PREEMPTED|gres/gpu:1'}
        for case,text in allowed.items():L.queue_admission(text,user,name)
        for case,text in refused.items():
            with self.assertRaisesRegex(ValueError,'already exists'):L.queue_admission(text,user,name)
        with self.assertRaisesRegex(ValueError,'malformed'):L.queue_admission('1|2|3',user,name)
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
        lines=body.splitlines();start=next(i for i,l in enumerate(lines) if l.startswith('cpu=$(cat a/4.txt)'))
        # The queue check sits after the receipt and package checks and before submit.
        self.assertTrue(lines[start-2].startswith('/usr/bin/python3 -I -s -B a/9.py'))
        self.assertTrue(lines[start+3].startswith('reply=$(/usr/bin/python3 -I -s -B 3.py submit'))
        snippet='\n'.join(lines[start:start+3])
        token=self.info['token'];name='a15_cot_ap'+token
        # (squeue rows, CPU job id in a/4.txt, expected)
        cases={'empty':('','1700',0),'own_cpu_check_completed':('1700|'+name,'1700',0),
               'other_project_general':('1701|x7job','1700',0),'other_lane_package_advanced':('1702|a15_cot_apa4282fee306d6','1700',0),
               'own_name_other_job':('1700|'+name+'\n1703|'+name,'1700',1),'own_name_prefix_only':('1704|'+name+'0','1700',0),
               'squeue_failure':(None,'1700',1),'missing_cpu_job':('',None,1)}
        results={}
        for case,(rows,cpu,expected) in cases.items():
            work=Path(tempfile.mkdtemp(dir=HERE.parent/'r1_fixtures_old',prefix='queue_'))
            (work/'a').mkdir()
            if cpu:(work/'a/4.txt').write_text(cpu+'\n')
            # A shell function stands in for the scheduler; functions take precedence over PATH.
            fake='squeue(){ printf "%s\\n" "$@" > "$Q_ARGS"; '+('return 2; }' if rows is None else 'printf "%s" "$Q_ROWS"; }')
            env=dict(PATH='/usr/bin:/bin',Q_ARGS=str(work/'args'),Q_ROWS=(rows or '')+('\n' if rows else ''))
            got=subprocess.run(['bash','--noprofile','--norc','-c','set -euo pipefail\nP=/project/community/jjyeung/'+token+'\n'+fake+'\n'+snippet+'\necho admitted\n'],cwd=work,env=env,capture_output=True,text=True)
            self.assertEqual(got.returncode!=0,expected==1,(case,got.stdout,got.stderr))
            self.assertEqual(got.stdout.strip()=='admitted',expected==0,case)
            if cpu:self.assertEqual((work/'args').read_text().splitlines(),['-u','jjyeung','-h','-t','all','-o','%i|%j'])
            results[case]='refused' if got.returncode else 'admitted'
        self.evidence['operator_queue_check']=dict(passed=True,command=snippet,cases=results,scripts=['o_check_sub.sh','o_sub_hand.sh'])

    def test_exclusive_node_routes(self):
        exclusive=dict(CUDA_VISIBLE_DEVICES='0,1,2,3',SLURM_JOB_GPUS='0,1,2,3',SLURM_GPUS_ON_NODE='4',SLURM_JOB_PARTITION='preempt')
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

    def test_preemption_trap_record(self):
        # The delivered batch header, with its job paths moved to a local directory.
        header=(self.package/'BATCH.sh').read_text().split("<<'A'\n",1)[0].rsplit('\n',2)[0]+'\n'
        self.assertEqual(header.count("' TERM\n"),1)
        work=Path(tempfile.mkdtemp(dir=HERE.parent/'r1_fixtures_old',prefix='preempt_'))
        (work/'a').mkdir()
        shared='/project/community/jjyeung/'+self.info['token']
        script=header.replace(shared,str(work))+'set -Eeuo pipefail\n'+sys.executable+''' -I -S -c '
import signal,sys,time
def stop(*a):
    open(sys.argv[1],"w").write("published\\n");sys.exit(1)
signal.signal(signal.SIGTERM,stop);open(sys.argv[2],"w").write("ready\\n");time.sleep(60)' '''+str(work/'published')+' '+str(work/'ready')+'\necho after\n'
        (work/'batch.sh').write_text(script)
        shell=subprocess.Popen(['bash','--noprofile','--norc',str(work/'batch.sh')],env=dict(PATH='/usr/bin:/bin',SLURM_JOB_ID='174301'),start_new_session=True)
        import time
        for _ in range(200):
            if (work/'ready').exists():break
            time.sleep(.05)
        # Slurm signals every process of the job: the shell and the supervisor.
        os.killpg(shell.pid,15)
        self.assertEqual(shell.wait(timeout=30),143)
        self.assertEqual((work/'published').read_text(),'published\n')
        records=(work/'a/21').read_text().splitlines()
        self.assertEqual(len(records),1);status=records[0].split()
        self.assertEqual((status[0],status[2]),('143','174301'))
        self.assertNotIn('after',(work/'a/19').read_text())
        self.evidence['preemption_trap']=dict(passed=True,trap_records=records,supervisor_finished_first=True,shell_status=143)

    def fetch(self,p,job):
        command=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
                 '/project/community/jjyeung/okh7/ae71c903',str(p.parent/'pool'),job,str(HERE/'orchard/o_fetch.sh')]
        return subprocess.run(command,env=dict(PATH='/usr/bin:/bin',USER='jjyeung'),capture_output=True,text=True)

    def test_preempted_job_fetch(self):
        cases={}
        # The supervisor was killed before publishing; the TERM trap left status 143.
        root,p,pub,env,argv=BT.BootstrapTests.setup_case(self,'clean')
        for name in ('19','24'):(p/'a'/name).write_bytes(b'')
        (p/'a/21').write_text('0 1 174300\n143 1 174302\n')
        (p/'a/12.txt').write_text('174302|PREEMPTED|0:15\n')
        got=self.fetch(p,'174302')
        self.assertEqual(got.returncode,0,got.stdout+got.stderr)
        self.assertIn('scheduler state: 174302|PREEMPTED|0:15',got.stderr)
        ex=BT.decoded((p/'a/f/EXIT.json').read_bytes());self.assertEqual(ex['status'],'FAILED')
        import tarfile
        with tarfile.open(p/'a/f/0.tgz') as archive:
            trace=BT.decoded(archive.extractfile('metadata/14.json').read())
        self.assertTrue(any('E82 143 1 174302' in line for line in trace['lines']),trace['lines'][:5])
        cases['trap_only']=dict(status=ex['status'],trap='143 1 174302',state='PREEMPTED')
        # Killed before any trap record: fetch names the job and the scheduler state.
        root,p,pub,env,argv=BT.BootstrapTests.setup_case(self,'clean')
        for name in ('19','24'):(p/'a'/name).write_bytes(b'')
        (p/'a/21').write_text('0 1 174300\n')
        (p/'a/12.txt').write_text('174303|CANCELLED by 0|0:9\n')
        got=self.fetch(p,'174303')
        self.assertNotEqual(got.returncode,0)
        self.assertIn('E85: job 174303 left no receipt and no nonzero trap record (scheduler state: 174303|CANCELLED by 0|0:9; ValueError: E81)',got.stderr)
        self.assertFalse((p/'a/f').exists())
        cases['no_record']=dict(error=got.stderr.strip().splitlines()[-1])
        self.evidence['preempted_fetch']=dict(passed=True,cases=cases)

    def test_time_guard(self):
        source=(self.package/'a/5.py').read_text()
        tree=ast.parse(source)
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='unit_config')
        scope={'os':os};exec(compile(ast.Module(body=[node],type_ignores=[]),'a/5.py','exec'),scope)
        cfg=json.loads(self.files['9.json']);self.assertEqual(cfg['budget_gpu_seconds'],3000)
        cases={}
        start=1_800_000_000
        for name,end in (('requested_50_min',start+3000),('later_end',start+3600),('no_end',None),('early_end',start+2000)):
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
