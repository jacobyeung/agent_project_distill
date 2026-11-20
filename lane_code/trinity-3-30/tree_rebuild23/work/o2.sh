export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173864
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,End,ExitCode
echo ===JD5; cat $X/jd5.sh; echo ===O11
