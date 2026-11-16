import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import assign as A
import build_rows as B
from tests.test_assign import item, resp


class BuildRows(unittest.TestCase):
    def test_packs_head_rows_that_validate(self):
        sys.path.insert(0, str(A.TREE))
        from student_pilot import ground_rows
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            items = [item(qid='q0'), item(qid='q1')]
            rs = [resp(qid='q0'), resp(qid='q1', pred='5')]
            (t / 'i.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in items))
            (t / 'r.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rs))
            A.run(t / 'i.jsonl', t / 'r.jsonl', t / 'a')
            m = B.run(t / 'i.jsonl', t / 'r.jsonl', t / 'a' / 'SELECTED.jsonl', t / 'o')
            self.assertEqual(m['counts'], {'object_counting|head': 1})
            rows = [json.loads(l) for l in open(t / 'o' / 'HEAD_ROWS.jsonl')]
            self.assertEqual(len(rows), 1)
            ground_rows.validate(rows[0])
            self.assertEqual(rows[0]['provenance']['assignment'], 'head')
            self.assertEqual(rows[0]['provenance']['room_key'], 'scannet/scene0232')

    def test_refuses_a_selection_that_is_no_longer_head(self):
        it, r = item(qid='q0'), resp(qid='q0', pred='5')
        with self.assertRaises(ValueError):
            B.pack_head(it, r, A.Eligibility())


if __name__ == '__main__':
    unittest.main()
