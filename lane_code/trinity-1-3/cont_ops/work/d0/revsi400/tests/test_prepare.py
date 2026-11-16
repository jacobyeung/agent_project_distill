import offline_guard
import ast
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit/launcher'))
import orchard_launcher as L
import export_stage as E
import opaque_io


def directory():
    p=ROOT/'evidence'/('prepare_'+uuid.uuid4().hex);p.mkdir();return p


class PrepareTests(unittest.TestCase):
    def test_all_steps_pair_and_identity_refusals(self):
        for step in (200,400,600,800,1000):
            p=directory();token=uuid.uuid4().hex[:12]
            a=L.prepare(token,p/'proof',mode='proof',step=step,media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
            (p/'proof/SUBMIT.out').write_text('170035\n');L.submission_record(p/'proof')
            b=L.prepare(uuid.uuid4().hex[:12],p/'production',step=step,proof_destination=p/'proof',media_root=a['media_root'])
            for cfg,name in [(a,'proof'),(b,'production')]:
                L.validate_request(cfg);L.validate_batch((p/name/'BATCH.sh').read_text(),cfg)
                command=L.submit_command(cfg['token'],proof=name=='proof',afterok=cfg['afterok'])
                compile(command[-1],'<operator>','exec')
            args=L.submit_argv(None,b['token'],afterok=b['afterok'])
            self.assertIn('--dependency=afterok:170035',args)
            self.assertIn('--time=00:25:00',args)
            self.assertEqual(a['wall_seconds'],1260);self.assertEqual(b['wall_seconds'],1500)
            self.assertIn('359fcc3c/m'+str(step),b['spec']['artifact']['path'])
            for word in ('revsi','vsi','distill','d0','qgen','split'):
                # Hex tokens can contain d0; inspect lexical components, not arbitrary hex substrings.
                self.assertNotIn(word,' '.join(x for x in args if not x.startswith('--job-name')).lower())
            for mutator in [lambda c:c['spec'].update(step=544),lambda c:c.update(afterok=None),lambda c:c.update(phase_b=True),lambda c:c.update(plan_sha256='x'),lambda c:c['spec']['artifact'].update(sha256='a'*64)]:
                bad=copy.deepcopy(b);mutator(bad)
                with self.assertRaises(ValueError):L.validate_request(bad)
            with self.assertRaises(ValueError):L.validate_batch((p/'proof/BATCH.sh').read_text()+'x',a)
        self.assertEqual(L.SSH[:3],['timeout','300','bash'])

    def test_request_guards_and_mismatched_proof(self):
        for token in ('p1234567890','revsi','../1234567890'):
            with self.assertRaises(ValueError):L.valid_token(token)
        for step in (100,544,True):
            with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',step=step)
        with self.assertRaises(ValueError):L.submit_argv(None,'a1234567890')
        with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',media_root='/bad')
        with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',pool='/tmp/revsi')
        with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
        p=directory();a=L.prepare('a1234567890',p/'a',mode='proof',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
        (p/'a/SUBMIT.out').write_text('123\n');L.submission_record(p/'a')
        with self.assertRaises(ValueError):L.prepare('a1234567890',p/'b',proof_destination=p/'a',media_root=a['media_root'])
        with self.assertRaises(ValueError):L.prepare('b1234567890',p/'b',step=200,proof_destination=p/'a',media_root=a['media_root'])
        with patch.object(L,'canonical',return_value='bad'):
            with self.assertRaises(ValueError):L.validate_request(a)

    def test_receipt_exact_and_bad_inputs(self):
        sample=Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/c6/m1.done').read_bytes()
        self.assertEqual(E.parse_done(sample,'359fcc3c',1)['bytes'],21583032320)
        for step in (200,400,600,800,1000):
            raw=f'q8/8865619b/359fcc3c_m{step}.tar 123 '.encode()+b'a'*64+b'\n'
            self.assertEqual(E.parse_done(raw,'359fcc3c',step)['bytes'],123)
            for bad in [raw+b'\n',raw.replace(b' 123 ',b' 0 '),raw.replace(b'359fcc3c',b'469ddece'),raw.replace(b'q8/8865619b',b'q8/00000000'),raw.replace(b'.tar ',b'.tar.part00-of-04 '),b'gs://cmu-gpucloud-jjyeung/'+raw,raw[:-3],raw.upper(),raw.replace(b' 123 ',b'\t123 ')]:
                with self.assertRaises(ValueError):E.parse_done(bad,'359fcc3c',step)
        for run,step in [('x',400),('359fcc3c',True),('359fcc3c',0)]:
            with self.assertRaises(ValueError):E.parse_done(b'',run,step)

    def test_hex_logs_are_reversible(self):
        out=io.BytesIO();body=b'revsi vsi split distill D0 qgen\n'
        opaque_io.encode(io.BytesIO(body),out)
        self.assertEqual(bytes.fromhex(out.getvalue().decode()),body)
        self.assertNotIn(b'revsi',out.getvalue())

    def test_bootstrap_in_process_and_no_live_entry(self):
        import base64,re,os
        import orchard_job as J
        p=directory();cfg=L.prepare('a'+uuid.uuid4().hex[:12],p/'prepared',mode='proof',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
        script=(p/'prepared/BATCH.sh').read_text()
        raw=base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'",script)[1])
        script=L.render_batch(raw,cfg['token'],str(p))
        body=script.split("<<'A_BATCH_BOOTSTRAP'\n",1)[1].rsplit('\nA_BATCH_BOOTSTRAP',1)[0]
        cwd=Path.cwd()
        with patch.dict(os.environ,SLURM_JOB_ID='123'),patch.object(os,'execv') as execute:
            try:exec(compile(body,'<bootstrap>','exec'),{'__name__':'fixture'})
            finally:os.chdir(cwd)
        execute.assert_called_once()
        local=p/('a_123_'+cfg['token'])
        self.assertEqual(json.loads((local/'bootstrap/CONFIG.json').read_text()),cfg)
        self.assertTrue((local/'bootstrap/export_stage.py').is_file())

    def test_checker_argv_uses_full_packaged_checker_without_video_mounts(self):
        import orchard_job as J
        import orchard_stage as S
        p=directory();(p/'bootstrap').mkdir();receipt=p/'receipt';receipt.mkdir()
        cfg=dict(spec=dict(package='/scratch/jjyeung/a123/p',interpreters=dict(p1cpu='/python'),models=dict(base=dict(path='/base'))))
        (p/'bootstrap/CONFIG.json').write_text(json.dumps(cfg))
        def run(argv,**kw):
            self.assertNotIn('--header-only',argv);self.assertIn('/scratch/jjyeung/a123/p/reader/out/export_check.py',argv)
            (receipt/'CHECK.json').write_text(json.dumps(dict(status='VERIFIED',step=400)))
            return type('Result',(),dict(stdout=b'private',stderr=b'',returncode=0))()
        with patch.object(S,'sha',side_effect=lambda path:E.CHECKER_PINS[Path(path).name]),patch.object(J,'namespace',return_value=[]) as ns,patch.object(J,'environment',return_value={}),patch.object(E.subprocess,'run',side_effect=run):
            self.assertEqual(E.run_export_checker(p,'/artifact','a'*64,400,True,receipt,'unused')['status'],'VERIFIED')
            ns.assert_called_once_with(p)
        with self.assertRaises(ValueError):E.run_export_checker(p,'/artifact','a'*64,400,False,receipt,'unused')
