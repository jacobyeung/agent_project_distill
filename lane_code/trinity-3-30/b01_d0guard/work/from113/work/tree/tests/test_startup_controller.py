import unittest
from unittest.mock import patch

from scripts.orchard import train_job
from student_pilot import provisional_data, startup_receipt


class StartupControllerTests(unittest.TestCase):
    def test_default_controller_keeps_native_validation(self):
        with patch.object(startup_receipt, 'load_prepared', return_value=None), \
                patch.object(provisional_data, 'load_protocol') as protocol, \
                patch.object(provisional_data, 'load_training') as manifest:
            self.assertIsNone(train_job.validate_startup('protocol', 'manifest', 'qwen36_27b'))
        protocol.assert_called_once_with('protocol', train_job.LABEL, student='qwen36_27b')
        manifest.assert_called_once_with('manifest', train_job.LABEL)

    def test_prepared_controller_reuses_only_the_native_receipt_validator(self):
        prepared = {'synthetic': True}
        with patch.object(startup_receipt, 'load_prepared', return_value=prepared) as receipt, \
                patch.object(provisional_data, 'load_protocol') as protocol, \
                patch.object(provisional_data, 'load_training') as manifest:
            self.assertEqual(train_job.validate_startup('protocol', 'manifest', 'qwen36_27b'), prepared)
        receipt.assert_called_once_with('manifest', 'protocol', train_job.LABEL, 'qwen36_27b')
        protocol.assert_not_called()
        manifest.assert_not_called()

    def test_bad_receipt_never_falls_back_to_unpinned_inputs(self):
        with patch.object(startup_receipt, 'load_prepared', side_effect=ValueError('changed receipt')), \
                patch.object(provisional_data, 'load_protocol') as protocol, \
                patch.object(provisional_data, 'load_training') as manifest:
            with self.assertRaisesRegex(ValueError, 'changed receipt'):
                train_job.validate_startup('protocol', 'manifest', 'qwen36_27b')
        protocol.assert_not_called()
        manifest.assert_not_called()


if __name__ == '__main__':
    unittest.main()
