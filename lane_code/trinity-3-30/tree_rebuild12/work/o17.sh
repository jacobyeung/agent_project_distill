set -e; X=/project/community/jjyeung/okh7/x_22c714e1
mv $X/l.json $X/a21c/l.json.bad
cat > $X/l.json <<"EOJ"
{
 "objects": [
  {
   "name": "q8/8865619b/6ed2c7aa_m400.tar.part00-of-04",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/0",
   "bytes": 5395758080
  },
  {
   "name": "q8/8865619b/6ed2c7aa_m400.tar.part01-of-04",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/1",
   "bytes": 5395758080
  },
  {
   "name": "q8/8865619b/6ed2c7aa_m400.tar.part02-of-04",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/2",
   "bytes": 5395758080
  },
  {
   "name": "q8/8865619b/6ed2c7aa_m400.tar.part03-of-04",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/3",
   "bytes": 5395758080
  }
 ],
 "metadata": [
  {
   "sha256": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/a4aee8afcf2e0711",
   "bytes": 7756,
   "name": "chat_template.jinja"
  },
  {
   "sha256": "d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/d0883072e01861ed",
   "bytes": 3126,
   "name": "config.json"
  },
  {
   "sha256": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/a9d356d7bdf1ef49",
   "bytes": 3353259,
   "name": "merges.txt"
  },
  {
   "sha256": "26d3539b516be613f39563617cb9d33b3f83d401298125be392c80cefb8f7fe5",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/26d3539b516be613",
   "bytes": 79657,
   "name": "model.safetensors.index.json"
  },
  {
   "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/27225450ac9c6529",
   "bytes": 390,
   "name": "preprocessor_config.json"
  },
  {
   "sha256": "316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/316230d6a809701f",
   "bytes": 16710,
   "name": "tokenizer_config.json"
  },
  {
   "sha256": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/7768af27c1fafa9c",
   "bytes": 385,
   "name": "video_preprocessor_config.json"
  },
  {
   "sha256": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003",
   "pool_path": "/project/community/jjyeung/okh7/x_22c714e1/w/t/ce99b4cb2983d118",
   "bytes": 6722759,
   "name": "vocab.json"
  }
 ]
}
EOJ
mkdir -p -m 700 $X/j; cat > $X/j.sh <<"EOJ"
#!/bin/bash
#SBATCH --job-name=a15_cot_apcbee11a6
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=192G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/%j.out
set -euo pipefail
umask 077
X=/project/community/jjyeung/okh7/x_22c714e1
echo "$(date -u +%FT%TZ) resolve start"
python3 -I -s -B $X/q/b/resolve.py --pool /project/community/jjyeung/okh7 --listing $X/l.json --output $X/j/r_${SLURM_JOB_ID}.json
echo "$(date -u +%FT%TZ) resolve done"
bash $X/q/job.sh $X/j/r_${SLURM_JOB_ID}.json
echo "$(date -u +%FT%TZ) job done"
EOJ
ls $X; sha256sum $X/l.json $X/j.sh; python3 -c "import json;d=json.load(open(\"$X/l.json\"));print(len(d[\"objects\"]),len(d[\"metadata\"]))"; cd $X/q && sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK" | head; echo SUMCHK_DONE
