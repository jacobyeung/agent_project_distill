P=/project/community/jjyeung/a3b73b53d92a7
cd $P; ls; wc -c 3.py; grep -n -o -E '.{0,120}(exclude|nodelist|add_argument|sbatch).{0,160}' 3.py | head -30
sinfo -p general -h -N -o "%N %t %G %C" ; TZ=UTC squeue -p general -h -w orchard-community-1 -o "%i %u %T %M %l %b"
