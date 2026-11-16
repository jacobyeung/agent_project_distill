set -u
O=/scratch/jjyeung/orch_n30/b04_e2ehook_m544h
hostname -s; df -h /scratch | tail -1; ls -la /scratch/jjyeung/k1/m544_parts/ | head
mkdir -p $O
if tmux has-session -t b04_m544h 2>/dev/null; then echo ALREADY_RUNNING; else
tmux new-session -d -s b04_m544h "cd $O && (cat /scratch/jjyeung/k1/m544_parts/469ddece_mstop.tar.part0* | nice -n 10 ionice -c3 tar xf - --wildcards '*/heads.pt' '*/full_weights/full_weights.json' '*/artifact.json'; echo TAR_RC=\$?; find $O -type f -printf '%s %p\n'; find $O -type f -exec sha256sum {} +) > $O/extract.log 2>&1"
echo STARTED; fi
