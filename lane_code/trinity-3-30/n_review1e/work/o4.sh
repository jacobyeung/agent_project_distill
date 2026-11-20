O=/project/community/jjyeung/okh7/x_22c714e1/o/173680; cd $O || exit 1; date -u +%TZ
for f in routing_selection.json receipt.json materialization.json k_receipt.json k_a0m.json k_b4r.json db_bytes.json timings.json; do echo "@@@ $f $(sha256sum < $f | cut -c1-64)"; cat $f; echo; done
ls -la rd0; sha256sum rd0/* p_sample.json proc_check.json
echo "@@@ summary"; head -c 6000 rd0/rdiff_summary.json; echo
echo "@@@ proc_check"; head -c 3500 proc_check.json; echo
ls -la /project/community/jjyeung/okh7/x_22c714e1/j | tail -5
