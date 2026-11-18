cd /scratch/jjyeung/orch_n30/reader_r1/work/fix7/b2
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B room_pair.py \
  --return-root work/ret --out work/scores
