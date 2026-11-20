cd /scratch/jjyeung; M=/scratch/jjyeung/n30_mirror/lever1
cat > $M/SAMPLE_src.sha <<'S'
76965f36006e76761fab9c81a3f7460df6ce2ab1d4ff130754def69fa49140cd  orch_n30/e3_geom/PLAN.md
75cdb3738972e42df45b7dd5cb510935c38825eb4527ce95bad2fa7ecdeb6f5d  orch_n30/e3_geom/work/harness/out/geometry/arkitscenes__47331294/S3+GO.npz
3ba31a38bf7e5e1248f0f8745917dc642a1dec2df8a8d0ad6a569c43ae03dd43  orch_n30/e3_geom/work/harness/out/geometry/arkitscenes__47332430/S2+GO.npz
cb2d38683028f76a2c046b29b81136a63e02311c0840f1998e6b2a1dd2f02ab4  orch_n30/e3_geom/work/harness/out/geometry/arkitscenes__47204392/S3+GO.npz
e39f40d6336264f1da097d1347ed254c119b4d2a5c2d46ecb0138d58cf0fea04  orch_n30/k1_ops3/work/e3gd/out/gd_tests/changed/baseline/geometry/synthetic__room/S4+G1.npz
1eccaa92f76bd6072b95fdc15d513a29078691292c664fd5022c2f3a98527fa4  orch_n30/k1_ops3/work/e3gd/out/geometry/arkitscenes__45662908/S1+G1.npz
fc9caa806f619f0ff82dc3d2d683f0bb44aa54aa867945f86e259884ad506d3d  orch_n30/k1_ops3/work/e3gd/out/geometry/scannetpp__469f112e38/S4+G1.npz
1510305f24a56c7294b97417d2457ef99aa7fd57f7837adf0c314c06a60d8864  orch_n30/k1_ops3/work/e3gd/out/geometry/scannetpp__edced53026/S3+GO.npz
12a394356eab47bc30e66527031d92aa2bb7002608986bffe62c7f4eb63c738b  orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/sensitivity_300/render/990fe45f0ae003d0/responses.json
42858a10527673c3f087dc788bf01014d1e0aaec2c918dc654edb14ee5273529  orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/render/7f36e8b8a4cbf046/COMPLETE.json
S
ls -d orch_cd/dose_pool orch_n30/b04host3 orch_n30/k1_ops3/kc/k1_build/work/kit_k1a orch_n30/e3_geom orch_n30/geo_k1 > $M/PREEXISTING.txt 2>&1; cat $M/PREEXISTING.txt
nice -n 19 tar xf $M/k1x_inputs.tar --skip-old-files; echo "x1 rc=$?"
nice -n 19 tar xf $M/k1x_inputs2.tar --skip-old-files; echo "x2 rc=$?"
echo "## compare pre-existing"; nice -n 19 tar df $M/k1x_inputs.tar orch_cd/dose_pool orch_n30/b04host3 orch_n30/k1_ops3/kc/k1_build/work/kit_k1a > $M/COMPARE.txt 2>&1; echo "cmp rc=$?"; wc -l $M/COMPARE.txt; head -8 $M/COMPARE.txt
sha256sum -c $M/SAMPLE_src.sha 2>&1 | tee $M/SAMPLE_check.txt | grep -c ': OK'
df -h /scratch | tail -1
C=/scratch/jjyeung/orch_n30/lever1_c; tail -2 $C/r3_run.log $C/r4_run.log; ls $C/r3 $C/r4
