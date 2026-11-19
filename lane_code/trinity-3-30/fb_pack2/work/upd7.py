S='/scratch/jjyeung/orch_n30/fb_pack2/STATUS.md'; t=open(S).read()
a=t.index('## Running at'); b=t.index('## Next (in order)')
t=t[:a]+'''## Running at 22:39Z (all on 2-28)
- Cursor fbp_patchA2rev (F2/patchA2rev, 22:22Z; PROMPT 1405eeb0): confirm review of PATCH_A2 3ecd924f.
- Cursor fbp_donor3rev (F2/donor3rev, 22:37Z; PROMPT ebbc8134): confirm review of PATCH_DONOR3 4253fbd1 (tar 495cadce).
- Cursor fbp_camform2rev (F2/camform2rev, 22:38Z; PROMPT 780dd9ff): confirm review of PATCH_CAMFORM2 7e7ae484 (tar 8be168b5; same bytes apply on A and A2). GO by 03:00Z.
- Codex fbp_prior2c (F2/prior2c, 22:34Z, ~1.5 h; fbp_prior2c_full.md b7fd3f06): prior checker fixes (preparation; prior -> second boundary unless discovery-run offsets).
- Done, parked for the second boundary: patch D F2/pointD/out (PATCH_POINT 13b8a54b, tar fdf380c6; overlaps donor runner file).

'''+t[b:]
t=t.replace('| Patch C camform [camformrev GO AFTER FIXES: M1 deferred-mode silent ignore; fix = camform2] |','| Patch C camform [superseded by camform2: F2/camform2/out PATCH_CAMFORM2.patch 7e7ae484 (7 files, applies on A and A2), tar 8be168b5; declaration-mode composition 11,979 rows, 2,000 rot + 1,996 dir lines; camform2rev RUNNING] |')
t=t.replace('[donor2rev GO AFTER FIXES M4 reader recipe only -> donor3;','[final candidate donor3: F2/donor3/out PATCH_DONOR3.patch 4253fbd1, tar 495cadce, donor3rev RUNNING; donor2rev M4 fixed there;')
open(S,'w').write(t)
