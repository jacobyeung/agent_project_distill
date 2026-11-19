"""Full-store division regression; production RGB availability is a separate gate."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from rebind import ROOT,load,sha,pin
from prepare_fix10 import DB,DIV,SOURCE,build,inputs

class Fix10(unittest.TestCase):
    def test_full_store_build_stream_division_with_and_without_remove(self):
        root=Path(tempfile.mkdtemp(prefix='division_test10_',dir=ROOT/'work'))
        extra=ROOT/'out/records/n.json'
        def pin_only(path,expected=None,**kwargs):
            self.assertIsInstance(expected,str);self.assertEqual(len(expected),64)
            return dict(path=str(path),sha256=expected)
        # This is an explicit RGB-I/O fixture, never production admission evidence.
        with patch('student_pilot.common.binding',new=pin_only):
            with self.assertRaisesRegex(ValueError,'C1 data violate scene division or unique row identity'):
                build(root/'without')
            result=build(root/'with',extra)
        evidence=load(ROOT/'out/FIX10_BUILD.json')
        self.assertEqual(result['count'],evidence['with']['count'])
        keys={json.loads(line)['row_key'] for line in extra.read_text().splitlines()}
        self.assertEqual(len(keys),601)
        division=load(DIV);train=set(division['train_scenes']);held=set(division['heldout_scenes'])
        conn=sqlite3.connect((root/'with/rows.sqlite').as_uri()+'?immutable=1',uri=True)
        seen=set()
        for text, in conn.execute('select row from rows'):
            row=json.loads(text);scene=row['dataset']+'/'+row['scene']
            self.assertIn(scene,train);self.assertNotIn(scene,held);self.assertNotIn(row['qid'],keys)
            self.assertNotIn(row['qid'],seen);seen.add(row['qid'])
        conn.close();self.assertEqual(len(seen),result['count'])
        self.assertEqual(sha(DB),load(ROOT/'out/BINDING.json')['database_sha256'])

    def test_remove_list_exact_and_staged(self):
        out=ROOT/'out';cfg=load(out/'config.json');binding=load(out/'BINDING.json')
        rows=[json.loads(line) for line in (out/'records/n.json').read_text().splitlines()]
        evidence=load(out/'FIX10_OFFENDERS.json')
        self.assertEqual({r['row_key'] for r in rows},{r['qid'] for r in evidence['rows']})
        self.assertEqual(len(rows),601);self.assertEqual(sha(out/'records/n.json'),cfg['remove_files'][-1]['sha256'])
        self.assertIn('n.json',binding['record_files'])
        import tarfile
        op=load(out/'OPERATOR.json')
        with tarfile.open(out/op['archive']) as archive:
            for name in ('n.json','records/n.json'):
                self.assertEqual(archive.extractfile(name).read(),(out/'records/n.json').read_bytes())
        deriv=load(out/'proof/DERIVATION.json')
        for path in deriv['fixture_paths']:
            staged=load(Path(path)/'k/0.json')['extra']
            matches=[v for v in staged if v.get('dest')==cfg['remove_files'][-1]['path']]
            self.assertEqual(len(matches),1);self.assertEqual(matches[0]['sha256'],sha(out/'records/n.json'))

    def test_all_capped_cells_and_refill(self):
        cells=load(ROOT/'out/FIX10_CELLS.json');changed={r['family']:r for r in cells if r['changed']}
        self.assertEqual(changed['room']['old_eligible'],431);self.assertEqual(changed['room']['eligible'],425)
        self.assertEqual(changed['room']['cents'],170);self.assertEqual(changed['direction']['cents'],3119)
        self.assertEqual(sum(r['cents'] for r in cells),12800)
        for row in cells:self.assertLessEqual(row['cents'],row['ceiling_cents'])
        self.assertEqual(sum(r['old_eligible']-r['eligible'] for r in cells),601)

if __name__=='__main__':unittest.main(verbosity=2)
