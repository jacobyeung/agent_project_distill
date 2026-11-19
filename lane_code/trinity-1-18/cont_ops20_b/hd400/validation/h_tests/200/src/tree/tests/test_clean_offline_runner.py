import importlib.util
import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

spec = importlib.util.spec_from_file_location("clean_offline_runner", Path(__file__).resolve().parents[1] / "scripts/run_clean_offline_tests.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DependencyGateTests(unittest.TestCase):
    def root(self):
        root = Path(os.environ["CLEAN_VSI590K_TEST_ROOT"]) / uuid4().hex
        root.mkdir(parents=True)
        return root

    def cases(self, count=15):
        called = []
        def execute(test):
            called.append(test.id())
        cls = type("DependencyFixture", (unittest.TestCase,), {f"test_{index:02d}": execute for index in range(count)})
        return cls, called

    def test_staging_a_real_file_enables_every_conditionally_blocked_test(self):
        root = self.root()
        dependency = root / "dependency.json"
        cls, called = self.cases()
        requirements = ({"files": [dependency]}, {})
        with patch.object(runner, "integration_dependencies", return_value=requirements):
            absent = list(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
            blocked = runner.condition_integration_tests(absent, root)
            self.assertEqual(len(blocked), 15)
            first = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(absent))
            self.assertEqual(len(first.skipped), 15)
            self.assertEqual(called, [])
            with dependency.open("x") as stream:
                stream.write("{}\n")
            staged = list(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
            self.assertEqual(runner.condition_integration_tests(staged, root), {})
            second = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(staged))
        self.assertTrue(second.wasSuccessful())
        self.assertEqual(second.testsRun, 15)
        self.assertEqual(second.skipped, [])
        self.assertEqual(len(called), 15)

    def test_missing_method_dependency_skips_only_that_method(self):
        root = self.root()
        cls, called = self.cases(2)
        cases = list(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
        with patch.object(runner, "integration_dependencies", side_effect=[({}, {"files": [root / "missing.json"]}), ({}, {})]):
            blocked = runner.condition_integration_tests(cases, root)
        result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(cases))
        self.assertEqual(len(blocked), 1)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(len(called), 1)

    def test_module_presence_and_absence_control_the_gate(self):
        root = self.root()
        self.assertEqual(runner.missing_dependencies({"modules": ["json"]}, root), [])
        self.assertEqual(runner.missing_dependencies({"modules": ["clean_fixture_missing_dependency_20260918"]}, root),
                         ["module:clean_fixture_missing_dependency_20260918"])

    def test_alternative_processor_filenames_are_conditioned_on_presence(self):
        root = self.root()
        paths = (root / "processor_config.json", root / "preprocessor_config.json")
        requirement = {"any_files": [paths]}
        self.assertEqual(len(runner.missing_dependencies(requirement, root)), 1)
        with paths[1].open("x") as stream:
            stream.write("{}\n")
        self.assertEqual(runner.missing_dependencies(requirement, root), [])

    def test_external_dependency_is_not_probed(self):
        with patch.object(Path, "is_file", side_effect=AssertionError("external stat attempted")):
            missing = runner.missing_dependencies({"files": [Path("/data2/unadmitted_fixture.json")]}, Path(os.environ["CLEAN_VSI590K_WORKSPACE"]))
        self.assertEqual(missing, ["fixture:/data2/unadmitted_fixture.json"])

    def test_all_fifteen_integration_tests_have_explicit_real_dependencies(self):
        import test_conversion
        import test_diagnostic
        import test_training
        tests = [test for cls in (test_conversion.ConversionTests, test_diagnostic.DiagnosticTests, test_training.AdapterTests)
                 for test in unittest.defaultTestLoader.loadTestsFromTestCase(cls)]
        self.assertEqual(len(tests), 15)
        for test in tests:
            with self.subTest(test=test.id()):
                shared, _ = runner.integration_dependencies(test)
                self.assertTrue(shared["files"])
                self.assertTrue(shared["modules"])


if __name__ == "__main__":
    unittest.main()
