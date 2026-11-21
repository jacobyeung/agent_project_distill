W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z12; A=$W/w24z11b/a_zffhb1q8; P=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1i; T=$N/r1f/tcpx
mkdir -p $R; date -u +%TZ
ls $A < /dev/null | tr '\n' ' '; echo; for d in $A/*; do [ -d $d ] && { echo "$d: $(ls $d < /dev/null | tr '\n' ' ')"; }; done
