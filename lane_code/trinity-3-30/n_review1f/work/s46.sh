R=/scratch/jjyeung/orch_n30/n_review/r1f; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
sed -n 40,50p $R/tcpx/student_pilot/s1_pool.py; echo @@; sed -n 128,138p $R/tcpx/student_pilot/s1_pool.py
D=$(ls -d $W/work/d173817/* | head -1); echo D=$D; ls $D | tr '\n' ' '; echo
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $R/chk/taska.py $D > $R/taska_d173817.json 2>&1; sha256sum $R/taska_d173817.json
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json; v=json.load(open('/scratch/jjyeung/orch_n30/n_review/r1f/taska_d173817.json'))
for k in ('a_content_paths_outside_allowed','a_target_or_encode_diff','b_paths_outside_four_classes','b_s1_source_leaves_not_paths_or_fps','b_unclassified','b_class_leaf_counts','c_other','c_population','na_attr','na_lists','nd_N_rows','nd_P_rows','nd_matched_rows','nd_N_without_P','nd_absent_count','nd_absent_unattributed','nd_retained_excluded','nd_U_Faithful','nd_database_sha256','nd_P_database_sha256','nd_task_ii','nd_task_iii','rt'):
    print(k, json.dumps(v.get(k))[:900])
print('chain routing', json.dumps(v['c_chain']['routing'])[:700])
print('rd script', {k:v['rd_summary'].get(k) for k in ('script_sha256','rdiff_sha256','mismatched','P_rows_absent_from_N')} if v.get('rd_summary') else None)
PY
