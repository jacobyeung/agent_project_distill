export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; test -e rcj/P_SAMPLE_I.json && { echo SAMPLE_PRESENT; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
cd qd && [ "$(sha256sum SHA256SUMS.txt | cut -c1-16)" = 259c14de1ff04938 ] && [ "$(sha256sum ../rcj/x.py | cut -c1-16)" = 7b9d646994904cca ] && [ "$(sha256sum ../rcj/rcj.sh | cut -c1-16)" = b23393f2db4dfe65 ] && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj/rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
