import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from dataset_builder_fixture import fixture_directory
from student_pilot.dataset_builder import build_dataset


class NativeAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("student_pilot.clean_conversion") is None or importlib.util.find_spec("clean_r1313_fixture") is None:
            raise unittest.SkipTest("The native converter verifier and its supplied offline fixture are not installed")
        from clean_r1313_fixture import Fixture, response_for
        from student_pilot import clean_conversion

        cls.converter = clean_conversion
        cls.output = fixture_directory("native_admission")
        workspace = Path(os.environ["CLEAN_VSI590K_WORKSPACE"])
        with patch.dict(os.environ, {"CLEAN_VSI590K_TEST_ROOT": str(cls.output / "sources")}):
            cls.fixture = Fixture(qids=["vsi590k_000001", "vsi590k_000002"])
        prepared = cls.fixture.prepare()
        lease = cls.fixture.lease(prepared["job"])
        run = cls.fixture.clean / "runs/dataset_test"
        with patch.object(clean_conversion, "native_transport", side_effect=lambda request, telemetry: response_for(request)) as transport:
            clean_conversion.run(workspace, prepared["job"]["path"], lease["path"], run)
        if transport.call_count != 2:
            raise AssertionError("Offline transport did not cover the exact synthetic call census")
        review = cls.fixture.review(run, qids=["vsi590k_000001"])
        cls.index = clean_conversion.admit(workspace, run, review["path"], cls.fixture.clean / "admissions/dataset_test")

    def test_real_native_admission_verifier_feeds_the_builder_without_a_new_review(self):
        result = build_dataset(self.index["path"], self.output / "packaged", self.fixture.workspace, fixture_only=True)
        manifest = json.loads(Path(result["manifest"]).read_text())
        self.assertEqual(manifest["admitted_count"], 1)
        self.assertEqual(manifest["example_count"], 1)
        self.assertEqual(manifest["examples"][0]["qid"], "vsi590k_000001")
        self.assertTrue(manifest["fixture_only"])
        self.assertFalse(manifest["training_eligible"])
        self.assertNotIn("vsi590k_000002", [row["qid"] for row in manifest["examples"]])
        self.assertEqual(manifest["examples"][0]["binding"]["sha256"],
                         json.loads(Path(self.index["path"]).read_text())["snapshot"]["sha256"])

    def test_native_verifier_failure_cannot_fall_back_to_list_admission(self):
        with patch.object(self.converter, "load_admitted", side_effect=ValueError("independent admission refused")):
            with self.assertRaisesRegex(ValueError, "independent admission refused"):
                build_dataset(self.index["path"], self.output / "refused", self.fixture.workspace, fixture_only=True)
        self.assertFalse((self.output / "refused/manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
