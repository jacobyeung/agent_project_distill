"""Exercise the generated proof shell against the sealed kit functions."""
import importlib.util
import json
import os
import re
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest

from rebind import ROOT, load, sha, write

SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052')


class Fix11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('proof11', ROOT/'out/proof/p.py')
        cls.proof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.proof)
        cls.kit = Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])
        cls.key = load(ROOT/'out/BINDING.json')['run_key']

    def fixture(self, *, numpy=True, mutation=None, record_bad=False):
        root = Path(tempfile.mkdtemp(prefix='proof11_', dir=ROOT/'work'))
        kh = root/'kit'
        stage = root/('tmp/jjyeung/a_'+self.key)
        s = stage/'root'
        x = root/'mount'
        p = s/'c7d31ddd'
        record = b'{"fixture":true}\n'
        import hashlib
        record_sha = hashlib.sha256(record).hexdigest()
        closure = '_jobs/cp4tk_'+'c'*12
        for path in (kh/'b', kh/'k', kh/'o', s/'aws/u/ap/8865619b/u',
                     p/'data2root', p/'runs/aws128p_20261025/models', s/'epochs',
                     stage/'runs', stage/'x_170956', p/'anyhost',
                     p/closure/'site_alias', p/'venvs/rwtrain_torch211_cu129/bin',
                     x/'b/student_pilot', s/'np226'):
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
        # The real c.sh is sourced unchanged; only fixture paths are remapped
        # after sourcing, in place of the outer namespace's bind mounts.
        (kh/'b/c.sh').symlink_to(self.kit/'b/c.sh')
        (kh/'b/r.sh').write_text('set -euo pipefail\n'
            'export TK_JOBDIR=child_only R1_RUNTIME_RECORD=child_only TK_RUNS_DIR=child_only\n'
            'printf "stub admission rc=0\\n"\n')
        (p/'anyhost'/(record_sha+'.json')).write_bytes(b'changed' if record_bad else record)
        bw = root/'bwrap_stub'
        bw.write_text('#!'+sys.executable+'''\n
import json, os, pathlib, sys
args = sys.argv[1:]; i = 0; mounts = []
two = {'--ro-bind', '--bind', '--dev-bind', '--symlink'}
one = {'--proc', '--tmpfs', '--dir', '--remount-ro', '--uid', '--gid'}
while i < len(args) and args[i].startswith('--'):
    option = args[i]
    if option in two:
        source, target = args[i+1:i+3]
        if option != '--symlink': assert pathlib.Path(source).exists(), source
        mounts.append([option, source, target]); i += 3
    elif option in one: i += 2
    elif option == '--unshare-user': i += 1
    else: raise AssertionError(option)
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
(root/'environment.json').write_text(json.dumps(dict(os.environ), sort_keys=True))
(root/'mounts.json').write_text(json.dumps(mounts))
os.execv(args[i], args[i:])
''')
        bw.chmod(0o700)
        py = p/'venvs/rwtrain_torch211_cu129/bin/python'
        py.symlink_to(sys.executable)
        (x/'b/student_pilot/__init__.py').write_text('')
        (x/'b/student_pilot/loader_audit.py').write_text('''import json, os
from pathlib import Path
def main(x):
    assert x == str(Path(os.environ['FIXTURE_ROOT'])/'mount')
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    Path(os.environ['FIXTURE_ROOT'], 'loader_called.json').write_text(json.dumps({'status':'PASS','fixture':True}))
    print('loader-audit call reached under set -u', flush=True)
''')
        current = dict(commit='fixture', closure=dict(file='unused', sha256='c'*64),
                       bwrap=dict(file=str(bw), sha256=sha(bw)),
                       record=dict(file='unused', sha256=record_sha))
        if numpy: current['np'] = dict(file='unused', sha256='d'*64)
        write(kh/'k/0.json', current)
        full = self.proof.program((ROOT/'out/operator/jb.sh').read_text(),
                                  (self.kit/'job.sh').read_text())
        boundary = '\n/bin/bash "$ROOT/b/r.sh" p 0\n'
        self.assertEqual(full.count(boundary), 1)
        shell = full[full.index(boundary):]
        remap = '\n'.join(name+'='+shlex.quote(str(value)) for name, value in dict(
            S=s, U=s/'aws/u', NX=stage/'x_170956', NR=stage/'runs', X=x,
            AS=root/'as', AL=root/'al', P=p, EPOCHS=s/'epochs').items())+'\n'
        shell = shell.replace('source "$ROOT/b/c.sh"\n', 'source "$ROOT/b/c.sh"\n'+remap)
        if mutation: shell = mutation(shell)
        shell = 'set -euo pipefail\numask 077\n/usr/bin/python3() { '+shlex.quote(sys.executable)+' "$@"; }\nROOT='+shlex.quote(str(kh))+'\n'+shell
        (root/'entry.sh').write_text(shell)
        env = dict(PATH='/usr/bin:/bin', HOME=str(root), SLURM_JOB_ID='170956',
                   CUDA_VISIBLE_DEVICES='', FIXTURE_ROOT=str(root))
        def runner(args, **kwargs):
            return subprocess.run(args, env=env, **kwargs)
        outcome = self.proof.execute(['/bin/bash', '-s'], shell, root/'shell.log',
            lambda: dict(loader_fixture=load(root/'loader_called.json')), runner=runner)
        write(root/'receipt.json', outcome)
        return root, outcome

    def test_post_admission_nounset_through_loader_and_receipt(self):
        cases = []
        for numpy in (False, True):
            root, outcome = self.fixture(numpy=numpy)
            self.assertEqual(outcome['rc'], 0, (root/'shell.log').read_text())
            self.assertEqual(outcome['status'], 'PASS')
            self.assertEqual(outcome['loader_fixture']['status'], 'PASS')
            env = load(root/'environment.json')
            stage = root/('tmp/jjyeung/a_'+self.key)
            jobdir = stage/'jobs/170956.proof'
            self.assertEqual(env['TK_JOBDIR'], str(jobdir))
            self.assertEqual(env['TK_RUNS_DIR'], str(stage/'runs'))
            self.assertEqual(stat.S_IMODE(jobdir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE((jobdir/'tmp').stat().st_mode), 0o700)
            self.assertTrue(Path(env['R1_RUNTIME_RECORD']).is_file())
            self.assertEqual(env['ANYHOST_NEUTRAL_RUNTIME'], env['R1_RUNTIME_RECORD'])
            for name, suffix in dict(TMPDIR='tmp', HF_HOME='cache/hf',
                    XDG_CACHE_HOME='cache', TORCH_HOME='cache/torch',
                    TRITON_CACHE_DIR='cache/triton').items():
                self.assertEqual(env[name], str(jobdir/suffix))
            self.assertIn(['--bind', str(jobdir), str(jobdir)], load(root/'mounts.json'))
            for name in ('TK_KIT_HOME', 'R1_MOUNT', 'R1_TRAINER', 'TRAINER',
                         'ANYHOST_JOBS', 'PILOT_VENV', 'PYTHONPATH', 'A_SITE_PROFILE',
                         'STUDENT_MODEL_ROOT', 'STUDENT_FRAME_ROOT_MAP', 'C1_INIT_LOCAL'):
                self.assertTrue(env[name], name)
            self.assertEqual(env['PYTHONPATH'].startswith(str(stage/'root/np226')+':'), numpy)
            cases.append(dict(numpy=numpy, fixture=str(root), rc=outcome['rc'],
                              shell_sha256=sha(root/'entry.sh')))
        write(ROOT/'out/proof/POST_ADMISSION_SHELL.json', dict(status='PASS',
            config_identity=load(ROOT/'out/BINDING.json')['config_identity'],
            kit_c_sha256=sha(self.kit/'b/c.sh'), proof_sha256=sha(ROOT/'out/proof/p.py'),
            cases=cases, scope='Real sealed c.sh functions; stub admission, bwrap and loader body; no production execution'))

    def test_missing_environment_mutants_fail_under_nounset(self):
        for line, error in (
            ('export TK_JOBDIR="${S%/root}/jobs/${SLURM_JOB_ID:?}.proof"\n', 'TK_JOBDIR'),
            ('export R1_RUNTIME_RECORD="$P/anyhost/$proof_record_sha.json"\n', 'R1_RUNTIME_RECORD')):
            root, outcome = self.fixture(mutation=lambda s: s.replace(line, ''))
            self.assertNotEqual(outcome['rc'], 0)
            self.assertIn(error+': unbound variable', (root/'shell.log').read_text())
            self.assertFalse((root/'loader_called.json').exists())

    def test_private_jobdir_refuses_reuse_and_symlink(self):
        for setup in ('mkdir -m 700 "$TK_JOBDIR"\n', 'ln -s "$S" "$TK_JOBDIR"\n'):
            root, outcome = self.fixture(mutation=lambda s: s.replace(
                'mkdir -m 700 "$TK_JOBDIR"\n', setup+'mkdir -m 700 "$TK_JOBDIR"\n'))
            self.assertNotEqual(outcome['rc'], 0)
            self.assertFalse((root/'loader_called.json').exists())

    def test_staged_runtime_record_is_verified(self):
        root, outcome = self.fixture(record_bad=True)
        self.assertNotEqual(outcome['rc'], 0)
        self.assertIn('sha differs:', (root/'shell.log').read_text())
        self.assertFalse((root/'loader_called.json').exists())

    def test_all_kit_environment_reads_have_an_audited_owner(self):
        owners = {
            'c.sh source assignments': 'AS AL K X R HX IN REV P RR EPOCHS S U HM NX NR CUR COMMIT CLOSURE_DIR',
            'proof caller': 'TK_KIT_HOME TK_JOBDIR R1_RUNTIME_RECORD',
            'allocation validated by proof main': 'SLURM_JOB_ID',
            'tk_env before use': 'ANYHOST_JOBS PILOT_VENV PYTHONPATH TMPDIR',
            'optional guarded staging flag': 'TK_LIGHT',
        }
        reads = set(re.findall(r'\$\{?([A-Z_][A-Z_0-9]*)', (self.kit/'b/c.sh').read_text()))
        self.assertEqual(reads, {name for names in owners.values() for name in names.split()})
        write(ROOT/'out/proof/ENVIRONMENT_AUDIT11.json', dict(status='PASS',
            kit_c_sha256=sha(self.kit/'b/c.sh'),
            owners={owner: names.split() for owner, names in owners.items()},
            caller_parity=['TK_RUNS_DIR'],
            scope='All uppercase shell variable reads in c.sh, including staging and persistence; locals and positional arguments audited by their defining functions'))

    def test_identity_and_protected_bytes_unchanged(self):
        for name in ('r1p_code.tar',):
            self.assertEqual(sha(ROOT/'out'/name), sha(SNAP/'out'/name))
        self.assertEqual(load(ROOT/'out/config.json')['h1']['routing_pose_targets'], True)
        for path, expected in load(ROOT/'out/FIX11_PROTECTED_ARCHIVES.json').items():
            self.assertEqual(sha(ROOT/path), expected)
        old_kit = Path(load(SNAP/'out/proof/DERIVATION.json')['fixture_paths'][0])
        for name in ('b/c.sh', 'b/r.sh', 'b/p0.sh'):
            expected=(old_kit/name).read_text()
            if name=='b/c.sh':expected=expected.replace('rsync -rt "$HX/b"','rsync -rt --chmod=D700 "$HX/b"')
            self.assertEqual((self.kit/name).read_text().replace(self.key,'673bc60f'),expected)
        self.assertEqual(load(ROOT/'out/config.json')['continuation']['run'],'673bc60f')

    def test_archive_embeds_fixed_proof_and_reseals(self):
        import ast
        import base64
        import hashlib
        import zlib
        op = load(ROOT/'out/OPERATOR.json')
        archive = ROOT/'out'/op['archive']
        self.assertEqual(sha(archive), op['sha256'])
        self.assertNotIn(str(archive.relative_to(ROOT)), load(ROOT/'out/FIX11_PROTECTED_ARCHIVES.json'))
        with tarfile.open(archive) as tf:
            script = tf.extractfile(op['proof_script']).read().decode()
            for row in tf.extractfile('sums.txt').read().decode().splitlines():
                expected, name = row.split('  ', 1)
                self.assertEqual(hashlib.sha256(tf.extractfile(name).read()).hexdigest(), expected)
        blobline = next(line for line in script.splitlines() if line.startswith('raw=zlib.'))
        call = ast.parse(blobline).body[0].value.args[0]
        raw = zlib.decompress(base64.b64decode(ast.literal_eval(call.args[0])))
        self.assertEqual(raw, (ROOT/'out/proof/p.py').read_bytes())
        fixture = Path(load(ROOT/'out/proof/PRE_SUBMISSION.json')['fixture'])/'ready'
        output = Path(tempfile.mkdtemp(prefix='seal11_', dir=ROOT/'work'))/'authority.json'
        result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/seal_proof.py'),
            '--kit', str(fixture), '--bundle', str(ROOT/'out/operator'),
            '--partition', load(ROOT/'out/BINDING.json')['proof_partition'],
            '--binding', str(ROOT/'out/BINDING.json'), '--out', str(output)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0, result.stderr)
        authority = load(output)
        self.assertEqual(authority['bundle_files'][op['proof_script']], sha(ROOT/'out/operator'/op['proof_script']))
        self.assertEqual(authority['identity'], load(ROOT/'out/BINDING.json')['config_identity'])
        write(ROOT/'out/proof/RESEAL11.json', dict(status='PASS', fixture_authority=str(output),
            authority_sha256=sha(output), config_identity=authority['identity'],
            archive=op['archive'], archive_sha256=op['sha256'],
            scope='Local production-form deployment fixture; production authority must be resealed on the deployed kit'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
