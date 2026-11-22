export TZ=UTC; date -u +%TZ
timeout 60 srun --overlap --jobid 174246 -N1 -n1 nice -n 10 bash -c 'K=/project/community/jjyeung/okh7/x_22c714e1/n; T=/tmp/q_22c714e1_174246/p/s/student_pilot; sha256sum $K/b/u.py $K/b/t.py $K/b/e.sh $K/k/j.json $T/carrier_c1_run.py $T/r1_persisted.py $T/p3_provenance.py | cut -c1-200; sha256sum /tmp/q_22c714e1_174246/j.sh | cut -c1-120; ls -ld /tmp/q_22c714e1_174246/rp /tmp/q_22c714e1 /tmp/jjyeung/q_22c714e1 2>&1 | cut -c1-200; date -u +%FT%TZ' 2>&1
echo srun_rc=$?
