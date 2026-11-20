export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
squeue -u $USER -h -o "%i %P %j %T" | grep -E "24d9b8e2" && { echo QUEUED; exit 1; }
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 8ae781f4cd655a53 ] && [ "$(cd qd && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find qd -name __pycache__)" ] && [ "$(sha256sum jd5.sh | cut -c1-16)" = 7b3097104b4bd3f5 ] && [ "$(sha256sum dbb3.py | cut -c1-16)" = 4ca1926a44148f22 ] && sbatch -p advanced $X/jd5.sh; sleep 20
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"; squeue -p advanced -h -o "%u %T %b" | sort | uniq -c | head; df -h /project/community | tail -1
