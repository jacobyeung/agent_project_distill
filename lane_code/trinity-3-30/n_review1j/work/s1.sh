K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix/n_go; R=/scratch/jjyeung/orch_n30/n_review/r1j/t
date -u +%TZ; mkdir -p $R; sha256sum $K/k/t_e047002134f979bd.tar < /dev/null; tar xf $K/k/t_e047002134f979bd.tar -C $R < /dev/null; ls $R | head; 
C=$(ls -d $R/student_pilot $R/*/student_pilot 2>/dev/null | head -1); echo C=$C; wc -l $C/carrier_c1_run.py < /dev/null
grep -n "def \|differs" $C/carrier_c1_run.py < /dev/null | awk -F: '$1>380 && $1<620' 
