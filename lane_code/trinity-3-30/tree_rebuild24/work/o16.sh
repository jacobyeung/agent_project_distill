export TZ=UTC; date -u +%TZ; J=173964; X=/project/community/jjyeung/okh7/x_22c714e1
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 21 ] || { echo BELOW_FLOOR; exit 1; }
H=4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84; test -e $X/u/$H && { echo ALREADY; exit 0; }
timeout 400 srun --overlap --jobid $J -n1 -c1 --mem=2G bash -c '
N=/tmp/q_22c714e1_173964; X='"$X"'; H='"$H"'
ls -la $N/dr/p/q/base $N/dr/p/q/base/pool 2>&1 | head -12
test -s $N/dr/p/q/base/receipt.json || { echo NOT_READY; exit 0; }
B=$(find $N/dr/p/q/base -type f -size 837255168c | head -1); test -n "$B" || { echo NO_837_FILE; exit 0; }; echo B=$B
h=$(nice -n 10 sha256sum $B | cut -c1-64); echo BASE_SHA $h $(stat -c %s $B)
[ "$h" = "$H" ] || { echo BASE_DIFFERS; exit 1; }
nice -n 10 ionice -c3 cp $B $X/u/$H.part && h2=$(nice -n 10 sha256sum $X/u/$H.part | cut -c1-64) && [ "$h2" = "$H" ] && chmod 600 $X/u/$H.part && mv $X/u/$H.part $X/u/$H && echo COPIED && ls -la $X/u/$H' < /dev/null 2>&1 | tail -12
df -BG /project/community | tail -1
