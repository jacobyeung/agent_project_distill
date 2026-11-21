set -e
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo "project_free=${F}G $(date -u +%FT%TZ)"; [ "$F" -ge 15 ] || { echo "HOLD below 15 GiB floor"; exit 3; }
G=$(TZ=UTC squeue -u $USER -h -p general -o '%i %j'); echo "general: $G"; [ -z "$G" ] || { echo "HOLD: our job on general"; exit 5; }
P=/project/community/jjyeung/okh7/a15_cot_ap87f4ae5c2f44f
/usr/bin/python3 -I -s -B "$P/3.py" submit
echo submit_rc=$?
TZ=UTC squeue -u $USER -h -p general -o '%i %j %T %M'
