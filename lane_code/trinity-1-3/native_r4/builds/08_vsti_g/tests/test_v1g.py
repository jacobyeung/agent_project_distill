"""Real staged paths must be covered by the production read bindings."""
from pathlib import Path
import sys,unittest
B=Path(__file__).resolve().parents[1]
sys.path.append(str(B/'work'))
import path_audit
class Paths(unittest.TestCase):
    def test_real_metadata_audit(self):
        value=path_audit.build();path_audit.assert_audit(value)
        self.assertEqual(value['step'],544)
        self.assertEqual(len(value['model_members']),13)
        rows=[r for r in value['paths'] if r['path'].startswith(value['model_root'])]
        self.assertTrue(rows)
        self.assertTrue(all(r['target']==value['model_root'] and r['writable'] is False for r in rows))
        self.assertFalse(any(b['target']=='/project/community/jjyeung' for b in value['bindings']))
    def test_missing_snapshot_fails_closed(self):
        value=path_audit.build(omit_snapshot=True)
        with self.assertRaises(ValueError):path_audit.assert_audit(value)
        self.assertIn(value['model_root']+'/tokenizer_config.json',value['unbound'])
    def test_escape_fails_closed(self):
        value=path_audit.build();value['paths'][0]['bound']=False
        with self.assertRaises(ValueError):path_audit.assert_audit(value)
if __name__=='__main__':unittest.main()
