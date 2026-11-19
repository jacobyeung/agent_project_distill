"""Write the bounded report and package the checked row kit."""
import json,hashlib,statistics,collections,tarfile
from pathlib import Path
from census import W,BASE,sha,band

def main():
 checks=json.load(open(W/'out/CHECKS.json'));assert checks['status']=='PASS_LOCAL_CHECKS_TARGET_SHORTFALL'
 rows=[json.loads(l) for l in open(W/'out/rows.jsonl')];before=[json.loads(l) for l in open(W/'inputs/store_room_rows.jsonl')]
 census=json.load(open(W/'out/CENSUS.json'));build=json.load(open(W/'out/BUILD.json'));wording=json.load(open(W/'out/WORDING.json'))
 baseline=[float(r['answer'])/(10.76391041670972230833350556 if r['provenance']['details']['unit']=='square feet' else 1) for r in before]
 areas=[r['provenance']['room_measurement']['area_m2'] for r in rows];old=collections.Counter(map(band,baseline));new=collections.Counter(map(band,areas));after=old+new
 checks['read30']=dict(status='PASS_ASSISTANT_TEXT_REVIEW',rows=30,qids=build['review_qids'],sha256=sha(W/'out/READ30.md'),scope='Read all 30 questions, full target traces, canonical scenes, and exact areas from the complete JSON records. Grammar and label consistency pass. No raw RGB visual inspection; visibility and relations are checked from GT rasters.')
 checks['input_sha256'][str(W/'finalize.py')]=sha(__file__)
 (W/'out/CHECKS.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
 inputs={str(W/f):sha(W/f) for f in ['census.py','find_bindings.py','prepare.py','wording.py','generate.py','check.py','finalize.py','out/CENSUS.json','out/PREPARED.json','out/WORDING.json','out/BUILD.json','out/CHECKS.json','out/rows.jsonl','inputs/store_room_rows.jsonl']}
 metrics=dict(input_sha256=inputs,unit='m2',before_rows=len(before),added_rows=len(rows),after_rows=len(before)+len(rows),before_histogram=dict(old),added_histogram=dict(new),after_histogram=dict(after),before_median=statistics.median(baseline),after_median=statistics.median(baseline+areas),before_mean=statistics.mean(baseline),after_mean=statistics.mean(baseline+areas),mix_scope='Hypothetical append to store-v7 room family; store itself unchanged.')
 (W/'out/HISTOGRAM.json').write_text(json.dumps(metrics,indent=2,sort_keys=True)+'\n')
 report=[
 '# sb_rowLR: traced large-room rows',
 '',
 'Built 72 checked rows: 24 at ≥40 m², including 12 at ≥60 m², plus 48 controls at 10–40 m².',
 'The requested 600 large rows are short by 576. The local pool has only six eligible captures at ≥60 m².',
 'Two rows per capture and the 50% ≥60 requirement cap this pool at 24 large rows; no scene was repeated more than twice.',
 '',
 '| Dataset | Local GT captures | Pass exclusions | ≥40 m² | ≥60 m² | New rows |',
 '|---|---:|---:|---:|---:|---:|',
 '| ScanNet | 69 | 35 | 2 | 1 | 24 |',
 '| ScanNet++ | 102 | 71 | 17 | 5 | 48 |',
 '| ARKitScenes | 0 | 0 | 0 | 0 | 0 |',
 '',
 'These are counts in the discovered local pool, not totals for the datasets. ARKitScenes training GT is MISSING in that pool.',
 'The 35 eligible ScanNet captures cover 28 physical rooms; the 71 ScanNet++ captures cover 71 rooms.',
 'All 19 eligible large captures have exact-pin store image bindings and qualifying landmark traces.',
 'The build selects 12 large captures (six in each large band) and 24 controls, with two question variants per physical room.',
 '',
 '| Dataset | 10–20 | 20–40 | 40–60 | 60–100 | ≥100 m² |',
 '|---|---:|---:|---:|---:|---:|',
 '| ScanNet | 12 | 8 | 2 | 2 | 0 |',
 '| ScanNet++ | 12 | 16 | 10 | 8 | 2 |',
 '',
 '| Room area (m²) | Store v7 before | Added | Hypothetical after |',
 '|---|---:|---:|---:|'
 ]
 for b in ['<20','20-40','40-60','60-100','>=100']:report.append(f'| {b} | {old[b]} | {new[b]} | {after[b]} |')
 report += [
 '',
 f'The room family grows from 431 to 503 rows. Its median moves from {metrics["before_median"]:.2f} to {metrics["after_median"]:.2f} m²; its mean moves from {metrics["before_mean"]:.2f} to {metrics["after_mean"]:.2f} m².',
 'The ≥40 share rises from 3.7% to 8.0%. The controls limit the median change to 0.88 m²; the area prior is not unchanged.',
 'Square-foot labels are converted to m² for the histogram. The source family contains 357 square-metre rows and 74 square-foot rows.',
 '',
 'The build uses w19’s newer sealed tree_r1 (8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa).',
 'The trace follows rows_r1/work/codeF/build_room.py: unique-label, disjoint-stem landmarks, best-view pixel share ≥0.01, and the farthest horizontal pair.',
 'The third landmark is between the pair only at projection 0.25–0.75 and perpendicular distance <0.35 times the pair length.',
 'The label follows room_v314 sensor geometry: stride-four depth pixels, native z-up poses and per-frame intrinsics; 5 cm XY cells above percentile-1 height minus 0.1 m; 0.2 m disk closing and hole filling.',
 'The trace stays qualitative and gives the rounded square-metre label after </think>. It contains no routed room call.',
 'GT lives at /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt, a path cited by the kit’s pool_room fixture.',
 'New rows derive room labels from that GT and retain exact image pins and licenses from checked store-v7 scene rows; sources need not already be room questions.',
 '',
 'Checks: exact nine-cell counts; 72 unique qids and formula-derived candidate_ids; zero store identity collisions; 36 sources and physical rooms, each used twice.',
 'Checks: independent per-row back-projection, occupancy area, landmark visibility/ranking, relation and target reconstruction pass on all 72 rows.',
 'Checks: 44 exact-pin room_v4 metric labels agree with room_v314; five-way room exclusions have zero output hits; no unlisted field changes.',
 'N validation passes for all new rows and source uses through r2_adapters.normalize and r2_contract.validate(vqa); the shared trace grammar also passes.',
 'ground_rows.pack/validate is NOT_APPLICABLE to the required direct form: that API requires a routed room computation. The native direct intake branch is the relevant check.',
 'Thirty complete records are in READ30.md; I read every sampled question and trace. Visibility was checked numerically, without reading RGB images from NFS.',
 f'Wording: authored variants pass normalized character edit distance >0.25 against {wording["unique_corpus_wordings"]:,} distinct wordings in the local kit/item corpus; 0 variants removed. Minimum distances: 0.619 and 0.573.',
 'Wording scope: 173 kit/mirror JSON or JSONL files scanned, 43 with question text; NFKC, casefold and word-token normalization.',
 '',
 'MISSING: /scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/QIDS.jsonl.gz; no claim of complete external benchmark wording coverage.',
 'MISSING: original room_v4 raster roots /scratch/jjyeung/orch_n30/rows_a2/work/rroot_v3/{new,k1r}; the kit-referenced local GT pool supplies this build instead.',
 'Not done: 600-row target, ARKitScenes coverage, complete dataset census, full benchmark-bank wording audit, RGB-byte verification, store merge or training.',
 'The 600-row target needs at least 150 eligible ≥60 m² scenes at the two-row cap; only six are available here (144 more needed).',
 'Borderline chronology retained: none. Before/after above describes the requested distribution comparison.',
 '',
 'Reproduce all reported counts: `python census.py; python find_bindings.py; python prepare.py; python wording.py; python generate.py; python check.py; python finalize.py`.',
 'Use `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` for each command; all reads are local after the supplied reference snapshots.',
 'census.py produces pool eligibility and baseline counts; prepare.py checks traces/bindings; generate.py asserts cells; check.py produces validation counts; finalize.py produces histograms and this report.',
 'out/sb_rowLR.tar contains code, row/source snapshots and reports. Its full sha256 is in out/sb_rowLR.tar.sha256.'
 ]
 assert len(report)<=80,len(report)
 (W/'out/REPORT.md').write_text('\n'.join(report)+'\n')
 (W/'STATUS.md').write_text('Complete feasible local build: 72 rows pass independent geometry, trace, identity, field, exclusion, reuse, native direct-intake and local wording checks; all 30 sampled traces were read. The build contains 24 large rows, half at least 60 m², and remains 576 large rows short because only six qualifying ≥60 m² captures are available. out/REPORT.md records the histogram, exact missing inputs, check scope and reproduction commands. No store merge or training was performed.\n')
 files=[W/f for f in ['census.py','find_bindings.py','prepare.py','wording.py','generate.py','check.py','finalize.py','STATUS.md']]
 files += [p for p in (W/'out').iterdir() if p.is_file() and p.suffix in {'.json','.jsonl','.md','.log','.txt'}]
 files += [W/f for f in ['inputs/INPUT_SHA256.json','inputs/ROWS_V7_R1_20261117.md','inputs/R1_M200_TRACE_ANALYSIS_20261119.md','inputs/coverage_rows_v2.py','inputs/check_cov_v2.py','inputs/store_room_rows.jsonl','inputs/binding_sources.jsonl']]
 manifest=dict(input_sha256={str(W/'out/CHECKS.json'):sha(W/'out/CHECKS.json')},files={str(p.relative_to(W)):sha(p) for p in sorted(files)})
 (W/'out/PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');files.append(W/'out/PACKAGE_MANIFEST.json')
 archive=W/'out/sb_rowLR.tar'
 with tarfile.open(archive,'w') as tf:
  for p in sorted(set(files)):tf.add(p,arcname=str(p.relative_to(W)),recursive=False)
 (W/'out/sb_rowLR.tar.sha256').write_text(sha(archive)+'  sb_rowLR.tar\n')
 print('REPORT lines',len(report),'ARCHIVE',archive.stat().st_size,sha(archive))
if __name__=='__main__':main()
