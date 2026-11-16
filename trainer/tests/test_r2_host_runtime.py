"""Exercise host containment, init mapping and source-bound statement accounting."""
import hashlib
import inspect
import io
import os
from pathlib import Path
import tarfile
import unittest
from unittest.mock import patch
from launch_r2 import runtime as R
from student_pilot.p3_provenance import file_pin
from tests.test_r2_data_path import directory


def marker():
    value=1
    return value


class Runtime(unittest.TestCase):
    def test_write_boundary_and_statement_receipt(self):
        root=directory()
        with R.bounded_writes(root,1000000):
            (root/'a').mkdir()
            (root/'a/f').write_text('ok')
            (root/'a/g').symlink_to(root/'a/f')
            with self.assertRaisesRegex(ValueError,'outside'):
                (root.parent/'outside-proof').write_text('never written')
            with self.assertRaisesRegex(ValueError,'network'):
                R.audit('socket.connect',())
            with self.assertRaisesRegex(ValueError,'outside'):
                R.audit('sqlite3.connect',('file:/outside/db?mode=rwc',))
        record=dict(source=file_pin(__file__),line=inspect.getsourcelines(marker)[1]+1)
        with R.statement_hits([record]) as hits:self.assertEqual(marker(),1)
        self.assertTrue(R.checked_hits([record],hits)[0]['reached'])
        with self.assertRaisesRegex(ValueError,'not reached'):R.checked_hits([record],set())
        self.assertEqual(len(R.obligations()),5)
        with patch.object(inspect,'getsourcelines',return_value=(['pass'],1)):
            with self.assertRaisesRegex(ValueError,'ambiguous'):R.obligations()

    def test_delivered_archive_native_mirror(self):
        from student_pilot.carrier_c1_run import init_mirror
        root=directory()
        members={'m544/artifact.json':b'{}','m544/heads.pt':b'tiny','m544/full_weights/a':b'tiny'}
        def archive(name,values):
            with tarfile.open(root/name,'w') as tar:
                for key,raw in values.items():
                    info=tarfile.TarInfo(key);info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
            return file_pin(root/name)
        hashes={k:hashlib.sha256(v).hexdigest() for k,v in members.items()}
        value=R.init_layout(archive('a.tar',members),root/'a',hashes,100)
        with patch.dict(os.environ,{'C1_INIT_LOCAL':value['mirror_root']}):
            local=init_mirror(value['artifact'])
            self.assertEqual((local/'heads.pt').read_bytes(),b'tiny')
            self.assertEqual((local/'full_weights/a').read_bytes(),b'tiny')
        small={'m544/artifact.json':b'{}'}
        with self.assertRaisesRegex(ValueError,'required member'):
            R.init_layout(archive('b.tar',small),root/'b',{k:hashlib.sha256(v).hexdigest() for k,v in small.items()},100)

    def test_descendant_lineage_authentication(self):
        from tests.test_r2_build3 import tiny_export
        from student_pilot.r2_contract import lineage_init,INIT
        root=directory();tiny_export(root)
        lineage_init({'sha256':INIT['artifact_sha256']})
        lineage_init(file_pin(root/'donor.json'))
        (root/'other.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'binding'):lineage_init(file_pin(root/'other.json'))
        with self.assertRaisesRegex(ValueError,'binding'):lineage_init({'sha256':'f'*64})
