from pathlib import Path
L=Path(__file__).resolve().parents[2];p=L/'work/build23b/tests.py';s=p.read_text();at=s.index(' def test_member_constructor_checks_before_source_reader')
s=s[:at]+''' def test_request_card_binding(self):
  c=cfg();v=card();v['cells'].append(dict(type='camera_wording',stream='routing',rows_per_step=1))
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:request.card.cells:camera_wording'):
    C.routing_request(c,dict(routing_base=c['streams']['routing'],card=pin('request_card',v)))
 def test_request_composed_receipt_binding(self):
  c=cfg();p=pin('request_composed',dict(source_membership={'path':'unread','sha256':'0'*64}))
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:request.routing_base.source_membership'):
    C.routing_request(c,dict(routing_base=p))
 def test_source_names_authenticates_config_catalog(self):
  c=bound(cfg(),'row_sources','recovery')
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:r1_training.row_sources:recovery'):C.source_names({},c)
''' +s[at:];p.write_text(s)
