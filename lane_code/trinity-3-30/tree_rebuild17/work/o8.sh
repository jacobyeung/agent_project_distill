export TZ=UTC; date -u +%TZ; J=173555
st=$(squeue -h -j $J -o %T); echo "state $st"; [ "$st" = PENDING ] || exit 0
scontrol update JobId=$J TresPerNode=gres/gpu:1 2>&1 || scontrol update JobId=$J Gres=gpu:1 2>&1
scontrol update JobId=$J ReqNodeList= 2>&1
sleep 5; scontrol show job $J | grep -E "TresPerNode|ReqNodeList|NumCPUs|MinMemory|JobState|Reason|TRES=" | tr -s ' ' | cut -c1-200
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"
