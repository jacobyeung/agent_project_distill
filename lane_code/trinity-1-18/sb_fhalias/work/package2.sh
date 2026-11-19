#!/bin/bash
set -eu
cd /scratch/jjyeung/orch_n30/sb_fhalias
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
nice -n 10 tar -cf out/sb_fhalias2.tar \
 STATUS.md work/tree_before work/tree_after work/base work/support work/build15 work/build_n1 work/n1fix2 \
 work/run.sh work/check_missing_intake_tree.py work/check_boundary2.py work/run_focused.py work/run_focused_exact.py work/run_host_regression.py work/alias2_tests.py \
 work/compare_boundary2.py work/check_static2.py work/seal_patch2.py work/finalize2.py work/verify_archive2.py work/package2.sh \
 out/ALIAS.patch out/FHALIAS2_REPORT.md out/FHALIAS2_RESULTS.json out/CHANGED_FILES.json out/STATIC_CHECKS2.json out/BOUNDARY_DIFF2.json out/BOUNDARY_MATRIX2.tsv \
 out/TREE_BEFORE.sha256 out/TREE_AFTER.sha256 out/host_before2_final.json out/host_after2_final.json out/host_before2_final.log out/host_after2_final.log \
 out/host_before2_final_checks.json out/host_after2_checks.json out/host_before2_final_checks.log out/host_after2_checks.log \
 out/boundary_before2_contract.json out/boundary_after2_contract.json out/boundary_before2_contract.log out/boundary_after2_contract.log \
 out/exact_before2_main.json out/exact_after2_main.json out/exact_before2_main.log out/exact_after2_main.log \
 out/focused_before2_edges.json out/focused_after2_edges.json out/focused_before2_edges.log out/focused_after2_edges.log \
 out/focused_before2_producer.json out/focused_after2_producer.json out/focused_before2_producer.log out/focused_after2_producer.log \
 work/missing_intake_before2 work/missing_intake_after2 out/missing_intake_before2.json out/missing_intake_after2.json out/missing_intake_before2.log out/missing_intake_after2.log \
 out/patch_dry_run2.log out/static2.log out/seal2.log out/source_matches.txt out/source_pattern_audit.txt out/nonpython_matches.txt out/source_text_consumers.txt
nice -n 10 sha256sum out/sb_fhalias2.tar > out/sb_fhalias2.tar.sha256
