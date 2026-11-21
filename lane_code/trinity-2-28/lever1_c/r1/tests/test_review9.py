"""Check durable output and shell limits without a scheduler."""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import runpy
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(HERE),str(HERE/'tests')]
import import_audit as A
import test_bootstrap as B


class Review9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info=json.loads((HERE/'out/BUILD.json').read_text())
        cls.outer=A.unpack((HERE/'out/delivery.tgz').read_bytes())
        cls.evidence=dict(delivery_sha256=hashlib.sha256((HERE/'out/delivery.tgz').read_bytes()).hexdigest())
    @classmethod
    def tearDownClass(cls):
        (HERE/'out/REVIEW9_CHECKS.json').write_text(json.dumps(cls.evidence,indent=2)+'\n')

    def test_all_delivered_output_routes(self):
        pending=list(self.outer.items());seen=set();allowlist=[]
        pending += [('shell/'+p.name,p.read_bytes()) for p in (HERE/'orchard').glob('*.sh')]
        while pending:
            name,data=pending.pop();key=hashlib.sha256(data).hexdigest()
            if key in seen:continue
            seen.add(key)
            if data.startswith(b'\x1f\x8b'):
                pending.extend((name+'/'+n,d) for n,d in A.unpack(data).items());continue
            text=data.decode('utf-8',errors='replace')
            for line in text.splitlines():
                if '/dev/null' in line:
                    # Immutable serving policy names allowed system reads;
                    # it never opens, redirects, or submits an output there.
                    self.assertTrue(line.startswith('SYSTEM_PREFIXES = '),(name,line[:200]))
                    allowlist.append(name)
            if name.endswith('.sh') and "<<'A'\n" in text:
                text=text.split("<<'A'\n",1)[1].rsplit('\nA',1)[0]
            try:tree=ast.parse(text)
            except (SyntaxError,ValueError):continue
            for node in ast.walk(tree):
                if isinstance(node,ast.Constant) and isinstance(node.value,str) and len(node.value)>100:
                    try:raw=bytes.fromhex(node.value)
                    except ValueError:continue
                    pending.append((name+'/literal.py',raw))
        self.assertEqual(len(allowlist),1)
        self.evidence['output_route_scan']=dict(passed=True,unique_files_and_embedded_blobs=len(seen),discarding_routes=[],read_policy_allowlist=allowlist)

    def test_supervisor_overflow_real_batch_header(self):
        root,p,pub,env,argv=B.BootstrapTests.setup_case(self,'supervisor_noise')
        header=(p/'BATCH.sh').read_text().split('/usr/bin/python3 -I -s -B - ',1)[0]
        header=header.replace('/project/community/jjyeung/'+pub['token']+'/a/',str(p/'a')+'/')
        script=root/'overflow.sh';script.write_text(header+shlex.join(argv)+'\n')
        result=subprocess.run(['bash',str(script)],env=env,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((p/'a/19').stat().st_size,524288)
        fetch=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
               '/project/community/jjyeung/okh7/ae71c903',str(root/'pool'),'173925',str(HERE/'orchard/o_fetch.sh')]
        got=subprocess.run(fetch,env=env,capture_output=True)
        self.assertEqual(got.returncode,0,got.stderr)
        with tarfile.open(p/'a/f/0.tgz') as archive:
            cause=B.decoded(archive.extractfile('metadata/14.json').read())
            self.assertTrue(any('E83 19' in line for line in cause['lines']))
        size=sum(f.stat().st_size for base in (p,root/'pool') for f in base.rglob('*') if f.is_file())
        size+=(HERE/'out/delivery.tgz').stat().st_size
        self.assertLess(size,48_000_000)
        self.evidence['supervisor_overflow']=dict(passed=True,sink_bytes=524288,production_failure_fetch=True,project_observed_bytes=size,cause=cause)

    def test_scheduler_files_and_submission_failure(self):
        root=Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='sink_'))/'a';root.mkdir()
        body=b'#!/bin/bash\nulimit -S -f 512\n';(root.parent/'BATCH.sh').write_bytes(body)
        helper=root/'27.py';helper.write_bytes(self.outer['a/27.py'])
        submit=runpy.run_path(str(helper))['submit'];calls=[]
        def control(argv,**kwargs):
            self.assertEqual(argv[0],'sbatch');calls.append(argv)
            for name in ('19','24','21'):
                self.assertTrue(stat.S_ISREG((root/name).stat().st_mode))
            return subprocess.CompletedProcess(argv,1,stdout=b'1001\n',stderr=b'injected submission failure')
        with patch.object(subprocess,'run',side_effect=control):
            result=submit(root,['sbatch','--parsable'],input=body,capture_output=True)
        self.assertEqual(result.returncode,1);self.assertEqual(len(calls),1)
        with patch.object(subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'E84'):submit(root,['sbatch'],input=b'uncapped batch',capture_output=True)
            run.assert_not_called()
        (root/'19').write_bytes(b'x'*524288)
        with patch.object(subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'E76'):submit(root,['sbatch'],input=body,capture_output=True)
            run.assert_not_called()
        bounded=3*524288
        self.assertLess(bounded,2_000_000)
        self.evidence['scheduler_files']=dict(passed=True,sealed_batch_only=True,no_collector=True,no_fifo=True,failure_preserved=True,precreated=True,oversize_rejected=True,combined_diagnostics_bound=bounded,total_project_bound=48_000_000)

    def test_shell_file_limit_remains_in_force(self):
        batch=self.outer['BATCH.sh'].decode()
        source=batch.split("<<'A'\n",1)[1].rsplit('\nA',1)[0]
        self.assertNotIn('resource.setrlimit',source)
        root=Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='limit_'))
        (root/'27.py').write_bytes(self.outer['a/27.py'])
        header=batch.split('/usr/bin/python3 -I -s -B - ',1)[0].replace('/project/community/jjyeung/'+self.info['token']+'/a/',str(root)+'/')
        code="import os,resource,signal,sys\nassert resource.getrlimit(resource.RLIMIT_FSIZE)[0]==524288\nsignal.signal(signal.SIGXFSZ,signal.SIG_IGN)\nf=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT,0o600)\ntry:\n for _ in range(256):os.write(f,b'x'*8192)\nexcept OSError:pass\nelse:raise AssertionError('limit absent')\n"
        script=root/'test.sh';script.write_text(header+shlex.join([sys.executable,'-I','-s','-B','-c',code,str(root/'26')])+'\n')
        result=subprocess.run(['bash',str(script)],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((root/'26').stat().st_size,524288)
        self.evidence['fsize']=dict(passed=True,cap=524288,restored_in_supervisor=False)


if __name__=='__main__':unittest.main(verbosity=2)
