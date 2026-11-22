# REPORT_GTCD_ARK (kit_ark; lever7; text saved by the lane from the builder's reply)
Seal gtcd/SHA256SUMS_GTCD_ARK (64 files, f7b7a5a4...). Sealed gtcd/kit unchanged (SHA256SUMS_GTCD still checks).
## Diff vs kit (frames.py, seeds.py, the four old tests byte-identical)
- gtc_common.py: DENSE_ARK_ROOT=gtcd/dense_ark, DENSE_ARK_MANIFEST=dense_ark/DENSE_D_ARK.json, OUT_ARK=gtcd/out_ark; ScanNet constants unchanged.
- dense.py: ARKit run must be --datasets arkit alone with its own --out; writes <out>/DENSE_D_ARK.json + .sha256; refuses ARKit into dense/; ScanNet path unchanged.
- track.py: manifest/out dir from GTCD_DENSE/GTCD_TRACK_OUT or flags; pairing check (ARKit manifest never into out/track; ScanNet never into out_ark/track).
- launch_gpu.sh: --dense M --out D (or env); checks SHA256SUMS_GTCD_ARK; ARKit manifest needs explicit --out, must match its .sha256, may not write out/track; both paths on /scratch; no-arg inner command equals the sealed kit's except cd kit_ark and explicit default --dense.
- relift_t.py: reads both units (complete/absent/incomplete/no_ok_capture); three populations ScanNet+ScanNet++, ARKit, pooled, each with d, d-a beside d-b, share of e-a, d-t, e-a, b-a, per-dataset stats and P/R, the registered reading on that population, a label; pooled only when both units complete; a..b must equal RELIFT_GTCB.json; output out_ark/RELIFT_GTCD_ARK.json, no overwrite; prints only status.
- seal.sh: SHA256SUMS_GTCD_ARK over kit_ark code/tests, out/seeds_b, dense/DENSE_D.json; ARKit manifest checked by its own .sha256. run_cpu_rehearsal.sh passes --dense/--out.
## Tests (gtcd/work/kit_ark_tests/): old tests pass in kit_ark (units 24/24, dense, launch_dry, relift_t 7/7); test_dense_ark (synthetic 483-frame copy of 43828324 with real served anchors: 32/32, ScanNet DENSE_D.json bytes+mtime kept, refusals); test_relift_units (toy d=GT: d=e on 117 in all three populations 84/33/117, P/R 1; d=b -> d-b=0; ARKit absent -> ARKit and pooled not_read; incomplete/foreign cases); test_launch_dry_ark (8 refusals). No CPU rehearsal on real ARKit frames yet.
## Lane commands (G=/scratch/jjyeung/orch_n30/lever7/gtcd, SAM=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python)
1. decode: cd $G/arkit && $SAM -B tools/decode_arkit.py --raw raw --plan plan/PLAN_ARKIT.json --frames frames --rejected frames_rejected --manifest DECODE_ARKIT.json --workers 8
2. dense: cd $G/kit_ark && $SAM -B dense.py --datasets arkit --workers 8 --out $G/dense_ark --frames-dir arkit=$G/arkit/frames/{id}
3. copy: cd /scratch/jjyeung/orch_n30/lever7 && tar cf - gtcd/kit_ark gtcd/dense_ark gtcd/SHA256SUMS_GTCD_ARK | ssh -o ConnectTimeout=20 trinity-0-13.ib 'cd /scratch/jjyeung/orch_n30/lever7 && tar xf - && cd gtcd && sha256sum --quiet -c SHA256SUMS_GTCD_ARK && (cd dense_ark && sha256sum --quiet -c DENSE_D_ARK.json.sha256) && echo OK'
4. launch on 0-13: cd $G && tmux new-session -d -s gtcd_ark_gpu "bash kit_ark/launch_gpu.sh d --dense $G/dense_ark/DENSE_D_ARK.json --out $G/out_ark/track"
5. back: cd $G/out_ark && tar cf - track | ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/lever7/gtcd/out_ark && cd /scratch/jjyeung/orch_n30/lever7/gtcd/out_ark && tar xf -'
6. relift on 2-28: cd $G/kit_ark && CUDA_VISIBLE_DEVICES='' nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B relift_t.py -> out_ark/RELIFT_GTCD_ARK.json; fresh review before reading.
## Removal candidates: work/test_dense_ark (~153 MB), work/toy_units, work/dry_launch_test_ark, work/kit_ark_tests.
