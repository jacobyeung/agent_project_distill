mkdir -p /scratch/jjyeung/n30_mirror/corpus_work && cd /scratch/jjyeung/n30_mirror/corpus_work || exit 1
cat > list.sh <<'EOS'
cd /scratch/jjyeung/n30_mirror
for t in old_lanes_3_30/old_lanes_3_30_a.tar old_lanes_3_30/old_lanes_3_30_b.tar cont_ops/*.tar; do
  b=$(basename $t .tar); nice -n 10 ionice -c3 tar tvf $t > /scratch/jjyeung/n30_mirror/corpus_work/$b.list 2>&1; echo "$b $?" >> /scratch/jjyeung/n30_mirror/corpus_work/DONE
done
echo ALL >> /scratch/jjyeung/n30_mirror/corpus_work/DONE
EOS
tmux new-session -d -s corpus_list "bash /scratch/jjyeung/n30_mirror/corpus_work/list.sh"
sleep 2; tmux ls | grep corpus
ls /scratch/jjyeung/orch_n30/k1_ops3/ /scratch/jjyeung/orch_n30/k1_ops3/work | head -60
