set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; N=$X/n23b
squeue -u $USER -h -o "%i %P %j %T" | grep cbee11a6 && { echo "MY JOB STILL QUEUED/RUNNING; stop"; exit 1; }
test ! -e $X/a23 && mkdir -m 700 $X/a23
cd $N; for f in $(find q -type f); do r=${f#q/}; if [ -e $X/q/$r ]; then mkdir -p $X/a23/$(dirname $r); mv $X/q/$r $X/a23/$r; fi; done
for f in $(find u -type f); do if [ -e $X/$f ]; then cmp -s $f $X/$f || { echo "DIFFERS $f"; exit 1; }; else cp -p $f $X/$f; fi; done
mv $X/j.sh $X/a23/j.sh_a35cf12d && cp -p $N/j.sh $X/j.sh
cd $N/q && for f in $(find . -type f | sed 's#^\./##'); do mkdir -p $X/q/$(dirname $f); cp -p $f $X/q/$f; done
cd $X/q; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q " \*\?\(\./\)\?$f\$" SHA256SUMS.txt || { mkdir -p $X/a23/$(dirname $f); mv $f $X/a23/$f; echo "moved extra $f"; } ;; esac; done
for d in $(find . -name __pycache__); do mv $d $X/a23/pyc_$(date +%s)_$(basename $(dirname $d)); echo "moved $d"; done
sha256sum SHA256SUMS.txt | cut -c1-16; sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK" | head -3; echo "files $(find . -type f | wc -l) pyc $(find . -name __pycache__ | wc -l) lines $(wc -l < SHA256SUMS.txt)"
sha256sum $X/j.sh $X/l.json | cut -c1-16
ls /project/community/jjyeung/okh7/l_94a76bda/in/e00 >/dev/null && cd $X && sbatch $X/j.sh; sleep 5; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
