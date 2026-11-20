"""Source-only scale/gravity audit; quoted design numbers are not recomputed."""
import hashlib,json
from pathlib import Path
import serving_reference as R

def main():
    a4=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4/src/b/e2e_reader')
    comparisons=[]
    for name in ['stage1.py','real.py','geometry.py','generate.py']:
        actual=R.read(a4/name);local=R.read(R.ROOT/'reader_src/e2e_reader'/name)
        comparisons.append(dict(source=str(a4/name),local=str(R.ROOT/'reader_src/e2e_reader'/name),equal=actual==local))
    for path in [R.PACK/'designer_evidence/san_kit.py',R.PACK/'r1_src/b/heads/selector/sl118/sl_tables.py',
        R.PACK/'r1_src/b/heads/selector/isolate_tables.py',R.SEL/'work/run_iso/selector_head.json',
        R.SEL/'sl118/SCALES_S4.json',R.ROOT/'inputs/HEAD_ACCURACY_DESIGN_20261119.md',R.ROOT/'provenance_v2.py',
        Path('/scratch/jjyeung/n30_mirror/tower_redecide/work/reprice.py')]:R.read(path)
    lines=[
      'The routed reader uses own-depth scale and checkpoint gravity; the selector was trained on S4/G1 geometry.',
      f'`A4` below means `{a4}`; `PACK` means `{R.PACK}`; `SEL` means `{R.SEL}`.',
      'Step 200 uses A4; step 544 combines camera read 0 and distance read 1 from b1 (`PACK/designer_evidence/san_kit.py:168-180`).',
      'Both routed contracts use median(own depth / G3T depth) over finite positive depths above median tower confidence (`A4/stage1.py:39-73`).',
      'The depth comes from that checkpoint’s prefill; no [0.1,10] own-depth gate is applied (`A4/stage1.py:48-60`).',
      'The default is OwnDepthScale, and gravity comes directly from the prefill gravity head (`A4/real.py:64-87`).',
      'Serving converts log(scale) through float32 exp (`A4/generate.py:42-46`).',
      'Serving removes the terminal up-axis rejection but retains the sealed shape/rotation/intrinsic checks (`A4/geometry.py:22-39`).',
      'Stored arrays and tower reconstruction enter this same contract (`A4/geometry.py:42-90`).',
      'This CPU replay uses the stored step-544 own tensors; it does not recreate a step-200 prefill or assert equal numeric scales across checkpoints.',
      'run_iso records caps_iso as training data and weights 6d97c524… (`SEL/work/run_iso/selector_head.json:160-173`).',
      'Those tables use S4 = exp(b0 + b1 log(h_raw) + b2 log(span)); G1 is the normalized mean tower camera up vector (`PACK/r1_src/b/heads/selector/sl118/sl_tables.py:58-87,129-166`; `SEL/sl118/SCALES_S4.json`).',
      'Isolation retains S4 and G1 and recomputes per-name features (`PACK/r1_src/b/heads/selector/isolate_tables.py:25-63`).',
      'The design’s S4/G1 GT-mask lifting prices are 28.0 plain, 61.4 best-frame, 38.8 majority-hull, 69.7 bestspread, and 69.8 cut-and-vote on 1,001 stored-label train rows (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:39`).',
      'The corrected S4/G1 prices are 67.91 train and 66.94 held-out, quoted from the design; these are GT-mask geometry prices, not scores of the selector table (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:38`).',
      'The roughly 3-point oracle-scale bound is relative to S4 and cannot be assigned to own-depth serving (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:30,70`).',
      'The 74.30 train / 75.05 held-out GD prices use reviewed convert geometry, distinct from S4/G1 and from serving’s guard/rounding (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:38`; `/scratch/jjyeung/n30_mirror/tower_redecide/work/reprice.py:6-7,56-58`).',
      'The routed 61.8 step-544 and 65.3 step-200 gap scores and their frame/margin bands come from served responses (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:36`), not S4/G1 table replay.',
      'The exploratory 50.7 size price is a dev-S1 name-within-room join, not a K1 selector-table score (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:43`).',
      'MISSING: source-level attribution for the quoted 60.4/68.0 pipeline pair and record-only 58.6% top-1/4.7% null values; the design does not identify their executable/input pins (`inputs/HEAD_ACCURACY_DESIGN_20261119.md:27,45`). No geometry mapping is invented.',
      'Commands: `bash run.sh provenance_v2.py`; `bash run.sh serving_reference.py`. SOURCE_PROVENANCE.json hashes all audited sources; REFERENCE_REBUILD.json records the new geometry and labels.',
    ]
    assert len(lines)<=25
    (R.ROOT/'out/SCALE_PROVENANCE.md').write_text('\n'.join(lines)+'\n')
    R.write(R.OUT/'SOURCE_PROVENANCE.json',dict(reader_comparisons=comparisons,heldout_evaluated=False,
        quote_only='Existing design figures are quoted for provenance; no new held-out or routed scoring is performed.'))
    print(json.dumps(comparisons,indent=2))

if __name__=='__main__':main()
