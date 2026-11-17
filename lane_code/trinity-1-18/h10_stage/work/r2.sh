K=/scratch/jjyeung/orch_n30/h1_headsft/kit
ls -la $K >&2; ls $K/tmp $K/tmp/b9 >&2 2>&1; find $K -maxdepth 3 -name 'TRANSPORT*' >&2
df -h /scratch >&2
tar cf - -C $K orchard_h10 $(cd $K && find . -maxdepth 3 -name 'TRANSPORT*.json' -printf '%P\n')
