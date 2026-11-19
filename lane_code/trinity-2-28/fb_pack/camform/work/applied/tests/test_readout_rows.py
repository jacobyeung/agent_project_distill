import unittest
from unittest import mock

from student_pilot import decoupled_v_run as run


class ReadoutRowTests(unittest.TestCase):
    def test_heldout_rows_without_target_encode_with_the_training_target(self):
        seen = []

        def fake(processor, row):
            seen.append(row)
            return {'pixel_values_videos': 'px', 'video_grid_thw': 'grid', 'input_ids': 'ids'}, {}
        heldout = {'qid': 'q', 'student_input': {'question': 'x'}}
        training = {**heldout, 'target': 'kept'}
        with mock.patch('student_pilot.pose_samples.encode_row', fake):
            self.assertEqual(run.encode(None, heldout), {'pixel_values_videos': 'px', 'video_grid_thw': 'grid'})
            run.encode(None, training)
        self.assertEqual(seen[0]['target'], run.READOUT_TARGET)
        self.assertNotIn('target', heldout)
        self.assertEqual(seen[1]['target'], 'kept')


if __name__ == '__main__':
    unittest.main()
