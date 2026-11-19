"""The dense-cache identity must invalidate caches after the required pose-row change."""
import hashlib
import json
from pathlib import Path
import unittest

from student_pilot import c1r_dense

E6456BC_RUNTIME = json.loads('{"c1r_clips.py": "b5e45f6f34c6420aaa44fc5223d3744d44474972a0c7b3def3b7b043b8b90e88", "c1r_dense.py": "949eb50e0ed4cdf00453c2746d443fe15b8ccba8c4775aad3729fae653a11d9c", "c1r_ref.py": "b83a0d948bde2948292f60a6b967298ee1cc4581ae82ea8a977dd38928d52de3", "c1r_targets.py": "a2e1ed8d20709230dcdb300a79f58e3e877a8bbee72453268049bc3d922b4177", "camera_targets.py": "59a9475e87c6eb49fc103e8077ec224746f06fcdbde9b0a1a38088cb1aed18a4", "pose_samples.py": "af500f96ad6215ce6756bdec4e7d9571402f6033839213672e3cd85245a3981a", "recording_pose.py": "f58c572aa11ec12cabdb9569ca5a31f3ca057fa5f5246407954ace9596599194"}')


class DenseCacheBinding(unittest.TestCase):
    def test_loader_runtime_identity_equals_cp1(self):
        current=c1r_dense.runtime_identity()
        expected={name:hashlib.sha256((Path(c1r_dense.__file__).parent/name).read_bytes()).hexdigest()
                  for name in E6456BC_RUNTIME}
        self.assertEqual(current,expected)
        self.assertEqual({name for name in current if current[name]!=E6456BC_RUNTIME[name]}, {'pose_samples.py'})


if __name__ == '__main__':
    unittest.main()
