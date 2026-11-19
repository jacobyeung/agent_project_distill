set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
test -d $X/q/b/__pycache__ && mv $X/q/b/__pycache__ $X/a21g/pycache_dir_empty_1415Z
cd $X/q; sha256sum SHA256SUMS.txt | cut -c1-16; sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK" | head -3; echo "files $(find . -type f | wc -l) dirs_pyc $(find . -name __pycache__ | wc -l) lines $(wc -l < SHA256SUMS.txt)"
sha256sum $X/j.sh $X/l.json | cut -c1-16
ls /project/community/jjyeung/okh7/l_94a76bda/in/e00 >/dev/null && squeue -u $USER -h -o "%i %P %j %T"
cd $X; sbatch $X/j.sh; sleep 5; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
