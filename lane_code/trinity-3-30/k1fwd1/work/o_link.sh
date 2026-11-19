set -e
D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
test ! -e LINKS.json
cat > l.sh <<'S'
#!/bin/bash
cd /project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5 && /usr/bin/python3 -I -s -B build.py link > l.out 2>&1; echo "rc=$? $(date -u +%T)" >> l.out
S
chmod 700 l.sh
/usr/local/bin/sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --time=01:00:00 --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap90eaf12c47ba5 l.sh
