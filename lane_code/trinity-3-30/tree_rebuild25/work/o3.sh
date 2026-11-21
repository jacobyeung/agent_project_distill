export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
wc -c $X/jd7.sh; grep -n '[r]m -\|trap\|j7\.py\|SBATCH\|work exit\|/tmp\|N=' $X/jd7.sh | cut -c1-250 | head -50
sinfo -n orchard-community-4 -h -o "%n %T %C" ; squeue -w orchard-community-4 -h -o "%i %u %P %T" | head
