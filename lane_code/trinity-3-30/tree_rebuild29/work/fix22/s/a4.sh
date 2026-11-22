W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W || exit 1
ls w34/n_go/k >&2; sha256sum w34/n_go/SHA256SUMS.txt >&2
tar czf - w24y2/out/apply_24m4x.py w24y2/out/TREE_SEAL.json w24y2/out/BUILD24M4X2_REPORT.md w24y2/out/BUILD24M4Y2_REPORT.md w24y2/out/RCJ_USAGE.md w24y2/out/RCJ_FILES_24M4Y2.sha256 w24y2/out/TREE_FILES.sha256 w24y2/out/UPLOADS_24M4Y2.list w24y2/out/DELIVERY_24M4Y2.json w24y2/out/TREE_CHANGE_24M4X.patch
