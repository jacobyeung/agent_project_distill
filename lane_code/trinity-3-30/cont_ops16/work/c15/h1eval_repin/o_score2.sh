#!/bin/bash
# ossh payload: install $P/a/sc2.sh (srun scoring block only of sc.sh) and start it detached if general holds no job of mine
export TZ=UTC; P=/project/community/jjyeung/bf94a7976a7e9
G=$(squeue -u jjyeung -p general -h -o "%i %j %T %r" 2>&1); echo "GEN[$G]"
if [ -n "$G" ]; then echo "REFUSED: general not clear"; exit 9; fi
test -s $P/a/s/curve.json && { echo "REFUSED: $P/a/s/curve.json already exists"; exit 8; }
cat > $P/a/sc2.sh <<'IN'
#!/bin/bash
P=/project/community/jjyeung/bf94a7976a7e9; L=$P/a/score.log; export TZ=UTC
grep -q RETURN_OK $L || { echo "sc2 no RETURN_OK $(date -u +%TZ)" >> $L; exit 1; }
echo "sc2 start $(date -u +%TZ)" >> $L
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" TZ=UTC \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_ap76cb66051b \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" --return-tar "$P/a/f/0.tgz" --submerge "$P/a/6.py" --results "$P/a/s" >> $L 2>&1
echo "score rc=$? $(date -u +%TZ)" >> $L
IN
chmod 700 $P/a/sc2.sh
cd $P/a && setsid nohup bash $P/a/sc2.sh > $P/a/sc2.nohup 2>&1 < /dev/null &
sleep 20; squeue -u jjyeung -h -o "%i %j %P %T %M %R"; tail -n 3 $P/a/score.log
