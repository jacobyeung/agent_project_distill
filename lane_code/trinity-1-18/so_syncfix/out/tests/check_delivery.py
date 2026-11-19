"""Explicit artifact regressions; run after packaging, or against the preserved delivery."""
import hashlib
import os
from pathlib import Path
import sys
import tarfile
import unittest

PACKAGE = Path(os.environ.get('LCS_DELIVERY', str(Path(__file__).resolve().parents[1])))


class DeliveryTests(unittest.TestCase):
    def test_report_uses_verified_mux_protocol_and_controlpersist_citations(self):
        report = (PACKAGE / 'REPORT.md').read_text()
        self.assertIn('/usr/share/doc/openssh/PROTOCOL.mux', report)
        self.assertIn('84', report)
        self.assertIn('99', report)
        self.assertIn('man ssh_config', report)
        self.assertIn('idle (with no client connections)', report)
        self.assertNotIn('stdfd_devnull', report)
        self.assertNotIn('identity of the incident\'s pipe holder is **unverified**', report)

    def test_header_install_backup_and_calibration_documentation(self):
        report = (PACKAGE / 'REPORT.md').read_text()
        header = (PACKAGE / 'tools' / 'lane_code_sync.sh').read_text().split('B=${', 1)[0]
        self.assertIn('$S/LCS_ROBUST_SYNC', header)
        self.assertIn('lane_sync', report)
        self.assertIn('calibrate_budgets.py', report)
        self.assertIn('--stage-only', report)
        self.assertIn('PREIMAGE.sha256', report)
        installer = (PACKAGE / 'install_tools.py').read_text()
        self.assertIn('os.replace', installer)
        self.assertIn('preimage.tar', installer)
        self.assertIn('flock', installer)

    def test_archive_has_one_top_level_and_exact_member_checksums(self):
        expected = (PACKAGE / 'so_syncfix_bundle.tar.gz.sha256').read_text().split()[0]
        self.assertEqual(hashlib.sha256((PACKAGE / 'so_syncfix_bundle.tar.gz').read_bytes()).hexdigest(), expected)
        with tarfile.open(str(PACKAGE / 'so_syncfix_bundle.tar.gz'), 'r:gz') as archive:
            self.assertEqual(set(member.name.split('/')[0] for member in archive), {'so_syncfix'})
            manifest = archive.extractfile('so_syncfix/SHA256SUMS').read().decode()
            self.assertEqual(manifest, (PACKAGE / 'SHA256SUMS').read_text())
            count = 0
            for line in manifest.splitlines():
                digest, name = line.split(None, 1)
                data = archive.extractfile('so_syncfix/' + name).read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest, name)
                self.assertEqual(data, (PACKAGE / name).read_bytes(), name)
                count += 1
        print('MEASURE archive_verified_members=%d top_level=so_syncfix' % count, flush=True)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DeliveryTests))
    sys.exit(0 if result.wasSuccessful() else 1)
