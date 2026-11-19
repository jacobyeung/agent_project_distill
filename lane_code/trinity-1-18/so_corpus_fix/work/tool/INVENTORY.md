# Read inventory (corpus lane, 2026-11-19 07:00Z)

Staging corpus: trinity-3-30:/scratch/jjyeung/orch_n30/corpus/stage/ (reads/, index/, INDEX.jsonl). Tool: corpus/tool/ingest_read.py (formats kit, routed), corpus_score.py, SCHEMA.md.

## A. Ingested (11 reads, 11,811 items, 26.3 MB gz)
| read_id | job | items | headline as stored (mean score) |
|---|---|---|---|
| 673bc60f_s200_devS1R0_direct_a8102c3207b | 172646 | 3120 | B2048 68.82 (main primary 77.34) |
| 673bc60f_s100_devS1R0_direct_a5d2d909067 | 172466 | 3120 | B2048 67.35 |
| 469ddece_s544_devS1R0_direct_adff67f7ae9 | 171197 | 1781 | B2048 56.01 (a7 only) |
| 673bc60f_s200_facing_direct_a2e46c0504e | 172658 | 300 | B2048 91.00 |
| 469ddece_s544_vsti_direct_acb2faedd41 | 172475 | 900 | 46.11 |
| 673bc60f_s200_vsti_direct_a35f73e87f0 | 172654 | 900 | 58.33 |
| 673bc60f_s200_devS1_routed_A4 | 172744 | 636 | tower 75.27 |
| 673bc60f_s200_room134_routed_B5 | 172858 | 134 | room 64.40 |
| 469ddece_s544_devS1_routed_b1.r0 | 171253 | 636 | tower 66.59 (null_argmax) |
| 469ddece_s544_devS1_routed_b1.r1 | 171253 | 150 | distance 28.27 (candidates_argmax) |
| 469ddece_s544_room134_routed_b2 | 172456 | 134 | room 6.57 |
Staging also holds an empty 0-item file for FAILED 170928 (aed15a8b7cb); it will not be published (tool fix pending: refuse 0-item returns).

## B. On trinity-3-30, needs a new adapter (second Codex job)
- Official VSI-Bench direct, step 544, Orchard 170008, 4,008 items: b07_offread/in/ret_vsi (result.tar.gz 6.1 MB). official: true.
- Official ReVSI 999 t32 direct, step 544, Orchard 170037, 679 items: b07_offread/in/ret_revsi (1.6 MB). official: true.
- Native routed dev-S1, step 544, Orchard 170056, 636 items: b04_e2ehook/work/n13/full_c8r/result.tar.gz (95.3 MB; also unpacked n13/ret). Same bytes size as Orchard okh7/n2r/b07a20b364 and trinity-1-18 old_lanes b01_d0guard/work/from113/work/full_c8r.
- readk a4cadd8934b (fix-1c reader check read, 4.1 MB; copies in d0/, h1read/, h1face/, h1vsti/ readk): kit format, to ingest once.
- D@544 R0-dev held-out distance (cont_ops18 package d00c03dcc685e, job 172957, running): routed; ingest when fetched.

## C. Only on Orchard (okh7, depth 3; sizes of result.tar.gz)
- ae71c903_fetched: a24ea1a1936 (H1-1 m100, 170808) 14.3 MB; ae470417b41 (D0 m200 R0-dev, 170757) 10.7 MB; af35386aa3e (D0 m100, 170786) 14.4 MB; aed15a8b7cb (FAILED 170928) 0.3 MB. Local x/ copies hold metadata only.
- ae71c903 (pool): a37de5787ed 0.2 MB, b01ec87a6f29b00029{a7c 0.0, a87 4.2, ab2 0.3, ac6 0.4, ad2 0.9} MB, bf94a7976a7e900029b5e 4.0 MB, e09e45fda45db00029c87 0.0 MB (identity to be read from each tar's metadata).
- n2r: b07a20b364 95.3 MB (= 170056), d627d31523064791d2ce3456 89.8 MB, d12e2a0337651f2637e988f9 2.0 MB.
- x27ret: pb59bef09f3 0.4 MB, pb906babb42 0.3 MB.
- b7e31d84a90c62f5 (K1 own phase): 170235/ad2472b1be07d4193 97.9 MB, 170235/c75955208369b4e48 1.0 MB, 170193 and 170206 returns 0.0 MB (failed).
- Routed package returns a15_cot_ap*/f/0.tgz with EXIT.json only for b635a315de01e (B5) and d60a20ec01296 (A4): both already local.
Total Orchard-only read bytes: about 0.33 GB (n2r and K1 dominate).

## D. trinity-1-18
- n30_mirror/cont_ops/*.tar (c16_mirror, h1pkt_fix5, h1read_fix1c, h1read_fix2, h1vsti_v1): the same kit returns as trinity-3-30 (a8102c3207b, a5d2d909067, adff67f7ae9, a2e46c0504e, a35f73e87f0, acb2faedd41, a4cadd8934b). Nothing new.
- old_lanes_3_30_{a,b}.tar (40 GB): b07 and b01 build trees hold CPU rehearsal returns on fixtures (not student reads); real returns: b01_d0guard/work/from113/work/full_c8r (= 170056) and .../work/p9/result.tar.gz (identity to check). Listings: trinity-1-18:/scratch/jjyeung/n30_mirror/corpus_work/*.list.
- k1_ops3 (68 GB): K1 build/rehearsal evidence; RH_RESULT.tar (182.8 MB) and rh_result_1_3_r3.tar (191.7 MB) are K1 head-read results (not generation traces), to be checked.

## E. Lost (records name them; files on trinity-2-18 / 2-28 / 1-3): list being compiled from distill_design records.
