K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf23c/pkg/work/build21/kits
head -c 600 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/out/UPLOADS_NEW_23C.json >&2; echo >&2
tar cf - -C $K q/b/g.py q/SHA256SUMS.txt q/BUILD.json | base64 -w0
