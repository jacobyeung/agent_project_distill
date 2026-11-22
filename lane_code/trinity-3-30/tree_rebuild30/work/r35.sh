set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-64)" = ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591 ] && echo KIT_OK
[ "$(sha256sum jn8.sh | cut -c1-16)" = 2de401bd4370b13e ] && echo JN8_OK
[ "$(sha256sum n_s/sess_174444.json | cut -c1-16)" = 4f989518278b29ff ] && echo SESS_OK
squeue -j 174444 -h -o "%i %P %j %T %r" | grep -q JobHeldUser && scontrol release 174444 && echo "174444 RELEASED $(date -u +%TZ)"
sleep 15; squeue -j 174444 -h -o "%i %P %j %T %M %N %R"; squeue -j 174444 -h --start -o "%i %S %R" 2>/dev/null || true
