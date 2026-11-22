export TZ=UTC; date -u +%TZ; mkdir -p ~/a15o
cat > ~/a15o/l.sh <<'IN'
#!/bin/bash
df -B1 /tmp | tail -1; echo "-- owned by jjyeung under /tmp:"
for e in $(find /tmp -maxdepth 1 -mindepth 1 -user jjyeung 2>/dev/null); do s=$(timeout 100 du -sxB1 "$e" 2>/dev/null | cut -f1); echo "$s $(stat -c %y "$e" | cut -c1-19) $e"; done | sort -n
echo "-- /tmp/jjyeung:"; ls -la /tmp/jjyeung 2>&1 | head -20; date -u +%TZ
IN
for N in orchard-community-3 orchard-community-2; do
sbatch -p preempt -w $N -N1 -n1 -c2 --mem=2G -t 00:08:00 --job-name a15_cot_apb2a413982c51 -o ~/a15o/$N.out bash ~/a15o/l.sh
done
