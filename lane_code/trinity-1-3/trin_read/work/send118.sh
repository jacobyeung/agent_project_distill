cat > /tmp/trin_read_send.sh <<'EOS'
cd /scratch/jjyeung/k1/m544_parts || exit 9
date -u +%FT%TZ > /tmp/trin_read_send.start
cat 469ddece_mstop.tar.part00-of-04 469ddece_mstop.tar.part01-of-04 469ddece_mstop.tar.part02-of-04 469ddece_mstop.tar.part03-of-04 | timeout 3600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-3.ib 'bash /scratch/jjyeung/orch_n30/trin_read/work/recv_export.sh'
echo "rc=$? $(date -u +%FT%TZ)" > /tmp/trin_read_send.rc
EOS
tmux new-session -d -s trin_read_send 'bash /tmp/trin_read_send.sh'
sleep 2; tmux ls | grep trin_read; cat /tmp/trin_read_send.start
