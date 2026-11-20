import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=D/'arm_negatives.py';s=(L/'work/build24m4e/arm_negatives.py').read_text()
s=s.replace('("bad_digest","R1_ROUTING_SELECTION_PIN_INVALID")','("bad_digest","R1_REVIEWED_REGENERATED_DIFFERS")').replace('("wrong_db","R1_ROUTING_SELECTION_DATABASE_DIFFERS")','("wrong_db","R1_ROUTING_REGENERATED_DATABASE_DIFFERS")')
s=s.replace('    with patch.object(arm,"L",workspace):','''    reviewed=v.get("regenerated_sha256")
    if not isinstance(reviewed,str) or len(reviewed)!=64:reviewed=selection["regenerated_sha256"]
    verdict=N/(case+"_RESULT.txt");verdict.write_text("Synthetic test only: PASS\\n"+J.sha(p)+"\\n"+reviewed+"\\n")
    auth=dict(reviewed_selection_sha256=J.sha(p),reviewed_regenerated_sha256=reviewed,review_verdict=verdict)
    with patch.object(arm,"L",workspace):''')
s=s.replace('arm.apply(p,q,out,base_path=bp)','arm.apply(p,q,out,base_path=bp,**auth)')
p.write_text(s)
p=D/'run_suites.py';s=p.read_text().replace("'coverage_tests','arm_missing_test')", "'coverage_tests','arm_missing_test','arm_negatives')");replace(p,s)
p=D/'validation.py';s=p.read_text().replace('len(tests)==14','len(tests)==15').replace('All 14 scan, kit','All 15 scan, kit');replace(p,s)
