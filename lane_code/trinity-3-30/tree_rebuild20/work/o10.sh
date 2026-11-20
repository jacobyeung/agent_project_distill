export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
for f in x.py:f443615a44912025 rcj.sh:b23393f2db4dfe65 pc.py:a4ef242bb690f3e3 nd.py:696f73c4bbbc2923 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
cd qd && [ "$(sha256sum SHA256SUMS.txt | cut -c1-16)" = aaa03e5831a79c75 ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj/rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
