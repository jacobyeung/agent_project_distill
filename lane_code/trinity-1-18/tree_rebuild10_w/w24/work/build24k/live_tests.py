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

L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
sys.path.insert(0,str(D))
import live as C

WRITER='''import hashlib,json,sys
from pathlib import Path
s,key,p=sys.argv[2:5];raw=Path(p).read_bytes();width=(len(raw)+3)//4
out=Path(s).parent/'objects';out.mkdir(exist_ok=True)
with Path(s+'.receipts.jsonl').open('a') as f:
 for i in range(4):
  part=raw[i*width:(i+1)*width];name=key+f'.part{i:02d}-of-04'
  (out/name.replace('/','_')).write_bytes(part)
  f.write(json.dumps(dict(name=name,bytes=len(part),offset=i*width,sha256=hashlib.sha256(part).hexdigest(),generation=str(i+1)))+'\\n')
'''
EVIDENCE={}


def fixture(name):
    root=D/'live_tests_v2'/name;root.mkdir(parents=True,exist_ok=False)
    kit=root/'kit';(kit/'k').mkdir(parents=True);(kit/'b').mkdir()
    node=root/'node';node.mkdir();train=node/'p/q/r';train.mkdir(parents=True)
    target=root/'target';target.mkdir();home=target/'n_s';home.mkdir(mode=0o700)
    C.put(kit/'k/p.json',dict(n_root=str(target)))
    C.put(kit/'k/n.json',dict(output='/run/469ddece'))
    C.put(kit/'k/y.json',dict(objects={x:'q9/test/'+x+'.tar' for x in ('m100','mstop','mstopB','mstopC','ckstop')}))
    (kit/'b/pc.py').write_bytes((D/'live.py').read_bytes());(kit/'b/pc.sh').write_bytes((D/'live.sh').read_bytes())
    (kit/'b/gc.py').write_text(WRITER)
    (kit/'b/sr.py').write_bytes((L/'work/build24k/sr.py').read_bytes())
    return C.Copier(kit,node,'41',home=home),root


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
        with (c.root/'t.log').open('wb') as f:f.seek(41_000_000);f.write(b'LAST')
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
        c.exports();self.assertEqual(C.read(c.live/'gcs_m100.json')['status'],'export not uploaded: sessions unusable (file missing)')
        self.assertEqual(len(list(c.spool.glob('*.tar'))),1)
        C.put(c.home/'sess.json',{});os.chmod(c.home/'sess.json',0o600)
        c.writer.write_text('raise SystemExit(1)\n');c.exports()
        self.assertFalse((c.live/'gcs_m100.done').exists())
        c.writer.write_text(WRITER);c.exports()
        done=c.live/'gcs_m100.done';v=C.read(done);stamp=done.stat().st_mtime_ns;c.exports()
        self.assertEqual(done.stat().st_mtime_ns,stamp)
        archive=next(c.spool.glob('*.tar'))
        self.assertEqual(v['sha256'],C.sha(archive));self.assertEqual(v['bytes'],archive.stat().st_size)
        self.assertEqual(v['marker_sha256'],C.sha(m));EVIDENCE['export']=v

    def test_stop_generation_claims_once(self):
        c,root=fixture('claims');C.put(c.home/'sess.json',{});os.chmod(c.home/'sess.json',0o600)
        for step in (3,7,9):state(c,'m'+str(step))
        c.exports()
        names={C.read(p)['generation'] for p in c.live.glob('gcs_*.done')}
        self.assertEqual(names,{'mstop','mstopB','mstopC'})
        state(c,'m11')
        c.exports();self.assertEqual(C.read(c.live/'gcs_m11.json')['status'],'pending retry')

    def test_stop_checkpoint_space_branches(self):
        c,root=fixture('checkpoint_project');state(c,'checkpoint_000001');last=state(c,'checkpoint_000003')
        with patch.object(C.shutil,'disk_usage',return_value=SimpleNamespace(free=100*1024**3)):c.stop_checkpoint()
        v=C.read(c.live/'ckstop.json');self.assertEqual(v['status'],'project');self.assertEqual(v['marker_sha256'],C.sha(last))
        self.assertEqual(len(list((c.target/'n_ck/41').glob('*.tar'))),1)
        EVIDENCE['checkpoint_project']=v
        c,root=fixture('checkpoint_gcs');state(c,'checkpoint_000003')
        usage=lambda p:SimpleNamespace(free=0 if Path(p)==c.target else 100*1024**3)
        with patch.object(C.shutil,'disk_usage',side_effect=usage):c.stop_checkpoint()
        self.assertEqual(C.read(c.live/'ckstop.json')['status'],'left node-local')
        C.put(c.home/'sess.json',{});os.chmod(c.home/'sess.json',0o600)
        with patch.object(C.shutil,'disk_usage',side_effect=usage):c.stop_checkpoint()
        self.assertEqual(C.read(c.live/'ckstop.json')['status'],'gcs')
        EVIDENCE['checkpoint_fallback']=C.read(c.live/'gcs_checkpoint_000003.done')

    def test_term_final_copy(self):
        c,root=fixture('term')
        script=root/'job.sh'
        script.write_text('set -eu\nROOT='+repr(str(c.kit))+'\nN='+repr(str(c.root))+'\nexport SLURM_JOB_ID=41\nsource "$ROOT/b/pc.sh"\nprintf ready > "$N/ready"\nsleep 5 &\nwait $!\n')
        with (root/'job.log').open('w') as log:
            p=subprocess.Popen(['/bin/bash',str(script)],stdout=log,stderr=subprocess.STDOUT)
            end=time.monotonic()+10
            while not (c.root/'ready').exists() and time.monotonic()<end:time.sleep(.05)
            self.assertTrue((c.root/'ready').exists())
            (c.root/'t.log').write_text('last line before TERM\n')
            p.send_signal(signal.SIGTERM);rc=p.wait(timeout=20)
        self.assertEqual(rc,143);self.assertEqual((c.live/'t.log').read_text(),'last line before TERM\n')
        EVIDENCE['term']=dict(exit=rc,last_copy=C.read(c.live/'copy.json'))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Live24F))
    (D/'LIVE_TESTS.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,evidence=EVIDENCE),indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
