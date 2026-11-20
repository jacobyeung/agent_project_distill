export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
for f in x.py:4b5c5aa532ecc581 rcj.sh:b23393f2db4dfe65 pc.py:bd87252b711f9a2b nd.py:532301cbf24ecc4d ch.py:75f98528d18111d3 f.json:d8b7807a9dd4ea5b ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
for K in q:df93cfba9769ca82 n:797255ae1421d27f qd:8ae781f4cd655a53; do [ "$(sha256sum ${K%%:*}/SHA256SUMS.txt | cut -c1-16)" = "${K##*:}" ] && [ "$(cd ${K%%:*} && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] || { echo "BAD kit $K"; exit 1; }; done
cd qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj/rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
