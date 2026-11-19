from pathlib import Path
L=Path(__file__).resolve().parents[2];p=L/'work/tree_r1/student_pilot/r1_coverage.py';s=p.read_text()
s=s.replace("            if pin is not None:\n                receipt = document(pin)", "            if pin is not None:\n                if field == 'request.routing_base':\n                    from .r1_handover import pin_values\n                    if pin_values(pin) != pin_values((cfg or {}).get('streams', {}).get('routing')):\n                        raise ValueError('R1_ROUTING_BASE_DIFFERS')\n                receipt = document(pin)")
p.write_text(s)
p=L/'work/build23b/tests.py';s=p.read_text().replace("'R1_MINIMAL_SLICE_BOUND:request.routing_base.source_membership'):\n    C.routing_request(c,dict(routing_base=p))", "'R1_ROUTING_BASE_DIFFERS'):\n    C.routing_request(c,dict(routing_base=p))")
p.write_text(s)
