F=/scratch/jjyeung/orch_n30/fb_pack/fov/build2; grep -n "grid_uv\|anchor_indices\|FOV_CHECK\|fov.check\|served_equal\|rows\b\|'rows'\|\"rows\"" $F/score_fov.py | cut -c1-220 | head -40
