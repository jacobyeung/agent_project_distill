cd /project/community/jjyeung/okh7 || exit 1
for d in x_*; do [ -d $d ] || continue; echo "== $d $(du -sh $d 2>/dev/null | cut -f1)"; find $d -maxdepth 2 -printf "%s %p\n" 2>/dev/null | grep -i -E "metric|config|receipt|card|mix|loss|step|\.json|\.jsonl|\.log" | grep -v -E "\.done$" | awk '{printf "  %.2fM %s\n",$1/1e6,$2}' | head -25; done
