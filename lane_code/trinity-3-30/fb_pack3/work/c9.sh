F=/scratch/jjyeung/orch_n30/fb_pack; C=$F/combo; mkdir -p $C/out; cd $C
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json,hashlib,re
C='/scratch/jjyeung/orch_n30/fb_pack/combo'; F='/scratch/jjyeung/orch_n30/fb_pack'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def last(p): return open(p).read().strip().splitlines()[-1]
pt={'PATCH_A2':F+'/patchA2/out/PATCH_A2.patch','PATCH_DONOR3':F+'/donor3/out/PATCH_DONOR3.patch','PATCH_CAMFORM2_ON_A2':F+'/camform2/out/PATCH_CAMFORM2_ON_A2.patch'}
r={'schema':'fb-pack-combined-patch-check-v1','order':'PATCH_A2 -> PATCH_DONOR3 -> PATCH_CAMFORM2_ON_A2 (patch -p1 --fuzz=0), on tree R 24l4t',
 'base':{'tar':'/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out/tree_rebuild_b24l4t_c558ad33.tar','tar_sha256':sha('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out/tree_rebuild_b24l4t_c558ad33.tar'),'tree':'work/tree_r1','seal_reproduced':'c558ad33286680e17c45ec54c825a9f236e80fd789f4ce6b0189273cd63fc16c','files':946},
 'patches':{k:{'path':v,'sha256':sha(v),'apply':'clean, fuzz 0, no offsets'} for k,v in pt.items()},
 'combined':{'path':C+'/X','files':955,'tree_sha256':'93f1d925dc6639d95271dda217a90f8b41950c5c769276aeaf6181477ff5f62e','method':'student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest (reproduces c558ad33 on the untouched tree)'},
 'tests_before_on_R_plus_test_files':{t:last(C+f'/before_{t}.log') for t in ['test_r1_patch_a2','test_r1_subset','test_scale_donor','test_r1_camera_trace_form','test_r1_camera_trace_form2']},
 'tests_after_on_combined':last(C+'/after2.log'),
 'after_failure':'tests/test_host24l4t.py::PointingResolution::test_random_rows_never_admit_a_baseline_refusal: needs the sibling comparison tree tree_r1_24l4r (absent in the package); fails identically on untouched R (R_host.log: 1 failed, 75 passed)',
 'env':'TMPDIR and LANE_TEST_OUTPUT set to combo/tmp, combo/lto_*; PYTHONPATH=tree; p1cpu env; nice 10, 8 threads',
 'not_tree_changes':{'recovery':'760 admitted rows ride in the routing slices (route/out), no tree file','pointing_K1_list':'REMOVE_POINTING_K1_HELDOUT.jsonl d21e374f binds by config under 24l4t protected_rooms role, no tree file'},
 'pointing_list_sha256':sha(F+'/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl')}
open(C+'/out/COMBINED_CHECK.json','w').write(json.dumps(r,indent=1)); print(json.dumps(r['tests_before_on_R_plus_test_files']),r['tests_after_on_combined'],r['pointing_list_sha256'][:12])
P
cd X && tar cf $C/out/tree_combined_93f1d925.tar --exclude=__pycache__ . && cd $C/out && sha256sum COMBINED_CHECK.json tree_combined_93f1d925.tar && ls -la tree_combined_93f1d925.tar
find $C/X -name __pycache__ -type d | wc -l
