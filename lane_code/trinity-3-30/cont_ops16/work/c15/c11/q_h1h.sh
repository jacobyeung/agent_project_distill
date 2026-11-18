K=/scratch/jjyeung/orch_n30/h1_headsft/kit/orchard_h10
ls -la $K | head -40
wc -l $K/OPERATIONS.md
grep -n -i -E 'export|binding|step|m100|m200|17c4ffa4|359fcc3c|prepare|token' $K/OPERATIONS.md | head -60 | cut -c1-260
ls -t /scratch/jjyeung/orch_n30/h1_headsft | head; head -c 2500 /scratch/jjyeung/orch_n30/h1_headsft/STATUS.md
