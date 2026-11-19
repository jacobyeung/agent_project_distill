"""Exercise sealed kit imports, writable local copies and CPU partitions."""
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from rebind import ROOT, load, sha, write


class ZContinuationModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kit = Path(load(ROOT/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'
        spec = importlib.util.spec_from_file_location('proof_c2', ROOT/'out/proof/p.py')
        cls.proof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.proof)

    def root(self):
        return Path(tempfile.mkdtemp(prefix='cont2_test_', dir=ROOT/'work'))

    def test_derived_code_directories_are_sealed(self):
        for kit in [self.kit, *map(Path, load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'])]:
            directories = [kit/'b', *(p for p in (kit/'b').rglob('*') if p.is_dir())]
            self.assertGreater(len(directories), 1)
            for p in directories:
                self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o500, str(p))
            self.assertEqual(list((kit/'b').rglob('*.pyc')), [])

    def test_isolated_job_prefix_preserves_inventory(self):
        root = self.root(); kit = root/'kit'
        def clone(src, dst):
            if Path(src).suffix in ('.tar','.gz') and Path(src).stat().st_size > 1_000_000:
                os.link(src, dst); return dst
            return shutil.copy2(src, dst)
        shutil.copytree(self.kit, kit, copy_function=clone)
        launch = load(kit/'k/launch.json')
        launch['persistent_run_root'] = str(root/'slots')
        write(kit/'k/launch.json', launch)
        sums = kit/'SHA256SUMS.txt'
        names = [line.split('  ', 1)[1] for line in sums.read_text().splitlines()]
        sums.write_text(''.join(sha(kit/n)+'  '+n+'\n' for n in names))
        write(kit/'ANON_OK.json', dict(status='CLEAN', hits=0, manifest_sha256=sha(sums), fixture=True))
        env = {**os.environ, 'SLURM_JOB_ID':'191201', 'TK_KIT_HOME':str(kit),
               'SLURM_JOB_PARTITION':'general','SLURM_JOB_NUM_NODES':'1','SLURM_GPUS_ON_NODE':'0',
               'PYTHONDONTWRITEBYTECODE':'1', 'CUDA_VISIBLE_DEVICES':''}
        isolated=subprocess.run([sys.executable,'-I','-c',
            'import sys; assert sys.flags.isolated and not sys.dont_write_bytecode'],env=env,capture_output=True)
        self.assertEqual(isolated.returncode,0,isolated.stderr)
        for command in ([str(kit/'b/p0.py'),str(kit),'p','--metadata-only'],
                        [str(kit/'b/g.py'),str(kit),'p'],
                        [str(kit/'b/r8.py'),launch['run_directory'],'--kit',str(kit)]):
            result = subprocess.run([sys.executable,'-I',*command], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable,'-B',str(kit/'b/a.py'),str(kit)],
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((kit/'b/__pycache__').exists())
        self.assertEqual(list((kit/'b').rglob('*.pyc')), [])
        self.assertTrue((root/'slots/RUN.json').is_file())
        # Exercise the continuation-only import under the same isolated CLI.
        import continuation
        donor_root=root/'donor'
        continuation.fixture(donor_root,load(kit/'k/a0.json'),load(kit/'k/7.json'))
        launch['run_directory']=str(donor_root)
        launch['persistent_run_root']=str(root/'donor_slots')
        write(kit/'k/launch.json',launch)
        sums.write_text(''.join(sha(kit/n)+'  '+n+'\n' for n in names))
        write(kit/'ANON_OK.json',dict(status='CLEAN',hits=0,manifest_sha256=sha(sums),fixture=True))
        result=subprocess.run([sys.executable,'-I',str(kit/'b/r8.py'),str(donor_root),'--kit',str(kit)],
                              env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'u')
        result=subprocess.run([sys.executable,'-B',str(kit/'b/a.py'),str(kit)],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(list((kit/'b').rglob('*.pyc')),[])


    def test_tk_nx_and_proof_directory_modes(self):
        root=self.root(); source=root/'source'; work=root/'work'
        source.mkdir(mode=0o700);work.mkdir(mode=0o700)
        shutil.copytree(self.kit/'b',source/'b')
        (source/'k').mkdir(mode=0o700)
        for name in ('k/0.json','SHA256SUMS.txt'):
            (source/name).write_bytes((self.kit/name).read_bytes())
        write(source/'ANON_OK.json',dict(fixture=True,manifest_sha256=sha(source/'SHA256SUMS.txt')))
        shell='set -euo pipefail\numask 077\n/usr/bin/python3() { '+shlex.quote(sys.executable)+' "$@"; }\n'
        shell+='export TK_KIT_HOME='+shlex.quote(str(source))+'\nsource "$TK_KIT_HOME/b/c.sh"\n'
        shell+='\n'.join(k+'='+shlex.quote(str(v)) for k,v in
                         dict(HX=source,HM=work/'mirror',NX=work/'nx',NR=work/'runs').items())
        shell+='\ntk_nx\n'
        result=subprocess.run(['/bin/bash','-c',shell],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.proof.directory_modes(work),dict(status='PASS',bad=[]))
        self.assertEqual(stat.S_IMODE((source/'b').stat().st_mode),0o500)
        self.assertEqual(stat.S_IMODE((work/'nx/b/sa').stat().st_mode),0o700)
        (work/'nx/b/sa').chmod(0o500)
        self.assertEqual(self.proof.directory_modes(work)['status'],'FAIL')

    def test_redeploy_refuses_sealed_kit_before_reading_archive(self):
        result=subprocess.run([sys.executable,'-I',str(self.kit/'b/z.py'),
                               '/nonexistent','0'*64,str(self.kit)],text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Sealed kit refuses in-place redeployment',result.stderr)

    def test_proof_authority_partitions_and_training_resources(self):
        auth=load(self.kit/'k/4.json')
        self.assertEqual(auth['allowed_partitions'],['advanced','general','bootstrap'])
        root=self.root()
        for partition in ('general','bootstrap'):
            out=root/(partition+'.json')
            result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/seal_proof.py'),
                '--kit',str(self.kit),'--bundle',str(ROOT/'out/operator'),
                '--binding',str(ROOT/'out/BINDING.json'),'--partition',partition,'--out',str(out)],
                text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            authority=load(out)
            self.assertEqual(authority['allowed_partitions'],['general','bootstrap'])
            with patch.dict(os.environ,dict(SLURM_JOB_PARTITION=partition,CUDA_VISIBLE_DEVICES='',SLURM_GPUS_ON_NODE='0')):
                self.assertEqual(self.proof.proof_allocation(authority)['partition'],partition)
                with self.assertRaisesRegex(ValueError,'not authorized'):
                    self.proof.proof_allocation({**authority,'allowed_partitions':[]})
        job=(self.kit/'job.sh').read_text()
        self.assertIn('--partition=advanced',job)
        self.assertIn('--gpus-per-node=4',job)
        self.assertIn('--time=24:00:00',job)
