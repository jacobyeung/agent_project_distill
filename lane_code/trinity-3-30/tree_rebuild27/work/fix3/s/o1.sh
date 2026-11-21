X=/project/community/jjyeung/okh7/x_22c714e1
cd $X/o/174101 || exit 1
ls -la >&2
echo "=== q.log tail" >&2
tail -c 5000 q.log >&2
tar czf - RESULT.json q0.json r1.json a6.json receipt.json refresh.json materialization.json q.steps
