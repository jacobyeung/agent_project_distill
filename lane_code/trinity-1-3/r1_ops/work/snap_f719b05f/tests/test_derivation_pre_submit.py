"""Production-form record tests; all writes stay in this lane's local fixtures."""
import copy,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DRIVER=Path('/scratch/jjyeung/orch_n30/r1_ops/work/drv')
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')

class DerivationEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(tempfile.mkdtemp(prefix='pre_submit_',dir=ROOT/'work'))
        cls.bundle=ROOT/'out/operator';cls.source=cls.root/'source'
        shutil.copytree(DRIVER/'fixture_h',cls.source)
        # Only the absent data archives become sentinels; runtime bytes retain
        # their production pins. This fixture cannot attest native data.
        manifest=dict(reversed(line.split('  ',1)) for line in (cls.source/'SHA256SUMS.txt').read_text().splitlines())
        cls.sentinels=[]
        for name in manifest:
            path=cls.source/name
            if not path.exists():
                path.write_bytes(b'LOCAL TEST SENTINEL; NOT PRODUCTION\n')
                manifest[name]=sha(path);cls.sentinels.append(name)
        (cls.source/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()))
        if len(cls.sentinels)!=2:raise AssertionError('Fixture archive membership changed')
        if load(DRIVER/'fixture_b/BINDING.json')['config_identity']!=load(cls.bundle/'BINDING.json')['config_identity']:
            raise AssertionError('Driver fixture identity differs')
        # Use the same observed H1 records and builder as drv/test_local.py.
        old=cls.root/'old';old.mkdir();observed=(DRIVER/'o3.out').read_text()
        for name in ('review.json','staging.json','archive.json'):
            write(old/name,json.JSONDecoder().raw_decode(observed.split('== '+name+'\n',1)[1])[0])
        shutil.copyfile(cls.source/'k/4.json',old/'4.json')
        cls.evidence=cls.root/'e';cls.evidence.mkdir();write(cls.evidence/'c.json',{'missing':[],'fixture':True})
        spec=importlib.util.spec_from_file_location('driver_evidence',DRIVER/'evidence_body.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        builder.make_records(cls.bundle,cls.source,old,cls.evidence,{'missing':[]},
                             {'fixture':True,'reviews':{'review_r1p':'SIMULATED','review_r1p2':'SIMULATED'}})
        archived=load(cls.evidence/'archive.json')
        archived.update(location=load(ROOT/'out/OPERATOR.json')['bundle']+'/t.tar',fixture=True)
        write(cls.evidence/'archive.json',archived)
        native=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/evidence/fix7_selection/orchard_equal_6c18a2bf/o/native')
        receipt=load(native/'receipt.json');local=cls.root/'native';local.mkdir()
        for entry in receipt['sources'].values():
            if 'selection' in entry:
                name=Path(entry['selection']['path']).name
                shutil.copyfile(native/name,local/name);entry['selection']['path']=str(local/name)
        write(local/'receipt.json',receipt)
        subprocess.run([sys.executable,'-B',str(cls.bundle/'q.py'),'--parent',str(cls.source/'k/pool_selection_eac5f9f0.json'),
            '--indices',str(cls.source/'k'),'--native-receipt',str(local/'receipt.json'),
            '--implementation',str(cls.bundle/'j.json'),'--code-record',str(cls.bundle/'c.json'),
            '--out',str(cls.root/'q')],check=True,stdout=subprocess.DEVNULL)

    def derive(self,name,evidence=None):
        # A profile guard fails on entry to allocation-only code, without
        # replacing any verifier or persistent-writer function.
        runner="""import os,runpy,sys
from pathlib import Path
assert 'SLURM_JOB_ID' not in os.environ
allowed=Path(sys.argv[1]).resolve()
def audit(event,args):
    if event=='open':
        path,mode,flags=args
        writing=flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
    elif event in ('os.mkdir','os.chmod'):
        path=args[0];writing=True
    else:return
    if writing and isinstance(path,(str,bytes)) and not Path(os.fsdecode(path)).resolve().is_relative_to(allowed):
        raise AssertionError('Derivation wrote outside fixture: '+str(path))
def profile(frame,event,arg):
    if event=='call' and (frame.f_code.co_name=='persistent_launch' or Path(frame.f_code.co_filename).name=='r8.py'):
        raise AssertionError('Derivation entered allocation-time persistence')
sys.addaudithook(audit);sys.setprofile(profile)
sys.argv=sys.argv[2:]
runpy.run_path(sys.argv[0],run_name='__main__')
"""
        env={k:v for k,v in os.environ.items() if not k.startswith('SLURM')}
        args=[sys.executable,'-B','-c',runner,str(self.root),str(self.bundle/'d.py'),
              '--source',str(self.source),'--source-manifest-sha256',sha(self.source/'SHA256SUMS.txt'),
              '--packet',str(self.bundle),'--bundle',str(self.bundle),'--selection-evidence',str(self.root/'q/q.json'),
              '--evidence',str(evidence or self.evidence),'--out',str(self.root/name)]
        result=subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (self.root/(name+'.log')).write_text(result.stdout+result.stderr)
        return result

    def test_production_records_ready_without_slurm_or_persistent_writes(self):
        result=self.derive('ready');self.assertEqual(result.returncode,0,result.stderr)
        receipt=load(self.root/'ready.json');launch=load(self.root/'ready/k/launch.json')
        self.assertEqual(receipt['status'],'READY');self.assertEqual(launch['status'],'READY')
        self.assertFalse(receipt['production_authorized'])
        baseline=Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])
        for path in (baseline/'b').rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                self.assertEqual(sha(path),sha(self.root/'ready/b'/path.relative_to(baseline/'b')))
        self.assertEqual(sha(baseline/'job.sh'),sha(self.root/'ready/job.sh'))
        write(ROOT/'out/proof/PRE_SUBMISSION.json',dict(status='PASS',config_identity=receipt['config_identity'],
            operator_archive_sha256=sha(ROOT/'out'/load(ROOT/'out/OPERATOR.json')['archive']),
            slurm_identity_present=False,persistent_entry_called=False,writes_confined_to_fixture=True,
            inherited_runtime_unchanged=True,source_sentinels=self.sentinels,fixture=str(self.root),
            scope='Production-form records from driver builder; two missing data archives replaced only in local fixture; no production authorization or native data proof.'))

    def test_wrong_evidence_identity_refused_during_derivation(self):
        for filename in ('review.json','staging.json','4.json','archive.json'):
            with self.subTest(record=filename):
                evidence=self.root/('bad_'+filename);shutil.copytree(self.evidence,evidence)
                value=load(evidence/filename)
                value['tree_sha256' if filename=='archive.json' else 'config_sha256']='0'*64
                write(evidence/filename,value)
                result=self.derive('rejected_'+filename,evidence)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('Off-scratch source archive' if filename=='archive.json' else 'Evidence identity',result.stderr)
                self.assertFalse((self.root/('rejected_'+filename+'.json')).exists())

    def test_record_schema_and_bindings_refused(self):
        sys.path.insert(0,str(ROOT/'tools'))
        from derive_deployment import validate_evidence
        # Reuse a derived kit to keep negative record tests bounded.
        result=self.derive('mutants');self.assertEqual(result.returncode,0,result.stderr)
        kit=self.root/'mutants';launch=load(kit/'k/launch.json')
        mutations=[('review.json','verdict','PENDING'),('review.json','reviewer',''),
            ('review.json','source_revision','sha256:'+'0'*64),('review.json','admission_contract_sha256','0'*64),
            ('staging.json','missing',['missing']),('staging.json','project_community_write_bytes',1),
            ('staging.json','source_revision','sha256:'+'0'*64),('archive.json','durable',False),
            ('archive.json','sha256','0'*64),('archive.json','location','/tmp/fixture'),
            ('4.json','modes',['t']),('4.json','source_revision','sha256:'+'0'*64),
            ('4.json','admission_contract_sha256','0'*64),('4.json','allow_until_utc','2026-11-21T00:00:00Z')]
        for filename,key,value in mutations:
            with self.subTest(record=filename,field=key):
                path=kit/'k'/filename;raw=path.read_bytes();record=load(path);record[key]=value;write(path,record)
                altered=copy.deepcopy(launch)
                if filename!='4.json':altered[filename[:-5]]['sha256']=sha(path)
                write(kit/'k/launch.json',altered)
                with self.assertRaises(ValueError):validate_evidence(kit)
                path.write_bytes(raw);write(kit/'k/launch.json',launch)

if __name__=='__main__':unittest.main(verbosity=2)
