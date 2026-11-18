cd /scratch/jjyeung/orch_n30/reader_r1/work/fix7/b1
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B tower_pair.py \
  --package src \
  --own /scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170631/items.jsonl /scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170706/items.jsonl /scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out work/scores
