export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=174246; L=$X/o/${J}_live
s=$(squeue -j $J -h -o '%T|%M|%N|%r' 2>/dev/null); [ -z "$s" ] && s="GONE|$(sacct -j $J -n -X -P -o State,ExitCode,Elapsed | head -1)"
n=$(grep -o '"n": [0-9]*' $L/live.json 2>/dev/null | grep -o '[0-9]*'); lu=$(grep -o '"last": "[^"]*"' $L/live.json 2>/dev/null | cut -d'"' -f4)
mem=$(awk '/^job /{j=1} /^step /{j=0} j&&/^memory.current/{getline;c=$1} j&&/^anon /{a=$2} j&&/^shmem /{h=$2} j&&/^file /{f=$2} j&&/^file_dirty/{d=$2} END{printf "cur=%.1fG anon=%.1fG shm=%.1fG file=%.1fG dirty=%.1fG",c/2^30,a/2^30,h/2^30,f/2^30,d/2^30}' $L/mem.txt 2>/dev/null)
lim=$(grep '^limit' $L/mem.txt 2>/dev/null | awk '{print $2}'); tmp=$(awk '$NF=="/tmp"{print $4}' $L/df.txt 2>/dev/null | head -1)
j2=$(stat -c %s $X/o/$J/j2.log 2>/dev/null); ql=$(stat -c %s $L/t_q.log 2>/dev/null); al=$(cat $L/alarm.txt 2>/dev/null | tail -2 | tr '\n' ';')
g=$(grep -v '^utc' $L/gate.txt 2>/dev/null | tr '\n' ';'); kl=$(ls $X/o/$J/live 2>/dev/null | wc -l)
echo "$(date -u +%TZ) state=$s n=$n last=$lu $mem lim=$lim tmp_freeK=$tmp j2=$j2 tq=$ql kitlive=$kl alarm=[$al] gate=[$g] hold=$(test -e $X/o/$J/HOLD.txt && echo YES || echo no)"
echo "  q: $(tail -c 300 $L/t_q.log 2>/dev/null | tail -2 | tr '\n' '|' | cut -c1-260)"
echo "  j2: $(tail -2 $X/o/$J/j2.log 2>/dev/null | tr '\n' '|' | cut -c1-260)"
echo "  kq: $(stat -c %s $X/o/$J/live/q.log 2>/dev/null) $(ls $X/o/$J/live 2>/dev/null | tr "\n" ,) | $(tail -c 400 $X/o/$J/live/q.log 2>/dev/null | tr -c "[:print:]\n" "?" | tail -1 | cut -c1-200)"
echo "  kt: $(stat -c %s $X/o/$J/live/t.log 2>/dev/null) | $(tail -c 1500 $X/o/$J/live/t.log 2>/dev/null | tr -c "[:print:]\n" "?" | tail -3 | tr "\n" "|" | cut -c1-900)"
