set -u
M=/scratch/jjyeung/n30_mirror/b07_offread
echo "== ls"; ls -la $M 2>&1 | head -20
for t in $M/*.tar $M/*/*.tar; do
  [ -f "$t" ] || continue
  echo "-- tar $t $(stat -c %s $t) py_members=$(tar tf $t 2>/dev/null | grep -c '\.py$')"
  for m in $(tar tf $t 2>/dev/null | grep '\.py$'); do
    tar xOf $t "$m" 2>/dev/null | grep -n -I -E "obb|axesLengths|axes_lengths|half_extent|obb_lengths|instances\.json|box_grid|extent" | sed "s#^#EXT $m:#" | cut -c1-220
    tar xOf $t "$m" 2>/dev/null | grep -n -I -E "def [a-z_]*unit|feet|inch|centimet|ground_truth *=|released|convert" | sed "s#^#UNIT $m:#" | cut -c1-220
  done | head -80
done
echo "== loose py"; find $M -maxdepth 5 -name '*.py' 2>/dev/null | wc -l
find $M -maxdepth 5 -name '*.py' 2>/dev/null | xargs -r grep -n -I -E "obb|axesLengths|half_extent|obb_lengths|box_grid" 2>/dev/null | cut -c1-220 | head -20
