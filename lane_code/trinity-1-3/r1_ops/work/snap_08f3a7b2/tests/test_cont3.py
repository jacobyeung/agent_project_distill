"""Exercise the sealed authority with the real gate and authorizer on CPU."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import unittest
from rebind import ROOT, load, sha, write
from r4 import fields, validate


class ZTrainingAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kit=Path(load(ROOT/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'

    def check(self, mode, partition, gpus, *, nodes='1', wall=None, allocation_mode=None, passes=True):
        # Only absent native data and persistent slots are fixtures. g.check,
        # i.authorize, x.ready and every resource/identity check execute normally.
        runner='''import copy,sys
from pathlib import Path
from unittest.mock import patch
root=Path(sys.argv[1]);mode=sys.argv[2];sys.path.insert(0,str(root/'b'))
import g,i,d,r8
def prepared(root,cfg,*args):
    cfg=copy.deepcopy(cfg)
    cfg['preparation']={'path':'/fixture/prepared.json','sha256':'0'*64}
    return cfg
with patch.object(d,'effective',side_effect=prepared),patch.object(r8,'main',return_value=mode):
    results=[]
    for check in (lambda:g.check(root,mode=mode),lambda:i.authorize(root,mode,'0')):
        try:check();results.append('PASS')
        except (ValueError,KeyError) as e:results.append(type(e).__name__+': '+str(e))
    print(__import__('json').dumps(results))
'''
        env={k:v for k,v in os.environ.items() if not k.startswith(('SLURM','TK_ALLOCATION_MODE'))}
        env.update(SLURM_JOB_PARTITION=partition,SLURM_GPUS_ON_NODE=str(gpus),SLURM_JOB_NUM_NODES=nodes,
                   SLURM_JOB_ID='191303',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
        if wall is not None:env['SLURM_TIMELIMIT']=wall
        if allocation_mode is not None:env['TK_ALLOCATION_MODE']=allocation_mode
        result=subprocess.run([sys.executable,'-I','-B','-c',runner,str(self.kit),mode],
                              env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        import json
        outcomes=json.loads(result.stdout)
        self.assertEqual([x=='PASS' for x in outcomes],[passes,passes],outcomes)

    def test_sealed_fields_and_manifest(self):
        auth=load(self.kit/'k/4.json');validate(auth)
        inventory={n:h for h,n in (row.split('  ',1) for row in (self.kit/'SHA256SUMS.txt').read_text().splitlines())}
        for name in ('k/4.json','b/r4.py','b/g.py','b/i.py','job.sh'):
            self.assertEqual(sha(self.kit/name),inventory[name])
        self.assertEqual(load(self.kit/'k/launch.json')['slot']['wall_seconds'],86400)
        self.assertFalse(auth['production_go_granted'])
        self.assertEqual(auth['resume'],'latest')
        for key in fields():
            mutant=copy.deepcopy(auth);mutant.pop(key)
            with self.assertRaises(ValueError):validate(mutant)
        write(ROOT/'out/proof/CONT3_AUTHORITY.json',dict(status='PASS',authority=auth,
            authority_sha256=sha(self.kit/'k/4.json'),manifest_sha256=sha(self.kit/'SHA256SUMS.txt'),
            scope='Local fixture; no production admission or GO'))

    def test_proof_modes(self):
        for partition in ('general','bootstrap'):
            self.check('p',partition,0,wall='240')

    def test_training_modes(self):
        for mode in ('t','u'):
            self.check(mode,'advanced',4,wall='1-00:00:00')

    def test_in_job_cpu_admission_uses_training_allocation(self):
        job=(self.kit/'job.sh').read_text();shell=(self.kit/'b/r.sh').read_text()
        self.assertLess(job.index('export TK_ALLOCATION_MODE=u'),job.index('"$ROOT/b/p0.sh"'))
        self.assertLess(shell.index('export TK_ALLOCATION_MODE="$1"'),shell.index('"$HX/b/r.sh" p'))
        for mode in ('t','u'):
            self.check('p','advanced',4,wall='1440',allocation_mode=mode)

    def test_wrong_modes_gpus_partitions_nodes_and_wall_refuse(self):
        for mode,partition,gpus in [('x','advanced',4),('invalid','general',0),
                ('p','general',4),('p','advanced',0),('p','advanced',4),
                ('u','advanced',0),('t','advanced',8),('u','general',4),('t','bootstrap',4)]:
            with self.subTest(mode=mode,partition=partition,gpus=gpus):
                self.check(mode,partition,gpus,passes=False)
        self.check('u','advanced',4,nodes='2',passes=False)
        self.check('u','advanced',4,wall='780',passes=False)
        self.check('p','general',0,wall='1440',passes=False)
        self.check('p','general',0,allocation_mode='u',passes=False)
        self.check('u','advanced',4,allocation_mode='p',passes=False)


if __name__=='__main__':unittest.main(verbosity=2)
