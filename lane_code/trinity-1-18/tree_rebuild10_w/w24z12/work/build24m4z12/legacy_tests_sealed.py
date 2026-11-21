from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

L=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12');D=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/work/build24m4z12/legacy_suite_sealed')
sys.path.insert(0,str(D))
import importlib.util
sp=importlib.util.spec_from_file_location('current_pc','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go/b/pc.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C)
C.CAP=2_000_000;C.LOG_CAP=500_000

WRITER="import os,sys,runpy,http.client,concurrent.futures\nfrom pathlib import Path\nsys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/work/build24m4z12')\nfrom strict_sink import Connection\n__import__('strict_sink').install()\nos.environ['STRICT_SESSIONS']=sys.argv[2]\nos.environ['STRICT_SINK']=os.environ.get('FAKE_SINK',str(Path(sys.argv[2]).parent/'objects'))\nkit=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n')\nif os.environ.get('STRICT_OLD')=='1':\n d=runpy.run_path(str(kit/'b/gc.py'),run_name='gc_runtime')\n d['main'].__globals__['ProcessPoolExecutor']=concurrent.futures.ThreadPoolExecutor\n raise SystemExit(d['main'](sys.argv[1:]))\nd=runpy.run_path(str(kit/'b/pc.py'),run_name='pc_runtime')\nraise SystemExit(d['writer_main']([str(kit/'b/gc.py'),*sys.argv[1:]]))\n"

EVIDENCE={}


def fixture(name):
    root=D/'live_tests_v2'/name;root.mkdir(parents=True,exist_ok=False)
    kit=root/'kit';(kit/'k').mkdir(parents=True);(kit/'b').mkdir()
    node=root/'node';node.mkdir();train=node/'p/q/r';train.mkdir(parents=True)
    target=root/'target';target.mkdir();home=target/'n_s';home.mkdir(mode=0o700)
    C.put(kit/'k/p.json',dict(n_root=str(target)))
    C.put(kit/'k/n.json',dict(output='/run/469ddece'))
    C.put(kit/'k/y.json',dict(objects={x:'q9/test/'+x+'.tar' for x in ('m100','mstop','mstopB','mstopC','ckstop','o',*('ck%02d'%i for i in range(16)))}))
    (kit/'b/pc.py').write_bytes(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go/b/pc.py').read_bytes());(kit/'b/pc.sh').write_bytes(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go/b/pc.sh').read_bytes())
    (kit/'b/writer.py').write_text(WRITER)
    (kit/'b/gc.py').write_bytes((L/'out/kit_n/b/gc.py').read_bytes())
    (kit/'b/sr.py').write_bytes(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go/b/sr.py').read_bytes())
    C.put(home/'sess.json',{v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,v in C.read(kit/'k/y.json')['objects'].items() for i in range(4)});os.chmod(home/'sess.json',0o600)
    (home/'sess_41.json').write_bytes((home/'sess.json').read_bytes());(home/'sess_41.json').chmod(0o600)
    # The launch finalizer uses these unchanged helpers with the new four-file kit.
    for name in ('o.py','z.py','wh.json','ep.py'):
        (kit/'b'/name).write_bytes((L/'out/kit_n_go/b'/name).read_bytes())
    for name in ('g.json','r.json'):
        (kit/'k'/name).write_bytes((L/'out/kit_n_go/k'/name).read_bytes())
    return C.Copier(kit,node,'41',home=home,writer=kit/'b/writer.py'),root


def state(c,name):
    d=c.train/name;d.mkdir()
    (d/'w.bin').write_bytes(b'weight boundary'*43)
    marker=d/('complete.json' if name.startswith('checkpoint_') else 'artifact.json')
    C.put(marker,dict(step=int(name.split('_')[-1]) if name.startswith('checkpoint_') else int(name[1:]),files={'w.bin':C.sha(d/'w.bin')}))
    return marker


class Live24F(unittest.TestCase):
    def test_byte_cap_and_marker_only_listing(self):
        c,root=fixture('cap')
        # Sparse input crosses the real production cap without allocating RAM.
        with (c.root/'t.log').open('wb') as f:f.seek(510_000);f.write(b'LAST')
        (c.root/'q.log').write_bytes(b'canary\n')
        (c.train/'metrics_41.jsonl').write_text('{"loss":1}\n')
        (c.root/'41.steps').write_text('stage ready\n')
        marker=state(c,'m100');state(c,'checkpoint_000001')
        copied=c.small()
        self.assertLessEqual(copied,50_000_000)
        self.assertEqual((c.live/'t.log').read_bytes()[-4:],b'LAST')
        self.assertFalse((c.live/'w.bin').exists())
        listing=C.read(c.live/'markers.json')
        self.assertEqual({x['name'] for x in listing},{'m100/artifact.json','checkpoint_000001/complete.json'})
        self.assertEqual(next(x['sha256'] for x in listing if x['name'].startswith('m100')),C.sha(marker))
        EVIDENCE['cap']=dict(copied_bytes=copied,limit=50_000_000,listing=listing)

    def test_no_sessions_retry_done_and_idempotence(self):
        c,root=fixture('retry');m=state(c,'m100')
        cached=c.spool/'private/sess.json';cached.rename(c.spool/'private/held.json')
        (c.home/'sess.json').rename(c.home/'held.json')
        with self.assertRaisesRegex(ValueError,'file missing'):C.Copier(c.kit,c.root,'41',home=c.home)
        (c.home/'held.json').rename(c.home/'sess.json');(c.spool/'private/held.json').rename(cached)
        C.put(c.home/'sess.json',{});os.chmod(c.home/'sess.json',0o600)
        c.writer.write_text('raise SystemExit(1)\n');c.exports()
        self.assertFalse((c.state/'gcs_m100.done').exists())
        c.writer.write_text(WRITER);c.exports()
        done=c.state/'gcs_m100.done';v=C.read(done);stamp=done.stat().st_mtime_ns;c.exports()
        self.assertEqual(done.stat().st_mtime_ns,stamp)
        archive=next(c.spool.glob('*.tar'))
        self.assertEqual(v['sha256'],C.sha(archive));self.assertEqual(v['bytes'],archive.stat().st_size)
        self.assertEqual(v['marker_sha256'],C.sha(m));EVIDENCE['export']=v

    def test_stop_generation_claims_once(self):
        c,root=fixture('claims');C.put(c.home/'sess.json',{});os.chmod(c.home/'sess.json',0o600)
        for step in (3,7,9):state(c,'m'+str(step))
        c.exports()
        names={C.read(p)['generation'] for p in c.state.glob('gcs_*.done')}
        self.assertEqual(names,{'mstop','mstopB','mstopC'})
        state(c,'m11')
        c.exports();self.assertEqual(C.read(c.state/'gcs_m11.json')['status'],'pending retry')

    def test_stop_checkpoint_space_branches(self):
        c,root=fixture('checkpoint_project');c.final_pass=True;state(c,'checkpoint_000001');last=state(c,'checkpoint_000003')
        with patch.object(C.shutil,'disk_usage',return_value=SimpleNamespace(free=100*1024**3)):c.stop_checkpoint()
        v=C.read(c.state/'ckstop.json');self.assertEqual(v['status'],'gcs');self.assertEqual(v['marker_sha256'],C.sha(last))
        self.assertFalse((c.target/'n_ck/41').exists())
        EVIDENCE['checkpoint_ample']=v
        c,root=fixture('checkpoint_gcs');c.final_pass=True;state(c,'checkpoint_000003')
        usage=lambda p:SimpleNamespace(free=0 if Path(p)==c.target else 100*1024**3)
        with patch.object(C.shutil,'disk_usage',side_effect=usage):c.stop_checkpoint()
        self.assertEqual(C.read(c.state/'ckstop.json')['status'],'gcs')
        EVIDENCE['checkpoint_full']=C.read(c.state/'gcs_checkpoint_000003_stop.done')
        c,root=fixture('checkpoint_local_full');c.final_pass=True;state(c,'checkpoint_000003')
        with patch.object(C.shutil,'disk_usage',return_value=SimpleNamespace(free=0)):
            with self.assertRaisesRegex(ValueError,'E95'):c.stop_checkpoint()
        self.assertFalse((c.state/'gcs_checkpoint_000003_stop.done').exists())

    def test_term_sealed_copy(self):
        v=json.loads((L/'work/enospc12sealed/results4.json').read_text())
        self.assertEqual(len(v),2)
        self.assertTrue(all(r['ok'] and r['result']['checkpoint'] and r['result']['returncode']==0 for r in v))
        EVIDENCE['term']=dict(superseded_by='signals_current.py: TERM and USR1',results=v)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Live24F))
    (D/'LIVE_TESTS.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,evidence=EVIDENCE),indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
