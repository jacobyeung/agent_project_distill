R=/scratch/jjyeung/orch_n30
cat >> $R/sb_cachk/prompts/sb_cachk.md <<'X'
## Addendum (coordinator, before launch)
- The builder wrote out/v2/BARS_AMENDMENT.json (sha256 58f29c15..., 11:43:56Z) beside the unchanged BARS_FROZEN.json: judge whether the amendment keeps every bar and was written before any GPU-priced number, and make the guard bind BOTH files (missing or altered amendment refuses as well).
- The kit's revised GPU hours (0.80 / 1.59 / 1.98 / 2.37 / 2.45 h cumulative) mean the 2.0 h stop drops S_GT/A32 and both S_PHR arms. Check the arithmetic and say what hard stop would keep S_PHR/D64 (the phrase-seeded carry arm) and whether S_PHR could be ordered before S_GT/A32 without touching the decision arm (S_A0/D64 first).
X
tail -3 $R/sb_cachk/prompts/sb_cachk.md | cut -c1-80; tail -2 $R/sb_queue/codexq.log; cat $R/sb_queue/queue.txt | tr "\n" " "
