"""Validate rendered driver pins and fail-closed review/session boundaries locally."""
import hashlib,importlib.util,json,re,sys,tarfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rebind import ROOT,load,sha
from cprime_gate import B1,GO
D=Path('/scratch/jjyeung/orch_n30/r1_ops/work/drv_cp')

class Drivers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.op=load(ROOT/'out/OPERATOR.json');cls.pins=load(D/'PACKET_PINS.json')
        spec=importlib.util.spec_from_file_location('cp_review',D/'review_policy.py')
        cls.review=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.review)

    def test_final_pins_and_archive_inventory(self):
        self.assertEqual(self.pins['outer'],sha(ROOT/'out'/self.op['archive']))
        self.assertEqual(self.pins['identity'],load(ROOT/'out/BINDING.json')['config_identity'])
        with tarfile.open(ROOT/'out'/self.op['archive']) as tf:
            names=tf.getnames();self.assertEqual(len(names),self.pins['members'])
            self.assertNotIn('B1R_MAPPING.json',names)
            self.assertEqual(hashlib.sha256(tf.extractfile('z.json').read()).hexdigest(),B1)
            self.assertEqual(tf.extractfile('z.json').read(),tf.extractfile('records/z.json').read())

    def test_review_chain_hashes_original_text(self):
        texts=load(D/'ANTECEDENT_TEXTS.json')
        texts['rcp.txt']='Packet Cprime: GO\nConfig '+self.pins['identity']+'\n'
        record=self.review.build_chain(texts,self.pins['identity'],self.pins['tree'],self.pins['outer'])
        self.assertEqual(len(record['reviews']),12)
        self.assertEqual(record['final_reviewer'],'review_cprime')
        self.assertFalse(record['production_go_granted'])
        for value in record['reviews'].values():
            self.assertEqual(value['sha256'],hashlib.sha256(texts[value['file']].encode()).hexdigest())

    def test_review_refuses_missing_foreign_or_conditional(self):
        texts=load(D/'ANTECEDENT_TEXTS.json')
        with self.assertRaises(ValueError):self.review.build_chain(texts,self.pins['identity'],self.pins['tree'],self.pins['outer'])
        for content in ('Packet Cprime: GO\n'+'f'*64,'Packet Cprime: GO pending audit\n'+self.pins['identity'],
                        'Packet Cprime: NO-GO\n'+self.pins['identity']):
            texts['rcp.txt']=content
            with self.subTest(content=content),self.assertRaises(ValueError):
                self.review.build_chain(texts,self.pins['identity'],self.pins['tree'],self.pins['outer'])

    def test_driver_sequence_and_submit_resources(self):
        required=('u1.sh','q1.sh','rv1.sh','ev1.sh','evp1.sh','dv1.sh','dvp1.sh','scan1.sh','sc1.sh','L1_mint.sh','si1.sh','pre1.sh','mon.sh')
        for name in required:self.assertTrue((D/name).is_file(),name)
        for path in D.glob('*.sh'):self.assertIsNone(re.search(r'@[A-Z_]+@',path.read_text()),path.name)
        for name in ('pr1.sh','rehearsal1.sh'):self.assertFalse((D/name).exists())
        submit=(D/('go_submit_canary_delta_'+self.pins['outer'][:8]+'.sh')).read_text()
        self.assertIn(GO,submit);self.assertIn('ADMISSION_JOB=172180',submit)
        self.assertIn('unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME PROOF_JOB',submit)
        wrapper=(ROOT/'out/operator/jb.sh').read_text()
        self.assertIn('24:00:00',wrapper);self.assertIn('advanced',wrapper)
        pre=(D/'pre1.sh').read_text();self.assertIn("pointer['rows']=='rebind'",pre);self.assertNotIn('cinputs',pre)

    def test_fresh_sessions_and_inert_pending_drivers(self):
        names=(D/'e.txt').read_text().splitlines();self.assertEqual(len(names),20);self.assertEqual(len(set(names)),20)
        self.assertTrue(all(self.pins['run'] in x for x in names))
        mint=(D/'L1_mint.sh').read_text();self.assertIn(self.pins['outer'][:8],mint);self.assertIn('noclobber',mint)
        helper=Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py')
        self.assertEqual(sha(helper),'b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d')
        for name in ('rv1.sh','sc1.sh','si1.sh'):self.assertIn('exit 4',(D/name).read_text())

if __name__=='__main__':unittest.main(verbosity=2)
