"""Replay the review's intake loop on the published-schema manifests."""
import collections
import json
import os
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.r2_intake import intake
from student_pilot.r2_materialize import materialize
source=(L/'work/review1/evidence/run_intake.py').read_text()
body=source[source.index('d = Path(sys.argv[1])'):]
body=body.replace("d.glob('*.manifest.json')","d.glob('**/manifest.json')")
body=body.replace("summary[rep['family']]", "summary[str(m.relative_to(d))]")
sys.argv=['review_intake',str(L/'work/build4/rows_complete'),str(L/'work/build4/review_intake_final')]
exec(compile(body,'review_intake_body','exec'),globals())
