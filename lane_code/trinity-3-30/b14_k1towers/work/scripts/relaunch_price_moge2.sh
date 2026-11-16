G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; MODEL=moge2
tmux new-session -d -s b14_price_$MODEL "bash $G/logs/price_$MODEL.sh"
sleep 90; cat logs/convert_$MODEL.log | tail -5; tail -n1 logs/price_${MODEL}_0.log
