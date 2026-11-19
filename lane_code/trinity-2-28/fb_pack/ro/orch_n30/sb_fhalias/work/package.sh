#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/sb_fhalias
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
nice -n 10 tar -cf out/sb_fhalias.tar \
 STATUS.md work/tree_before work/tree_after work/base work/support work/build15 work/build_n1 work/n1fix2 \
 work/run.sh work/check_boundary.py work/run_focused.py work/run_focused_exact.py work/run_host_regression.py work/compare_boundary.py work/check_static.py work/seal_patch.py work/finalize.py work/verify_archive.py work/package.sh \
 out/ALIAS.patch out/FHALIAS_REPORT.md out/CHANGED_FILES.json out/STATIC_CHECKS.json out/BOUNDARY_DIFF.json out/BOUNDARY_MATRIX.tsv out/FOCUSED_DIFF.json \
 out/TREE_BEFORE.sha256 out/TREE_AFTER.sha256 out/host_before.json out/host_after.json out/host_before.log out/host_after.log \
 out/boundary_before.json out/boundary_after.json out/boundary_before.log out/boundary_after.log \
 out/exact_before_main.json out/exact_after_main.json out/exact_before_main.log out/exact_after_main.log \
 out/focused_before_edges.json out/focused_after_edges.json out/focused_before_edges.log out/focused_after_edges.log \
 out/focused_before_producer.json out/focused_after_producer.json out/focused_before_producer.log out/focused_after_producer.log
sha256sum out/sb_fhalias.tar > out/sb_fhalias.tar.sha256
