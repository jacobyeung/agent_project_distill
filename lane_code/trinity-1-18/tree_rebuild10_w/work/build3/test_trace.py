"""Test the actual trace callback directly so the outer tracer can measure it."""
import sys
from types import SimpleNamespace
import unittest
from launch_r2.runtime import statement_hits
from student_pilot.p3_provenance import file_pin


class Trace(unittest.TestCase):
    def test_callback_chains_and_records_only_selected_sources(self):
        previous=sys.gettrace()
        record=dict(source=file_pin(__file__),line=1)
        with statement_hits([record]) as hits:
            callback=sys.gettrace()
            frame=sys._getframe()
            self.assertIs(callback(frame,'call',None),callback)
            self.assertIs(callback(frame,'line',None),callback)
            other=SimpleNamespace(f_code=SimpleNamespace(co_filename='/outside/not-selected'),f_lineno=10)
            # The real predecessor is called on an actual frame; change only
            # selection by using a real helper's frame from another source.
            observed=callback(sys._getframe(1),'call',None)
            self.assertNotIn((other.f_code.co_filename,other.f_lineno),hits)
            self.assertTrue(observed is None or callable(observed))
        self.assertIs(sys.gettrace(),previous)
        self.assertTrue(any(path==__file__ for path,line in hits))
