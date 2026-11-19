from pathlib import Path
import sys,os,runpy
L=Path(__file__).resolve().parents[2];B=L/'work/build20'
sys.path.insert(0,str(L/'work/tree_r1'))
for name in ('r1_handover','r1_training','r1_components','r2_contract'):
    module=__import__('student_pilot.'+name,fromlist=[name])
    exec(compile((B/'base'/(name+'.py')).read_text(),str(B/'base'/(name+'.py')),'exec'),module.__dict__)
sys.argv=[str(B/'test20.py'),'tests.test_r1_build20.Review20.test_real_pose_target',
    'tests.test_r1_build20.Review20.test_selection_binds_returned_identity','tests.test_r1_build20.Review20.test_guard_status_tampering']
os.environ['B20_PROOF']='before'
runpy.run_path(str(B/'test20.py'),run_name='__main__')
