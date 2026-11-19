"""Run a delivered suite unchanged; encode completed fixtures between test cases."""
import os,runpy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from compact import compact
original=unittest.TextTestResult.stopTest
def stop(self,test):
    original(self,test)
    for key in ('PACK_TEST_WORK','PACK_REVIEW_WORK','PACK_R2_WORK','PACK_R3_WORK','PACK_R4_WORK'):
        if key in os.environ:compact(os.environ[key])
unittest.TextTestResult.stopTest=stop
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
