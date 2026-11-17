export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; T=b01ec87a6f29b00029ad2
cd $W
sha256sum r2/sj/h10sub3_$T/items.jsonl p446/items/devs1_routed.json r2/sj/h10ret_$T/logs/30.log >&2
tar czf - r2/sj/h10sub3_$T/items.jsonl r2/sj/h10ret_$T/logs/30.log r2/sj/h10ret_$T/metadata/journals/3/0/item_mapping.json r2/sj/h10ret_$T/metadata/journals/3/0/environment.json r2/sj/h10ret_$T/metadata/a/30.json r2/sj/h10ret_$T/metadata/a/5.py p446/items/devs1_routed.json p446/h1eval p446/tree/trace_format p446/8.py p446/9.json p446/orchard_h10 p446/rows/a0_recovery.jsonl p446/rows/ground_fixtures.jsonl p446/rows/mix_h1.py $(cd $W && ls p446/tree/student_pilot/*.py) p446/b/e2e_reader p446/b/heads/selector 2>/dev/null
