D=/scratch/jjyeung/orch_n30/sb_maskfail
K=/scratch/jjyeung/orch_n30/sb_kbox4
pf(){ if [ -f "$1" ]; then echo "=== FILE $1 ($(stat -c %s "$1") bytes)"; head -c ${2:-40000} "$1"; echo; else echo "=== MISSING $1"; fi; }
pf $D/classify.py; pf $D/analyze.py 30000; pf $D/finalize.py 12000; pf $D/run.sh; pf $D/STATUS.md
echo "=== LS prompts"; ls -la $D/prompts
for f in $D/prompts/*; do pf "$f" 30000; done
pf $D/out/MISSING_INPUTS.json 15000
pf $D/out/SPLITS.json 130000
echo "=== LS kbox4"; ls -la $K | head -50; echo "=== LS kbox4/out"; ls -la $K/out | head -60; echo "=== LS kbox4/out/box_ladder"; ls -la $K/out/box_ladder | head -60
pf $K/out/REPORT.md 40000; pf $K/out/LADDER_TRAIN.txt 20000; pf $K/out/box_ladder/DECISION.json 30000; pf $K/out/SCALE_PROVENANCE.md 12000; pf $K/run.sh 6000
echo "=== LS mirrors"; ls -la /scratch/jjyeung/n30_mirror/b05_owngrd/ 2>&1 | head -40; ls -la /scratch/jjyeung/n30_mirror/sb_headacc2/ 2>&1 | head; ls -la /scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS 2>&1 | head -30
echo "=== LS teacher"; ls -la $D/teacher | head -20
echo "=== DF"; df -h /scratch | tail -1; nproc; free -g | head -2
