from common import *
p=D/'closure.py';s=p.read_text().replace("'student_pilot.row_removals'}","'student_pilot.row_removals','student_pilot.batches','student_pilot.carrier_c1_routing','student_pilot.ground_tokens','student_pilot.mdg_decode_tokens'}")
replace(p,s)
