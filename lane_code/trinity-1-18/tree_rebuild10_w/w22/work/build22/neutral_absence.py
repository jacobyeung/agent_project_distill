"""Use neutral job-visible slot codes without broadening absence admission."""
from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';p=L/'work/tree_r1/student_pilot/r1_absence.py'
s=p.read_text()
assert "SLOT_CODES" not in s
(D/'before/r1_absence_named.py').write_text(s)
s=s.replace("PREFIXES =", "SLOT_CODES = {'0':'heads_gf1_connector','1':'heads_frame_embeddings'}\n\nPREFIXES =",1)
s=s.replace("slots=cfg.get('r1_training',{}).get('not_present_slots',[])\n    if not slots:return {}\n    if set(slots)!=set(PREFIXES) or len(slots)!=2:raise ValueError('NOT_PRESENT_SLOT_FORBIDDEN')", "codes=cfg.get('r1_training',{}).get('not_present_slots',[])\n    if not codes:return {}\n    if not isinstance(codes,list) or set(codes)!=set(SLOT_CODES) or len(codes)!=2:raise ValueError('NOT_PRESENT_SLOT_FORBIDDEN')\n    slots=[SLOT_CODES[code] for code in codes]")
s=s.replace("'not_present_slots':list(PREFIXES)","'not_present_slots':list(SLOT_CODES)")
p.write_text(s)
p=L/'work/tree_r1/student_pilot/r1_components.py';s=p.read_text()
s=s.replace('evidence as absence_evidence, PREFIXES','evidence as absence_evidence, SLOT_CODES')
s=s.replace("'not_present_slots':list(PREFIXES)","'not_present_slots':list(SLOT_CODES)")
p.write_text(s)
for name in ('config.json','kit_config.json'):
 p=D/'inputs'/name;v=json.loads(p.read_text());v['r1_training']['not_present_slots']=['0','1'];p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for name in ('records.py','prepare_capacity.py'):
 p=D/name;s=p.read_text();s=s.replace("['heads_gf1_connector','heads_frame_embeddings']","['0','1']");p.write_text(s)
p=D/'absence_test.py';s=p.read_text().replace("list(A.PREFIXES)","list(A.SLOT_CODES)");p.write_text(s)
p=D/'kit_tests.py';s=p.read_text().replace("{'heads_gf1_connector','heads_frame_embeddings'}","{'0','1'}");p.write_text(s)
p=D/'new_tests.py';s=p.read_text().replace("'absence_test','scanner_test'","'absence_test','scanner_test','neutral_test'");p.write_text(s)
print('Activated neutral absence slot codes')
