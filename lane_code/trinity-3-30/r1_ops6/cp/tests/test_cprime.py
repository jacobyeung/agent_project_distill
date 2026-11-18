"""Cprime delta policy and emitted-gate refusals, using explicit local fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rebind import ROOT,load,write,sha
from build_cprime import SNAP
from cprime_gate import BASE,B1,GO,REMOVE_PATH,RECEIPT,LOG,ALLOWED,identity,digest,validate_delta,add_delta
from cprime_recovery import launch_contract

class Cprime(unittest.TestCase):
    def setUp(self):
        self.base=load(SNAP/'out/config.json');self.cfg=load(ROOT/'out/config.json')
        self.ids=load(ROOT/'out/CPRIME_IDENTITIES.json')
        contract=launch_contract();contract['directory']=self.cfg['output']+'/inputs'
        self.ids['contract']=digest(contract)

    def test_b1r_row_keys_and_non_pool_bytes_exact(self):
        from cprime_removal import SOURCE,ORIGINAL,PATTERN,transform
        original=SOURCE.read_bytes();changed=(ROOT/'out/records/z.json').read_bytes()
        self.assertEqual(sha(SOURCE),ORIGINAL)
        self.assertEqual(hashlib.sha256(changed).hexdigest(),B1)
        self.assertEqual(transform(original)[0],changed)
        left=original.splitlines(keepends=True);right=changed.splitlines(keepends=True)
        self.assertEqual(len(left),17879)
        self.assertEqual([json.loads(x)['row_key'] for x in left],[json.loads(x)['row_key'] for x in right])
        for a,b in zip(left,right,strict=True):
            ma=PATTERN.search(a);mb=PATTERN.search(b)
            self.assertEqual(a[:ma.start(2)]+a[ma.end(2):],b[:mb.start(2)]+b[mb.end(2):])
        self.assertNotIn(b'ARKIT',changed)

    def test_exact_config_delta(self):
        validate_delta(self.base,self.cfg,self.ids)
        self.assertEqual(self.cfg['remove_files'][:-1],self.base['remove_files'])
        self.assertEqual(self.cfg['type_mix']['streams']['routing'],self.base['type_mix']['streams']['routing'])

    def test_config_refuses_other_cell(self):
        cfg=copy.deepcopy(self.cfg);cfg['type_mix']['streams']['vqa']['cells']['room']['cents']+=1
        with self.assertRaisesRegex(ValueError,'allow-list'):validate_delta(self.base,cfg,self.ids)

    def test_config_refuses_store_pin(self):
        cfg=copy.deepcopy(self.cfg);cfg['streams']['vqa']['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'allow-list'):validate_delta(self.base,cfg,self.ids)

    def test_config_refuses_stop_step(self):
        cfg=copy.deepcopy(self.cfg);cfg['h1']['stop_after_step']=601
        with self.assertRaisesRegex(ValueError,'allow-list'):validate_delta(self.base,cfg,self.ids)

    def test_config_refuses_excluded_identity_field(self):
        cfg=copy.deepcopy(self.cfg);cfg['admission']['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'allow-list'):validate_delta(self.base,cfg,self.ids)

    def test_config_refuses_remove_and_path_mutants(self):
        for key in ('remove_files','output','preparation_output'):
            cfg=copy.deepcopy(self.cfg)
            if key=='remove_files':cfg[key]=list(reversed(cfg[key]))
            else:cfg[key]+='bad'
            with self.subTest(key=key),self.assertRaises(ValueError):validate_delta(self.base,cfg,self.ids)

    def fixture(self):
        root=Path(tempfile.mkdtemp(prefix='cprime_gate_',dir=ROOT/'work'));old=root/'old';k=root/'kit';b=root/'bundle'
        for d in (old/'o',old/'k',old/'b',k/'k',k/'b',k/'o',b):d.mkdir(parents=True,exist_ok=True)
        contract=launch_contract()
        oldcur=dict(extra=[dict(dest=self.cfg['type_mix']['unit_rows']['path'],sha256=self.cfg['type_mix']['unit_rows']['sha256'],parts=['unit'])])
        store=load(SNAP/'out/records/d.json')
        oldcur['extra'].append(dict(dest=store['database']['path'],sha256=store['database']['sha256'],parts=['database']))
        stage=b'fixture staging 05b8ac69';(old/'b/c.sh').write_bytes(stage)
        write(old/'k/config.json',self.base);write(old/'k/launch.json',dict(in_job_admission=contract))
        write(old/'k/0.json',oldcur)
        (old/'SHA256SUMS.txt').write_text(''.join(sha(old/n)+'  '+n+'\n' for n in ('k/config.json','k/launch.json','k/0.json','b/c.sh')))
        checks={n:dict(status='PASS') for n in ('directory_modes','empty_root','resume_pointer','runtime_binaries','temporary_paths')}
        checks['resume_pointer'].update(fixture=True,step=200,run='673bc60f')
        receipt=dict(job='172180',config_identity=BASE,checks=checks,manifest_sha256=sha(old/'SHA256SUMS.txt'),
            config=dict(file='k/config.json',sha256=sha(old/'k/config.json')),contract_sha256=digest(contract),
            runtime_sha256={'b/c.sh':sha(old/'b/c.sh')},selection=self.cfg['s1_routing']['selection'])
        write(old/'o/172180.proof.json',receipt)
        log='2026-11-18T04:00:00Z | exit rc=0\n'+''.join(json.dumps(dict(remove_list=dict(file=p)))+'\n' for p in self.base['remove_files'])
        (old/'o/172180.proof.log').write_text(log)
        write(k/'k/config.json',self.cfg)
        contract['directory']=self.cfg['output']+'/inputs'
        write(k/'k/launch.json',dict(config=dict(file='k/config.json',sha256=sha(k/'k/config.json')),in_job_admission=contract))
        cur=copy.deepcopy(oldcur);cur['extra'].append(dict(dest=REMOVE_PATH,sha256=B1,parts=[self.ids['bun']+'/z.json']))
        write(k/'k/0.json',cur);(k/'b/c.sh').write_bytes(stage.replace(b'05b8ac69',self.ids['run_key'].encode()))
        (k/'b/a.py').write_text("def main(k):\n (k/'verified').write_text('yes')\n")
        (k/'SHA256SUMS.txt').write_text('fixture manifest\n')
        write(b/'ids.json',self.ids);write(b/'config.json',self.cfg)
        (b/'c4.json').write_bytes((SNAP/'out/config.json').read_bytes())
        (b/'d.json').write_bytes((SNAP/'out/records/d.json').read_bytes());(b/'jb.sh').write_text('fixture wrapper')
        # B1 bytes are separately authenticated in the build; this small gate fixture substitutes a test digest everywhere.
        (b/'z.json').write_bytes(b'fixture B1\n')
        write(b/'go.json',dict(production_go_granted=True,config_sha256=self.ids['identity'],admission_contract_sha256=self.ids['contract'],
            wrapper_sha256=sha(b/'jb.sh'),manifest_sha256=sha(k/'SHA256SUMS.txt'),canary_delta=True,authority='sha256:'+GO))
        script=add_delta((SNAP/'out/operator/s.sh').read_text())
        code=script.split("<<'P'\n",1)[1].split('\nP\n',1)[0]
        # Replace only fixture locators/evidence pins. Keep config B1 and deterministic identity derivation unchanged.
        code=code.replace(repr(ALLOWED[1]),repr(str(old))).replace(RECEIPT,sha(old/'o/172180.proof.json')).replace(LOG,sha(old/'o/172180.proof.log'))
        code=code.replace("pinned(b/'z.json',B1)","pinned(b/'z.json',"+repr(sha(b/'z.json'))+")")
        env={key:value for key,value in os.environ.items() if key not in ('PYTHONOPTIMIZE','PROOF_JOB')}
        env.update(ADMISSION_JOB='172180',ADMISSION_KIT=str(old))
        return dict(root=root,old=old,k=k,b=b,code=code,env=env)

    def gate(self,f,success):
        result=subprocess.run([sys.executable,'-I','-B','-',str(f['k']),str(f['b'])],input=f['code'],env=f['env'],text=True,capture_output=True)
        self.assertEqual(result.returncode==0,success,result.stdout+result.stderr)
        self.assertEqual((f['k']/'verified').exists(),success)
        self.assertEqual((f['k']/'o/canary_delta.json').exists(),success)

    def test_gate_accepts_without_proof_job(self):self.gate(self.fixture(),True)

    def test_gate_accepts_pinned_production_review_binding(self):
        f=self.fixture()
        for root in (f['old'],f['k']):
            write(root/'k/review.json',dict(status='GO',fixture=True))
            cfg=load(root/'k/config.json');cfg['admission']=dict(path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/review.json',sha256=sha(root/'k/review.json'))
            write(root/'k/config.json',cfg)
            launch=load(root/'k/launch.json');launch.update(config=dict(file='k/config.json',sha256=sha(root/'k/config.json')),review=dict(file='k/review.json',sha256=sha(root/'k/review.json')))
            write(root/'k/launch.json',launch)
        old=f['old'];before=sha(old/'o/172180.proof.json')
        (old/'SHA256SUMS.txt').write_text(''.join(sha(old/n)+'  '+n+'\n' for n in ('k/config.json','k/launch.json','k/0.json','b/c.sh','k/review.json')))
        receipt=load(old/'o/172180.proof.json');receipt.update(config=load(old/'k/launch.json')['config'],manifest_sha256=sha(old/'SHA256SUMS.txt'))
        write(old/'o/172180.proof.json',receipt);f['code']=f['code'].replace(before,sha(old/'o/172180.proof.json'))
        self.gate(f,True)

    def test_gate_refuses_wrong_admission_job(self):
        f=self.fixture();f['env']['ADMISSION_JOB']='172181';self.gate(f,False)

    def test_gate_refuses_wrong_admission_pin(self):
        f=self.fixture();p=f['old']/'o/172180.proof.json';p.write_bytes(p.read_bytes()+b' ');self.gate(f,False)

    def test_gate_refuses_wrong_admission_log_pin(self):
        f=self.fixture();p=f['old']/'o/172180.proof.log';p.write_bytes(p.read_bytes()+b' ');self.gate(f,False)

    def test_gate_refuses_wrong_go_sha(self):
        f=self.fixture();go=load(f['b']/'go.json');go['authority']='sha256:'+'f'*64;write(f['b']/'go.json',go);self.gate(f,False)

    def test_gate_refuses_conflicting_modes(self):
        f=self.fixture();go=load(f['b']/'go.json');go['canary']=True;write(f['b']/'go.json',go);self.gate(f,False)

    def test_gate_refuses_unlisted_config_change(self):
        f=self.fixture();cfg=copy.deepcopy(self.cfg);cfg['h1']['stop_after_step']=800
        write(f['k']/'k/config.json',cfg);write(f['b']/'config.json',cfg)
        launch=load(f['k']/'k/launch.json');launch['config']['sha256']=sha(f['k']/'k/config.json');write(f['k']/'k/launch.json',launch)
        self.gate(f,False)

    def test_gate_refuses_staging_change(self):
        f=self.fixture();cur=load(f['k']/'k/0.json');cur['extra'][0]['sha256']='f'*64;write(f['k']/'k/0.json',cur);self.gate(f,False)

    def test_gate_retains_existing_pass_and_canary_bodies(self):
        old=(SNAP/'out/operator/s.sh').read_text();new=add_delta(old)
        oldbranch=old.split("if go.get('canary') is True:\n",1)[1].split('\nsys.path.insert',1)[0]
        newbranch=new.split("elif go.get('canary') is True:\n",1)[1].split('\nsys.path.insert',1)[0]
        self.assertEqual(newbranch,oldbranch)
        self.assertEqual(old.split('\nP\n',1)[1],new.split('\nP\n',1)[1])
        self.assertIn(RECEIPT,new);self.assertIn(LOG,new);self.assertIn(GO,new)

if __name__=='__main__':unittest.main(verbosity=2)
