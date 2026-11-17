export TZ=UTC
cd /project/community/jjyeung/b01ec87a6f29b
for spec in "4 01:15:00" "2 02:30:00" "1 04:00:00"; do set -- $spec
 CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus $1 --time $2 > /dev/null; echo "check $1 $2 rc=$?"
 A_N=$1 A_T=$2 nice -n 19 bash SUBMIT.cmd --test-only 2>&1 | head -2
done
tail -4 /project/community/jjyeung/okh7/e6fc152498/rh.out
