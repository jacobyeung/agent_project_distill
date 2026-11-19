export TZ=UTC; O=/project/community/jjyeung/okh7; X=$O/x_22c714e1
test -e $O/l_94a76bda || ln -s /project/community/jjyeung/distill/okit $O/l_94a76bda
test -e $O/l_3d48eea0 || ln -s /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar $O/l_3d48eea0
ls -la $O/l_94a76bda $O/l_3d48eea0; ls $O/l_94a76bda/in | head -5; stat -L -c %s $O/l_3d48eea0
squeue -u $USER -h -o '%i %P %j %T'; sbatch $X/j.sh; sleep 5; squeue -u $USER -o '%.10i %.10P %.22j %.8T %.10M %R'
