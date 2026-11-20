export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
for f in x.py:7fe00c24ecf605cb rcj.sh:b23393f2db4dfe65 pc.py:bd87252b711f9a2b nd.py:d7055420a7096bc1 ch.py:c931ab55d8f6e4d6 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
for K in q:df93cfba9769ca82 n:797255ae1421d27f qd:8ae781f4cd655a53; do [ "$(sha256sum ${K%%:*}/SHA256SUMS.txt | cut -c1-16)" = "${K##*:}" ] && [ "$(cd ${K%%:*} && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] || { echo "BAD kit $K"; exit 1; }; done
cd qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj/rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
