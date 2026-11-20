export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
squeue -u $USER -h -o "%j" | grep -q f482d730ca91 && { echo QUEUED; exit 1; }
for f in e2.sh:7df901f392c6efc8 e2.py:bf01d22f6aa09115 observe.py:c6def00dd6bb8b57 run.sh:df2d5cf38797f606 k.tgz:130d0ea2ba9337c0 pins.json:0de1c49d2f502b9c; do [ "$(sha256sum e2/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD $f"; exit 1; }; done
sbatch --hold $X/e2/e2.sh; sleep 5; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
