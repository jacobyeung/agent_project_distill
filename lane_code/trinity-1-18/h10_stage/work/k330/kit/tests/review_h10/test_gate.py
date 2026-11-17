"""Run all six independent reviewer probes against this kit."""
import os
from pathlib import Path
import subprocess
import sys
import pytest

@pytest.mark.parametrize('name',['t_score','t_merge_types','t_map','t_modes','t_modes_tilt','t_cached_modes'])
def test_review(name,tmp_path):
    script=Path(__file__).with_name(name+'.py')
    code="from h1eval.h10.launch import reader_factory; reader_factory('/scratch/jjyeung/orch_n30/b04_e2ehook'); import runpy; runpy.run_path("+repr(str(script))+",run_name='__main__')"
    result=subprocess.run([sys.executable,'-B','-c',code],env=dict(os.environ,A_TEST=str(tmp_path)),capture_output=True,text=True)
    (tmp_path/'probe.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
