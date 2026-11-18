export TZ=UTC
set -euo pipefail
umask 077
O=/project/community/jjyeung/okh7; KH=$O/x_69d2930d; BUN=$O/i_69d2930d
[[ -z "$(squeue -h -u $USER -n a15_cot_ap673bc60f -p advanced -o %i)" ]] || { echo 'REFUSED: training job queued'; exit 3; }
D=$O/pyc_x69_171337
[[ ! -e $D ]] || { echo "REFUSED: $D exists"; exit 3; }
[[ -d $KH/b/__pycache__ && ! -L $KH/b/__pycache__ ]] || { echo 'REFUSED: no pycache dir'; exit 3; }
mv -n -- "$KH/b/__pycache__" "$D"
chmod 500 "$KH/b"
stat -c '%a %n' "$KH/b" "$D"; ls "$D"
ls -la --time-style=+%H:%M:%S "$KH/arm" "$KH/runs" | head; ls -la --time-style=+%H:%M:%S $BUN | grep -E 'training|go.json|job.id|canary'
/usr/bin/python3 -I -B "$KH/b/a.py" "$KH" && echo "PASS a.py inventory after fix"
[[ ! -e "$KH/b/__pycache__" ]] && echo "PASS no pycache after a.py"
ls -la $O/r 2>/dev/null | grep 673bc60f || echo 'no O/r/673bc60f'
