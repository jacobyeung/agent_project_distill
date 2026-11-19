from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];P=W.parent
paths=[P/'donorrev/REVIEW_VERDICT.md']
paths.extend(P/'donor/out'/n for n in ('PATCH_DONOR.patch','FILES_TOUCHED.json','REPORT.md','READER_REQUEST.md','REAL_WEIGHT_COMMAND.sh','K1_INVARIANCE.json','EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json'))
paths.extend(sorted((P/'donor/code').glob('*.py')))
paths.extend(P/'donorrev/work'/n for n in ('K1_MINE_FILM0.json','K1_MINE_FILM1.json','brittle_mine.py','FSDP_MINE.json','parity_mine.py','run_suite.py'))
paths.append(Path(__file__).resolve())
missing=[str(p) for p in paths if not p.is_file()]
inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
(W/'out/INPUTS.json').write_text(json.dumps(dict(input_sha256=inputs,missing=missing,command='python code/input_inventory.py',scope='Task inputs and reused harness origins. Reviewer JSON is inherited evidence, not a claim that its tests were rerun here.'),indent=2)+'\n')
print('Named inputs hashed:',len(inputs),'missing:',missing)
