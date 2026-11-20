"""ARKit regression checks for chronological anchors and preserved deliverables."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from round3 import *

class Round3Tests(unittest.TestCase):
    def test_lexical_boundary_requires_timestamp_sort(self):
        names=['41069053_999.131.png','41069053_1004.513.png']
        self.assertNotEqual(sorted(names),names)
        self.assertEqual(sorted(names,key=ts),names)

    def test_reference_reproduced_without_tolerance_change(self):
        r=read(OUT/'REPRODUCTION.json')['arkitscenes']
        self.assertTrue(r['passed'])
        self.assertEqual(len(r['arrays']),12)
        self.assertTrue(all(a['exact_equal'] and a['passed'] for a in r['arrays'].values()))
        self.assertEqual(r['tolerance_sha256'],sha(OUT/'REPRO_TOLERANCE.md'))
        self.assertEqual(sha(r['actual']),sha(r['reference']))
        self.assertEqual(r['anchor_order'],'chronological')

    def test_all_target_anchor_lists_are_chronological(self):
        ordering=read(OUT/'ARKIT_ORDER_CHECKS.json')
        manifest={m['scene']:m for m in read(ROOT/'DEVS1_MANIFEST.json')['captures']}
        for cid in TARGETS['arkitscenes']:
            r=ordering[cid]
            self.assertTrue(r['lexical_equals_chronological'])
            self.assertTrue(r['listing_is_chronological'])
            self.assertEqual(len(r['anchor_timestamps']),32)
            self.assertEqual(r['anchor_timestamps'],sorted(r['anchor_timestamps']))
            self.assertEqual(r['anchor_indices'],manifest['arkitscenes/'+cid]['anchor_indices'])

    def test_prior_fifteen_npzs_and_audits_preserved(self):
        self.assertEqual(len(preserved_npzs()),15)
        old=read(BASE/'CAPTURE_CHECKS.json');new=read(OUT/'CAPTURE_CHECKS.json')
        for c,r in old['captures'].items():self.assertEqual(r,new['captures'][c])
        self.assertEqual(old['objects'],[r for r in new['objects'] if r['capture'] in old['captures']])
        self.assertTrue((OUT/'NOGT_REPORT.md').read_bytes().startswith((BASE/'NOGT_REPORT.md').read_bytes()))
        self.assertTrue((OUT/'SHA256SUMS').read_bytes().startswith((BASE/'SHA256SUMS').read_bytes()))

    def test_arkit_builds_have_complete_measured_checks(self):
        builds=read(OUT/'BUILDS.json');checks=read(OUT/'CAPTURE_CHECKS.json')
        self.assertEqual(len(checks['captures']),22)
        for cid in TARGETS['arkitscenes']:
            c='arkitscenes/'+cid;b=builds[c];r=checks['captures'][c]
            self.assertTrue(b['built'])
            self.assertEqual(b['evidence']['sha256'],sha(b['path']))
            self.assertTrue(r['identity_passed'])
            self.assertEqual(len(r['frames']),32)
            self.assertTrue(all(f['verified'] for f in r['frames']))
            self.assertGreater(r['geometry']['visible_instance_frames'],0)
            for arm in ['t1','t2']:
                self.assertGreater(r['arms'][arm]['objects'],0)
                self.assertIsNotNone(r['arms'][arm]['same_median'])
            self.assertEqual(r['passed'],r['identity_passed'] and r['geometry']['passed'] and r['binding_passed'] and r['colmap_passed'])
        for r in checks['receipts'].values():
            self.assertTrue(r['sha256_verified'])
            self.assertFalse(r['salvaged'])

    def test_current_npz_checksums(self):
        latest={}
        for line in (OUT/'SHA256SUMS').read_text().splitlines():
            digest,name=line.split('  ',1);latest[name]=digest
        for b in read(OUT/'BUILDS.json').values():
            self.assertEqual(latest[str(Path(b['path']).relative_to(ROOT))],sha(b['path']))

    def test_total_verdict_matches_capture_results(self):
        v=read(OUT/'VERDICT.json');checks=read(OUT/'CAPTURE_CHECKS.json')['captures']
        self.assertEqual(v['passed'],sum(r['passed'] for r in checks.values()))
        self.assertEqual(v['built'],22)
        self.assertEqual(v['verdict'],'PASS' if v['passed']>=15 else 'FAIL')

if __name__=='__main__':unittest.main(verbosity=2)
