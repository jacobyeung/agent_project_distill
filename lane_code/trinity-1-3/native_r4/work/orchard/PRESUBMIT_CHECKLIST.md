# Pre-submit checklist for every Orchard packet of this lane (fail closed)
1. sha256 of every staged input (a/b/c/d tars, FAMILY.json) equals its pin (`sha256sum -c`).
2. `tar tvf` member types of every input tar are only '-' and 'd'; record the counts; any other type (h, l, ...) stops the submission.
3. GCS second copies exist; c/u.py verifies all four by generation (receipts file).
4. `squeue -p general -u $USER` shows no own job; record the check.
5. sbatch line: --nice=200 --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time ending by 16:30Z (never past 17:45Z).
Scripts: q7_packet2.sh (1-3 + packet), q8_sbatch2.sh (4-5).
