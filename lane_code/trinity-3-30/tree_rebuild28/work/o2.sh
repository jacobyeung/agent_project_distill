set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 929ab2139b6dd408 ] && echo KIT_OK
squeue -u $USER -h -o "%i %P %j %T %M %R"
test -e o/174134/HOLD.txt && touch o/174134/RELEASE && echo "RELEASE written $(date -u +%TZ)"
for i in $(seq 1 16); do sleep 15; s=$(squeue -j 174134 -h -o %T 2>/dev/null || true); [ -z "$s" ] && break; done
echo "174134 after wait: [${s}] $(date -u +%TZ)"; sacct -j 174134 -n -X -P -o State,ExitCode,Elapsed,End | head -1
if [ -z "$s" ]; then scontrol release 174198 && echo "174198 RELEASED $(date -u +%TZ)"; else echo NOT_RELEASED_174198; fi
sleep 10; squeue -u $USER -h -o "%i %P %j %T %M %R"; squeue -j 174198 -h --start -o "%i %S %R" 2>/dev/null || true
