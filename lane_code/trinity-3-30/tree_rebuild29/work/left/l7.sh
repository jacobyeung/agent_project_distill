export TZ=UTC; date -u +%TZ
cat > ~/a15o/d.sh <<'IN'
#!/bin/bash
df -B1 -x tmpfs -x devtmpfs -x overlay 2>/dev/null | awk '{print $1,$2,$4,$6}'; df -B1 /dev/shm | tail -1; lsblk -b -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null | head -30; free -b | head -2
IN
chmod 700 ~/a15o/d.sh; sbatch -p preempt -w orchard-community-3 -N1 -n1 -c1 --mem=1G -t 00:04:00 --job-name a15_cot_apb2a413982c51 -o ~/a15o/d3.out ~/a15o/d.sh
