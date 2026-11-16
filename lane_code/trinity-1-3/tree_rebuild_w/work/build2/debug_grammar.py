import os
from pathlib import Path
import sys
import tempfile
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
tempfile.tempdir=str(L/'work/tmp')
from tests.test_r2_families import ground
from tests.test_r2_data_path import directory
from student_pilot import trace_grammar as G
import re
row=ground(directory(),'units')
body=re.search(r'<think>(.*?)</think>',row['target'],re.S).group(1)
body=re.sub(r'Call: measure ','I will measure ',body)
print(body)
print(G.validate_trace(body,form='program',question=row['question'],n_frames=32))
