from pathlib import Path
import fcntl,json,os,runpy,sys,tarfile,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24f'
sys.path[:0]=[str(D),str(L/'work/build24')]
import live as C,live_tests as F,joblib as J
F.D=D/'runtime_tests';F.D.mkdir(exist_ok=True)
for n in ('live.py','live.sh'):(F.D/n).write_bytes((D/n).read_bytes())
EVIDENCE={}


class Runtime(unittest.TestCase):
    def test_native_archive_race(self):
        c,root=F.fixture('race');marker=F.state(c,'m100');identity=C.sha(marker)
        persist=c.train/'persist';persist.mkdir();(persist/(identity+'.local.claim')).write_text(identity)
        with self.assertRaisesRegex(ValueError,'E100'):c.exports()
        self.assertFalse(list(c.spool.glob('*.tar')))
        archive=persist/(identity+'.tar')
        with tarfile.open(archive,'w') as t:
            for p in sorted(marker.parent.iterdir()):t.add(p,arcname=p.name)
        C.put(persist/(identity+'.local.json'),dict(source={'sha256':identity},archive=dict(path='/logical/persist/'+archive.name,sha256=C.sha(archive))))
        c.exports();self.assertEqual(C.read(c.live/'gcs_m100.json')['archive'],str(archive))
        C.put(c.home/'sess.json',{});c.exports()
        self.assertTrue((c.live/'gcs_m100.done').exists());self.assertFalse(list(c.spool.glob('*.tar')))
        EVIDENCE['native_archive_reused']=C.read(c.live/'gcs_m100.done')

    def test_small_copy_does_not_wait_for_weight_lock(self):
        c,root=F.fixture('independent');(c.root/'t.log').write_text('during upload\n')
        with (c.spool/'lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);start=time.monotonic();c.small()
            self.assertLess(time.monotonic()-start,1)
        self.assertEqual((c.live/'t.log').read_text(),'during upload\n')
        EVIDENCE['independent_small_copy']=True

    def test_batch_clock_and_launcher_inheritance(self):
        import subprocess
        value='1795111111';k=L/'out/kit_n_go';calls=[]
        def launch(*a,**kw):calls.append((a,kw));return SimpleNamespace(returncode=0)
        with patch.dict(os.environ,{'TK_JOB_START':value}),patch.object(sys,'argv',[str(k/'b/t.py'),'/tmp/q/p','/tmp/q/v.json']),patch('subprocess.run',launch):
            with self.assertRaises(SystemExit) as e:runpy.run_path(str(k/'b/t.py'),run_name='__main__')
        self.assertEqual(e.exception.code,0);self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][1]['env']['TK_JOB_START'],value)
        self.assertIn('--nproc_per_node=4',calls[0][0][0])
        args=J.load(D/'sequence_final/n/view.json')
        result=subprocess.run(args+['--setenv','TK_JOB_START',value,'/opt/py/bin/python3.12','-B','-c','import os; print("TK_JOB_START="+os.environ["TK_JOB_START"])'],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'TK_JOB_START='+value)
        print(result.stdout.strip(),flush=True)
        EVIDENCE['clock']=dict(bwrap_stdout=result.stdout.strip(),launcher_environment=value,actual_distributed_workers='external go_rehearsal.sh')


if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Runtime))
    (D/'RUNTIME_TESTS.json').write_text(json.dumps(dict(passed=r.wasSuccessful(),tests=r.testsRun,evidence=EVIDENCE),indent=2)+'\n')
    raise SystemExit(not r.wasSuccessful())
