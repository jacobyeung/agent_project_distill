"""Targeted tests for the conclusions: frame parsing, visibility and A3x."""
import unittest
import anchor_analysis as A


class Tests(unittest.TestCase):
    def test_fractional_frame_is_not_truncated(self):
        c, missed = A.parse_citations('Step 1: find the door, first seen in frame 44.9.')
        self.assertEqual(c[0]['frame_text'], '44.9')
        self.assertFalse(missed)

    def test_sentence_period_and_unparsed_line(self):
        c, missed = A.parse_citations('The chair is seen in frame 9.\nA strange frame 10 line.')
        self.assertEqual((c[0]['noun'], c[0]['frame_text']), ('chair', '9'))
        self.assertEqual(len(missed), 1)

    def test_visibility_one_based_and_missing_frame_map(self):
        gt = dict(ids=[0], labels=['chair'], valid=[True]*32,
                  frame_indices=list(range(32)), shares=[[0., .01]+[0.]*30])
        c = dict(noun='chair', frame_text='2')
        self.assertTrue(A.score_claim(c,gt,list(range(32)))['visible'])
        self.assertFalse(A.score_claim(dict(c,frame_text='1'),gt,list(range(32)))['visible'])
        self.assertEqual(A.score_claim(c,gt,[1]*32)['status'],'frame_map_mismatch')
        self.assertFalse(A.score_claim(dict(c,frame_text='33'),gt,list(range(32)))['visible'])
        self.assertFalse(A.score_claim(dict(c,frame_text='2.5'),gt,list(range(32)))['visible'])

    def test_same_label_instances_are_not_unioned(self):
        gt = dict(ids=[0,1], labels=['chair','chair'], valid=[True]*32,
                  frame_indices=list(range(32)), shares=[[.006,.02]+[0.]*30,[.006,.02]+[0.]*30])
        c=A.score_claim(dict(noun='chair',frame_text='1'),gt,list(range(32)))
        self.assertFalse(c['unique'])
        self.assertFalse(c['visible'])
        self.assertTrue(c['visible_any'])

    def test_a3x_uses_cited_frame_and_has_no_fallback(self):
        candidates=[dict(id='a',members={'1':999,'2':2}),dict(id='b',members={'2':9})]
        self.assertEqual(A.a3x(candidates,2)['id'],'b')
        self.assertIsNone(A.a3x(candidates,3))
        self.assertEqual(A.a3x([dict(id='a',members={'1':9}),dict(id='b',members={'1':9})],1)['id'],'a')

    def test_anchor_threshold_and_neighbor_tie(self):
        vis={'1':.009,'2':.03,'3':.10,'4':.03,'7':.10}
        self.assertEqual(A.best_anchor(vis),3)
        self.assertEqual(A.neighbor_anchor(vis,3),2)
        self.assertIsNone(A.best_anchor({'1':.009}))
        self.assertIsNone(A.neighbor_anchor({'1':.1,'3':.2},1,True))

    def test_room_bootstrap_retains_all_rows_of_sampled_room(self):
        rows=[dict(room='a',score=1),dict(room='b',score=0),dict(room='b',score=0)]
        r=A.rate(rows,lambda x:x['score'])
        self.assertEqual(r['rate'],1/3)
        self.assertEqual(r['ci95'],[0.,1.])
        self.assertEqual(r['rooms'],2)


if __name__ == '__main__':
    unittest.main()
