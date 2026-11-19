from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1'
p=T/'student_pilot/r1_coverage.py';s=p.read_text()
s=s.replace("            if name not in AUDIT_SOURCE_NAMES:","            if name not in AUDIT_SOURCE_NAMES or name in deferred_names():")
s=s.replace("    if read_pins:\n        sampling =", "    if read_pins:\n        for field, pin in (('streams.routing', (cfg or {}).get('streams', {}).get('routing')),\n                           ('request.routing_base', (request or {}).get('routing_base'))):\n            if pin is not None:\n                receipt = document(pin)\n                if receipt.get('source_membership'):\n                    slice_bound(field+'.source_membership', '<present>',\n                                'R1_ROUTING_BASE_INVALID:R1_DEFERRED_MEMBERSHIP_NONEMPTY')\n        sampling =")
s=s.replace("    if deferred(cfg, sources=sources):", "    if deferred(cfg, sources=sources, read_pins=True):")
p.write_text(s)
p=T/'student_pilot/r1_population.py';s=p.read_text()
s=s.replace("    output = Path(output)\n    output.mkdir(parents=True, exist_ok=True)\n    card = load(pinned(card_pin))\n    from .r1_coverage import deferred, deferred_card\n    minimal = deferred(cfg, read_pins=True, card=card)", "    from .r1_coverage import deferred, deferred_card\n    minimal = deferred(cfg, read_pins=True)\n    output = Path(output)\n    output.mkdir(parents=True, exist_ok=True)\n    card = load(pinned(card_pin))\n    deferred(cfg, card=card)")
p.write_text(s)
# The central receipt check runs for every metadata-aware entry, including s1.
p=L/'work/build23b/tests.py';s=p.read_text().replace("'R1_MINIMAL_SLICE_BOUND:request.routing_base.source_membership'", "'R1_MINIMAL_SLICE_BOUND:streams.routing.source_membership'")
s=s.replace(" def test_request_base_membership_refuses(self):", " def test_central_stream_receipt_membership_refuses(self):\n  c=cfg();c['streams']['routing']=pin('receipt_bound',dict(source_membership={'path':'unread_source','sha256':'0'*64}))\n  with scope(PATHS):\n   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:streams.routing.source_membership'):C.deferred(c,read_pins=True)\n def test_request_base_membership_refuses(self):")
p.write_text(s)
