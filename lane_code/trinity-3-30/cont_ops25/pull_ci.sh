exec 3>&1 1>&2
cd /scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_cam && tar czf - CAMERA_ITEMS_R8.json >&3
tail -2 /scratch/jjyeung/orch_n30/cont_ops25_c/r9_run.log
