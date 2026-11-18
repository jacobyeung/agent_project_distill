"""Run the emitted launch gate with local kit evidence and a stub squeue."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from canary_gate import OLD_KH, RECEIPT_SHA, LOG_SHA
from rebind import ROOT, load, sha, write

ACTIVE_A = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_9dd2fbb7')
SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_a5dc8f30')
EVIDENCE = Path('/scratch/jjyeung/orch_n30/r1_ops/work')


def body(script):
    return script.split("<<'P'\n", 1)[1].split('\nP\n', 1)[0]


class Fix12(unittest.TestCase):
    def fixture(self, *, job_file=True):
        root = Path(tempfile.mkdtemp(prefix='gate12_', dir=ROOT/'work'))
        k, b, old, binpath = [root/n for n in ('kit', 'bundle', 'old', 'bin')]
        for d in (k/'k', k/'b', k/'o', b, old/'k', old/'b', old/'o', binpath):
            d.mkdir(parents=True, exist_ok=True, mode=0o700)
        for d in (k,b,old):d.chmod(0o700)
        source = Path(load(ACTIVE_A/'out/proof/DERIVATION.json')['fixture_paths'][0])
        for name in ('k/0.json', 'b/c.sh'):
            (k/name).write_bytes((source/name).read_bytes())
            (old/name).write_bytes((source/name).read_bytes())
        cfg = load(ACTIVE_A/'out/config.json')
        for target in (k, old):
            write(target/'k/cfg.json', cfg)
            write(target/'k/launch.json', dict(config=dict(file='k/cfg.json',sha256=sha(target/'k/cfg.json'))))
        (k/'b/a.py').write_text("from pathlib import Path\ndef main(k):\n (Path(k)/'verified').write_text('yes')\n")
        for target in (k, old):
            (target/'SHA256SUMS.txt').write_text(''.join(sha(target/n)+'  '+n+'\n' for n in ('k/0.json','k/cfg.json','b/c.sh')))
        for n in ('ids.json', 'jb.sh', 'd.json'):
            (b/n).write_bytes((ACTIVE_A/'out/operator'/n).read_bytes())
        ids = load(b/'ids.json')
        write(b/'go.json', dict(production_go_granted=True,config_sha256=ids['identity'],
            admission_contract_sha256=ids['contract'],wrapper_sha256=sha(b/'jb.sh'),
            manifest_sha256=sha(k/'SHA256SUMS.txt'),canary=True))
        if job_file:(b/'job.id').write_text('171200\n')
        r = load(EVIDENCE/'f170956.proof.json')
        r['manifest_sha256'] = sha(old/'SHA256SUMS.txt')
        r['config'] = load(old/'k/launch.json')['config']
        write(old/'o/170956.proof.json', r)
        (old/'o/170956.proof.log').write_bytes((EVIDENCE/'f170956.proof.log').read_bytes())
        sq = binpath/'squeue'
        sq.write_text('#!/bin/bash\nset -eu\n[[ "$TZ" == UTC ]]\n'
            '[[ "$*" == "--noheader --jobs 171200 --format=%i|%T|%j" ]]\n'
            'printf "%s\\n" "${SQ_ROW-171200|RUNNING|a15_cot_ap673bc60f}"\nexit "${SQ_RC:-0}"\n')
        sq.chmod(0o700)
        code = body((ACTIVE_A/'out/operator/s.sh').read_text()).replace(repr(OLD_KH), repr(str(old)))
        # Only the fixture receipt pin changes: its manifest and config paths
        # refer to local bytes. The real receipt/log pins get a separate test.
        code = code.replace(RECEIPT_SHA, sha(old/'o/170956.proof.json'))
        return dict(root=root,k=k,b=b,old=old,code=code,env=dict(os.environ,
            PROOF_JOB='171200',ADMISSION_JOB='170956',PATH=str(binpath)+':'+os.environ['PATH']))

    def run_gate(self, f, ok=False):
        r = subprocess.run([sys.executable,'-I','-B','-',str(f['k']),str(f['b'])],
            input=f['code'],env={k:v for k,v in f['env'].items() if k!='PYTHONOPTIMIZE'},
            text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.assertEqual(r.returncode==0, ok, r.stdout)
        self.assertEqual((f['k']/'verified').exists(),ok)
        if ok and load(f['b']/'go.json').get('canary') is True:
            record=load(f['k']/'o/171200.canary.json')
            self.assertIs(record['canary'],True)
            self.assertEqual(record['admission_job'],'170956')
            self.assertEqual(record['proof_job'],'171200')
        elif not ok:
            self.assertFalse((f['k']/'o/171200.canary.json').exists())

    def test_pass_branch_and_submit_line_byte_equal(self):
        before=(SNAP/'out/operator/s.sh').read_text();after=(ACTIVE_A/'out/operator/s.sh').read_text()
        old=body(before);new=body(after)
        start=old.index("assert re.fullmatch('[1-9][0-9]*',job)")
        end=old.index("\nsys.path.insert",start)
        branch=new.split('\nelse:\n',1)[1].split('\nsys.path.insert',1)[0]
        self.assertEqual('\n'.join(x[1:] for x in branch.splitlines()).rstrip(),old[start:end].rstrip())
        self.assertEqual(before.split('\nP\n',1)[1],after.split('\nP\n',1)[1])
        self.assertEqual(old[:start],new[:new.index("if go.get('canary') is True:")])

    def test_real_evidence_pins(self):
        self.assertEqual(sha(EVIDENCE/'f170956.proof.json'),RECEIPT_SHA)
        self.assertEqual(sha(EVIDENCE/'f170956.proof.log'),LOG_SHA)
        script=(ACTIVE_A/'out/operator/s.sh').read_text()
        for value in (OLD_KH,RECEIPT_SHA,LOG_SHA):self.assertIn(value,script)

    def test_canary_pending_and_running(self):
        for state in ('PENDING','RUNNING'):
            with self.subTest(state=state):
                f=self.fixture();f['env']['SQ_ROW']='171200|'+state+'|a15_cot_ap673bc60f'
                self.run_gate(f,True)

    def test_full_shell_canary_reaches_unchanged_sbatch(self):
        f=self.fixture();b=f['b'];k=f['k']
        (b/'sums.txt').write_text(''.join(sha(b/n)+'  '+n+'\n' for n in ('ids.json','jb.sh','d.json')))
        sbatch=f['root']/'bin/sbatch'
        sbatch.write_text('#!/bin/bash\nset -eu\n[[ "$TZ" == UTC ]]\n'
            '[[ -z "${TK_JOB_START+x}" ]]\nprintf "%s\\n" "$@" > "$ARGV_FILE"\n')
        sbatch.chmod(0o700)
        script=(ACTIVE_A/'out/operator/s.sh').read_text()
        script=script.replace(body(script),f['code'])
        for key,value in (('O',f['root']),('BUN',b),('KH',k)):
            script='\n'.join(key+'='+shlex.quote(str(value)) if line.startswith(key+'=') else line for line in script.split('\n'))
        script=script.replace('env -u PYTHONOPTIMIZE python3 -I -B - ',
            'env -u PYTHONOPTIMIZE '+shlex.quote(sys.executable)+' -I -B - ')
        f['env'].update(ARGV_FILE=str(f['root']/'argv'),TK_JOB_START='must-unset',PYTHONOPTIMIZE='2')
        r=subprocess.run(['bash','-c',script],env=f['env'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.assertEqual(r.returncode,0,r.stdout)
        self.assertTrue(load(k/'o/171200.canary.json')['canary'])
        self.assertEqual((f['root']/'argv').read_text().splitlines(),['-J','a15_cot_ap673bc60f','-o','/dev/null',
            '-e',str(k/'o/%j.err'),'-A','mt01','-p','advanced','-N1','--ntasks=1','--gres=gpu:4',
            '-c','48','--mem=800G','-t','13:00:00','--signal=B:USR1@3600','--no-requeue',str(b/'jb.sh')])

    def test_no_canary_uses_pass_path(self):
        for flag in (None,False,'true',1):
            with self.subTest(flag=flag):
                f=self.fixture();go=load(f['b']/'go.json');go.pop('canary')
                if flag is not None:go['canary']=flag
                write(f['b']/'go.json',go);self.run_gate(f)

    def test_pass_fixture_and_predicate_refusals(self):
        base=dict(status='PASS',rc=0,job='171200',cuda_visible_devices='',effective_config_verified=True,
            first_batch_executed=False,training_executed=False,admission_result=dict(status='PREPARED'),
            prepared_seals={'fixture':True},real_job_reuse=False,
            checks={n:dict(status='PASS') for n in ('disk_plan','routing_selection','empty_root','temporary_paths',
                'runtime_binaries','directory_modes','loader_audit','required_families')})
        mutations=[None,('status','FAIL'),('rc',1),('job','other'),('effective_config_verified',False),
            ('first_batch_executed',True),('training_executed',True),('prepared_seals',None),('real_job_reuse',True),
            ('cuda_visible_devices','0'),('admission_result',{'status':'FAIL'}),('checks',{})]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                f=self.fixture();go=load(f['b']/'go.json');go.pop('canary');write(f['b']/'go.json',go)
                proof=copy.deepcopy(base);proof.update(config_identity=go['config_sha256'],contract_sha256=go['admission_contract_sha256'],
                    config=load(f['k']/'k/launch.json')['config'],manifest_sha256=go['manifest_sha256'],wrapper_sha256=go['wrapper_sha256'])
                if mutation:proof[mutation[0]]=mutation[1]
                write(f['k']/'o/171200.proof.json',proof);self.run_gate(f,mutation is None)

    def test_admission_job_refusals(self):
        for job in ('','170955','0170956','170956\n'):
            with self.subTest(job=job):
                f=self.fixture();f['env']['ADMISSION_JOB']=job;self.run_gate(f)

    def test_proof_job_refusals(self):
        for job in ('','abc','0','-1','171201','170956','171200;id'):
            with self.subTest(job=job):
                f=self.fixture();f['env']['PROOF_JOB']=job;self.run_gate(f)
        f=self.fixture();f['env'].pop('PROOF_JOB');self.run_gate(f)
        self.run_gate(self.fixture(job_file=False))

    def test_queue_refusals(self):
        for row in ('','171200|COMPLETED|a15_cot_ap673bc60f','171200|FAILED|a15_cot_ap673bc60f',
                    '171200|RUNNING|wrong','171201|RUNNING|a15_cot_ap673bc60f',
                    '171200|RUNNING|a15_cot_ap673bc60f\n171200|PENDING|a15_cot_ap673bc60f'):
            with self.subTest(row=row):
                f=self.fixture();f['env']['SQ_ROW']=row;self.run_gate(f)
        f=self.fixture();f['env']['SQ_RC']='1';self.run_gate(f)

    def test_receipt_and_log_sha_refusals(self):
        for name in ('170956.proof.json','170956.proof.log'):
            with self.subTest(name=name):
                f=self.fixture();p=f['old']/'o'/name;p.write_bytes(p.read_bytes()+b' ');self.run_gate(f)

    def test_receipt_semantic_refusals(self):
        for key,value in (('config_identity','wrong'),('contract_sha256','wrong'),('job','170955')):
            with self.subTest(key=key):
                f=self.fixture();p=f['old']/'o/170956.proof.json';before=sha(p)
                r=load(p);r[key]=value;write(p,r);f['code']=f['code'].replace(before,sha(p));self.run_gate(f)

    def test_log_without_exit_and_remove_hash_refused(self):
        for a,b in (('exit rc=0','exit rc=1'),('02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411','0'*64)):
            with self.subTest(mutation=a):
                f=self.fixture();p=f['old']/'o/170956.proof.log';p.write_text(p.read_text().replace(a,b))
                f['code']=f['code'].replace(LOG_SHA,sha(p));self.run_gate(f)

    def test_staged_hash_and_old_manifest_refusals(self):
        f=self.fixture();p=f['k']/'k/0.json';r=load(p);r['extra'][0]['sha256']='0'*64;write(p,r);self.run_gate(f)
        f=self.fixture();p=f['old']/'SHA256SUMS.txt';p.write_text(p.read_text()+'\n');self.run_gate(f)
        f=self.fixture();p=f['old']/'k/0.json';p.write_bytes(p.read_bytes()+b' ');self.run_gate(f)

    def test_existing_go_fields_still_required(self):
        for key in ('production_go_granted','config_sha256','admission_contract_sha256','wrapper_sha256','manifest_sha256'):
            with self.subTest(key=key):
                f=self.fixture();go=load(f['b']/'go.json');go.pop(key);write(f['b']/'go.json',go);self.run_gate(f)


if __name__=='__main__':unittest.main(verbosity=2)
