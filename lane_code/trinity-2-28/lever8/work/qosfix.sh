set -u
j=174439
st=$(squeue -j $j -h -o '%T %P %q %r')
echo "before: $st"
case "$st" in "PENDING preempt general_qos"*) ;; *) echo "E1 unexpected state, no change"; exit 1;; esac
if ! scontrol update JobId=$j QOS=preempt_qos; then
  scancel $j && echo "E2 update refused; cancelled" || echo "E2 update refused; CANCEL FAILED"; exit 1
fi
sj=$(scontrol show job $j)
g(){ printf '%s\n' "$sj" | tr ' ' '\n' | sed -n "s/^$1=//p"; }
q=$(g QOS); p=$(g Partition); r=$(g Requeue); x=$(g ExcNodeList)
echo "after: QOS=$q Partition=$p Requeue=$r Reason=$(g Reason) exc_has_c4=$(scontrol show hostnames "$x" | grep -cx orchard-community-4) exc_has_c0_3=$(scontrol show hostnames "$x" | grep -cE '^orchard-community-[0-3]$')"
if [ "$q" != preempt_qos ] || [ "$p" != preempt ] || [ "$r" != 0 ] || scontrol show hostnames "$x" | grep -qE '^orchard-community-[0-3]$'; then
  scancel $j && echo "E3 mismatch; cancelled" || echo "E3 mismatch; CANCEL FAILED"; exit 1
fi
sleep 20; squeue -j $j -h -o '%T %P %q %r'
