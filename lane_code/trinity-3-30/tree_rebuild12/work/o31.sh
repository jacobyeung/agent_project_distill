set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X/q
mkdir -p -m 700 $X/a21e/pyc && mv b/__pycache__ $X/a21e/pyc/
n=$(find . -type f ! -name SHA256SUMS.txt ! -name BUILD.json | wc -l); echo files=$n sums=$(wc -l < SHA256SUMS.txt); sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ': OK' | head -3; find . -name '__pycache__'
test "$n" = "$(wc -l < SHA256SUMS.txt)"
squeue -u $USER -h -o '%i %P %j %T'; g=$(squeue -u $USER -p general -h -o %i | wc -l); echo general_ours=$g
if [ "$g" = "0" ]; then sbatch -p general $X/j.sh; fi; sleep 5; squeue -u $USER -o '%.10i %.10P %.22j %.8T %.10M %R'
