from pathlib import Path
import sys
B=Path(__file__).resolve().parents[1];R=B.parents[1]
sys.path.append(str(B/'code'))
from adapter import *
from engine import *
from boundary import Boundary
spec=dict(tree=str(R/'from113/work/tree'),artifact={'path':'fixture','sha256':digest('fixture')},config={'path':'fixture','sha256':digest('fixture')})
initialize(spec)
b=validate_bound(B/'work/a0/BOUND.json')
from scorer import comparator_check
print(comparator_check([R/'in/comparators/f17.per_question_scores.jsonl',R/'in/comparators/p1m200.per_question_scores.jsonl'],B/'out/SCORER_CHECK.json'))
boundary=Boundary();g=B/'work/g1/GEOMETRY.json'
print(run(B/'work/a0/BOUND.json',spec,g,B/'work/j2',boundary=boundary))
merge(B/'work/a0/BOUND.json',[B/'work/j2'],B/'work/MERGED.json')
