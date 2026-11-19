"""Package the checked packet; verify every declared local input and every tar member."""
from common import *
import tarfile,io

def main():
 c=load(ROOT/'out/CHECKS.json');b=load(ROOT/'out/BUILD.json');assert c['status']=='PASS'
 files=[Path(p) for p in ['out/relative_count.jsonl','out/BUILD.json','out/ROW_CHECKS.json','out/CHECKS.json','out/GT_CHECK.json','out/WORDING_CHECK.json','out/RASTER_CHECK.json','out/READ40.md','out/READ40_TEXT.md','out/READ40_REVIEW.json','out/CROSS_FAMILY_REVIEW.json','out/BINDING.json','out/room_audit_final/audit.json','out/room_audit_final/rows.sqlite']]
 verified={}
 for rel in files:
  if rel.suffix!='.json':continue
  data=json.loads((ROOT/rel).read_text());pins=data.get('input_sha256',data.get('inputs'))
  assert isinstance(pins,dict) and pins,rel
  for name,value in pins.items():
   want=value['sha256'] if isinstance(value,dict) else value
   assert str(name).startswith('/scratch/'),('outside local inputs',name)
   if name not in verified:verified[name]=sha(name)
   assert verified[name]==want,('input digest mismatch',str(rel),name,want,verified[name])
   PINS[name]=want
 assert sha(ROOT/'out/relative_count.jsonl')==b['output']['sha256']
 assert c['rows']==4000 and c['manual_read']['rows']==40
 # The complete JSON examples must be exact members of the delivered packet.
 allrows={r['qid']:r for r in rows(ROOT/'out/relative_count.jsonl')}
 examples=[json.loads(s) for s in re.findall(r'```json\n(.*?)\n```',(ROOT/'out/READ40.md').read_text(),re.S)]
 assert len(examples)==40 and all(r==allrows[r['qid']] for r in examples)
 code_pins()
 dump(ROOT/'out/INPUT_CHECK.json',dict(status='PASS',input_sha256=dict(PINS),declared_local_inputs_verified=len(verified),complete_read40_rows_verified=40,command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python code/package.py'))
 report=f'''The relative-count packet is **PASS for CPU data checks; ready for tree_rebuild binding**. It is not bound to a production store.

`out/relative_count.jsonl` contains 4,000 rows from 1,803 b12 total-count source rows. The 20 wordings each have 200 rows.
Each target has two counting-procedure lines, one qualitative comparison in question order, and one option letter after `</think>`.
The procedure body matches the pinned v7 object_counting row exactly after category substitution. Numeric step labels are omitted.
Every think block contains zero numbers, number words, instance lists, tool calls, or stated measurements.
Only the target and input-hash provenance differ from the selected sb_rowC rows; questions, options, frames, identifiers and sampling match.

Balance: first category larger 1,800; second category larger 1,800; equal 400. Every template has 90/90/20.
Letters: A=1,334; B=1,333; C=1,333. Each template has 66 or 67 occurrences of each letter.
Dataset rows: ARKitScenes=3,195; ScanNet=805. The packet covers 739 captures and 444 physical rooms.
Reuse maxima: source=8; unordered pair=4; oriented pair=2; capture=24. Full per-template and count-bucket tables are in CHECKS.json.

N tree: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7` (w24 TREE_SEAL).
All 4,000 pass `trace_grammar.validate_trace`, `validate_row`, `r1_counting.admit`, and `r1_training.row_check`.
All 4,000 pass `ground_rows.pack/validate` through the direct-to-ground serialization adapter, which preserves think bytes and wraps only the answer.
All 4,000 qids and candidate_ids are unique; every candidate_id matches the kit formula.
Independent set cardinalities from b12 totals reproduce every comparison and option letter; the exact-match scorer accepts every GT target.
All 739 selected local GT rasters match their source/census/raster-audit SHA-256 pins. Raster arithmetic is inherited by hash; totals arithmetic is fresh.
The native room checker resolves every row. R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4 and K1 4d4736cf each have zero hits.
Wording distance passes on all 4,000 rows: minimum 0.5666666667 against the required 0.4 threshold.
The references contain 139 dev-S1 relative-count items, 130 unique wordings; R0-dev has zero relative-count items among 2,169 items.
Distance uses NFKC/casefold/word-token normalization and character Levenshtein divided by maximum length; normalized text is ASCII. The C++ routine passes 300 Python-oracle cases.

I read all 40 complete question/option/target/answer/GT summaries: one unequal row and one tie per template. READ40.md prints the corresponding full JSON rows.
The object_counting/relative_count cross-family review passes: the procedure is shared, while the relative-count answer is the matching option letter.
READ40_REVIEW.json and CROSS_FAMILY_REVIEW.json identify the reviewed rows and scope; this is a primary-agent review.

BINDING.json documents direct VQA store augmentation, the existing configuration fields, the counting cell and required production proofs.
N's direction-twin verifier is specific to its pinned twins; tree_rebuild must add authenticated support for this family and regenerate the store/receipt/room/plan bindings.
N's current removal-key reader does not consume provenance.relative_count.source_qid; tree_rebuild must bind the verified b12 source key explicitly.
This packet makes no tree changes. It supplies no fabricated production receipt, scene mapping, native admitted offsets, or accuracy claim.
No required packet input is missing. RGB inspection, frame-host preparation, production-store augmentation and training were not run.

Commands below run from this workspace with `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1`.
`python code/build.py` authenticates the v7 store procedure and writes the 4,000 rows and BUILD.json.
`python code/check.py` produces every row/GT/identity/balance/scorer count, wording distance and oracle count, ROW_CHECKS.json and the 40-row read files.
`g++ -O3 -shared -fPIC code/nearest.cpp -o code/nearest.so` builds the exact distance implementation.
`python code/raster_hash_check.py` produces the 739 byte matches in RASTER_CHECK.json.
`python /scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py --store "$PWD/out/relative_count.jsonl" --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 --lists /scratch/jjyeung/orch_n30/sb_auditfix2/inputs/lists --out "$PWD/out/room_audit_final"` produces room counts and exclusion hits; its output directory must be empty.
`sed -n '1,260p' out/READ40_TEXT.md` and `sed -n '261,560p' out/READ40_TEXT.md` supplied the manual read.
`python code/review_binding.py` records that completed review, checks the cross-family contract, writes BINDING.json and consolidates CHECKS.json.
`python code/package.py` verifies every declared local input SHA-256 and exact full-JSON read sample, then produces the report, archive and PACKAGE_CHECK.json.
Every JSON audit binds its inputs by SHA-256; every delivered row retains its source/frame hashes and adds the build-input hashes.
The package includes code, rows, full read samples and audits. Reproduction requires the pinned read-only inputs; RGB, raster arrays and the v7 store are not bundled.
Archive: `out/fbp_relcnt.tar`; SHA-256: `out/fbp_relcnt.tar.sha256` and `out/SHA256SUMS.txt`. Check with `sha256sum -c out/fbp_relcnt.tar.sha256`.
No-archaeology review: no borderline historical wording is retained. This is an internal build report.
'''
 assert len(report.splitlines())<=80
 (ROOT/'out/REPORT.md').write_text(report)
 status('The 4,000-row relative-count packet passes every requested CPU data check, the 40-row manual read, and the cross-family review. All five room exclusion counts are zero and the minimum wording distance is 0.566667. BINDING.json records the required N augmentation and configuration work; no production store or tree was changed. The final report, archive and SHA-256 receipt are in out/.')
 files.extend([Path('out/INPUT_CHECK.json'),Path('out/REPORT.md'),Path('STATUS.md')])
 files.extend(sorted(p.relative_to(ROOT) for p in (ROOT/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.cpp','.so')))
 filehashes={str(p):sha(ROOT/p) for p in files}
 manifest=dict(input_sha256={str(ROOT/p):h for p,h in ((Path(k),v) for k,v in filehashes.items())},members={k:dict(sha256=v,bytes=(ROOT/k).stat().st_size) for k,v in filehashes.items()},command='python code/package.py')
 dump(ROOT/'out/PACKAGE_MANIFEST.json',manifest);files.append(Path('out/PACKAGE_MANIFEST.json'))
 package=ROOT/'out/fbp_relcnt.tar'
 with tarfile.open(package,'w') as tar:
  for rel in files:tar.add(ROOT/rel,arcname=str(rel),recursive=False)
 tarhash=sha(package)
 with tarfile.open(package,'r') as tar:
  members=tar.getmembers();assert len(members)==len(files)
  for member in members:
   h=hashlib.sha256(tar.extractfile(member).read()).hexdigest();assert h==sha(ROOT/member.name),member.name
 archivecheck=dict(status='PASS',input_sha256={str(package):tarhash,str(ROOT/'out/PACKAGE_MANIFEST.json'):sha(ROOT/'out/PACKAGE_MANIFEST.json'),str(ROOT/'code/package.py'):sha(ROOT/'code/package.py')},archive_bytes=package.stat().st_size,members_verified=len(members),workspace_bytes=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),command='python code/package.py')
 assert archivecheck['workspace_bytes']<1_000_000_000
 dump(ROOT/'out/PACKAGE_CHECK.json',archivecheck)
 sums=f'{tarhash}  out/fbp_relcnt.tar\n'
 (ROOT/'out/fbp_relcnt.tar.sha256').write_text(sums);(ROOT/'out/SHA256SUMS.txt').write_text(sums)
 print(json.dumps(archivecheck));print('archive_sha256',tarhash)
if __name__=='__main__':main()
