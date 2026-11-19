"""Default discovery includes review and real-return tests stored under t/."""

def load_tests(loader, suite, pattern):
    for module in ('tests.test_synthetic', 't.test_review', 't.test_real_round1'):
        suite.addTests(loader.loadTestsFromName(module))
    return suite
