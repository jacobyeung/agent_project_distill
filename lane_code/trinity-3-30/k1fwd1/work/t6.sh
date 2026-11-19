K=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $K; tar czf - *.py *.json *.txt *.sh manifest_v2/DIFF.json packet/PACKAGE.json packet/UPLOAD.json packet/CONFIG.json inputs/depth_heads.json $(find reference -name '*.py' -size -400k) 2>/dev/null
